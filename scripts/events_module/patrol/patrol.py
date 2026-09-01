#!/usr/bin/env python3
# -*- coding: ascii -*-
import logging
import random
from copy import deepcopy
from os.path import exists as path_exists
from random import choice, randint, choices
from typing import List, Tuple, Optional, Union

import pygame

from scripts.cat import pronouns
from scripts.cat.cats import Cat
from scripts.cat_relations.enums import RelType
from scripts.cat.enums import CatAge, CatRank, CatGroup, CatCompatibility
from scripts.clan import Clan
from scripts.cat.history import History
from scripts.clan_package.settings import get_clan_setting
from scripts.config import get_config
from scripts.events_module.event_filters import (
    event_for_tags,
    get_frequency,
    find_new_frequency,
    filter_relationship_type,
    check_relationship_value,
    get_personality_compatibility,
    event_for_location,
    event_for_season,
    cat_for_event,
    event_for_poi,
)
from scripts.events_module.patrol.patrol_event import PatrolEvent
from scripts.events_module.patrol.patrol_outcome import PatrolOutcome
from scripts.game_structure import localization, constants
from scripts.game_structure.game.settings import game_setting_get
from scripts.game_structure import game
from scripts.game_structure.localization import load_lang_resource
from scripts.events_module.text_adjust import (
    process_text,
    adjust_prey_abbr,
    get_special_snippet_list,
    find_special_list_types,
    adjust_list_text,
    event_text_adjust,
)
from scripts.clan_package.get_clan_cats import find_alive_cats_with_rank
from scripts.game_structure.game.switches import (
    switch_get_value,
    Switch,
    switch_append_list_value,
)

from scripts.events_module.filter_random_cats import choose_random_cats
from scripts.lifegen_utility import get_cluster
from scripts.special_dates import SpecialDate, is_today


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------- #
#                              PATROL CLASS START                              #
# ---------------------------------------------------------------------------- #
"""
When adding new patrols, use \n to add a paragraph break in the text
"""


