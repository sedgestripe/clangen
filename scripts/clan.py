# pylint: disable=line-too-long
"""

TODO: Docs


"""
# testt
# pylint: enable=line-too-long

import logging
import os
import statistics
from random import choice, choices, randint, getrandbits
from typing import Literal

import i18n
import ujson

from scripts.cat.cats import Cat, cat_class, BACKSTORIES
from scripts.cat.enums import CatRank, CatGroup, CatSocial, CatAge
from scripts.cat_relations.inheritance import Inheritance
from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.enums import CatRank, CatGroup, CatSocial, CatCompatibility
from scripts.cat.factories.new_cat_factory import NewCatFactory
from scripts.cat.factories.enums import CatType
from scripts.cat.names import names
from scripts.cat.save_load import (
    save_cats,
    get_faded_ids,
    load_faded_cat_ids,
    prune_dead_relationships,
)
from scripts.clan_package.clan_names import get_possible_clan_names
from scripts.clan_package.settings import (
    save_clan_settings,
    load_clan_settings,
    get_clan_setting,
)
from scripts.game_structure.game.settings import game_setting_get
from scripts.clan_package.settings.clan_settings import (
    reset_loaded_clan_settings,
    set_clan_setting,
)
from scripts.clan_resources.freshkill import FreshkillPile, Nutrition
from scripts.clan_resources.herb.herb_supply import HerbSupply
from scripts.clan_resources.point_of_interest import (
    load_pois,
    get_poi_save_dict,
    generate_and_add_new_poi,
    PoiType,
    get_poi_names_set,
    clear_pois,
)
from scripts.config import get_config
from scripts.events_module.future.future_event import FutureEvent
from scripts.events_module.generate_events import OngoingEvent
from scripts.game_structure import constants
from scripts.game_structure.game.save_load import safe_save, save_clanlist, read_clans
from scripts.game_structure.game.switches import (
    switch_set_value,
    switch_get_value,
    Switch,
)
from scripts.game_structure import game
from scripts.cat.pelts import Pelt
from scripts.housekeeping.datadir import get_save_dir
from scripts.housekeeping.version import get_version_info, SAVE_VERSION_NUMBER
from scripts.clan_package.clan_symbols import clan_symbol_sprite
from scripts.clan_package.get_clan_cats import (
    get_living_clan_cat_count,
    find_alive_cats_with_rank,
)
from scripts.screens.screens_core.screens_core import rebuild_top_menu_buttons

from scripts.events_module.consequences import create_new_cat
from scripts.clan_package.get_clan_cats import get_possible_mates

logger = logging.getLogger(__name__)