class Patrol:
    used_patrols = []

    def __init__(self):
        self.patrol_event: Optional[PatrolEvent] = None

        self.patrol_leader = None
        self.random_cat = None
        self.patrol_cats = []
        self.patrol_apprentices = []
        self.other_clan = None
        self.intro_text = ""

        self.patrol_statuses = {}
        self.patrol_status_list = []

        # lifegen cat dict for random abbrevs ^^

        # Holds new cats for easy access
        self.new_cats: List[List[Cat]] = []

        # LIFEGEN: random cats
        # constraints present in the patrol JSON
        self.lifegen_cat_constraints = {}
        self.lifegen_relationship_constraints = []

        # list of cats who were chosen as r_c's for each patrol
        self.chosen_lifegen_cats = []
        # ---

        # False if no debug patrol set, value if one is set
        self.debug_patrol: Union[bool, str] = False

        # the patrols
        self.HUNTING_SZN = None
        self.HUNTING = None
        self.TRAINING_SZN = None
        self.TRAINING = None
        self.BORDER_SZN = None
        self.BORDER = None
        self.MEDCAT_SZN = None
        self.MEDCAT = None
        self.NEW_CAT = None
        self.NEW_CAT_HOSTILE = None
        self.NEW_CAT_WELCOMING = None
        self.OTHER_CLAN = None
        self.OTHER_CLAN_HOSTILE = None
        self.OTHER_CLAN_ALLIES = None
        self.HUNTING_GEN = None
        self.BORDER_GEN = None
        self.TRAINING_GEN = None
        self.MEDCAT_GEN = None
        self.DISASTER = None

        self.GEN_LIFEGEN = None
        self.KIT_LIFEGEN = None
        self.APP_LIFEGEN = None
        self.WARRIOR_LIFEGEN = None
        self.MEDAPP_LIFEGEN = None
        self.MED_LIFEGEN = None
        self.QUEENAPP_LIFEGEN = None
        self.QUEEN_LIFEGEN = None
        self.MEDIATORAPP_LIFEGEN = None
        self.MEDIATOR_LIFEGEN = None
        self.DEPUTY_LIFEGEN = None
        self.LEADER_LIFEGEN = None
        self.ELDER_LIFEGEN = None

        self.DF_LIFEGEN = None
        self.DATE_LIFEGEN = None

    def setup_patrol(self, patrol_cats: List[Cat], patrol_type: str) -> str:
        # Add cats

        print("PATROL START ---------------------------------------------------")

        self.add_patrol_cats(patrol_cats, game.clan, patrol_type)

        self.debug_patrol = (
            constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
            if constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
            else False
        )

        final_patrols, final_romance_patrols = self.get_possible_patrols(
            str(game.clan.current_season).casefold(),
            str(
                game.clan.biome
                if not game.clan.override_biome
                else game.clan.override_biome
            ).casefold(),
            str(game.clan.camp_bg).casefold(),
            patrol_type,
            get_clan_setting("disasters"),
        )

        # lifegen: debug to print all possible patrols
        # print("Patrols:")
        # for i in final_patrols:
        #     print(i.patrol_id)

        print(
            f"Total Number of Possible Patrols | normal: {len(final_patrols)}, romantic: {len(final_romance_patrols)} "
        )

        if final_patrols:
            normal_event_choice = choices(
                final_patrols, weights=[x.weight for x in final_patrols]
            )[0]
        else:
            print("ERROR: NO POSSIBLE NORMAL PATROLS FOUND for: ", self.patrol_statuses)
            raise RuntimeError

        romantic_event_choice = None
        if final_romance_patrols:
            romantic_event_choice = choices(
                final_romance_patrols, [x.weight for x in final_romance_patrols]
            )[0]

        if romantic_event_choice and Patrol.decide_if_romantic(
            romantic_event_choice,
            self.patrol_leader,
            self.random_cat,
            self.patrol_apprentices,
        ):
            print("did the romance")
            self.patrol_event = romantic_event_choice
        else:
            self.patrol_event = normal_event_choice
            # print("CHOSE PATROL:", self.patrol_event.patrol_id)
            # print("CAT CONSTRAINTS:", self.patrol_event.lifegen_cat_constraints)
            # print("REL CONSTRAINTS:", self.patrol_event.lifegen_relationship_constraints)
            # print("LG CATS:", self.patrol_event.chosen_lifegen_cats)
            # if self.patrol_event.chosen_lifegen_cats:
            #     for cat in self.patrol_event.chosen_lifegen_cats:
            #         print(cat.name)

        Patrol.used_patrols.append(self.patrol_event.patrol_id)

        patrol_cat_ids = []
        for c in patrol_cats:
            patrol_cat_ids.append(c.ID)
        if game.clan.your_cat.ID in patrol_cat_ids:
            if switch_get_value(Switch.patrol_category) == "lifegen":
                switch_append_list_value(Switch.patrolled, "2")

            elif switch_get_value(Switch.patrol_category) == "clangen":
                switch_append_list_value(Switch.patrolled, "1")
            elif switch_get_value(Switch.patrol_category) == "date":
                switch_append_list_value(Switch.patrolled, "4")
            else:
                switch_append_list_value(Switch.patrolled, "3")

        return event_text_adjust(
            Cat,
            self.patrol_event.intro_text,
            patrol_leader=self.patrol_leader,
            random_cat=self.random_cat,
            patrol_cats=self.patrol_cats,
            patrol_apprentices=self.patrol_apprentices,
            new_cats=self.new_cats,
            clan=game.clan,
            other_clan=self.other_clan,
            chosen_lifegen_cats=self.patrol_event.chosen_lifegen_cats,
        )

    def proceed_patrol(
        self, path: str = "proceed"
    ) -> Tuple[str, str, list, Optional[str]]:
        """Proceed the patrol to the next step.
        path can be: "proceed", "antag", or "decline" """

        if path == "decline":
            if self.patrol_event:
                print(
                    f"PATROL ID: {self.patrol_event.patrol_id} | SUCCESS: N/A (did not proceed)"
                )
                return (
                    event_text_adjust(
                        Cat,
                        self.patrol_event.decline_text,
                        patrol_leader=self.patrol_leader,
                        random_cat=self.random_cat,
                        patrol_cats=self.patrol_cats,
                        patrol_apprentices=self.patrol_apprentices,
                        new_cats=self.new_cats,
                        clan=game.clan,
                        other_clan=self.other_clan,
                        chosen_lifegen_cats=self.patrol_event.chosen_lifegen_cats,
                    ),
                    "",
                    [],
                    None,
                )

            else:
                return "Error - no event chosen", "", None

        return self.determine_outcome(
            antagonize=(path == "antag"),
            chosen_lifegen_cats=self.patrol_event.chosen_lifegen_cats,
        )

    def add_patrol_cats(
        self, patrol_cats: List[Cat], clan: Clan, patrol_type: str = None
    ) -> None:
        """Add the list of cats to the patrol class and handles to set all needed values.

        Parameters
        ----------
        patrol_cats : list
            list of cats which are on the patrol

        clan: Clan
            the Clan class of the game, this parameter is needed to make tests possible

        Returns
        ----------
        """
        for cat in patrol_cats:
            self.patrol_cats.append(cat)

            if cat.status.rank.is_any_apprentice_rank():
                self.patrol_apprentices.append(cat)

            self.patrol_status_list.append(cat.status.rank)

            if cat.status.rank in self.patrol_statuses:
                self.patrol_statuses[cat.status.rank] += 1
            else:
                self.patrol_statuses[cat.status.rank] = 1

            # LG ---
            if cat.status.group == CatGroup.DARK_FOREST and cat != game.clan.your_cat:
                if "df" in self.patrol_statuses:
                    self.patrol_statuses["df"] += 1
                else:
                    self.patrol_statuses["df"] = 1
            # ---

            # Combined patrol_statuses catagories
            if cat.status.rank in (CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE):
                if "healer cats" in self.patrol_statuses:
                    self.patrol_statuses["healer cats"] += 1
                else:
                    self.patrol_statuses["healer cats"] = 1

            if cat.status.rank.is_any_apprentice_rank():
                if "all apprentices" in self.patrol_statuses:
                    self.patrol_statuses["all apprentices"] += 1
                else:
                    self.patrol_statuses["all apprentices"] = 1

            if (
                cat.status.rank.is_any_adult_warrior_like_rank()
                and cat.age != CatAge.ADOLESCENT
            ):
                if "normal adult" in self.patrol_statuses:
                    self.patrol_statuses["normal adult"] += 1
                else:
                    self.patrol_statuses["normal adult"] = 1

            if switch_get_value(Switch.patrol_category) == "clangen":
                game.patrolled.append(cat.ID)
            elif switch_get_value(Switch.patrol_category) == "date":
                game.dated_cats.append(cat.ID)

        # PATROL LEADER AND RANDOM CAT CAN NOT CHANGE AFTER SET-UP

        # DETERMINE PATROL LEADER
        # sets medcat as leader if they're in the patrol
        if CatRank.MEDICINE_CAT in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.MEDICINE_CAT)
            self.patrol_leader = self.patrol_cats[index]
            # If there is no medicine cat, but there is a medicine cat apprentice, set them as the patrol leader.
            # This prevents warrior from being treated as medicine cats in medicine cat patrols.
        elif CatRank.MEDICINE_APPRENTICE in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.MEDICINE_APPRENTICE)
            self.patrol_leader = self.patrol_cats[index]
            # then we just make sure that this app will also be app1
            self.patrol_apprentices.remove(self.patrol_leader)
            self.patrol_apprentices = [self.patrol_leader] + self.patrol_apprentices
            # sets leader as patrol leader
        elif CatRank.LEADER in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.LEADER)
            self.patrol_leader = self.patrol_cats[index]
        elif CatRank.DEPUTY in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.DEPUTY)
            self.patrol_leader = self.patrol_cats[index]
        else:
            # Get the oldest cat
            possible_leader = [
                i
                for i in self.patrol_cats
                if not i.status.rank.is_any_apprentice_rank()
            ]
            if possible_leader:
                # Flip a coin to pick the most experience, or oldest.
                if randint(0, 1):
                    possible_leader.sort(key=lambda x: x.moons)
                else:
                    possible_leader.sort(key=lambda x: x.experience)
                self.patrol_leader = possible_leader[-1]
            else:
                self.patrol_leader = choice(self.patrol_cats)

        if clan.all_other_clans and len(clan.all_other_clans) > 0:
            self.other_clan = choice(clan.all_other_clans)
        else:
            self.other_clan = None

        if switch_get_value(Switch.patrol_category) != "clangen":
            self.patrol_leader = game.clan.your_cat
            # youre always da leader here

        # DETERMINE RANDOM CAT
        # Find random cat
        if switch_get_value(Switch.patrol_category) == "date":
            for date_cat in patrol_cats:
                if date_cat.ID != game.clan.your_cat.ID:
                    self.random_cat = date_cat
                    break
        elif len(patrol_cats) > 1 and switch_get_value(Switch.patrol_category) == "df":
            # LG: if theres df cats on the patrol, r_c will always be DF
            # to make writing a bit more open
            df_patrol_cats = [
                i
                for i in patrol_cats
                if (
                    i.status.group == CatGroup.DARK_FOREST
                    and i.ID != game.clan.your_cat.ID
                )
            ]
            if df_patrol_cats:
                self.random_cat = choice(df_patrol_cats)
            else:
                possible_random_cats = [
                    i for i in patrol_cats if i.ID != game.clan.your_cat.ID
                ]
                self.random_cat = choice(possible_random_cats)
        # Find random cat
        else:
            if len(patrol_cats) > 1:
                # prioritize grabbing an adult as the random cat
                if self.patrol_statuses.get("normal adult", 0) > 1:
                    self.random_cat = choice(
                        [
                            i
                            for i in self.patrol_cats
                            if i != self.patrol_leader
                            and i not in self.patrol_apprentices
                        ]
                    )
                # if no adults, grab anyone
                else:
                    self.random_cat = choice(
                        [i for i in patrol_cats if i != self.patrol_leader]
                    )
            else:
                self.random_cat = choice(patrol_cats)

        if self.random_cat is None and self.patrol_cats:
            self.random_cat = (
                self.patrol_leader
                if self.patrol_leader in self.patrol_cats
                else self.patrol_cats[0]
            )

        print("Patrol Leader:", str(self.patrol_leader.name))
        print("Random Cat:", str(self.random_cat.name))

    def get_possible_patrols(
        self,
        current_season: str,
        biome: str,
        camp: str,
        patrol_type: str,
        game_setting_disaster=None,
    ) -> Tuple[List[PatrolEvent]]:
        # ---------------------------------------------------------------------------- #
        #                                LOAD RESOURCES                                #
        # ---------------------------------------------------------------------------- #
        biome = biome.lower()
        camp = camp.lower()
        game_setting_disaster = (
            game_setting_disaster
            if game_setting_disaster is not None
            else get_clan_setting("disasters")
        )
        season = current_season.lower()
        biome_dir = f"{biome}/"
        leaf = f"{season}"
        self.update_resources(biome_dir, leaf)

        possible_patrols = []
        # This is for debugging purposes, load-in *ALL* the possible patrols when debug_override_patrol_stat_requirements is true. (May require longer loading time)
        if constants.CONFIG["patrol_generation"][
            "debug_override_patrol_stat_requirements"
        ]:
            leaves = ["greenleaf", "leaf-bare", "leaf-fall", "newleaf", "any"]
            for biome in constants.BIOME_TYPES:
                for leaf in leaves:
                    biome_dir = f"{biome.lower()}/"
                    self.update_resources(biome_dir, leaf)
                    possible_patrols.extend(self.generate_patrol_events(self.HUNTING))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.HUNTING_SZN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.BORDER))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.BORDER_SZN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.TRAINING))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.TRAINING_SZN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.MEDCAT))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MEDCAT_SZN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.HUNTING_GEN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.BORDER_GEN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.TRAINING_GEN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MEDCAT_GEN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.DISASTER))
                    possible_patrols.extend(self.generate_patrol_events(self.NEW_CAT))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.NEW_CAT_WELCOMING)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.NEW_CAT_HOSTILE)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.OTHER_CLAN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.OTHER_CLAN_ALLIES)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.OTHER_CLAN_HOSTILE)
                    )

        # this next one is needed for Classic specifically
        patrol_type = (
            "med"
            if [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE]
            in self.patrol_status_list
            else patrol_type
        )
        patrol_size = len(self.patrol_cats)
        reputation = game.clan.reputation  # reputation with outsiders
        other_clan = self.other_clan
        hostile_rep = False
        neutral_rep = False
        welcoming_rep = False
        clan_neutral = False
        clan_hostile = False
        clan_allies = False
        clan_size = int(len(game.clan.clan_cats))
        chance = 0
        # assigning other_clan relations
        other_clan_standing = other_clan.get_standing() if other_clan else None
        if other_clan_standing == "ally":
            clan_allies = True
        elif other_clan_standing == "hostile":
            clan_hostile = True
        elif other_clan_standing == "neutral":
            clan_neutral = True
        # chance for each kind of loner event to occur
        small_clan = False
        if clan_size < 20:
            small_clan = True
        regular_chance = int(random.getrandbits(2))
        hostile_chance = int(random.getrandbits(5))
        welcoming_chance = int(random.getrandbits(1))
        if 1 <= int(reputation) <= 30:
            hostile_rep = True
            if small_clan:
                chance = welcoming_chance
            else:
                chance = hostile_chance
        elif 31 <= int(reputation) <= 70:
            neutral_rep = True
            if small_clan:
                chance = welcoming_chance
            else:
                chance = regular_chance
        elif int(reputation) >= 71:
            welcoming_rep = True
            chance = welcoming_chance

        if switch_get_value(Switch.patrol_category) == "clangen":
            possible_patrols.extend(self.generate_patrol_events(self.HUNTING))
            possible_patrols.extend(self.generate_patrol_events(self.HUNTING_SZN))
            possible_patrols.extend(self.generate_patrol_events(self.BORDER))
            possible_patrols.extend(self.generate_patrol_events(self.BORDER_SZN))
            possible_patrols.extend(self.generate_patrol_events(self.TRAINING))
            possible_patrols.extend(self.generate_patrol_events(self.TRAINING_SZN))
            possible_patrols.extend(self.generate_patrol_events(self.MEDCAT))
            possible_patrols.extend(self.generate_patrol_events(self.MEDCAT_SZN))
            possible_patrols.extend(self.generate_patrol_events(self.HUNTING_GEN))
            possible_patrols.extend(self.generate_patrol_events(self.BORDER_GEN))
            possible_patrols.extend(self.generate_patrol_events(self.TRAINING_GEN))
            possible_patrols.extend(self.generate_patrol_events(self.MEDCAT_GEN))
        elif switch_get_value(Switch.patrol_category) == "lifegen":
            status = game.clan.your_cat.status.rank
            if status == CatRank.KITTEN:
                possible_patrols.extend(self.generate_patrol_events(self.KIT_LIFEGEN))
            else:
                possible_patrols.extend(self.generate_patrol_events(self.GEN_LIFEGEN))

                if status == CatRank.APPRENTICE:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.APP_LIFEGEN)
                    )
                elif status == CatRank.MEDICINE_APPRENTICE:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MEDAPP_LIFEGEN)
                    )
                elif status == CatRank.MEDIATOR_APPRENTICE:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MEDIATORAPP_LIFEGEN)
                    )
                elif status == CatRank.QUEENS_APPRENTICE:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.QUEENAPP_LIFEGEN)
                    )
                elif status == CatRank.QUEEN:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.QUEEN_LIFEGEN)
                    )
                elif status == CatRank.MEDICINE_CAT:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MED_LIFEGEN)
                    )
                elif status == CatRank.MEDIATOR:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MEDIATOR_LIFEGEN)
                    )
                elif status == CatRank.DEPUTY:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.DEPUTY_LIFEGEN)
                    )
                elif status == CatRank.LEADER:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.LEADER_LIFEGEN)
                    )
                elif status == CatRank.ELDER:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.ELDER_LIFEGEN)
                    )
                else:
                    possible_patrols.extend(
                        self.generate_patrol_events(self.WARRIOR_LIFEGEN)
                    )
        elif switch_get_value(Switch.patrol_category) == "date":
            possible_patrols.extend(self.generate_patrol_events(self.DATE_LIFEGEN))
        else:
            possible_patrols.extend(self.generate_patrol_events(self.DF_LIFEGEN))

        if (
            game_setting_disaster
            and switch_get_value(Switch.patrol_category) == "clangen"
        ):
            dis_chance = int(random.getrandbits(3))  # disaster patrol chance
            if dis_chance == 1:
                possible_patrols.extend(self.generate_patrol_events(self.DISASTER))

        # new cat patrols
        if chance == 1 and switch_get_value(Switch.patrol_category) == "clangen":
            if welcoming_rep:
                possible_patrols.extend(
                    self.generate_patrol_events(self.NEW_CAT_WELCOMING)
                )
            elif neutral_rep:
                possible_patrols.extend(self.generate_patrol_events(self.NEW_CAT))
            elif hostile_rep:
                possible_patrols.extend(
                    self.generate_patrol_events(self.NEW_CAT_HOSTILE)
                )

        # other Clan patrols
        if other_clan and switch_get_value(Switch.patrol_category) == "clangen":
            if clan_neutral:
                possible_patrols.extend(self.generate_patrol_events(self.OTHER_CLAN))
            elif clan_allies:
                possible_patrols.extend(
                    self.generate_patrol_events(self.OTHER_CLAN_ALLIES)
                )
            elif clan_hostile:
                possible_patrols.extend(
                    self.generate_patrol_events(self.OTHER_CLAN_HOSTILE)
                )
        patrol_ids = [patrol.patrol_id for patrol in possible_patrols]
        if self.debug_patrol and self.debug_patrol not in patrol_ids:
            print(
                "DEBUG: requested patrol not present (check spelling/mismatched season, biome, patrol type, new cat flag, other clan relations, disaster setting)"
            )

        final_patrols, final_romance_patrols = self.get_filtered_patrols(
            possible_patrols, biome, camp, current_season, patrol_type
        )

        # This is a debug option, this allows you to remove any constraints of a patrol regarding location, session, biomes, etc.
        if constants.CONFIG["patrol_generation"][
            "debug_override_patrol_stat_requirements"
        ]:
            final_patrols = final_romance_patrols = possible_patrols
            # Logging
            print(
                "All patrol filters regarding location, session, etc. have been removed."
            )

        # This is a debug option. If the patrol_id set in "debug_ensure_patrol" is possible,
        # make it the *only* possible patrol
        if self.debug_patrol:
            for _pat in final_patrols + final_romance_patrols:
                if _pat.patrol_id == self.debug_patrol:
                    patrol_type = choice(_pat.types) if _pat.types != [] else "general"
                    rom = "non-romance"
                    if _pat in final_patrols:
                        final_patrols = [_pat]
                    elif _pat in final_romance_patrols:
                        final_romance_patrols = [_pat]
                        rom = "romance"
                    print(
                        f"debug_ensure_patrol_id: "
                        f'"{constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]}" '
                        f"is a possible {patrol_type} patrol, and was set as the only "
                        f"{patrol_type} {rom} patrol option"
                    )
                    break
            else:
                print(
                    f"debug_ensure_patrol_id: "
                    f'"{constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]}" '
                    f"is not found. Check output for reason."
                )
        return final_patrols, final_romance_patrols

    def _check_constraints(self, patrol: PatrolEvent) -> bool:
        if not filter_relationship_type(
            group=self.patrol_cats,
            filter_types=patrol.relationship_constraints,
            patrol_leader=self.patrol_leader,
        ):
            if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                print(
                    "DEBUG: requested patrol does not meet constraints (relationship type)"
                )
            return False

        if (
            patrol.pl_skill_constraints
            and not self.patrol_leader.skills.check_skill_requirement_list(
                patrol.pl_skill_constraints
            )
        ):
            if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                print("DEBUG: requested patrol does not meet constraints (pl_skill)")
            return False

        if (
            patrol.pl_trait_constraints
            and self.patrol_leader.personality.trait not in patrol.pl_trait_constraints
        ):
            if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                print("DEBUG: requested patrol does not meet constraints (pl_trait)")
            return False

        return True

    @staticmethod
    def decide_if_romantic(
        romantic_event, patrol_leader, random_cat, patrol_apprentices: list
    ) -> bool:
        # if no romance was available or the patrol lead and random cat aren't potential mates then use the normal event

        if not romantic_event:
            print("No romantic event")
            return False

        if "rom_two_apps" in romantic_event.tags:
            if len(patrol_apprentices) < 2:
                print("somehow, there are not enough apprentices for romantic patrol")
                return False
            love1 = patrol_apprentices[0]
            love2 = patrol_apprentices[1]
        else:
            love1 = patrol_leader
            love2 = random_cat

        if (
            not love1.is_potential_mate(love2, for_love_interest=True)
            and love1.ID not in love2.mate
        ):
            print("not a potential mate or current mate")
            return False

        print("attempted romance between:", love1.name, love2.name)
        chance_of_romance_patrol = constants.CONFIG["patrol_generation"][
            "chance_of_romance_patrol"
        ]

        if (
            get_personality_compatibility(love1, love2) == CatCompatibility.POSITIVE
            or love1.ID in love2.mate
        ):
            chance_of_romance_patrol -= 10
        else:
            chance_of_romance_patrol += 10

        values = [*RelType]
        for val in values:
            value_check = check_relationship_value(love1, love2, val)
            if value_check < 0:
                chance_of_romance_patrol -= 1
            elif value_check > 0:
                chance_of_romance_patrol += 2

        if (
            romantic_event.patrol_id
            == game.constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
        ):
            chance_of_romance_patrol = 1

        if chance_of_romance_patrol <= 0:
            chance_of_romance_patrol = 1
        print("final romance chance:", chance_of_romance_patrol)
        return not int(random.random() * chance_of_romance_patrol)

    def _filter_patrols(
        self,
        possible_patrols: List[PatrolEvent],
        biome: str,
        camp: str,
        current_season: str,
        patrol_type: str,
    ):
        chosen_frequency = get_frequency()
        used_frequencies = set()

        filtered_patrols = []
        romantic_patrols = []
        # This make sure general only gets hunting, border, or training patrols
        # chose fix type will make it not depending on the content amount
        if patrol_type == "general":
            patrol_type = random.choice(["hunting", "border", "training"])

        app_number_mentor_checks = {}
        for i in range(1, 7):
            app_number_mentor_checks[f"app{i}_mentored"] = (
                len(self.patrol_apprentices) >= i
                and self.patrol_apprentices[i - 1].mentor is not None
            )
        general_mentor_checks = (
            all(app.mentor for app in self.patrol_apprentices)
            if self.patrol_apprentices
            else False
        )
        has_mentor = {"general": general_mentor_checks, **app_number_mentor_checks}

        # makes sure that it grabs patrols in the correct biomes, season, with the correct number of cats
        # LG
        MAX_CHECKS = len(possible_patrols)
        checks = 0
        # --
        while not filtered_patrols:
            # LG: this is here to stop an endless load should any patrol issues occur
            if checks >= MAX_CHECKS:
                break
            for patrol in possible_patrols:
                # LG
                if switch_get_value(Switch.patrol_category) == "clangen":
                    # we dont have enough patrols to rely on the frequency like that......
                    # ---
                    if (
                        patrol.frequency != chosen_frequency
                        and patrol.patrol_id
                        != constants.CONFIG["patrol_generation"][
                            "debug_ensure_patrol_id"
                        ]
                    ):
                        continue
                # if not self._check_constraints(patrol):
                #     continue

                # LG
                patrol.chosen_lifegen_cats = []
                if patrol.lifegen_cat_constraints:
                    cat_dict = choose_random_cats(
                        cats_block=patrol.lifegen_cat_constraints,
                        rel_block=patrol.lifegen_relationship_constraints
                        if patrol.lifegen_relationship_constraints
                        else [],
                        your_cat=game.clan.your_cat,
                        the_cat=None,
                        cat_dict={"p_l": game.clan.your_cat},
                    )
                    if not cat_dict:
                        continue
                    for abbrev, cat_obj in cat_dict.items():
                        if "r_c:" in abbrev:
                            patrol.chosen_lifegen_cats.append(cat_obj)

                # Don't check for repeat patrols if ensure_patrol_id is being used.
                if (
                    constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
                    == ""
                    and patrol.patrol_id in self.used_patrols
                ):
                    continue

                if not (patrol.min_cats <= len(self.patrol_cats) <= patrol.max_cats):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (min or max cats range)"
                        )
                    continue

                flag = False
                for sta, num in patrol.min_max_status.items():
                    if len(num) != 2:
                        print(f"Issue with status limits: {patrol.patrol_id}")
                        continue

                    if not (num[0] <= self.patrol_statuses.get(sta, -1) <= num[1]):
                        flag = True
                        break
                if flag:
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (min max status)"
                        )
                    continue

                if not event_for_tags(
                    patrol.tags, Cat, mentor_tags_fulfilled=has_mentor
                ):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (tags)"
                        )
                    continue

                if not event_for_location(patrol.biome):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (biome)"
                        )
                    continue
                if camp not in patrol.camp and "any" not in patrol.camp:
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (camp)"
                        )
                    continue
                if not event_for_season(patrol.season):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (season)"
                        )
                    continue
                if not event_for_poi(patrol.poi):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print("DEBUG: requested patrol does not meet constraints (PoI)")
                    continue

                if switch_get_value(Switch.patrol_category) == "clangen":
                    # LG: these types dont apply to our patrols
                    if "hunting" not in patrol.types and patrol_type == "hunting":
                        if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                            print(
                                "DEBUG: requested patrol does not meet constraints (patrol type)"
                            )
                        continue
                    elif "border" not in patrol.types and patrol_type == "border":
                        if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                            print(
                                "DEBUG: requested patrol does not meet constraints (patrol type)"
                            )
                        continue
                    elif "training" not in patrol.types and patrol_type == "training":
                        if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                            print(
                                "DEBUG: requested patrol does not meet constraints (patrol type)"
                            )
                        continue
                    elif "herb_gathering" not in patrol.types and patrol_type == "med":
                        if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                            print(
                                "DEBUG: requested patrol does not meet constraints (patrol type)"
                            )
                        continue

                else:
                    if switch_get_value(Switch.patrol_category) == "lifegen":
                        if (
                            not any(
                                p in patrol.tags
                                for p in ["sc_lifegen", "ur_lifegen", "df_lifegen"]
                            )
                            and game.clan.your_cat.dead
                        ):
                            continue
                        if "sc_lifegen" in patrol.tags and (
                            not game.clan.your_cat.status.group == CatGroup.STARCLAN
                        ):
                            continue
                        elif "df_lifegen" in patrol.tags and (
                            not game.clan.your_cat.status.group == CatGroup.DARK_FOREST
                        ):
                            continue
                        elif "ur_lifegen" in patrol.tags and (
                            not game.clan.your_cat.status.group
                            == CatGroup.UNKNOWN_RESIDENCE
                        ):
                            continue
                    if switch_get_value(Switch.patrol_category) == "df":
                        if len(self.patrol_cats) > 1:
                            other_cat = self.patrol_cats[1]

                            if not other_cat.joined_df:
                                if "fellowtrainee" in patrol.tags:
                                    continue

                            else:
                                if "fellowtrainee" not in patrol.tags:
                                    continue

                        if "mc_death" in patrol.tags:
                            if random.randint(1, 8) != 1:
                                continue

                        if "shunned" in patrol.tags:
                            if not game.clan.your_cat.status.is_shunned():
                                continue
                    else:
                        if "shunned" in patrol.tags:
                            if not game.clan.your_cat.status.is_shunned():
                                continue

                        if "shunned" not in patrol.tags and "df" not in patrol.tags:
                            if game.clan.your_cat.status.is_shunned():
                                continue
                    if switch_get_value(Switch.patrol_category) == "date":
                        if "df" in patrol.tags:
                            if len(self.patrol_cats) > 1:
                                other_cat = self.patrol_cats[1]
                                if (
                                    not game.clan.your_cat.joined_df
                                    or not other_cat.joined_df
                                ):
                                    # need both cats to be trainees for goop romance
                                    continue

                    if "bloodthirsty_only" in patrol.tags:
                        mentor = Cat.all_cats.get(game.clan.your_cat.mentor)
                        if mentor is None or mentor.personality.trait != "bloodthirsty":
                            continue

                # cruel season tag check
                if "cruel_season" in patrol.tags:
                    if game.clan and game.clan.game_mode != "cruel_season":
                        continue

                if "romance" in patrol.tags:
                    romantic_patrols.append(patrol)
                else:
                    filtered_patrols.append(patrol)

                checks += 1

            if not filtered_patrols:
                # if we've circled back around to 4 then we need to reset the used patrols
                if 4 in used_frequencies and chosen_frequency == 4:
                    self.used_patrols.clear()
                    used_frequencies.clear()
                else:
                    used_frequencies.add(chosen_frequency)
                    chosen_frequency = find_new_frequency(used_frequencies)

        # make sure the hunting patrols are balanced
        if patrol_type == "hunting":
            filtered_patrols = self.balance_hunting(filtered_patrols)

        return filtered_patrols, romantic_patrols

    def get_filtered_patrols(
        self, possible_patrols, biome, camp, current_season, patrol_type
    ):
        filtered_patrols, romantic_patrols = self._filter_patrols(
            possible_patrols, biome, camp, current_season, patrol_type
        )

        if patrol_type == "herb_gathering":
            target_herbs = game.clan.herb_supply.sorted_by_need
            herb_filtered_patrols = []
            herb_romance_patrols = []

            for i in range(len(target_herbs)):
                herb_filtered_patrols = [
                    patrol
                    for patrol in filtered_patrols
                    if target_herbs[i] in patrol.herbs_given
                    or "random_herbs" in patrol.herbs_given
                ]
                herb_romance_patrols = [
                    patrol
                    for patrol in romantic_patrols
                    if target_herbs[i] in patrol.herbs_given
                    or "random_herbs" in patrol.herbs_given
                ]
                if herb_filtered_patrols:
                    break

            if herb_filtered_patrols:
                filtered_patrols = herb_filtered_patrols
                romantic_patrols = herb_romance_patrols

                if self.debug_patrol and self.debug_patrol not in [
                    patrol.patrol_id for patrol in filtered_patrols + romantic_patrols
                ]:
                    print(
                        "DEBUG: requested patrol removed during herb filtering (not target herb)"
                    )

        if not filtered_patrols:
            print(
                "No normal patrols possible. Repeating filter with used patrols cleared."
            )
            self.used_patrols.clear()
            print("used patrols cleared", self.used_patrols)
            filtered_patrols, romantic_patrols = self._filter_patrols(
                possible_patrols, biome, camp, current_season, patrol_type
            )

            if not filtered_patrols:
                raise Exception(
                    "No matching patrols found! This may be a localization issue."
                )

        return filtered_patrols, romantic_patrols

    def generate_patrol_events(self, patrol_dict):
        all_patrol_events = []
        for patrol in patrol_dict:
            patrol_event = PatrolEvent(
                patrol_id=patrol.get("patrol_id"),
                biome=patrol.get("biome"),
                season=patrol.get("season"),
                camp=patrol.get("camp"),
                tags=patrol.get("tags"),
                frequency=patrol.get("frequency", 4),
                types=patrol.get("types"),
                lifegen_cat_constraints=patrol.get("random_cats"),
                lifegen_relationship_constraints=patrol.get("relationships"),
                intro_text=patrol.get("intro_text"),
                patrol_art=patrol.get("patrol_art"),
                patrol_art_clean=patrol.get("patrol_art_clean"),
                success_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("success_outcomes")
                ),
                fail_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("fail_outcomes"), success=False
                ),
                decline_text=patrol.get("decline_text"),
                chance_of_success=patrol.get("chance_of_success"),
                min_cats=patrol.get("min_cats", 1),
                max_cats=patrol.get("max_cats", 6),
                min_max_status=patrol.get("min_max_status"),
                antag_success_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("antag_success_outcomes"), antagonize=True
                ),
                antag_fail_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("antag_fail_outcomes"), success=False, antagonize=True
                ),
                relationship_constraints=patrol.get("relationship_constraint"),
                pl_skill_constraints=patrol.get("pl_skill_constraint"),
                pl_trait_constraints=patrol.get("pl_trait_constraints"),
            )

            all_patrol_events.append(patrol_event)

        return all_patrol_events

    def determine_outcome(
        self, antagonize=False, chosen_lifegen_cats=[]
    ) -> Tuple[str, str, list, Optional[str]]:
        if self.patrol_event is None:
            raise Exception("No patrol event supplied")

        if self.random_cat is None and self.patrol_cats:
            self.random_cat = (
                self.patrol_leader
                if self.patrol_leader in self.patrol_cats
                else self.patrol_cats[0]
            )

        # First Step - Filter outcomes and pick a fail and success outcome
        success_outcomes = (
            self.patrol_event.antag_success_outcomes
            if antagonize
            else self.patrol_event.success_outcomes
        )
        fail_outcomes = (
            self.patrol_event.antag_fail_outcomes
            if antagonize
            else self.patrol_event.fail_outcomes
        )

        # Filter the outcomes. Do this only once - this is also where stat cats are determined
        success_outcomes = PatrolOutcome.prepare_allowed_outcomes(
            success_outcomes, self
        )
        fail_outcomes = PatrolOutcome.prepare_allowed_outcomes(fail_outcomes, self)

        chosen_success = None
        chosen_failure = None

        # Choose a success and fail outcome
        chosen_frequency = get_frequency()
        used_frequencies = set()
        while not chosen_success or not chosen_failure:
            if not chosen_success:
                possible_successes = [
                    x for x in success_outcomes if x.frequency == chosen_frequency
                ]
                if possible_successes:
                    chosen_success = choices(
                        possible_successes,
                        weights=[x.weight for x in possible_successes],
                    )[0]
            if not chosen_failure:
                possible_failures = [
                    x for x in fail_outcomes if x.frequency == chosen_frequency
                ]
                if possible_failures:
                    chosen_failure = choices(
                        possible_failures, weights=[x.weight for x in possible_failures]
                    )[0]
            if not chosen_success or not chosen_failure:
                used_frequencies.add(chosen_frequency)
                chosen_frequency = find_new_frequency(used_frequencies)

        final_event, success = self.calculate_success(chosen_success, chosen_failure)

        if success and switch_get_value(Switch.patrol_category) == "date":
            try:
                game.clan.your_cat.relationships[self.random_cat.ID].romance += randint(
                    1, 5
                )
                game.clan.your_cat.relationships[self.random_cat.ID].trust += randint(
                    1, 5
                )
                game.clan.your_cat.relationships[self.random_cat.ID].comfort += randint(
                    1, 5
                )
                self.random_cat.relationships[game.clan.your_cat.ID].romance += randint(
                    1, 5
                )
                self.random_cat.relationships[game.clan.your_cat.ID].trust += randint(
                    1, 5
                )
                self.random_cat.relationships[game.clan.your_cat.ID].comfort += randint(
                    1, 5
                )
            except:
                print("ERROR: handling relationship changes in date patrol")
        elif not success and switch_get_value(Switch.patrol_category) == "date":
            try:
                self.random_cat.relationships[game.clan.your_cat.ID].romance -= randint(
                    1, 5
                )
                self.random_cat.relationships[game.clan.your_cat.ID].trust -= randint(
                    1, 5
                )
                self.random_cat.relationships[game.clan.your_cat.ID].comfort -= randint(
                    1, 5
                )
            except:
                print("ERROR: handling relationship changes in date patrol")
        print(f"PATROL ID: {self.patrol_event.patrol_id} | SUCCESS: {success}")
        print(
            f"Patrol Frequency: {self.patrol_event.frequency} | Patrol Weight: {self.patrol_event.weight}"
        )
        if success:
            print(
                f"Outcome Frequency: {chosen_success.frequency} | Outcome Weight: {chosen_success.weight}"
            )
        else:
            print(
                f"Outcome Frequency: {chosen_failure.frequency} | Outcome Weight: {chosen_failure.weight}"
            )

        if success and switch_get_value(Switch.patrol_category) == "df":
            game.clan.your_cat.df_patrols += 1
            # graduate from the Dark Forest after 5 successful DF patrols. Once
            # graduated, the cat can act as a mentor to other DF trainees.
            if (
                game.clan.your_cat.df_patrols >= 5
                and not game.clan.your_cat.graduated_df
            ):
                game.clan.your_cat.graduated_df = True

        print(f"PATROL ID: {self.patrol_event.patrol_id} | SUCCESS: {success}")

        # Run the chosen outcome
        self.chosen_lifegen_cats = chosen_lifegen_cats
        return final_event.execute_outcome(
            self, chosen_lifegen_cats=chosen_lifegen_cats
        )

    def calculate_success(
        self, success_outcome: PatrolOutcome, fail_outcome: PatrolOutcome
    ) -> Tuple[PatrolOutcome, bool]:
        """Returns both the chosen event, and a boolean that's True if success, and False is fail."""

        patrol_size = len(self.patrol_cats)
        total_exp = sum([x.experience for x in self.patrol_cats])
        path = (
            "patrol_generation.classic_difficulty_modifier"
            if game.clan.game_mode == "classic"
            else "patrol_generation.difficulty_modifier"
        )

        gm_modifier = get_config(path)

        exp_adustment = (
            (1 + 0.10 * patrol_size) * total_exp / (patrol_size * gm_modifier * 2)
        )

        success_chance = self.patrol_event.chance_of_success + int(exp_adustment)
        success_chance = min(success_chance, 90)

        # Now, apply success and fail skill
        print(
            "starting chance:",
            self.patrol_event.chance_of_success,
            "| EX_updated chance:",
            success_chance,
        )
        skill_updates = ""

        # Skill and trait stuff
        for kitty in self.patrol_cats:
            # SUCCESS OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in success_outcome.stat_skill
            )
            if is_exclusionary:
                skills_to_check = [
                    x.replace("-", "") for x in success_outcome.stat_skill
                ]
            else:
                skills_to_check = success_outcome.stat_skill

            hits = kitty.skills.check_skill_requirement_list(skills_to_check)

            if is_exclusionary and not hits:
                # if they don't have a disallowed skill, we increase the chance
                success_chance += (
                    1 * constants.CONFIG["patrol_generation"]["win_stat_cat_modifier"]
                )
            else:
                # if they had a required skill, we increase
                success_chance += (
                    hits
                    * constants.CONFIG["patrol_generation"]["win_stat_cat_modifier"]
                )

            # FAIL OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in fail_outcome.stat_skill
            )
            if is_exclusionary:
                skills_to_check = [x.replace("-", "") for x in fail_outcome.stat_skill]
            else:
                skills_to_check = fail_outcome.stat_skill
            hits = kitty.skills.check_skill_requirement_list(skills_to_check)

            if is_exclusionary and not hits:
                # if they don't have a disallowed skill, we decrease chance (fail mod is a negative)
                success_chance += (
                    1 * constants.CONFIG["patrol_generation"]["fail_stat_cat_modifier"]
                )
            else:
                # if they had the required skill, we decrease chance (fail mod is a negative)
                success_chance += (
                    hits
                    * constants.CONFIG["patrol_generation"]["fail_stat_cat_modifier"]
                )

            # SUCCESS OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in success_outcome.stat_trait
            )
            if is_exclusionary:
                trait_to_check = [
                    x.replace("-", "") for x in success_outcome.stat_trait
                ]
            else:
                trait_to_check = success_outcome.stat_trait

            if (is_exclusionary and kitty.personality.trait not in trait_to_check) or (
                kitty.personality.trait in trait_to_check
            ):
                success_chance += constants.CONFIG["patrol_generation"][
                    "win_stat_cat_modifier"
                ]

            # FAIL OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in fail_outcome.stat_trait
            )
            if is_exclusionary:
                trait_to_check = [x.replace("-", "") for x in fail_outcome.stat_trait]
            else:
                trait_to_check = fail_outcome.stat_trait

            if (is_exclusionary and kitty.personality.trait not in trait_to_check) or (
                kitty.personality.trait in trait_to_check
            ):
                success_chance += constants.CONFIG["patrol_generation"][
                    "fail_stat_cat_modifier"
                ]

            # LG
            cluster1, cluster2 = get_cluster(kitty.personality.trait)
            if (
                cluster1 in success_outcome.stat_cluster
                or cluster2
                and cluster2 in success_outcome.stat_cluster
            ):
                success_chance += constants.CONFIG["patrol_generation"][
                    "win_stat_cat_modifier"
                ]

            if (
                cluster1 in fail_outcome.stat_cluster
                or cluster2
                and cluster2 in fail_outcome.stat_cluster
            ):
                success_chance += constants.CONFIG["patrol_generation"][
                    "fail_stat_cat_modifier"
                ]
            # ---

            skill_updates += f"{kitty.name} updated chance to {success_chance} | "
        if switch_get_value(Switch.patrol_category) == "date":
            c = random.randint(1, 100)
            success_chance = 40
            date = None
            you = game.clan.your_cat
            if self.patrol_cats[0].ID == game.clan.your_cat.ID:
                date = self.patrol_cats[1]
            else:
                date = self.patrol_cats[0]
            if date.relationships.get(you.ID):
                if date.relationships.get(you.ID).romance > 50:
                    success_chance += 40
                elif date.relationships.get(you.ID).romance > 40:
                    success_chance += 30
                elif date.relationships.get(you.ID).romance > 30:
                    success_chance += 20
                elif date.relationships.get(you.ID).romance > 10:
                    success_chance += 10

                if date.relationships.get(you.ID).like > 40:
                    success_chance += 15
                elif date.relationships.get(you.ID).like > 30:
                    success_chance += 10
                elif date.relationships.get(you.ID).like > 20:
                    success_chance += 5

                if date.relationships.get(you.ID).like < -50:
                    success_chance -= 50
                if date.relationships.get(you.ID).like < -30:
                    success_chance -= 40
                if date.relationships.get(you.ID).like < -20:
                    success_chance -= 30
                if date.relationships.get(you.ID).like < -0:
                    success_chance -= 10
                success_chance += random.randint(-20, 20)
            success_chance = min(90, success_chance)
            success_chance = max(success_chance, 10)
            print(f"c: {c} chance: {success_chance}")
            if c < success_chance:
                if not date.relationships.get(you.ID):
                    date.create_one_relationship(you)
                if not you.relationships.get(date.ID):
                    you.create_one_relationship(date)
                date.relationships.get(you.ID).romance += 10
                you.relationships.get(date.ID).romance += 10
        if success_chance >= 120:
            success_chance = 115
            skill_updates += "success chance over 120, updated to 115"

        print(skill_updates)

        success = int(random.random() * 120) < success_chance

        # This is a debug option, this will forcefully change the outcome of a patrol
        if isinstance(
            constants.CONFIG["patrol_generation"]["debug_ensure_patrol_outcome"], bool
        ):
            success = constants.CONFIG["patrol_generation"][
                "debug_ensure_patrol_outcome"
            ]
            # Logging
            print(
                f"The outcome of {self.patrol_event.patrol_id} was altered to {success}"
            )

        return (success_outcome if success else fail_outcome, success)

    def update_resources(self, biome_dir, leaf):
        if switch_get_value(Switch.patrol_category) == "lifegen":
            resources = [
                # LIFEGEN
                ("GEN_LIFEGEN", "lifegen/general.json"),
                ("KIT_LIFEGEN", "lifegen/kit.json"),
                ("APP_LIFEGEN", "lifegen/app.json"),
                ("MEDAPP_LIFEGEN", "lifegen/medapp.json"),
                ("QUEENAPP_LIFEGEN", "lifegen/queenapp.json"),
                ("MEDIATORAPP_LIFEGEN", "lifegen/mediatorapp.json"),
                ("WARRIOR_LIFEGEN", "lifegen/warrior.json"),
                ("MED_LIFEGEN", "lifegen/med.json"),
                ("QUEEN_LIFEGEN", "lifegen/queen.json"),
                ("MEDIATOR_LIFEGEN", "lifegen/mediator.json"),
                ("DEPUTY_LIFEGEN", "lifegen/deputy.json"),
                ("LEADER_LIFEGEN", "lifegen/leader.json"),
                ("ELDER_LIFEGEN", "lifegen/elder.json"),
            ]
        elif switch_get_value(Switch.patrol_category) == "df":
            resources = [("DF_LIFEGEN", "lifegen/df.json")]
        elif switch_get_value(Switch.patrol_category) == "date":
            resources = [("DATE_LIFEGEN", "lifegen/date.json")]
        else:
            resources = [
                ("HUNTING_SZN", f"{biome_dir}hunting/{leaf}.json"),
                ("HUNTING", f"{biome_dir}hunting/any.json"),
                ("BORDER_SZN", f"{biome_dir}border/{leaf}.json"),
                ("BORDER", f"{biome_dir}border/any.json"),
                ("TRAINING_SZN", f"{biome_dir}training/{leaf}.json"),
                ("TRAINING", f"{biome_dir}training/any.json"),
                ("MEDCAT_SZN", f"{biome_dir}med/{leaf}.json"),
                ("MEDCAT", f"{biome_dir}med/any.json"),
                ("NEW_CAT", "new_cat.json"),
                ("NEW_CAT_HOSTILE", "new_cat_hostile.json"),
                ("NEW_CAT_WELCOMING", "new_cat_welcoming.json"),
                ("OTHER_CLAN", "other_clan.json"),
                ("OTHER_CLAN_HOSTILE", "other_clan_hostile.json"),
                ("OTHER_CLAN_ALLIES", "other_clan_allies.json"),
                ("HUNTING_GEN", "general/hunting.json"),
                ("BORDER_GEN", "general/border.json"),
                ("MEDCAT_GEN", "general/medcat.json"),
                ("TRAINING_GEN", "general/training.json"),
                ("DISASTER", "disaster.json"),
            ]
        for patrol_property, location in resources:
            try:
                setattr(
                    self, patrol_property, load_lang_resource(f"patrols/{location}")
                )
            except:
                raise Exception("Something went wrong loading patrols!")

    def balance_hunting(self, possible_patrols: list):
        """Filter the incoming hunting patrol list to balance the different kinds of hunting patrols.
        With this filtering, there should be more prey possible patrols.

            Parameters
            ----------
            possible_patrols : list
                list of patrols which should be filtered

            Returns
            ----------
            filtered_patrols : list
                list of patrols which is filtered
        """
        filtered_patrols = []

        # get first what kind of prey size which will be chosen
        biome = (
            game.clan.biome
            if not game.clan.override_biome
            else game.clan.override_biome
        )
        season = game.clan.current_season
        prey_size = ["very_small", "small", "medium", "large", "huge"]
        prey_size_random_weights = PATROL_BALANCE[biome][season]

        chosen_prey_size = choices(prey_size, weights=prey_size_random_weights)[0]
        print(f"chosen filter prey size: {chosen_prey_size}")

        # filter all possible patrol depending on the needed prey size
        for patrol in possible_patrols:
            # count the outcomes + prey size
            prey_size_to_outcome_amounts = {}
            for outcome in patrol.success_outcomes:
                # ignore skill or trait outcomes
                if outcome.stat_trait or outcome.stat_skill or outcome.stat_cluster:
                    continue
                if outcome.prey:
                    outcome_prey_size = outcome.prey[0]
                    if outcome_prey_size not in prey_size_to_outcome_amounts:
                        prey_size_to_outcome_amounts[outcome_prey_size] = 0
                    prey_size_to_outcome_amounts[outcome_prey_size] += 1

            # get the prey size with the most outcomes
            most_prey_size = ""
            max_occurrences = 0
            for size, amount in prey_size_to_outcome_amounts.items():
                if amount >= max_occurrences:
                    most_prey_size = size

            if chosen_prey_size == most_prey_size:
                filtered_patrols.append(patrol)
            elif self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                print(
                    "DEBUG: requested patrol does not meet constraints (failed prey balancing)"
                )
        # if the filtering results in an empty list, don't filter and return whole possible patrols
        if len(filtered_patrols) <= 0:
            print(
                "---- WARNING ---- filtering to balance out the hunting, didn't work."
            )
            filtered_patrols = possible_patrols
        return filtered_patrols

    def get_patrol_art(self) -> pygame.Surface:
        """Return's patrol art surface"""
        if not self.patrol_event or not isinstance(self.patrol_event.patrol_art, str):
            return pygame.Surface((600, 600), flags=pygame.SRCALPHA)

        root_dir = "resources/images/patrol_art/"

        if not game_setting_get("gore") and self.patrol_event.patrol_art_clean:
            file_name = self.patrol_event.patrol_art_clean
        else:
            file_name = self.patrol_event.patrol_art

        if not isinstance(file_name, str) or not path_exists(
            f"{root_dir}{file_name}.png"
        ):
            if "herb_gathering" in self.patrol_event.types:
                file_name = "med"
            elif "hunting" in self.patrol_event.types:
                file_name = "hunt"
            elif "border" in self.patrol_event.types:
                file_name = "bord"
            else:
                file_name = "train"

            file_name = f"{file_name}_general_intro"

        if is_today(SpecialDate.APRIL_FOOLS):
            april_fools_root_dir = "resources/images/patrol_art/april_fools/"
            if path_exists(f"{april_fools_root_dir}{file_name}.png"):
                return pygame.image.load(f"{april_fools_root_dir}{file_name}.png")

        return pygame.image.load(f"{root_dir}{file_name}.png")


# ---------------------------------------------------------------------------- #
#                               PATROL CLASS END                               #
# ---------------------------------------------------------------------------- #

PATROL_WEIGHT_ADAPTION = constants.CONFIG["prey"]["patrol_weight_adaption"]
PATROL_BALANCE = constants.CONFIG["prey"]["patrol_balance"]