class Clan:
    """

    TODO: Docs

    """

    clan_cats = []

    age = 0
    all_other_clans = []

    grief_strings = {}

    def __init__(
        self,
        save_id="",
        display_name=None,
        leader=None,
        deputy=None,
        medicine_cat=None,
        biome="Forest",
        camp_bg=None,
        rogue_group_bg=None,
        loner_group_bg=None,
        household_bg=None,
        no_group_bg=None,
        symbol=None,
        game_mode="classic",
        cruel_cards: list[str] = None,
        starting_members=None,
        starting_season="Newleaf",
        followingsc=True,
        your_cat=None,
        focus_cat=None,
        clan_age=None,
        starting_size="small",
        self_run_init_functions=True,
    ):
        """
        :param save_id: The save file name for the Clan, this should not be used for player-facing text beyond the save file screen
        :param display_name: The display name for the Clan, this is what should appear while the playing the game.
        """
        if save_id == "":
            return

        if starting_members is None:
            starting_members = []

        self.save_id = save_id
        self.name = display_name if display_name else save_id

        # needs to happen immediately so that any config retrievals will be accurate
        self.cruel_cards: list[str] = cruel_cards if cruel_cards else []
        game.clan = self

        self.leader = leader
        self._leader_lives = 9
        self.leader_predecessors = 0
        self.deputy = deputy
        self.deputy_predecessors = 0
        self.medicine_cat = medicine_cat
        self.med_cat_list = []
        self.med_cat_predecessors = 0

        self.med_cat_number = len(
            self.med_cat_list
        )  # Must do this after the medicine cat is added to the list.
        self.age = 0
        self.starting_season = starting_season
        self.instructor = None
        # ^^ starclan guide

        self.clan_cats = []
        self.biome = biome
        self.override_biome = None
        self.camp_bg = camp_bg

        self.rogue_group_bg = rogue_group_bg
        self.loner_group_bg = loner_group_bg
        self.household_bg = household_bg
        self.no_group_bg = no_group_bg

        self.chosen_symbol = symbol
        self.game_mode = game_mode
        self.pregnancy_data = {}
        self.inheritance = {}
        # NEW LG STUFF
        self.demon = None
        # ^^ dark forest guide
        self.followingsc = followingsc

        self.your_cat = your_cat
        self.murdered = {}
        self.exile_return = False
        self.affair = False
        self.achievements = []
        self.talks = []
        self.focus = ""
        self.focus_moons = 0
        self.focus_cat = focus_cat
        self.clan_age = clan_age if clan_age else "established"
        self.custom_pronouns = {}

        switch_set_value(Switch.biome, biome)

        switch_set_value(Switch.camp_bg, camp_bg)
        switch_set_value(Switch.rogue_group_bg, rogue_group_bg)
        switch_set_value(Switch.loner_group_bg, loner_group_bg)
        switch_set_value(Switch.household_bg, household_bg)
        switch_set_value(Switch.no_group_bg, no_group_bg)

        switch_set_value(Switch.game_mode, game_mode)

        # Reputation is for loners/kittypets/outsiders in general that wish to join the clan.
        # it's a range from 1-100, with 30-70 being neutral, 71-100 being "welcoming",
        # and 1-29 being "hostile". if you're hostile to outsiders, they will VERY RARELY show up.
        self._reputation = get_config(
            "outsiders.starting_reputation",
            creating_clan=True,
            card_list_override=self.cruel_cards,
        )

        self.all_other_clans: list[OtherClan] = []
        self.other_clan_IDs = []

        self.starting_members = starting_members
        if game_mode in ("expanded", "cruel_season"):
            self.freshkill_pile = FreshkillPile()
        else:
            self.freshkill_pile = None
        self.herb_supply = HerbSupply()
        self.primary_disaster = None
        self.secondary_disaster = None
        self.war = {
            "at_war": False,
            "enemy": None,
            "duration": 0,
        }
        self.future_events = []
        self.last_focus_change = None
        self.clans_in_focus = []

        if self_run_init_functions:
            self.post_initialization_functions()
        self.disaster = ""
        self.second_disaster = ""
        self.disaster_moon = 0
        self.second_disaster_moon = 0

        rebuild_top_menu_buttons()

    @property
    def current_season(self):
        season_length = get_config("seasons.length")
        modifiers = {
            season: i * season_length
            for i, season in enumerate(get_config("seasons.calendar"))
        }
        return (
            self.starting_season
            if get_config("seasons.lock_season")
            else constants.SEASON_CALENDAR[
                (self.age + modifiers[self.starting_season]) % 12
            ]
        )

    @property
    def name(self):
        return i18n.t("general.clan", name=self.prefix)

    @name.setter
    def name(self, value):
        self.prefix = value

    @property
    def leader_lives(self):
        return min(self._leader_lives, get_config("death_related.max_leader_lives"))

    @leader_lives.setter
    def leader_lives(self, value):
        self._leader_lives = min(value, get_config("death_related.max_leader_lives"))

    # The clan couldn't save itself in time due to issues arising, for example, from this function: "if deputy is not
    # None: self.deputy.status_change('deputy') -> game.clan.remove_med_cat(self)"
    def post_initialization_functions(self):
        if self.deputy and self.deputy.status.alive_in_player_clan:
            self.deputy.rank_change(CatRank.DEPUTY, new_thought=False)
            self.clan_cats.append(self.deputy.ID)

        if self.leader and self.leader.status.alive_in_player_clan:
            self.leader.rank_change(CatRank.LEADER, new_thought=False)
            self.clan_cats.append(self.leader.ID)

        if self.medicine_cat and self.medicine_cat.status.alive_in_player_clan:
            self.clan_cats.append(self.medicine_cat.ID)
            self.med_cat_list.append(self.medicine_cat.ID)
            if self.medicine_cat.status.rank != CatRank.MEDICINE_CAT:
                Cat.all_cats[self.medicine_cat.ID].rank_change(
                    CatRank.MEDICINE_CAT, new_thought=False
                )

    @property
    def settings(self):
        """DEPRECATED: use get_clan_setting() and set_clan_setting() instead.
        WILL CRASH if you try and use this anyway."""
        import warnings

        warnings.warn(
            "Use get_clan_setting() and set_clan_setting() instead. WILL CRASH if you try and use this anyway.",
            DeprecationWarning,
            2,
        )
        raise Exception(
            "clan.settings has been deprecated, use get_clan_setting() and set_clan_setting() instead. Unrecoverable."
        )

    def create_clan(self, your_cat=None, clan_age="new", unborn=False):
        """
        This function is only called once a new clan is
        created in the 'clan created' screen, not every time
        the program starts
        """
        self.clan_age = clan_age
        game.reset_used_group_IDs()
        switch_set_value(Switch.clan_save_id, self.save_id)
        reset_loaded_clan_settings()
        game.starclan = Afterlife()
        game.dark_forest = Afterlife()
        instructor_rank = choice(
            (
                CatRank.APPRENTICE,
                CatRank.MEDIATOR_APPRENTICE,
                CatRank.MEDICINE_APPRENTICE,
                CatRank.WARRIOR,
                CatRank.MEDICINE_CAT,
                CatRank.LEADER,
                CatRank.MEDIATOR,
                CatRank.DEPUTY,
                CatRank.ELDER,
                CatRank.QUEEN,
                CatRank.QUEENS_APPRENTICE,
            )
        )

        self.instructor = NewCatFactory.create_cat(
            status_dict={"rank": instructor_rank, "group_ID": CatGroup.STARCLAN_ID},
            backstory=choice(
                BACKSTORIES["backstory_categories"]["new_sc_guide_backstories"]
            )
            if self.clan_age == "new"
            else choice(BACKSTORIES["backstory_categories"]["clan_guide_backstories"]),
        )
        self.instructor.dead_for = randint(20, 200)

        self.add_cat(self.instructor)

        self.demon = NewCatFactory.create_cat(
            status_dict={"rank": instructor_rank, "group_ID": CatGroup.DARK_FOREST_ID},
            backstory=choice(
                BACKSTORIES["backstory_categories"]["new_df_guide_backstories"]
            )
            if self.clan_age == "new"
            else choice(BACKSTORIES["backstory_categories"]["df_backstories"]),
        )

        self.demon.dead_for = randint(20, 200)
        self.add_cat(self.demon)
        self.all_other_clans = []

        self.your_cat = your_cat
        if unborn:
            self.your_cat.moons = -1
            self.your_cat.parent1 = None
            self.your_cat.parent2 = None
            self.your_cat.adoptive_parents = []

        self.add_cat(self.your_cat)
        switch_set_value(Switch.cat, None)

        key_copy = tuple(Cat.all_cats.keys())
        for i in key_copy:  # Going through all currently existing cats
            # cat_class is a Cat-object
            not_found = True
            for x in self.starting_members:
                if Cat.all_cats[i] == x:
                    self.add_cat(Cat.all_cats[i])
                    not_found = False
            if (
                Cat.all_cats[i] != self.leader
                and Cat.all_cats[i] != self.medicine_cat
                and Cat.all_cats[i] != self.deputy
                and Cat.all_cats[i] != self.instructor
                and Cat.all_cats[i] != self.demon
                and Cat.all_cats[i] != self.your_cat
                and not_found
            ):
                Cat.all_cats[i].example = True
                self.remove_cat(Cat.all_cats[i].ID)

        number_other_clans = randint(3, 5)
        for _ in range(number_other_clans):
            other_clan = OtherClan()
            self.all_other_clans.append(other_clan)

        # remove any already loaded points of interest
        clear_pois()

        generate_and_add_new_poi(game.clan.biome, PoiType.GATHERING)
        generate_and_add_new_poi(game.clan.biome, PoiType.MOONPLACE)
        for i in range(3):
            generate_and_add_new_poi(game.clan.biome, PoiType.TERRAIN)

        self.save_clan()
        # this has to be done after saving the first time
        # doing this without any previous clans will cause a crash otherwise
        if self.clan_age == "established":
            self.generate_mates()
            self.generate_families()
            self.populate_sc()
            self.populate_ur()
            self.populate_df()
        else:
            self.generate_outsiders()
            self.generate_outsider_mates()
            self.generate_outsider_families()

        self.populate_your_group()

        # give thoughts,actions and relationships to cats
        # LIFEGEN: this is moved down to after we generate outsiders and dead cats
        for cat_id in Cat.all_cats:
            the_cat = Cat.all_cats.get(cat_id)
            the_cat.init_all_relationships()
            if self.clan_age == "new" and the_cat not in (self.instructor, self.demon):
                if the_cat.backstory == "clanborn" and the_cat.status.rank not in (
                    CatRank.KITTEN,
                    CatRank.NEWBORN,
                ):
                    the_cat.backstory = "clan_founder"
            if the_cat.status.rank == CatRank.APPRENTICE:
                the_cat.rank_change(CatRank.APPRENTICE)
            the_cat.get_new_thought()

        # # create leader's ceremony
        # self.leader.generate_lead_ceremony()
        # lifegen commented out

        save_cats(game.clan.save_id, Cat, game)
        self.save_clan()
        save_clanlist(self.save_id)
        switch_set_value(Switch.clan_list, read_clans())

        # CHECK IF CAMP BG IS SET -fail-safe in case it gets set to None-
        # LG: it WILL be set to None if the MC is born outside of it
        if switch_get_value(Switch.camp_bg) is None:
            random_camp_options = ["camp1", "camp2"]
            random_camp = choice(random_camp_options)
            switch_set_value(Switch.camp_bg, random_camp)
        # LG
        if not switch_get_value(Switch.rogue_group_bg):
            switch_set_value(Switch.rogue_group_bg, "camp1")
        if not switch_get_value(Switch.loner_group_bg):
            switch_set_value(Switch.loner_group_bg, "camp1")
        if not switch_get_value(Switch.household_bg):
            switch_set_value(Switch.household_bg, "camp1")
        if not switch_get_value(Switch.no_group_bg):
            switch_set_value(Switch.no_group_bg, "camp1")

        # if no game mode chosen, set to Classic
        if switch_get_value(Switch.game_mode) == "":
            switch_set_value(Switch.game_mode, "classic")
            self.game_mode = "classic"

        # makes sure all the settings are at their starting positions
        self._adjust_settings()

    def generate_mates(self):
        """Generates up to three pairs of mates."""

        def get_adult_mateless_cat():
            alive_cats = [
                i
                for i in Cat.all_cats.values()
                if (i.moons >= 14 and i.status.alive_in_player_clan)
            ]
            if alive_cats:
                return choice(alive_cats)
            return None

        num_mates = randint(0, 3)

        for i in range(num_mates):
            same_age_cats = []
            random_cat = get_adult_mateless_cat()
            if random_cat:
                same_age_cats = get_possible_mates(random_cat)[0]

            if same_age_cats:
                random_mate_cat = choice(same_age_cats)
                if random_cat.is_potential_mate(random_mate_cat):
                    random_cat.set_mate(random_mate_cat)

    def generate_families(self):
        def get_kit_parent():
            alive_cats = [
                i
                for i in Cat.all_cats.values()
                if (i.moons >= 20 and i.moons <= 100 and i.status.alive_in_player_clan)
            ]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return choice(alive_cats)
            return None

        def get_app_parent():
            alive_cats = [
                i
                for i in Cat.all_cats.values()
                if (i.moons >= 40 and i.moons <= 100 and i.status.alive_in_player_clan)
            ]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return choice(alive_cats)
            return None

        clan_kits = find_alive_cats_with_rank(Cat, [CatRank.KITTEN])
        clan_apps = find_alive_cats_with_rank(
            Cat,
            [
                CatRank.APPRENTICE,
                CatRank.MEDICINE_APPRENTICE,
                CatRank.MEDIATOR_APPRENTICE,
                CatRank.QUEENS_APPRENTICE,
            ],
        )

        if not clan_kits and not clan_apps:
            return

        if clan_kits:
            for kit in clan_kits:
                if not kit.inheritance:
                    kit.inheritance = Inheritance(kit)
                if kit.backstory == "clanborn" and not kit.parent1:
                    parent = get_kit_parent()
                    if parent:
                        kit.parent1 = parent.ID
                        parent.inheritance.update_inheritance()

                        if parent.mate:
                            kit.parent2 = choice(parent.mate)
                            if not Cat.all_cats.get(kit.parent2).inheritance:
                                Cat.all_cats.get(kit.parent2).inheritance = Inheritance(
                                    Cat.all_cats.get(kit.parent2)
                                )
                            Cat.all_cats.get(
                                kit.parent2
                            ).inheritance.update_inheritance()

                        for other_kit in clan_kits:
                            if (
                                other_kit.ID != kit.ID
                                and kit.moons == other_kit.moons
                                and not other_kit.parent1
                                and other_kit.backstory == "clanborn"
                            ):
                                other_kit.parent1 = parent.ID
                                parent.inheritance.update_inheritance()
                                if kit.parent2:
                                    other_kit.parent2 = kit.parent2
                                    Cat.all_cats.get(
                                        kit.parent2
                                    ).inheritance.update_inheritance()
                                    if not other_kit.inheritance:
                                        other_kit.inheritance = Inheritance(other_kit)
                kit.inheritance.update_inheritance()

        if clan_apps:
            for app in clan_apps:
                if app.backstory == "clanborn":
                    parent = get_app_parent()
                    if parent:
                        app.parent1 = parent.ID
                        if not app.inheritance:
                            app.inheritance = Inheritance(app)
                        app.inheritance.update_inheritance()
                        parent.inheritance.update_inheritance()
                        if parent.mate:
                            app.parent2 = choice(parent.mate)
                            if not Cat.all_cats.get(app.parent2).inheritance:
                                Cat.all_cats.get(app.parent2).inheritance = Inheritance(
                                    Cat.all_cats.get(app.parent2)
                                )
                            app.inheritance.update_inheritance()
                            Cat.all_cats.get(
                                app.parent2
                            ).inheritance.update_inheritance()

        for cat in Cat.all_cats.values():
            if not cat.inheritance:
                cat.inheritance = Inheritance(cat)
            else:
                cat.inheritance.update_inheritance()

    def populate_sc(self):
        for i in range(randint(2, 5)):
            random_backstory = choice(
                [
                    "dead1",
                    "dead3",
                    "dead4",
                    "dead6",
                    "dead8",
                    "dead10",
                    "dead12",
                    "dead15",
                ]
            )
            sc_cat = create_new_cat(
                Cat,
                new_name=True,
                alive=False,
                backstory=random_backstory,
                original_group=CatGroup.NONE,
            )[0]
            sc_cat.history.beginning = None
            sc_cat.dead_for = randint(20, 200)
            sc_cat.status.add_to_group(CatGroup.STARCLAN_ID)
            sc_cat.history.add_afterlife_acceptance(
                CatGroup.STARCLAN, is_kit=sc_cat.age.is_baby()
            )
            self.add_cat(sc_cat)

    def populate_ur(self):
        for i in range(randint(2, 5)):
            random_backstory = choice(
                [
                    "dead1",
                    "dead2",
                    "dead3",
                    "dead4",
                    "dead5",
                    "dead6",
                    "dead8",
                    "dead9",
                    "dead10",
                    "dead11",
                    "dead12",
                ]
            )
            status = choice([CatRank.LONER, CatRank.KITTYPET])
            ur_cat = create_new_cat(
                Cat,
                rank=status,
                alive=False,
                outside=True,
                backstory=random_backstory,
                original_social=CatSocial.LONER,
            )[0]
            ur_cat.history.beginning = None
            ur_cat.dead_for = randint(20, 100)
            ur_cat.status.add_to_group(CatGroup.UNKNOWN_RESIDENCE_ID)
            self.add_cat(ur_cat)

    def populate_df(self):
        for i in range(randint(2, 5)):
            random_backstory = choice(
                [
                    "dead2",
                    "dead5",
                    "dead7",
                    "dead8",
                    "dead9",
                    "dead11",
                    "dead12",
                    "dead13",
                    "dead14",
                ]
            )
            df_cat = create_new_cat(
                Cat,
                new_name=True,
                alive=False,
                backstory=random_backstory,
                original_group=CatGroup.NONE,
            )[0]
            df_cat.history.beginning = None
            df_cat.dead_for = randint(20, 200)
            df_cat.status.add_to_group(CatGroup.DARK_FOREST_ID)
            df_cat.history.add_afterlife_acceptance(
                CatGroup.DARK_FOREST, is_kit=df_cat.age.is_baby()
            )
            self.add_cat(df_cat)

    def generate_outsiders(self):
        for i in range(randint(0, 5)):
            outsider = create_new_cat(
                Cat,
                moons=randint(15, 120),
                outside=True,
                original_social=choice(
                    (CatSocial.LONER, CatSocial.ROGUE, CatSocial.KITTYPET)
                ),
            )[0]
            outsider.history.beginning = None
            self.add_cat(outsider)

    def generate_outsider_mates(self):
        """Generates up to three pairs of mates."""

        def get_adult_mateless_cat():
            alive_cats = [
                i
                for i in Cat.all_cats.values()
                if i.moons >= 14 and not i.dead and not i.mate
            ]
            if alive_cats:
                return choice(alive_cats)
            return None

        num_mates = randint(0, 3)

        for i in range(num_mates):
            same_age_cats = []
            random_cat = get_adult_mateless_cat()
            if random_cat:
                same_age_cats = get_possible_mates(random_cat)[0]

            if same_age_cats:
                random_mate_cat = choice(same_age_cats)
                if random_cat.is_potential_mate(random_mate_cat):
                    random_cat.set_mate(random_mate_cat)

    def generate_outsider_families(self):
        def get_kit_parent():
            alive_cats = [
                i
                for i in Cat.all_cats.values()
                if i.moons >= 20 and i.moons <= 100 and not i.dead
            ]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return choice(alive_cats)
            return None

        def get_app_parent():
            alive_cats = [
                i
                for i in Cat.all_cats.values()
                if i.moons >= 40 and i.moons <= 100 and not i.dead
            ]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return choice(alive_cats)
            return None

        clan_kits = find_alive_cats_with_rank(Cat, [CatRank.NEWBORN, CatRank.KITTEN])
        clan_apps = find_alive_cats_with_rank(
            Cat,
            [
                CatRank.APPRENTICE,
                CatRank.MEDICINE_APPRENTICE,
                CatRank.MEDIATOR_APPRENTICE,
                CatRank.QUEENS_APPRENTICE,
            ],
        )

        if not clan_kits and not clan_apps:
            return

        if clan_kits:
            for kit in clan_kits:
                if not kit.inheritance:
                    kit.inheritance = Inheritance(kit)
                if kit.ID != game.clan.your_cat.ID and not kit.parent1:
                    parent = get_kit_parent()
                    if parent:
                        kit.parent1 = parent.ID
                        parent.inheritance.update_inheritance()

                        if parent.mate:
                            kit.parent2 = choice(parent.mate)
                            if not Cat.all_cats.get(kit.parent2).inheritance:
                                Cat.all_cats.get(kit.parent2).inheritance = Inheritance(
                                    Cat.all_cats.get(kit.parent2)
                                )
                            Cat.all_cats.get(
                                kit.parent2
                            ).inheritance.update_inheritance()

                        for other_kit in clan_kits:
                            if (
                                other_kit.ID != kit.ID
                                and other_kit.ID != game.clan.your_cat.ID
                                and kit.moons == other_kit.moons
                                and not other_kit.parent1
                            ):
                                other_kit.parent1 = parent.ID
                                parent.inheritance.update_inheritance()
                                if kit.parent2:
                                    other_kit.parent2 = kit.parent2
                                    Cat.all_cats.get(
                                        kit.parent2
                                    ).inheritance.update_inheritance()
                                    if not other_kit.inheritance:
                                        other_kit.inheritance = Inheritance(other_kit)
                kit.inheritance.update_inheritance()

        if clan_apps:
            for app in clan_apps:
                parent = get_app_parent()
                if parent:
                    app.parent1 = parent.ID
                    if not app.inheritance:
                        app.inheritance = Inheritance(app)
                    app.inheritance.update_inheritance()
                    parent.inheritance.update_inheritance()
                    if parent.mate:
                        app.parent2 = choice(parent.mate)
                        if not Cat.all_cats.get(app.parent2).inheritance:
                            Cat.all_cats.get(app.parent2).inheritance = Inheritance(
                                Cat.all_cats.get(app.parent2)
                            )
                        app.inheritance.update_inheritance()
                        Cat.all_cats.get(app.parent2).inheritance.update_inheritance()

    def populate_your_group(self):
        if not game.clan.your_cat:
            return
        group_ID = game.clan.your_cat.status.group_ID

        info_dict = {
            CatGroup.ROGUE_GROUP_ID: {
                "range": [0, 5],
                "social": CatSocial.ROGUE,
                "rank": CatRank.ROGUE,
            },
            CatGroup.LONER_GROUP_ID: {
                "range": [0, 5],
                "social": CatSocial.LONER,
                "rank": CatRank.LONER,
            },
            CatGroup.HOUSEHOLD_ID: {
                "range": [0, 2],
                "social": CatSocial.KITTYPET,
                "rank": CatRank.KITTYPET,
            },
        }

        if group_ID not in info_dict:
            return

        for i in range(
            info_dict[group_ID]["range"][0], info_dict[group_ID]["range"][1]
        ):
            new_cat = create_new_cat(
                Cat,
                rank=info_dict[group_ID]["rank"],
                original_social=info_dict[group_ID]["social"],
                new_name=False,
                outside=True,
            )[0]
            new_cat.history.beginning = None
            self.add_cat(new_cat)
            new_cat.status.add_to_group(group_ID)
            # print("Adding", new_cat.name, "to your group!", new_cat.status.group, game.clan.your_cat.status.group)
            # print(new_cat.ID)

    @staticmethod
    def _adjust_settings():
        """
        Make sure settings are at their starting positions as dictated in the game_config
        """
        # deputy
        if get_config("settings.force_enable.deputy"):
            set_clan_setting("deputy", True)
            save_clan_settings()

        # feeding order
        starting_order = get_config("prey.feeding.starting_order")
        for setting in [
            "low_rank",
            "high_rank",
            "youngest_first",
            "oldest_first",
            "hungriest_first",
            "experience_first",
        ]:
            set_clan_setting(setting, True if starting_order == setting else False)

        # feeding priority
        starting_priority = get_config("prey.feeding.starting_priority")
        for setting in ["hunter_first", "sick_injured_first"]:
            set_clan_setting(setting, True if starting_priority == setting else False)

    def add_cat(self, cat):  # cat is a 'Cat' object
        """Adds cat into the list of clan cats"""
        if cat.ID in Cat.all_cats and cat.ID not in self.clan_cats:
            self.clan_cats.append(cat.ID)

    def remove_cat(self, ID):  # ID is cat.ID
        """
        This function is for completely removing the cat from the game,
        it's not meant for a cat that's simply dead
        """

        if Cat.all_cats[ID] in Cat.all_cats_list:
            Cat.all_cats_list.remove(Cat.all_cats[ID])

        if ID in Cat.all_cats:
            Cat.all_cats.pop(ID)

        if ID in self.clan_cats:
            self.clan_cats.remove(ID)

    def __repr__(self):
        if self.save_id is not None:
            _ = (
                f"{self.save_id}: led by {self.leader.name}"
                f"with {self.medicine_cat.name} as med. cat"
            )
            return _

        else:
            return "No Clan"

    def new_leader(self, leader):
        """
        TODO: DOCS
        """

        if leader:
            leader.generate_lead_ceremony()
            self.leader = leader
            Cat.all_cats[leader.ID].rank_change(CatRank.LEADER)
            self.leader_predecessors += 1
            self.leader_lives = 9

        # todo: this leads nowhere, can it be deleted?
        switch_set_value(Switch.new_leader, None)

    def new_deputy(self, deputy):
        """
        TODO: DOCS
        """
        if deputy:
            self.deputy = deputy
            Cat.all_cats[deputy.ID].rank_change(CatRank.DEPUTY)
            self.deputy_predecessors += 1

    def new_medicine_cat(self, medicine_cat):
        """
        TODO: DOCS
        """
        if medicine_cat:
            if medicine_cat.status.rank != CatRank.MEDICINE_CAT:
                Cat.all_cats[medicine_cat.ID].rank_change(CatRank.MEDICINE_CAT)
            if medicine_cat.ID not in self.med_cat_list:
                self.med_cat_list.append(medicine_cat.ID)
            medicine_cat = self.med_cat_list[0]
            self.medicine_cat = Cat.all_cats[medicine_cat]
            self.med_cat_number = len(self.med_cat_list)

    def remove_med_cat(self, medicine_cat):
        """
        Removes a med cat. Use when retiring, or switching to warrior
        """
        if medicine_cat:
            if medicine_cat.ID in game.clan.med_cat_list:
                game.clan.med_cat_list.remove(medicine_cat.ID)
                game.clan.med_cat_number = len(game.clan.med_cat_list)
            if self.medicine_cat:
                if medicine_cat.ID == self.medicine_cat.ID:
                    if game.clan.med_cat_list:
                        game.clan.medicine_cat = Cat.fetch_cat(
                            game.clan.med_cat_list[0]
                        )
                        game.clan.med_cat_number = len(game.clan.med_cat_list)
                    else:
                        game.clan.medicine_cat = None

    @staticmethod
    def switch_clans(clan, save=True):
        """
        TODO: DOCS
        """
        if save:
            save_clanlist(clan, True)
        else:
            save_clanlist(clan)
        switch_set_value(Switch.switch_clan, True)

    def save_clan(self):
        """
        TODO: DOCS
        """

        clan_data = {
            "save_id": self.save_id,
            "displayname": self.prefix,
            "clanage": self.age,
            "biome": self.biome,
            "camp_bg": self.camp_bg,
            "rogue_group_bg": self.rogue_group_bg,
            "loner_group_bg": self.loner_group_bg,
            "household_bg": self.household_bg,
            "no_group_bg": self.no_group_bg,
            "clan_symbol": self.chosen_symbol,
            "gamemode": self.game_mode,
            "cruel_cards": self.cruel_cards,
            "used_group_IDs": game.used_group_IDs,
            "last_focus_change": self.last_focus_change,
            "clans_in_focus": self.clans_in_focus,
            "instructor": self.instructor.ID,
            "demon": self.demon.ID,
            "reputation": self.reputation,
            "following_starclan": self.followingsc,
            "mediated": game.mediated,
            "told_story": game.told_story,
            "starting_season": self.starting_season,
            "temperament": self.temperament,
            "just_died": game.just_died,
            "dead_cats_to_grieve": [x.ID for x in game.dead_cats_to_grieve if x],
            "grief_to_assign": game.clan.grief_strings,
            "version_name": SAVE_VERSION_NUMBER,
            "version_commit": get_version_info().version_number,
            "source_build": get_version_info().is_source_build,
            "murdered": self.murdered,
            "exile_return": self.exile_return,
            "affair": self.affair,
            "custom_pronouns": self.custom_pronouns,
            "clan_age": self.clan_age,
        }

        # LEADER DATA
        if self.leader:
            clan_data["leader"] = self.leader.ID
            clan_data["leader_lives"] = self.leader_lives
        else:
            clan_data["leader"] = None

        clan_data["leader_predecessors"] = self.leader_predecessors

        # DEPUTY DATA
        if self.deputy:
            clan_data["deputy"] = self.deputy.ID
        else:
            clan_data["deputy"] = None

        clan_data["deputy_predecessors"] = self.deputy_predecessors

        # MED CAT DATA
        if self.medicine_cat:
            clan_data["med_cat"] = self.medicine_cat.ID
        else:
            clan_data["med_cat"] = None
        clan_data["med_cat_number"] = self.med_cat_number
        clan_data["med_cat_predecessors"] = self.med_cat_predecessors

        # YOUR CAT DATA
        if self.your_cat:
            clan_data["your_cat"] = self.your_cat.ID
        else:
            alive_clan_cats = [
                x for x in Cat.all_cats_list if x.status.alive_in_player_clan
            ]
            clan_data["your_cat"] = (
                choice(alive_clan_cats).ID if alive_clan_cats else None
            )

        if self.focus_cat:
            clan_data["focus_cat"] = self.focus_cat.ID
        else:
            clan_data["focus_cat"] = None

        # LIST OF CLAN CATS
        clan_data["clan_cats"] = ",".join([str(i) for i in self.clan_cats])

        clan_data["faded_cats"] = ",".join([str(i) for i in get_faded_ids()])

        # Patrolled cats
        clan_data["patrolled_cats"] = [str(i) for i in game.patrolled]

        # OTHER CLANS
        clan_data["other_clans"] = [i.save_info() for i in self.all_other_clans]

        clan_data["war"] = self.war
        clan_data["achievements"] = self.achievements
        clan_data["talks"] = self.talks
        clan_data["disaster"] = self.disaster
        clan_data["disaster_moon"] = self.disaster_moon
        clan_data["focus"] = self.focus
        clan_data["focus_moons"] = self.focus_moons

        clan_data["poi"] = get_poi_save_dict()

        self.save_herb_supply(game.clan)
        self.save_disaster(game.clan)
        self.save_future_events(game.clan)
        self.save_pregnancy(game.clan)

        save_clan_settings()
        if game.clan.game_mode in ("expanded", "cruel_season"):
            self.save_freshkill_pile(game.clan)

        safe_save(f"{get_save_dir()}/{self.save_id}/clan.json", clan_data)

        if os.path.exists(f"{get_save_dir()}/{self.save_id}clan.json"):
            os.remove(f"{get_save_dir()}/{self.save_id}clan.json")
        elif os.path.exists(get_save_dir() + f"/{self.save_id}clan.txt") & (
            self.save_id != "current"
        ):
            os.remove(get_save_dir() + f"/{self.save_id}clan.txt")

    def load_clan(self):
        """
        TODO: DOCS
        """

        version_info = None
        game.reset_used_group_IDs()
        if os.path.exists(
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "clan.json"
        ) or os.path.exists(
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "/clan.json"
        ):
            version_info = self.load_clan_json()
        elif os.path.exists(
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "clan.txt"
        ):
            self.load_clan_txt()
        else:
            switch_set_value(
                Switch.error_message, "There was an error loading the clan.json"
            )

        # can't put this in post initialization bc guide isn't made before that func
        self.add_guide_influence()
        load_clan_settings()

        return version_info

    @staticmethod
    def add_guide_influence():
        """
        Adds guide's facet influences to their current afterlife
        """
        if game.clan.instructor.status.group == CatGroup.STARCLAN:
            game.starclan.adjust_facets_by_cat(game.clan.instructor)
        elif game.clan.instructor.status.group == CatGroup.DARK_FOREST:
            game.dark_forest.adjust_facets_by_cat(game.clan.instructor)

    def load_clan_txt(self):
        """
        TODO: DOCS
        """

        if not switch_get_value(Switch.clan_list):
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_other_clans.append(OtherClan())
            return
        if switch_get_value(Switch.clan_list)[0].strip() == "":
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_other_clans.append(OtherClan())
            return
        switch_set_value(
            Switch.error_message, "There was an error loading the clan.txt"
        )
        with open(
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "clan.txt",
            "r",
            encoding="utf-8",
        ) as read_file:  # pylint: disable=redefined-outer-name
            clan_data = read_file.read()
        clan_data = clan_data.replace("\t", ",")
        sections = clan_data.split("\n")
        if len(sections) == 8:
            general = sections[0].split(",")
            leader_info = sections[1].split(",")
            deputy_info = sections[2].split(",")
            med_cat_info = sections[3].split(",")
            instructor_info = sections[4]
            members = sections[5].split(",")
            demon_info = sections[6]
            other_clans = []
        elif len(sections) == 7:
            general = sections[0].split(",")
            leader_info = sections[1].split(",")
            deputy_info = sections[2].split(",")
            med_cat_info = sections[3].split(",")
            instructor_info = sections[4]
            members = sections[5].split(",")
            demon_info = sections[6]
            other_clans = []
        else:
            general = sections[0].split(",")
            leader_info = sections[1].split(",")
            deputy_info = 0, 0
            med_cat_info = sections[2].split(",")
            instructor_info = sections[3]
            members = sections[4].split(",")
            demon_info = sections[5]
            other_clans = []
        if len(general) == 9:
            if general[3] == "None":
                general[3] = "camp1"
            elif general[4] == "None":
                general[4] = 0
            elif general[7] == "None":
                general[7] = "classic"
            elif general[8] == "None":
                general[8] = 50
            game.clan = Clan(
                save_id=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                camp_bg=general[3],
                game_mode=general[7],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
            game.clan.reputation = general[8]
        elif len(general) == 8:
            if general[3] == "None":
                general[3] = "camp1"
            elif general[4] == "None":
                general[4] = 0
            elif general[7] == "None":
                general[7] = "classic"
            game.clan = Clan(
                save_id=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                camp_bg=general[3],
                game_mode=general[7],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        elif len(general) == 7:
            if general[4] == "None":
                general[4] = 0
            elif general[3] == "None":
                general[3] = "camp1"
            game.clan = Clan(
                save_id=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                camp_bg=general[3],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        elif len(general) == 3:
            game.clan = Clan(
                save_id=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        else:
            game.clan = Clan(
                general[0],
                Cat.all_cats[leader_info[0]],
                Cat.all_cats.get(deputy_info[0], None),
                Cat.all_cats.get(med_cat_info[0], None),
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        game.clan.age = int(general[1])
        game.clan.leader_lives, game.clan.leader_predecessors = int(
            leader_info[1]
        ), int(leader_info[2])

        if len(deputy_info) > 1:
            game.clan.deputy_predecessors = int(deputy_info[1])
        if len(med_cat_info) > 1:
            game.clan.med_cat_predecessors = int(med_cat_info[1])
        if len(med_cat_info) > 2:
            game.clan.med_cat_number = int(med_cat_info[2])
        if len(sections) > 4:
            if instructor_info in Cat.all_cats:
                game.clan.instructor = Cat.all_cats[instructor_info]
                game.clan.add_cat(game.clan.instructor)
        else:
            game.clan.instructor = NewCatFactory.create_cat(
                status_dict={
                    "rank": choice(
                        (CatRank.WARRIOR, CatRank.WARRIOR, CatRank.QUEEN, CatRank.ELDER)
                    ),
                    "group": CatGroup.STARCLAN,
                },
            )
            # update_sprite(game.clan.instructor)
            game.clan.instructor.dead = True
            game.clan.add_cat(game.clan.instructor)

        if len(sections) > 4:
            if demon_info in Cat.all_cats:
                game.clan.demon = Cat.all_cats[demon_info]
                game.clan.add_cat(game.clan.demon)
            else:
                game.clan.demon = NewCatFactory.create_cat(
                    status_dict={
                        "rank": choice(
                            (
                                CatRank.WARRIOR,
                                CatRank.WARRIOR,
                                CatRank.QUEEN,
                                CatRank.ELDER,
                            )
                        ),
                        "group": CatGroup.DARK_FOREST,
                    },
                )
                game.clan.demon.dead = True
                game.clan.add_cat(game.clan.demon)
        else:
            game.clan.demon = NewCatFactory.create_cat(
                status_dict={
                    "rank": choice((CatRank.WARRIOR, CatRank.WARRIOR, CatRank.ELDER)),
                    "group_ID": CatGroup.DARK_FOREST_ID,
                }
            )
            # update_sprite(game.clan.demon)
            game.clan.demon.dead = True
            game.clan.add_cat(game.clan.demon)

        if other_clans != [""]:
            for other_clan in other_clans:
                other_clan_info = other_clan.split(";")
                self.all_other_clans.append(
                    OtherClan(
                        other_clan_info[0], int(other_clan_info[1]), other_clan_info[2]
                    )
                )

        else:
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_other_clans.append(OtherClan())

        missing_cats = []
        for cat in members:
            if cat in Cat.all_cats:
                game.clan.add_cat(Cat.all_cats[cat])
            else:
                missing_cats.append(cat)
        if missing_cats:
            error = ValueError(
                f"clan.txt references {len(missing_cats)} cat(s) missing from "
                f"the cat file: {', '.join(missing_cats)}"
            )
            switch_set_value(
                Switch.error_message,
                "Some cats in this save could not be loaded! Please check the cat file for missing cats.",
            )
            switch_set_value(Switch.traceback, error)
            raise error
        self.load_pregnancy(game.clan)

        # assigning a symbol, since this save would be too old to have a chosen symbol
        game.clan.chosen_symbol = clan_symbol_sprite(game.clan, return_string=True)

        switch_set_value(Switch.error_message, "")

    def load_clan_json(self):
        """
        TODO: DOCS
        """
        if not switch_get_value(Switch.clan_list):
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_other_clans.append(OtherClan())
            return
        if switch_get_value(Switch.clan_list)[0].strip() == "":
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_other_clans.append(OtherClan())
            return

        switch_set_value(
            Switch.error_message, "There was an error loading the clan.json"
        )
        filename = (
            get_save_dir() + "/" + switch_get_value(Switch.clan_list)[0] + "/clan.json"
        )
        if not os.path.exists(filename):
            # legacy
            filename = (
                get_save_dir()
                + "/"
                + switch_get_value(Switch.clan_list)[0]
                + "clan.json"
            )
        with open(
            filename,
            "r",
            encoding="utf-8",
        ) as read_file:  # pylint: disable=redefined-outer-name
            clan_data = ujson.loads(read_file.read())

        # LG
        your_cat = None
        if clan_data["your_cat"]:
            your_cat = Cat.all_cats.get(clan_data["your_cat"])
        if your_cat is None:
            print("You don't have a cat! Choosing one for you...")
            candidates = [
                x for x in Cat.all_cats_list if x.status.alive_in_your_cat_group
            ]
            if candidates:
                your_cat = choice(candidates)
                print(f"Hello, {your_cat.name}!")
            else:
                print("No eligible cat found to assign as your_cat.")

        if clan_data["leader"]:
            leader = Cat.all_cats[clan_data["leader"]]
            leader_lives = clan_data["leader_lives"]
        else:
            leader = None
            leader_lives = 0

        if clan_data["deputy"]:
            deputy = Cat.all_cats[clan_data["deputy"]]
        else:
            deputy = None

        if clan_data["med_cat"]:
            med_cat = Cat.all_cats[clan_data["med_cat"]]
        else:
            med_cat = None

        # just checking if old param name is being used
        save_id = (
            clan_data.get("clanname")
            if clan_data.get("clanname")
            else clan_data.get("save_id")
        )

        # remove any already loaded points of interest
        clear_pois()

        load_pois(clan_data.get("poi", {"empty": []}))

        game.clan = Clan(
            save_id=save_id,
            display_name=clan_data.get(
                "displayname", None
            ),  # if no displayname is found, clan init just uses save_id
            leader=leader,
            deputy=deputy,
            your_cat=your_cat,
            medicine_cat=med_cat,
            biome=clan_data["biome"],
            camp_bg=clan_data["camp_bg"],
            rogue_group_bg=clan_data["rogue_group_bg"]
            if "rogue_group_bg" in clan_data
            else "camp1",
            loner_group_bg=clan_data["loner_group_bg"]
            if "loner_group_bg" in clan_data
            else "camp1",
            household_bg=clan_data["household_bg"]
            if "household_bg" in clan_data
            else "camp1",
            no_group_bg=clan_data["no_group_bg"]
            if "no_group_bg" in clan_data
            else "camp1",
            game_mode=clan_data["gamemode"],
            cruel_cards=[
                c
                for c in clan_data.get("cruel_cards", [])
                if c in constants.CRUEL_CARDS_ALL
            ],
            self_run_init_functions=False,
        )
        game.clan.post_initialization_functions()

        # LG
        if "following_starclan" in clan_data:
            game.clan.followingsc = clan_data["following_starclan"]
        else:
            game.clan.followingsc = True
        # ---

        # LG: loading used IDs used to be here, but its moved below other_clans loading now

        game.clan.reputation = clan_data["reputation"]

        game.clan.age = clan_data["clanage"]
        game.clan.starting_season = (
            clan_data["starting_season"]
            if "starting_season" in clan_data
            else "Newleaf"
        )
        game.clan.leader_lives = leader_lives
        game.clan.leader_predecessors = clan_data["leader_predecessors"]

        game.clan.deputy_predecessors = clan_data["deputy_predecessors"]
        game.clan.med_cat_predecessors = clan_data["med_cat_predecessors"]
        game.clan.med_cat_number = clan_data["med_cat_number"]
        # Allows for the custom pronouns to show up in the add pronoun list after the game has closed and reopened.
        if "custom_pronouns" in clan_data.keys():
            if clan_data["custom_pronouns"]:
                if isinstance(clan_data["custom_pronouns"], list):
                    # english-only pronouns from an old version
                    game.clan.custom_pronouns["en"] = clan_data["custom_pronouns"]
                else:
                    game.clan.custom_pronouns = clan_data["custom_pronouns"]

        # Instructor Info
        if clan_data["instructor"] in Cat.all_cats:
            game.clan.instructor = Cat.all_cats[clan_data["instructor"]]
            game.clan.add_cat(game.clan.instructor)
        else:
            game.clan.instructor = NewCatFactory.create_cat(
                status_dict={
                    "rank": choice((CatRank.WARRIOR, CatRank.WARRIOR, CatRank.ELDER)),
                    "group": CatGroup.STARCLAN,
                },
            )
            # update_sprite(game.clan.instructor)
            game.clan.instructor.dead = True
            game.clan.add_cat(game.clan.instructor)

        # demon Info
        if "demon" in clan_data and clan_data["demon"] in Cat.all_cats:
            game.clan.demon = Cat.all_cats[clan_data["demon"]]
            game.clan.add_cat(game.clan.demon)
            game.clan.demon.df = True
        else:
            game.clan.demon = NewCatFactory.create_cat(
                status_dict={
                    "rank": choice((CatRank.WARRIOR, CatRank.WARRIOR, CatRank.ELDER)),
                    "group_ID": CatGroup.DARK_FOREST_ID,
                }
            )
            game.clan.demon.dead = True
            game.clan.add_cat(game.clan.demon)
            game.clan.demon.df = True

        ##Commented this out because I don't know why it's in here twice. If lead/dep/med stuff starts sobbing... ye ##
        # game.clan.leader_lives = leader_lives
        # game.clan.leader_predecessors = clan_data["leader_predecessors"]

        # game.clan.deputy_predecessors = clan_data["deputy_predecessors"]
        # game.clan.med_cat_predecessors = clan_data["med_cat_predecessors"]
        # game.clan.med_cat_number = clan_data["med_cat_number"]

        # check for symbol
        if "clan_symbol" in clan_data:
            game.clan.chosen_symbol = clan_data["clan_symbol"]
        else:
            game.clan.chosen_symbol = clan_symbol_sprite(game.clan, return_string=True)

        if "other_clans" in clan_data:
            for other_clan in clan_data["other_clans"]:
                if not other_clan.get("group_ID"):
                    ID = game.get_free_group_ID(CatGroup.OTHER_CLAN)
                else:
                    ID = other_clan["group_ID"]
                game.clan.all_other_clans.append(
                    OtherClan(
                        name=other_clan.get("prefix", other_clan.get("name")),
                        relations=int(other_clan["relations"]),
                        temperament=other_clan["temperament"],
                        chosen_symbol=other_clan["chosen_symbol"],
                        ID=ID,
                    )
                )
        else:
            if "other_clan_chosen_symbol" not in clan_data:
                for name, relation, temper in zip(
                    clan_data["other_clans_names"].split(","),
                    clan_data["other_clans_relations"].split(","),
                    clan_data["other_clan_temperament"].split(","),
                ):
                    game.clan.all_other_clans.append(
                        OtherClan(name, int(relation), temper)
                    )
            else:
                for name, relation, temper, symbol in zip(
                    clan_data["other_clans_names"].split(","),
                    clan_data["other_clans_relations"].split(","),
                    clan_data["other_clan_temperament"].split(","),
                    clan_data["other_clan_chosen_symbol"].split(","),
                ):
                    game.clan.all_other_clans.append(
                        OtherClan(name, int(relation), temper, symbol)
                    )

        # LG
        # MOVED HERE
        if clan_data.get("used_group_IDs"):
            game.used_group_IDs = clan_data["used_group_IDs"]

            # LG
            # correct for new lifegen groups
            if game.used_group_IDs["5"] != CatGroup.ROGUE_GROUP:
                game.used_group_IDs["5"] = CatGroup.ROGUE_GROUP
            if game.used_group_IDs["6"] != CatGroup.LONER_GROUP:
                game.used_group_IDs["6"] = CatGroup.LONER_GROUP
            if game.used_group_IDs["7"] != CatGroup.HOUSEHOLD:
                game.used_group_IDs["7"] = CatGroup.HOUSEHOLD

            # fix clan IDs. so otherclans with 5, 6, or 7 as their id will move down the list
            # to make room for the above ones ^^
            count = 0
            for other_clan in game.clan.all_other_clans:
                count += 1
                if (
                    other_clan.group_ID in game.used_group_IDs
                    and game.used_group_IDs[other_clan.group_ID] != other_clan
                ):
                    # generate the new ID. adds to the last number in the existing list (7)
                    new_group_id = 7 + count
                    other_clan.group_ID = str(new_group_id)

                    # now add to game used IDs
                    game.used_group_IDs.update({str(new_group_id): CatGroup.OTHER_CLAN})

            self.convert_group_IDs()
            # ---

            for ID in game.used_group_IDs:
                game.used_group_IDs[ID] = CatGroup(game.used_group_IDs[ID])
        # ---

        missing_cats = []
        for cat in clan_data["clan_cats"].split(","):
            if cat in Cat.all_cats:
                game.clan.add_cat(Cat.all_cats[cat])
            else:
                missing_cats.append(cat)
        if missing_cats:
            error = ValueError(
                f"clan.json references {len(missing_cats)} cat(s) missing from "
                f"clan_cats.json: {', '.join(missing_cats)}"
            )
            switch_set_value(
                Switch.error_message,
                "Some cats in this save could not be loaded! Please check the cat file for missing cats.",
            )
            switch_set_value(Switch.traceback, error)
            raise error
        if "war" in clan_data:
            game.clan.war = clan_data["war"]

        load_faded_cat_ids(clan_data["clanname"])

        prune_dead_relationships(Cat)

        game.clan.last_focus_change = clan_data.get("last_focus_change")
        game.clan.clans_in_focus = clan_data.get("clans_in_focus", [])

        # Patrolled cats
        if "patrolled_cats" in clan_data:
            game.patrolled = clan_data["patrolled_cats"]

        if "dated_cats" in clan_data:
            game.dated_cats = clan_data["dated_cats"]

        # Mediated flag
        if "mediated" in clan_data:
            if not isinstance(clan_data["mediated"], list):
                game.mediated = []
            else:
                game.mediated = clan_data["mediated"]
        # LG: story flag
        if "told_story" in clan_data:
            if not isinstance(clan_data["told_story"], list):
                game.told_story = []
            else:
                game.told_story = clan_data["told_story"]

        game.clan.clan_age = (
            clan_data["clan_age"] if "clan_age" in clan_data else "established"
        )

        # Cat who had just died
        if "just_died" in clan_data:
            game.just_died = clan_data["just_died"]

        # Cats who need to be grieved
        if "dead_cats_to_grieve" in clan_data:
            game.dead_cats_to_grieve = [
                cat
                for x in clan_data["dead_cats_to_grieve"]
                if (cat := Cat.fetch_cat(x))
            ]

        # Cats who are gonna grieve
        if "grief_to_assign" in clan_data:
            game.clan.grief_strings = clan_data["grief_to_assign"]

        self.load_pregnancy(game.clan)
        self.load_herb_supply(game.clan)
        self.load_future_events(game.clan)
        self.load_disaster(game.clan)
        self.load_accessories()
        if game.clan.game_mode != "classic":
            self.load_freshkill_pile(game.clan)

        if "murdered" in clan_data:
            if isinstance(clan_data["murdered"], bool):
                game.clan.murdered = {}
            else:
                game.clan.murdered = clan_data["murdered"]

        if "affair" in clan_data:
            game.clan.affair = clan_data["affair"]

        if "exile_return" in clan_data:
            game.clan.exile_return = clan_data["exile_return"]

        if "achievements" in clan_data:
            achievement_list = []
            for item in clan_data["achievements"]:
                if not isinstance(item, list):
                    achievement_list.append([item, game.clan.your_cat.ID])
                else:
                    achievement_list.append(item)

            game.clan.achievements = achievement_list

        if "talks" in clan_data:
            game.clan.talks = clan_data["talks"]

        if "disaster" in clan_data:
            game.clan.disaster = clan_data["disaster"]

        if "disaster_moon" in clan_data:
            game.clan.disaster_moon = clan_data["disaster_moon"]

        if "focus" in clan_data:
            game.clan.focus = clan_data["focus"]

        if "focus_moons" in clan_data:
            game.clan.focus_moons = clan_data["focus_moons"]

        if "focus_cat" in clan_data:
            if clan_data["focus_cat"] is None:
                game.clan.focus_cat = None
            else:
                game.clan.focus_cat = Cat.all_cats[clan_data["focus_cat"]]

        switch_set_value(Switch.error_message, "")

        # Return Version Info.
        return {
            "version_name": clan_data.get("version_name"),
            "version_commit": clan_data.get("version_commit"),
            "source_build": clan_data.get("source_build"),
        }

    def convert_group_IDs(self):
        """
        LIFEGEN FUNCTION
        existing otherclan cats will now get a new group ID
        so otherclan cats from old saves dont randomly join rogue groups and stuff
        """

        for cat in Cat.all_cats_list:
            for group_ID in ["5", "6", "7"]:
                if cat.status.rank.is_any_clancat_rank():
                    for group in cat.status.standing_history.copy():
                        if group["group"] == group_ID:
                            index = cat.status.standing_history.index(group)
                            cat.status.standing_history.remove(group)

                            new_standing_block = {
                                "group": "8",
                                "standing": group["standing"],
                                "near": group["near"],
                            }
                            cat.status.standing_history.insert(
                                index, new_standing_block
                            )
                    for group in cat.status.group_history.copy():
                        if group["group"] == group_ID:
                            index = cat.status.group_history.index(group)
                            cat.status.group_history.remove(group)

                            new_group_block = {
                                "group": "8",
                                "rank": group["rank"],
                                "moons_as": group["moons_as"],
                            }
                            cat.status.group_history.insert(index, new_group_block)

    def load_accessories(self):
        """
        loads all accessories for cat inventories
        when all accessories is toggled on
        """
        if get_clan_setting("all accessories"):
            for cat in Cat.all_cats_list:
                if game_setting_get("lifegen_sprite_changes"):
                    acc_list = Pelt.all_lifegen_accessories
                else:
                    acc_list = Pelt.all_clangen_accessories

                if "NOTAIL" in cat.pelt.scars or "HALFTAIL" in cat.pelt.scars:
                    for acc in Pelt.tail_accessories:
                        if acc in acc_list:
                            try:
                                acc_list.remove(acc)
                            except ValueError:
                                print(
                                    f"attempted to remove {acc} from possible acc list, but it was not in the list!"
                                )
                # LG
                if "NOPAW" in cat.pelt.scars:
                    for acc in Pelt.paw_accessories:
                        if acc in acc_list:
                            try:
                                acc_list.remove(acc)
                            except ValueError:
                                print(
                                    f"attempted to remove {acc} from possible acc list, but it was not in the list!"
                                )
                return acc_list

    def load_pregnancy(self, clan):
        """
        Load the information about what cat is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.clan.save_id:
            return
        file_path = get_save_dir() + f"/{game.clan.save_id}/pregnancy.json"
        if os.path.exists(file_path):
            with open(
                file_path, "r", encoding="utf-8"
            ) as read_file:  # pylint: disable=redefined-outer-name
                clan.pregnancy_data = ujson.load(read_file)
        else:
            clan.pregnancy_data = {}

    def save_pregnancy(self, clan):
        """
        Save the information about what cat is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.clan.save_id:
            return

        safe_save(
            f"{get_save_dir()}/{game.clan.save_id}/pregnancy.json", clan.pregnancy_data
        )

    def load_disaster(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.save_id:
            return

        file_path = get_save_dir() + f"/{game.clan.save_id}/disasters/primary.json"
        try:
            if os.path.exists(file_path):
                with open(
                    file_path, "r", encoding="utf-8"
                ) as read_file:  # pylint: disable=redefined-outer-name
                    disaster = ujson.load(read_file)
                    if disaster:
                        clan.primary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=(
                                disaster["current_duration"]
                                if "current_duration" in disaster
                                else disaster["duration"]
                            ),
                            trigger_events=disaster["trigger_events"],
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            secondary_disasters=disaster["secondary_disasters"],
                            collateral_damage=disaster["collateral_damage"],
                        )
                    else:
                        clan.primary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.clan.save_id}/disasters")
                clan.primary_disaster = None
                with open(file_path, "w", encoding="utf-8") as rel_file:
                    json_string = ujson.dumps(clan.primary_disaster, indent=4)
                    rel_file.write(json_string)
        except Exception:
            logger.exception("Failed to load primary disaster; clearing it.")
            clan.primary_disaster = None

        file_path = get_save_dir() + f"/{game.clan.save_id}/disasters/secondary.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as read_file:
                    disaster = ujson.load(read_file)
                    if disaster:
                        clan.secondary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=(
                                disaster["current_duration"]
                                if "current_duration" in disaster
                                else disaster["duration"]
                            ),
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            collateral_damage=disaster["collateral_damage"],
                        )
                    else:
                        clan.secondary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.clan.save_id}/disasters")
                clan.secondary_disaster = None
                with open(file_path, "w", encoding="utf-8") as rel_file:
                    json_string = ujson.dumps(clan.secondary_disaster, indent=4)
                    rel_file.write(json_string)

        except Exception:
            logger.exception("Failed to load secondary disaster; clearing it.")
            clan.secondary_disaster = None

    def save_disaster(self, clan=game.clan):
        """
        TODO: DOCS
        """
        if not clan.save_id:
            return
        file_path = get_save_dir() + f"/{clan.save_id}/disasters/primary.json"
        if not os.path.isdir(f"{get_save_dir()}/{clan.save_id}/disasters"):
            os.mkdir(f"{get_save_dir()}/{clan.save_id}/disasters")
        if clan.primary_disaster:
            disaster = {
                "event": clan.primary_disaster.event,
                "tags": clan.primary_disaster.tags,
                "duration": clan.primary_disaster.duration,
                "current_duration": clan.primary_disaster.current_duration,
                "trigger_events": clan.primary_disaster.trigger_events,
                "progress_events": clan.primary_disaster.progress_events,
                "conclusion_events": clan.primary_disaster.conclusion_events,
                "secondary_disasters": clan.primary_disaster.secondary_disasters,
                "collateral_damage": clan.primary_disaster.collateral_damage,
            }
        else:
            disaster = {}

        safe_save(f"{get_save_dir()}/{clan.save_id}/disasters/primary.json", disaster)

        if clan.secondary_disaster:
            disaster = {
                "event": clan.secondary_disaster.event,
                "tags": clan.secondary_disaster.tags,
                "duration": clan.secondary_disaster.duration,
                "current_duration": clan.secondary_disaster.current_duration,
                "trigger_events": clan.secondary_disaster.trigger_events,
                "progress_events": clan.secondary_disaster.progress_events,
                "conclusion_events": clan.secondary_disaster.conclusion_events,
                "secondary_disasters": clan.secondary_disaster.secondary_disasters,
                "collateral_damage": clan.secondary_disaster.collateral_damage,
            }
        else:
            disaster = {}

        safe_save(f"{get_save_dir()}/{clan.save_id}/disasters/secondary.json", disaster)

    def load_future_events(self, clan):
        """
        Loads the Clan's saved future events
        """
        if not game.clan.save_id:
            return

        # load the current file path, if it exists in save
        file_path = f"{get_save_dir()}/{game.clan.save_id}/future_events.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as save_file:
                save_list = ujson.load(save_file)
                for event in save_list:
                    try:
                        game.clan.future_events.append(
                            FutureEvent(
                                parent_event=event["parent_event"],
                                event_type=event["event_type"],
                                pool=event["pool"],
                                moon_delay=event["moon_delay"],
                                involved_cats=event["involved_cats"],
                            )
                        )
                    except KeyError:
                        print(
                            f"WARNING: A saved future event was missing information and was not loaded. event: {event}"
                        )
                        continue

    def save_future_events(self, clan):
        """
        saves the Clan's current future events
        """
        save_list = []

        for event in game.clan.future_events:
            save_list.append(event.to_dict())

        safe_save(f"{get_save_dir()}/{game.clan.save_id}/future_events.json", save_list)

    def load_herb_supply(self, clan):
        """
        Loads the Clan's saved herb supply info
        """
        if not game.clan.save_id:
            return

        save_dir = get_save_dir()

        current_file_path = save_dir + f"/{game.clan.save_id}/herb_supply.json"
        old_file_path = save_dir + f"/{game.clan.save_id}/herbs.json"

        try:
            # load the old file path and convert the save data into current format
            if os.path.exists(old_file_path):
                with open(old_file_path, "r", encoding="utf-8") as save_file:
                    herbs = ujson.load(save_file)
                    clan.herb_supply = HerbSupply()
                    clan.herb_supply.convert_old_save(herbs)

            # load the current file path, if it exists in save
            elif os.path.exists(current_file_path):
                with open(current_file_path, "r", encoding="utf-8") as save_file:
                    herbs = ujson.load(save_file)
                    clan.herb_supply = HerbSupply(herb_supply=herbs)

            # else just start us with an empty herb supply
            else:
                clan.herb_supply = HerbSupply()

            clan.herb_supply.set_required_herb_count(get_living_clan_cat_count(Cat))
        except Exception:
            logger.exception(
                "Failed to load herb supply; starting with an empty supply."
            )
            clan.herb_supply = HerbSupply()

    def save_herb_supply(self, clan):
        """
        saves the Clan's current herb supply
        """
        if not clan.herb_supply:
            return

        combined_supply_dict = clan.herb_supply.combined_supply_dict
        combined_supply_dict = {
            group_key: {
                "storage": {
                    herb: [int(i) for i in amounts]
                    for herb, amounts in group_data["storage"].items()
                },
                "collected": {
                    herb: int(amount)
                    for herb, amount in group_data["collected"].items()
                },
            }
            for group_key, group_data in combined_supply_dict.items()
        }

        safe_save(
            f"{get_save_dir()}/{game.clan.save_id}/herb_supply.json",
            combined_supply_dict,
        )

        # delete old herb save file if it exists
        if os.path.exists(get_save_dir() + f"/{game.clan.save_id}/herbs.json"):
            os.remove(get_save_dir() + f"/{game.clan.save_id}/herbs.json")

    def load_freshkill_pile(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.save_id or clan.game_mode == "classic":
            return

        file_path = get_save_dir() + f"/{game.clan.save_id}/freshkill_pile.json"
        try:
            if os.path.exists(file_path):
                with open(
                    file_path, "r", encoding="utf-8"
                ) as read_file:  # pylint: disable=redefined-outer-name
                    pile = ujson.load(read_file)
                    clan.freshkill_pile = FreshkillPile(pile)

                file_path = get_save_dir() + f"/{game.clan.save_id}/nutrition_info.json"
                if os.path.exists(file_path) and clan.freshkill_pile:
                    with open(file_path, "r", encoding="utf-8") as read_file:
                        nutritions = ujson.load(read_file)
                        for k, nutr in nutritions.items():
                            nutrition = Nutrition()
                            nutrition.max_score = nutr["max_score"]
                            nutrition.current_score = nutr["current_score"]
                            clan.freshkill_pile.nutrition_info[k] = nutrition
                        if len(nutritions) <= 0:
                            for cat in Cat.all_cats_list:
                                clan.freshkill_pile.add_cat_to_nutrition(cat)
            else:
                clan.freshkill_pile = FreshkillPile()
        except Exception:
            logger.exception(
                "Failed to load freshkill pile; starting with an empty pile."
            )
            clan.freshkill_pile = FreshkillPile()

    def save_freshkill_pile(self, clan):
        """
        TODO: DOCS
        """
        if clan.game_mode == "classic" or not clan.freshkill_pile:
            return

        safe_save(
            f"{get_save_dir()}/{game.clan.save_id}/freshkill_pile.json",
            clan.freshkill_pile.pile,
        )

        data = {}
        for k, nutr in clan.freshkill_pile.nutrition_info.items():
            data[k] = {
                "max_score": nutr.max_score,
                "current_score": nutr.current_score,
                "percentage": nutr.percentage,
            }

        safe_save(f"{get_save_dir()}/{game.clan.save_id}/nutrition_info.json", data)

    ## Properties

    @property
    def reputation(self):
        return self._reputation

    @reputation.setter
    def reputation(self, a: int):
        rep = min(int(a), get_config("outsiders.max_reputation"))
        self._reputation = max(rep, get_config("outsiders.min_reputation"))

    @property
    def temperament(self) -> tuple[str, str]:
        """Temperament is determined whenever it's accessed. This makes sure it's always accurate to the
        current cats in the Clan. However, determining Clan temperament is slow!
        Clan temperament should be used as sparsely as possible, since
        it's pretty resource-intensive to determine it."""

        leader = (
            Cat.fetch_cat(self.leader)
            if isinstance(Cat.fetch_cat(self.leader), Cat)
            else None
        )
        deputy = (
            Cat.fetch_cat(self.deputy)
            if isinstance(Cat.fetch_cat(self.deputy), Cat)
            else None
        )
        medicine_cats = find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT])

        all_other_cats = [
            i
            for i in Cat.all_cats_list
            if i.status.rank
            not in (CatRank.LEADER, CatRank.DEPUTY, CatRank.MEDICINE_CAT)
            and i.status.alive_in_player_clan
        ]

        sociability_list = []
        aggression_list = []
        lawfulness_list = []
        stability_list = []

        # 3x influence
        if leader:
            sociability_list += [leader.personality.sociability] * 3
            aggression_list += [leader.personality.aggression] * 3
            lawfulness_list += [leader.personality.lawfulness] * 3
            stability_list += [leader.personality.stability] * 3

        # 2x influence
        if deputy:
            sociability_list += [deputy.personality.sociability] * 2
            aggression_list += [deputy.personality.aggression] * 2
            lawfulness_list += [deputy.personality.lawfulness] * 2
            stability_list += [deputy.personality.stability] * 2

        # collective influence
        if medicine_cats:
            sociability_list.append(
                statistics.median([i.personality.sociability for i in medicine_cats])
            )
            aggression_list.append(
                statistics.median([i.personality.aggression for i in medicine_cats])
            )
            lawfulness_list.append(
                statistics.median([i.personality.lawfulness for i in medicine_cats])
            )
            stability_list.append(
                statistics.median([i.personality.stability for i in medicine_cats])
            )

        # collective influence
        if all_other_cats:
            sociability_list.append(
                statistics.median([i.personality.sociability for i in all_other_cats])
            )
            aggression_list.append(
                statistics.median([i.personality.aggression for i in all_other_cats])
            )
            lawfulness_list.append(
                statistics.median([i.personality.lawfulness for i in all_other_cats])
            )
            stability_list.append(
                statistics.median([i.personality.stability for i in all_other_cats])
            )

        if not leader and not deputy and not medicine_cats and not all_other_cats:
            print("returned default temper: stoic, observant")
            return "stoic", "observant"

        # mean of [leader, leader, leader, deputy, deputy, medicine_cats, all_other_cats]
        clan_sociability = round(statistics.mean(sociability_list))
        clan_aggression = round(statistics.mean(aggression_list))
        clan_lawfulness = round(statistics.mean(lawfulness_list))
        clan_stability = round(statistics.mean(stability_list))

        return get_temper_alignment(
            clan_sociability, clan_aggression, clan_lawfulness, clan_stability
        )

    @temperament.setter
    def temperament(self, val):
        return


class OtherClan:
    """
    TODO: DOCS
    """

    interaction_dict = {
        "ally": ["offend", "praise"],
        "neutral": ["provoke", "befriend"],
        "hostile": ["antagonize", "appease", "declare"],
    }

    first_temper_list = []
    second_temper_list = []
    for _l in constants.TEMPERAMENT_DICTS[0].values():
        first_temper_list.extend(_l)
    for _l in constants.TEMPERAMENT_DICTS[1].values():
        second_temper_list.extend(_l)

    def __init__(
        self,
        name: str = "",
        relations: int = 0,
        temperament: tuple[str, str] = None,
        chosen_symbol: str = "",
        ID: int = 0,
    ):
        self.group_ID = ID
        if not self.group_ID:
            self.group_ID = game.get_free_group_ID(CatGroup.OTHER_CLAN)
        game.clan.other_clan_IDs.append(self.group_ID)

        self.name = name
        if not self.prefix:  # find name if clan has no name yet
            used_names = [str(i.name) for i in game.clan.all_other_clans] + [
                game.clan.name
            ]
            clan_names = get_possible_clan_names()
            self.name = choice(clan_names)  # name property will set self.prefix
            while self.name in used_names:  # making sure we don't repeat a name
                self.name = choice(clan_names)

        self._relations = relations or randint(
            get_config("clan_creation.starting_clan_relation")[0],
            get_config("clan_creation.starting_clan_relation")[1],
        )

        self.temperament: tuple[str, str]

        # detect old saves and convert
        if isinstance(temperament, str):
            used_tempers = []
            for clan in game.clan.all_other_clans:
                used_tempers.extend(clan.temperament)

            self.temperament = (
                temperament,
                choice([x for x in self.second_temper_list if x not in used_tempers]),
            )
        # assign if a saved temper exists
        elif temperament:
            self.temperament = temperament
        # find temperament
        else:
            used_tempers = []
            for clan in game.clan.all_other_clans:
                used_tempers.extend(clan.temperament)

            self.temperament = (
                choice([x for x in self.first_temper_list if x not in used_tempers]),
                choice([x for x in self.second_temper_list if x not in used_tempers]),
            )

        self.chosen_symbol = (
            None  # have to establish None first so that clan_symbol_sprite works
        )
        self.chosen_symbol = (
            chosen_symbol
            if chosen_symbol
            else clan_symbol_sprite(self, return_string=True)
        )

    def __repr__(self):
        # has indicators that this is unlocalized, just in case
        return f"{self.name}Clan"

    @property
    def name(self):
        return i18n.t("general.clan", name=self.prefix)

    @name.setter
    def name(self, value):
        self.prefix = value

    @property
    def relations(self):
        return min(self._relations, get_config("reputation.other_clans.relation_cap"))

    @relations.setter
    def relations(self, value):
        self._relations = min(value, get_config("reputation.other_clans.relation_cap"))

    def save_info(self):
        """
        Returns all the save information necessary for this clan
        """
        return {
            "group_ID": self.group_ID,
            "prefix": self.prefix,
            "relations": self.relations,
            "temperament": self.temperament,
            "chosen_symbol": self.chosen_symbol,
        }

    def get_standing(self) -> Literal["ally", "neutral", "hostile"]:
        """
        Gets if OtherClan is an ally, neutral, or hostile.

        :return: One of "ally", "neutral" or "hostile".
        """
        if self.relations <= get_config("reputation.other_clans.hostile"):
            return "hostile"
        elif self.relations <= get_config("reputation.other_clans.neutral"):
            return "neutral"
        return "ally"


class Afterlife:
    """
    Currently just used for tracking temperament & facets. All facets default to 8 if influencing_cats is empty.
    """

    def __init__(self):
        self.influencing_cats: set[str] = set()

        self._law: int = 0
        self._social: int = 0
        self._aggress: int = 0
        self._stable: int = 0

        self._total_aggression: int = 0
        self._total_lawfulness: int = 0
        self._total_sociability: int = 0
        self._total_stability: int = 0

    @property
    def aggression(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._aggress

    @aggression.setter
    def aggression(self, value):
        raise Exception(
            "ERROR: Afterlife aggression cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def sociability(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._social

    @sociability.setter
    def sociability(self, value):
        raise Exception(
            "ERROR: Afterlife sociability cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def lawfulness(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._law

    @lawfulness.setter
    def lawfulness(self, value):
        raise Exception(
            "ERROR: Afterlife lawfulness cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def stability(self) -> int:
        if not self.influencing_cats:
            return 8
        else:
            return self._stable

    @stability.setter
    def stability(self, value):
        raise Exception(
            "ERROR: Afterlife stability cannot be set manually as it is meant to be calculated from the currently dead cats."
        )

    @property
    def temperament(self) -> (str, str):
        return get_temper_alignment(
            self.sociability, self.aggression, self.lawfulness, self.stability
        )

    def adjust_facets_by_cat(self, cat: Cat, do_removal: bool = False):
        """
        Adjusts the afterlife's facet averages according to the facets of the given cat
        :param cat: The cat object adjust facets by
        :param do_removal: Set True if the cat's facets are being removed from the afterlife's
        """
        if do_removal:
            self.influencing_cats.remove(cat.ID)
        else:
            self.influencing_cats.add(cat.ID)

        num_of_influencers = len(self.influencing_cats)

        if do_removal:
            self._total_lawfulness -= cat.personality.lawfulness
            self._total_sociability -= cat.personality.sociability
            self._total_aggression -= cat.personality.aggression
            self._total_stability -= cat.personality.stability
        else:
            self._total_lawfulness += cat.personality.lawfulness
            self._total_sociability += cat.personality.sociability
            self._total_aggression += cat.personality.aggression
            self._total_stability += cat.personality.stability

        self._law = self._get_adjusted_facet_average(
            self._total_lawfulness,
            num_of_influencers,
        )

        self._social = self._get_adjusted_facet_average(
            self._total_sociability,
            num_of_influencers,
        )

        self._aggress = self._get_adjusted_facet_average(
            self._total_aggression,
            num_of_influencers,
        )

        self._stable = self._get_adjusted_facet_average(
            self._total_stability,
            num_of_influencers,
        )

    @staticmethod
    def _get_adjusted_facet_average(
        total: int,
        num_of_influencers: int,
    ) -> int:
        """
        Handles the math for adjust average facets.
        :param total: The facet's total value derived from all influencing cats
        :param num_of_influencers: The number of cats influencing the average
        :return: The adjusted average
        """
        if not num_of_influencers:
            return 0
        return total // num_of_influencers

    def get_compatibility(self, cat: Cat) -> CatCompatibility:
        """
        Returns the afterlife's personality compatibility with the given cat.
        """
        differences = [
            abs(self.lawfulness - cat.personality.lawfulness),
            abs(self.sociability - cat.personality.sociability),
            abs(self.aggression - cat.personality.aggression),
            abs(self.stability - cat.personality.stability),
        ]

        running_total = 0
        for x in differences:
            if x <= 4:
                running_total += 1
            elif x >= 6:
                running_total -= 1

        if running_total >= 2:
            return CatCompatibility.POSITIVE
        elif running_total <= -2:
            return CatCompatibility.NEGATIVE
        else:
            return CatCompatibility.NEUTRAL


def get_temper_alignment(
    sociability: int, aggression: int, lawfulness: int, stability: int
) -> tuple[str, str]:
    """
    Returns the temperament strings associated with given values
    """
    first_temper = _find_alignment(
        constants.TEMPERAMENT_DICTS[0], sociability, aggression
    )
    second_temper = _find_alignment(
        constants.TEMPERAMENT_DICTS[1], lawfulness, stability
    )

    return first_temper, second_temper


def _find_alignment(temper_dict: dict, first_value: int, second_value: int) -> str:
    """
    Helper function that returns the string on a temper alignment chart for the first and second values.
    :param temper_dict: The temper alignment chart dictionary.
    :param first_value: The first value to find the alignment for. This is the chart's "y_value", or when viewing it as a dictionary: its keys.
    :param second_value: The second value to find the alignment for. This is the chart's "x-value", or when viewing it as a dictionary: its values.
    """
    if 11 <= first_value:
        temper = list(temper_dict.values())[2]
    elif 7 <= first_value:
        temper = list(temper_dict.values())[1]
    else:
        temper = list(temper_dict.values())[0]

    if 11 <= second_value:
        temper = temper[2]
    elif 7 <= second_value:
        temper = temper[1]
    else:
        temper = temper[0]

    return temper


clan_class = Clan()
# clan_class.remove_cat(cat_class.ID)
