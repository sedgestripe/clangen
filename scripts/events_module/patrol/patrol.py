#!/usr/bin/env python3
# -*- coding: ascii -*-
import logging
import random
import statistics
from os.path import exists as path_exists
from random import choice, randint, choices, sample
from typing import List, Tuple, Optional, Union, Literal, TypedDict

import pygame

from scripts.cat.cats import Cat
from scripts.cat.enums import CatAge, CatRank, CatCompatibility, CatGroup
from scripts.cat_relations.enums import RelType
from scripts.cat_relations.relationship import create_one_relationship
from scripts.clan import get_temper_alignment
from scripts.clan_package.get_clan_cats import find_alive_cats_with_rank
from scripts.clan_resources.point_of_interest import get_poi_from_constraints
from scripts.config import get_config
from scripts.events_module.consequences import gather_cat_objects
from scripts.events_module.event_filters import (
    check_relationship_value,
    get_personality_compatibility,
)
from scripts.events_module.filter_random_cats import choose_random_cats
from scripts.events_module.patrol.enums import PatrolChoice
from scripts.events_module.patrol.generate_patrol_list import (
    get_patrol_list,
    get_lifegen_patrol_list,
    will_allow_outsider_patrols,
)
from scripts.events_module.patrol.lifegen_outcome import execute_lifegen_outcome
from scripts.events_module.patrol.patrol_event import PatrolEvent
from scripts.events_module.text_adjust import (
    event_text_adjust,
)
from scripts.events_module.text_pool_event import handle_consequences
from scripts.events_module.text_pool_event.check_general_constraints import (
    passes_general_constraints,
)
from scripts.events_module.text_pool_event.event_retrieval import get_valid_event
from scripts.events_module.text_pool_event.find_involved_cats import find_cats
from scripts.events_module.text_pool_event.text_pool_event import TextPoolEvent
from scripts.game_structure import game
from scripts.game_structure.game.settings import game_setting_get
from scripts.game_structure.game.switches import (
    Switch,
    switch_get_value,
    switch_append_list_value,
)
from scripts.special_dates import SpecialDate, is_today

logger = logging.getLogger(__name__)


def get_patrol_temperament(patrol_cats: list, patrol_leader=None) -> tuple[str, str]:
    """
    Determines the temperament of a patrol based on clan rank and patrol_leader
    """
    sociability, aggression, lawfulness, stability = [], [], [], []

    for cat in patrol_cats:
        rank = cat.status.rank
        if rank == CatRank.LEADER:
            weight = 3
        elif rank == CatRank.DEPUTY:
            weight = 2
        else:  # medicine cat and all others
            weight = 1

        sociability += [cat.personality.sociability] * weight
        aggression += [cat.personality.aggression] * weight
        lawfulness += [cat.personality.lawfulness] * weight
        stability += [cat.personality.stability] * weight

    if not sociability:  # empty patrol guard
        return "", ""

    return get_temper_alignment(
        round(statistics.mean(sociability)),
        round(statistics.mean(aggression)),
        round(statistics.mean(lawfulness)),
        round(statistics.mean(stability)),
    )


class Patrol:
    used_patrols = {"romance": [], "normal": []}

    def __init__(self):
        self.patrol_event: Optional[PatrolEvent] = None
        self.debug_patrol_id: str = ""
        self.other_clan = None
        self.temperament: tuple[str, str] = ("", "")
        """Set once the patrol cats are known, in begin_patrol"""

        self.patrol_cats: list[Cat] = []
        """Holds all the cats that are on the patrol"""
        self.involved_cats: dict[str, Union[list[Cat], Cat]] = {}
        """Cats directly involved and referenced in the event. Keys are their text abbreviation, values are the associated cat objects"""
        self.outcome_cats: TypedDict(
            "outcome_cats", {"success": dict[str, Cat], "failure": dict[str, Cat]}
        ) = {"success": {}, "failure": {}}
        self.chosen_poi = None

        # LG: randomly chosen r_c:X cats for each possible LifeGen patrol, key is the patrol's event_id
        self.lifegen_random_cats: dict[str, dict[str, Cat]] = {}

    def begin_patrol(self, patrol_cats: List[Cat], patrol_type: str) -> str:
        """
        Handles all the initial patrol setup, returns the prepared patrol intro text.
        :param patrol_cats: All cats that have been chosen for this patrol
        :param patrol_type: Type of patrol
        """
        self.debug_patrol_id = get_config("patrol_generation.debug_ensure.patrol_id")

        print("PATROL START ---------------------------------------------------")

        # Add cats
        self._add_patrol_cats(patrol_cats)

        # The patrol group can't change once it's set out, so this is fixed for the rest of the patrol
        self.temperament = get_patrol_temperament(
            self.patrol_cats, self.involved_cats.get("p_l")
        )

        # Choose other clan
        if game.clan.all_other_clans and len(game.clan.all_other_clans) > 0:
            self.other_clan = choice(game.clan.all_other_clans)
        else:
            self.other_clan = None

        # Find valid patrol
        self._load_patrols_and_set_patrol(patrol_type)
        self._create_needed_cats()

        # LG: track which patrol categories the player's cat has gone on this moon
        if game.clan.your_cat and game.clan.your_cat.ID in [
            c.ID for c in self.patrol_cats
        ]:
            switch_append_list_value(
                Switch.patrolled,
                {"clangen": "1", "lifegen": "2", "date": "4"}.get(
                    switch_get_value(Switch.patrol_category), "3"
                ),
            )

        if self.patrol_event.poi:
            self.chosen_poi = get_poi_from_constraints(
                self.patrol_event.poi.get("name"),
                self.patrol_event.poi.get("tags"),
                self.patrol_event.poi.get("category"),
            )

        # Return text adjusted patrol intro
        return event_text_adjust(
            Cat,
            choice(self.patrol_event.intro_strings),
            involved_cat_dict=self.involved_cats,
            clan=game.clan,
            other_clan=self.other_clan,
            chosen_poi=self.chosen_poi,
        )

    def proceed_patrol(
        self, path: PatrolChoice = PatrolChoice.PROCEED
    ) -> Tuple[str, str, dict, pygame.Surface | None]:
        """Proceed the patrol to the next step."""

        if path == PatrolChoice.DECLINE:
            if self.patrol_event:
                print(
                    f"PATROL ID: {self.patrol_event.event_id} | SUCCESS: N/A (did not proceed)"
                )
                return (
                    event_text_adjust(
                        Cat,
                        choice(self.patrol_event.decline_strings),
                        involved_cat_dict=self.involved_cats,
                        clan=game.clan,
                        other_clan=self.other_clan,
                        chosen_poi=self.chosen_poi,
                    ),
                    "",
                    {},
                    None,
                )
            else:
                return "Error - no event chosen", "", {}, None

        return self.determine_outcome(antagonize=(path == PatrolChoice.ANTAGONIZE))

    def _create_needed_cats(self):
        """
        Creates needed cats for the patrol start.  In its own function for unit testing purposes.
        """
        handle_consequences.create_needed_cats(
            self.patrol_event, self.involved_cats, self.other_clan
        )

    def _add_patrol_cats(self, patrol_cats: List[Cat]) -> None:
        """
        Sorts and categorizes patrol cats, then determines a patrol leader.
        :param patrol_cats: list of cats which are on the patrol
        """
        self.involved_cats.clear()

        # ADD TO PATROL_CATS

        self.patrol_cats = patrol_cats
        for cat in patrol_cats:
            # ADD TO STATUS LIST
            if cat.status.rank in self.involved_cats:
                self.involved_cats[cat.status.rank].append(cat)
            else:
                self.involved_cats[cat.status.rank] = [cat]

            # Combined patrol_statuses categories
            if cat.status.rank.is_any_medicine_rank():
                if "healer cats" in self.involved_cats:
                    self.involved_cats["healer cats"].append(cat)
                else:
                    self.involved_cats["healer cats"] = [cat]

            if cat.status.rank.is_any_apprentice_rank():
                if "all apprentices" in self.involved_cats:
                    self.involved_cats["all apprentices"].append(cat)
                else:
                    self.involved_cats["all apprentices"] = [cat]

            if (
                cat.status.rank.is_any_adult_warrior_like_rank()
                and cat.age != CatAge.ADOLESCENT
            ):
                if "normal adult" in self.involved_cats:
                    self.involved_cats["normal adult"].append(cat)
                else:
                    self.involved_cats["normal adult"] = [cat]

            # LG
            if cat.status.group == CatGroup.DARK_FOREST and cat != game.clan.your_cat:
                if "df" in self.involved_cats:
                    self.involved_cats["df"].append(cat)
                else:
                    self.involved_cats["df"] = [cat]

            # only ClanGen patrols use up a cat's patrol for the moon
            if switch_get_value(Switch.patrol_category) == "clangen":
                game.patrolled.append(cat.ID)
            elif switch_get_value(Switch.patrol_category) == "date":
                game.dated_cats.append(cat.ID)
            # ---

        # DETERMINE PATROL LEADER
        # THIS CANNOT CHANGE AFTER SET-UP
        # sets medcat as patrol leader if they're in the patrol
        if CatRank.MEDICINE_CAT in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.MEDICINE_CAT]

        # If there is no medicine cat, but there is a medicine cat apprentice, set them as the patrol leader.
        # This prevents warriors from being treated as medicine cats in medicine cat patrols.
        elif CatRank.MEDICINE_APPRENTICE in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.MEDICINE_APPRENTICE]

        # if no meddies set leader as patrol leader
        elif CatRank.LEADER in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.LEADER]

        # if no leader set the deputy as patrol leader
        elif CatRank.DEPUTY in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.DEPUTY]

        # if not deputy, try warriors
        elif CatRank.WARRIOR in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.WARRIOR]
        # if no warriors, set oldest or most experienced of any cats as patrol lead
        else:
            possible_leads = self.patrol_cats

        # Flip a coin to pick the most experienced or the oldest.
        if randint(0, 1):
            possible_leads.sort(key=lambda x: x.moons)
        else:
            possible_leads.sort(key=lambda x: x.experience)

        self.involved_cats["p_l"] = possible_leads[-1]

        # LG: you're always the leader of LifeGen patrols
        if switch_get_value(Switch.patrol_category) != "clangen":
            self.involved_cats["p_l"] = game.clan.your_cat
            self.involved_cats["y_c"] = game.clan.your_cat
            self._add_lifegen_random_cat(patrol_cats)
        # ---

        self.involved_cats["patrol_cats"] = patrol_cats
        # some_patrol will be a random assortment of the patrol cats, but not 1 nor all
        if len(patrol_cats) >= 3:
            self.involved_cats["some_patrol"] = sample(
                patrol_cats,
                k=randint(min(2, len(patrol_cats)), min(5, len(patrol_cats) - 1)),
            )

        print("Patrol Leader:", str(self.involved_cats["p_l"].name))

    def _add_lifegen_random_cat(self, patrol_cats: List[Cat]):
        """
        LG: LifeGen patrols still use the old r_c (random patrol cat) and o_c1-4 (other patrol cats) abbreviations
        """
        your_cat = game.clan.your_cat
        others = [c for c in patrol_cats if c.ID != your_cat.ID]

        random_cat = None
        if switch_get_value(Switch.patrol_category) == "date":
            random_cat = others[0] if others else None
        elif switch_get_value(Switch.patrol_category) == "df" and others:
            # if there's df cats on the patrol, r_c will always be DF to make writing a bit more open
            df_cats = [c for c in others if c.status.group == CatGroup.DARK_FOREST]
            random_cat = choice(df_cats) if df_cats else choice(others)
        elif others:
            # prioritize grabbing an adult as the random cat
            adults = [
                c for c in others if c in self.involved_cats.get("normal adult", [])
            ]
            random_cat = choice(adults) if adults else choice(others)

        if not random_cat:
            random_cat = self.involved_cats["p_l"]
        self.involved_cats["r_c"] = random_cat

        other_cats = [c for c in others if c != random_cat]
        for i, other_cat in enumerate(other_cats[:4]):
            self.involved_cats[f"o_c{i + 1}"] = other_cat

    def _load_patrols_and_set_patrol(
        self,
        patrol_type: str,
    ):
        # ---------------------------------------------------------------------------- #
        #                                LOAD RESOURCES                                #
        # ---------------------------------------------------------------------------- #

        # LG: LifeGen patrol categories have their own patrol pools
        if switch_get_value(Switch.patrol_category) != "clangen":
            self.patrol_event = self._filter_and_set_lifegen_patrol(
                get_lifegen_patrol_list(switch_get_value(Switch.patrol_category))
            )
            return

        # this is needed for Classic specifically
        # Classic doesn't let you pick patrol type, so instead we specify herb_gathering if meddies are present
        patrol_type = (
            "herb_gathering"
            if {CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE}.intersection(
                set(self.involved_cats.keys())
            )
            else patrol_type
        )
        # This make sure general only gets hunting, border, or training patrols
        if patrol_type == "general":
            # choosing a type now means that the type of patrol later chosen isn't influenced
            # by the amount of patrols available of that type
            patrol_type = random.choice(["hunting", "border", "training"])

        # GET PATROL LIST
        patrol_list = get_patrol_list(
            patrol_type,
            outsider_rep=will_allow_outsider_patrols(
                small_clan=int(len(game.clan.clan_cats))
                < get_config("patrol_generation.small_clan_threshold")
            ),
            other_clan_rep=self.other_clan.get_standing() if self.other_clan else None,
        )

        # INFORM -NOT PRESENT-
        patrol_ids = [patrol.event_id for patrol in patrol_list]
        if self.debug_patrol_id and self.debug_patrol_id not in patrol_ids:
            print(
                "DEBUG: requested patrol not present (check spelling/mismatched season, biome, patrol type, new cat flag, other clan relations, disaster setting)"
            )

        # DEBUG - NO FILTER
        # This is a debug option, this allows you to remove any constraints of a patrol regarding location, session, biomes, etc.
        if get_config(
            "patrol_generation.debug_ensure.override_patrol_stat_requirements"
        ):
            if self.debug_patrol_id:
                chosen_patrol = [
                    p for p in patrol_list if p.event_id == self.debug_patrol_id
                ][0]
            else:
                chosen_patrol = choice(patrol_list)
            print(
                "All patrol filters regarding location, session, etc. have been removed."
            )
        # FILTER PATROLS when no debug set
        else:
            chosen_patrol = self._filter_and_set_patrol(patrol_list, patrol_type)

        self.patrol_event = chosen_patrol

    def _decide_if_romantic(
        self, romantic_event: Optional[PatrolEvent], involved_cats: dict
    ) -> bool:
        """
        Finds the chance of this patrol being romantic based on the cats involved and their current relationship with each other
        :return: True if patrol should be romantic, False otherwise
        """

        if not romantic_event:
            print("No romantic event")
            return False

        if romantic_event == self.debug_patrol_id:
            return True

        chance_of_romance_patrol = get_config(
            "patrol_generation.chance_of_romance_patrol"
        )

        for block in romantic_event.relationship_constraint:
            if "can_romance" in block["constraints"]:
                # gather the kitty cats
                cats_from = gather_cat_objects(
                    Cat,
                    block["cats_from"],
                    event=self,
                    involved_cats=involved_cats,
                )
                cats_to = gather_cat_objects(
                    Cat, block["cats_to"], event=self, involved_cats=involved_cats
                )
                # now affect the chance depending on the compatibility
                for c in cats_from:
                    compatibility = [
                        get_personality_compatibility(c, love_cat)
                        for love_cat in cats_to
                        if love_cat != c
                    ]
                    for compat in compatibility:
                        if compat == CatCompatibility.POSITIVE:
                            chance_of_romance_patrol -= 5
                        elif compat == CatCompatibility.NEGATIVE:
                            chance_of_romance_patrol += 5

                    rel_values = [
                        check_relationship_value(c, love_cat, val)
                        for val in [*RelType]
                        for love_cat in cats_to
                        if love_cat != c
                    ]
                    for v in rel_values:
                        if v > 0:
                            chance_of_romance_patrol -= 1
                        else:
                            chance_of_romance_patrol += 1

        if chance_of_romance_patrol <= 0:
            chance_of_romance_patrol = 1
        print("final romance chance:", chance_of_romance_patrol)
        return not int(random.random() * chance_of_romance_patrol)

    def _filter_and_set_patrol(
        self,
        possible_patrols: List[PatrolEvent],
        patrol_type: str,
    ) -> PatrolEvent:
        # GET POSSIBLE PATROLS
        # filter for type initially
        possible_patrols = [
            p
            for p in possible_patrols
            if self._check_patrol_type(
                p, patrol_type, is_debug_patrol=p.event_id == self.debug_patrol_id
            )
        ]
        # make sure the hunting and herb patrols are balanced
        if patrol_type == "hunting" and not self.debug_patrol_id:
            possible_patrols = self._balance_hunting(possible_patrols)
        if patrol_type == "herb_gathering" and not self.debug_patrol_id:
            possible_patrols = self._balance_herbs(possible_patrols)

        # separate into the two lists
        normal_patrols: list[PatrolEvent] = []
        romantic_patrols: list[PatrolEvent] = []
        for p in possible_patrols:
            if "romance" in p.tags:
                romantic_patrols.append(p)
            else:
                normal_patrols.append(p)

        print(
            f"Total Number of Possible Patrols | normal: {len(normal_patrols)}, romantic: {len(romantic_patrols)} "
        )

        # GET PATROL
        chosen_patrol: Optional[PatrolEvent] = None

        # first we see if we can get a romantic patrol
        if romantic_patrols:
            chosen_patrol = self._set_valid_patrol(
                romantic_patrols.copy(), find_romance=True
            )

        # if no romantic patrol possible, we get a normal one!
        if not chosen_patrol:
            chosen_patrol = self._set_valid_patrol(
                normal_patrols.copy(), find_romance=False
            )
            if not chosen_patrol:
                raise Exception(
                    "ERROR: No patrols could be found, even after resetting the used patrol list."
                )

        return chosen_patrol

    def _filter_and_set_lifegen_patrol(
        self, possible_patrols: List[PatrolEvent]
    ) -> PatrolEvent:
        """
        LG: Filters the LifeGen patrol pool, picks the random r_c:X cats, and returns the chosen patrol
        """
        your_cat = game.clan.your_cat
        self.lifegen_random_cats.clear()

        normal_patrols: list[PatrolEvent] = []
        romantic_patrols: list[PatrolEvent] = []
        for patrol in possible_patrols:
            if not self._lifegen_patrol_allowed(patrol):
                continue

            if patrol.random_cats:
                cat_dict = choose_random_cats(
                    cats_block=patrol.random_cats,
                    rel_block=patrol.relationships,
                    your_cat=your_cat,
                    the_cat=None,
                    cat_dict={"p_l": your_cat},
                )
                if not cat_dict:
                    continue
                self.lifegen_random_cats[patrol.event_id] = {
                    abbr: c for abbr, c in cat_dict.items() if abbr.startswith("r_c:")
                }

            if "romance" in patrol.tags:
                romantic_patrols.append(patrol)
            else:
                normal_patrols.append(patrol)

        print(
            f"Total Number of Possible Patrols | normal: {len(normal_patrols)}, romantic: {len(romantic_patrols)} "
        )

        # we don't have enough patrols to rely on the frequency
        chosen_patrol = None
        if romantic_patrols:
            chosen_patrol = self._set_valid_patrol(
                romantic_patrols, find_romance=True, frequency_active=False
            )
        if not chosen_patrol:
            chosen_patrol = self._set_valid_patrol(
                normal_patrols, find_romance=False, frequency_active=False
            )
        if not chosen_patrol:
            raise RuntimeError("ERROR: No LifeGen patrols could be found.")

        # random cats go first, so that r_c:X gets replaced before r_c in the patrol texts
        self.involved_cats = {
            **self.lifegen_random_cats.get(chosen_patrol.event_id, {}),
            **self.involved_cats,
        }

        return chosen_patrol

    def _lifegen_patrol_allowed(self, patrol: PatrolEvent) -> bool:
        """
        LG: checks the LifeGen specific patrol tags
        """
        your_cat = game.clan.your_cat
        category = switch_get_value(Switch.patrol_category)
        is_shunned = your_cat.status.is_shunned()

        if category == "lifegen":
            afterlife_tags = {
                "sc_lifegen": CatGroup.STARCLAN,
                "df_lifegen": CatGroup.DARK_FOREST,
                "ur_lifegen": CatGroup.UNKNOWN_RESIDENCE,
            }
            if your_cat.dead and not any(t in patrol.tags for t in afterlife_tags):
                return False
            for tag, group in afterlife_tags.items():
                if tag in patrol.tags:
                    if your_cat.status.group != group:
                        return False
                    break

        if category == "df":
            if len(self.patrol_cats) > 1:
                other_cat = self.patrol_cats[1]
                if bool(other_cat.joined_df) != ("fellowtrainee" in patrol.tags):
                    return False

            if "mc_death" in patrol.tags and randint(1, 8) != 1:
                return False

            if "shunned" in patrol.tags and not is_shunned:
                return False
        else:
            if "shunned" in patrol.tags and not is_shunned:
                return False
            if "shunned" not in patrol.tags and "df" not in patrol.tags and is_shunned:
                return False

        if category == "date" and "df" in patrol.tags and len(self.patrol_cats) > 1:
            # need both cats to be trainees for goop romance
            if not your_cat.joined_df or not self.patrol_cats[1].joined_df:
                return False

        return True

    def _set_valid_patrol(
        self,
        possible_patrols: List[PatrolEvent],
        find_romance: bool = False,
        frequency_active: bool = True,
    ) -> Optional[PatrolEvent]:
        """
        Finds a valid patrol
        If one if found, sets the patrol event and involved cats,
            and returns the patrol event.
        """
        chosen_patrol = None
        patrols_to_test = [
            p
            for p in possible_patrols
            if p.event_id
            not in Patrol.used_patrols["romance" if find_romance else "normal"]
        ]
        while not chosen_patrol:
            chosen_patrol, involved_cats = get_valid_event(
                primary_cat=self.involved_cats["p_l"],
                involved_cats=self.involved_cats,
                interactable_cats=self.involved_cats["patrol_cats"],
                possible_events=patrols_to_test,
                other_clan=self.other_clan,
                ensured_id=self.debug_patrol_id,
                frequency_active=frequency_active,
            )
            if not chosen_patrol:
                if not Patrol.used_patrols["romance" if find_romance else "normal"]:
                    # No patrols found even after resetting used patrols.
                    # This should only be possible when filtering for romance patrols.
                    return None

                # if we couldn't find a patrol, then we need to clear the used_patrols and try again
                Patrol.used_patrols["romance" if find_romance else "normal"].clear()
                patrols_to_test = possible_patrols.copy()

        if find_romance:
            if not self._decide_if_romantic(chosen_patrol, involved_cats):
                return None
            Patrol.used_patrols["romance"].append(chosen_patrol.event_id)
        else:
            Patrol.used_patrols["normal"].append(chosen_patrol.event_id)

        self.patrol_event = chosen_patrol
        self.involved_cats = involved_cats
        return chosen_patrol

    @staticmethod
    def _check_patrol_type(
        patrol: PatrolEvent, patrol_type: str, is_debug_patrol: bool
    ) -> bool:
        # CHECK PATROL TYPE
        if patrol_type not in patrol.types:
            if is_debug_patrol:
                print("DEBUG: requested patrol does not meet constraints (patrol type)")
            return False

        return True

    def _find_allowed_outcomes(
        self, antagonize: bool = False
    ) -> tuple[TextPoolEvent, TextPoolEvent]:
        """
        Filters through possible outcomes to find appropriate outcomes for both failure and success
        :param antagonize: set True if the player chose to antagonize
        :return: success outcome, failure outcome
        """

        # find which set of outcomes we'll be using based on if the player choose to antagonize
        if antagonize:
            success_outcomes = self.patrol_event.antag_success_outcomes
            fail_outcomes = self.patrol_event.antag_fail_outcomes
        else:
            success_outcomes = self.patrol_event.success_outcomes
            fail_outcomes = self.patrol_event.fail_outcomes

        # LG: med_name can only be used if there's a medicine cat to name
        if not find_alive_cats_with_rank(Cat, [CatRank.MEDICINE_CAT], working=True):
            success_outcomes = [
                o
                for o in success_outcomes
                if not any("med_name" in text for text in o.strings)
            ] or success_outcomes
            fail_outcomes = [
                o
                for o in fail_outcomes
                if not any("med_name" in text for text in o.strings)
            ] or fail_outcomes

        debug_outcome = None
        if self.debug_patrol_id:
            # outcomes generate an ID based off their parent
            # it looks like {patrol_id}_{type of outcome}{index}
            outcome_index = get_config("patrol_generation.debug_ensure.outcome_index")
            outcome_type = get_config("patrol_generation.debug_ensure.outcome_type")
            debug_outcome = f"{self.debug_patrol_id}{'_antag' if antagonize else ''}{'_success' if outcome_type else '_fail'}{outcome_index}"

        # we'll get an outcome for both success and failure
        # FIND SUCCESS
        chosen_success, self.outcome_cats["success"] = get_valid_event(
            primary_cat=self.involved_cats["p_l"],
            involved_cats=self.involved_cats,
            interactable_cats=self.involved_cats["patrol_cats"],
            possible_events=success_outcomes,
            other_clan=self.other_clan,
            chosen_poi=self.chosen_poi if self.chosen_poi else None,
            ensured_id=debug_outcome,
        )

        if not chosen_success:
            raise Exception(
                f"Valid success outcome could not be found for {self.patrol_event.event_id}"
            )

        # FIND FAILURE
        chosen_failure, self.outcome_cats["failure"] = get_valid_event(
            primary_cat=self.involved_cats["p_l"],
            involved_cats=self.involved_cats,
            interactable_cats=self.involved_cats["patrol_cats"],
            possible_events=fail_outcomes,
            other_clan=self.other_clan,
            chosen_poi=self.chosen_poi if self.chosen_poi else None,
            ensured_id=debug_outcome,
        )
        if not chosen_failure:
            raise Exception(
                f"Valid fail outcome could not be found for {self.patrol_event.event_id}"
            )

        return chosen_success, chosen_failure

    def _check_outcome_constraints(
        self, outcome: TextPoolEvent, outcome_type: Literal["success", "failure"]
    ) -> bool:
        """
        Checks the outcome constraints and attempts to find appropriate cats. If the outcome is valid and cats are
        found, the cats will be added to the matching `self.outcome_cats` dict
        :param outcome: outcome to check
        :param outcome_type: the outcome_cats dict that the valid cats should be added to
        """
        # BASICS
        if not passes_general_constraints(
            outcome, self.involved_cats["p_l"], self.involved_cats
        ):
            return False

        # CATS
        outside_cats = [
            c
            for c in Cat.all_cats_list
            if (c.status.is_other_clancat or c.status.is_outsider) and not c.dead
        ]
        temp_involved_cats = self.involved_cats.copy()

        temp_involved_cats, will_create_how_many = find_cats(
            interactable_cats=temp_involved_cats["patrol_cats"],
            involved_cats=temp_involved_cats,
            outside_cats=outside_cats,
            event=outcome,
            other_clan=self.other_clan,
        )
        if not (temp_involved_cats or will_create_how_many):
            return False

        # if we're here, then we must have found all our cats!
        self.outcome_cats[outcome_type] = temp_involved_cats

        return True

    def determine_outcome(
        self, antagonize=False
    ) -> Tuple[str, str, dict, pygame.Surface | None]:
        if self.patrol_event is None:
            raise Exception("No patrol event supplied")

        success_outcome, fail_outcome = self._find_allowed_outcomes(antagonize)

        chosen_outcome, success = self.calculate_success(success_outcome, fail_outcome)

        # LG
        if switch_get_value(Switch.patrol_category) == "date":
            self._handle_date_relationships(success)
        elif switch_get_value(Switch.patrol_category) == "df" and success:
            game.clan.your_cat.df_patrols += 1
            # graduate from the Dark Forest after 5 successful DF patrols. Once
            # graduated, the cat can act as a mentor to other DF trainees.
            if (
                game.clan.your_cat.df_patrols >= 5
                and not game.clan.your_cat.graduated_df
            ):
                game.clan.your_cat.graduated_df = True
        # ---

        if not self.chosen_poi and chosen_outcome.poi:
            self.chosen_poi = get_poi_from_constraints(
                chosen_outcome.poi.get("name"),
                chosen_outcome.poi.get("tags"),
                chosen_outcome.poi.get("category"),
            )

        print(f"PATROL ID: {self.patrol_event.event_id} | SUCCESS: {success}")
        print(f"Success Outcome: {success_outcome} | Failure Outcome: {fail_outcome}")
        print(
            f"Patrol Frequency: {self.patrol_event.frequency} | Patrol Weight: {self.patrol_event.weight}"
        )
        print(
            f"Outcome Frequency: {chosen_outcome.frequency} | Outcome Weight: {chosen_outcome.weight}"
        )

        processed_text, results, rel_results = handle_consequences.execute_outcome(
            chosen_outcome,
            self.outcome_cats["success" if success else "failure"],
            self.other_clan,
            self.chosen_poi,
        )
        final_results = []
        for r in results.values():
            # filter out the "empty" values
            if r:
                final_results.append(r)

        # LG: murder, accessories, dark forest conversion and faith
        for r in execute_lifegen_outcome(
            self.patrol_event.lifegen_outcomes.get(chosen_outcome.event_id),
            self.outcome_cats["success" if success else "failure"],
            self.other_clan,
        ):
            if r and r.strip():
                final_results.append(r)

        # Run the chosen outcome
        return (
            processed_text,
            "\n".join(final_results),
            rel_results,
            self.get_patrol_art(chosen_outcome),
        )

    def calculate_success(
        self, success_outcome: TextPoolEvent, fail_outcome: TextPoolEvent
    ) -> Tuple[TextPoolEvent, bool]:
        """Returns both the chosen outcome, and a boolean that's True if success, and False if failure."""

        patrol_size = len(self.patrol_cats)
        total_exp = sum([x.experience for x in self.patrol_cats])
        path = (
            "patrol_generation.classic_difficulty_modifier"
            if game.clan.game_mode == "classic"
            else "patrol_generation.difficulty_modifier"
        )

        gm_modifier = get_config(path)

        exp_adjustment = (
            (1 + 0.10 * patrol_size) * total_exp / (patrol_size * gm_modifier * 2)
        )

        success_chance = self.patrol_event.chance_of_success + int(exp_adjustment)
        success_chance = min(success_chance, 90)

        # Now, apply success and fail skill
        print(
            "starting chance:",
            self.patrol_event.chance_of_success,
            "| EX_updated chance:",
            success_chance,
        )

        # Skill and trait stuff
        for abbr, constraints in success_outcome.involved_cats.items():
            # if this is present, then we know a cat must fulfill it
            if stat_block := constraints.get("stat"):
                cat = self.outcome_cats["success"].get(abbr)
                if not cat:
                    # likely an n_c cat that hasn't been made yet
                    continue
                if "skill" in stat_block:
                    success_chance += get_config(
                        "patrol_generation.skill_cat_modifier"
                    ) * cat.skills.check_skill_requirement_list(stat_block["skill"])
                    print(f"success chance increase to {success_chance}")
                elif "trait" in stat_block:
                    success_chance += get_config("patrol_generation.trait_cat_modifier")
                    print(f"success chance increase to {success_chance}")
            # LG: personality clusters count like traits
            elif constraints.get("cluster") and self.outcome_cats["success"].get(abbr):
                success_chance += get_config("patrol_generation.trait_cat_modifier")
                print(f"success chance increase to {success_chance}")

        # LG: dates depend on how your date feels about you
        if switch_get_value(Switch.patrol_category) == "date":
            success_chance = self._get_date_success_chance()

        if success_chance >= 120:
            success_chance = 115
            print("success chance over 120, updated to 115")

        success = int(random.random() * 120) < success_chance

        # This is a debug option, this will forcefully change the outcome of a patrol
        if isinstance(get_config("patrol_generation.debug_ensure.outcome_type"), bool):
            success = get_config("patrol_generation.debug_ensure.outcome_type")
            # Logging
            print(
                f"The outcome of {self.patrol_event.event_id} was altered to {success}"
            )

        return success_outcome if success else fail_outcome, success

    def _get_date_success_chance(self) -> int:
        """LG: Finds the success chance of a date patrol from the date's relationship towards the player's cat"""
        you = game.clan.your_cat
        date = self.involved_cats.get("r_c")
        success_chance = 40
        if not date or date is you:
            return success_chance

        relationship = date.relationships.get(you.ID)
        if relationship:
            if relationship.romance > 50:
                success_chance += 40
            elif relationship.romance > 40:
                success_chance += 30
            elif relationship.romance > 30:
                success_chance += 20
            elif relationship.romance > 10:
                success_chance += 10

            if relationship.like > 40:
                success_chance += 15
            elif relationship.like > 30:
                success_chance += 10
            elif relationship.like > 20:
                success_chance += 5

            if relationship.like < -50:
                success_chance -= 50
            if relationship.like < -30:
                success_chance -= 40
            if relationship.like < -20:
                success_chance -= 30
            if relationship.like < 0:
                success_chance -= 10
            success_chance += randint(-20, 20)
        success_chance = max(10, min(90, success_chance))

        if randint(1, 100) < success_chance:
            if not date.relationships.get(you.ID):
                create_one_relationship(date, you)
            if not you.relationships.get(date.ID):
                create_one_relationship(you, date)
            date.relationships[you.ID].romance += 10
            you.relationships[date.ID].romance += 10

        print(f"date success chance: {success_chance}")
        return success_chance

    def _handle_date_relationships(self, success: bool):
        """LG: date patrols affect the relationship between the player's cat and their date"""
        you = game.clan.your_cat
        date = self.involved_cats.get("r_c")
        if not date or date is you:
            return

        to_date = you.relationships.get(date.ID)
        from_date = date.relationships.get(you.ID)
        if success:
            for rel in (to_date, from_date):
                if not rel:
                    continue
                rel.romance += randint(1, 5)
                rel.trust += randint(1, 5)
                rel.comfort += randint(1, 5)
        elif from_date:
            from_date.romance -= randint(1, 5)
            from_date.trust -= randint(1, 5)
            from_date.comfort -= randint(1, 5)

    def _balance_hunting(
        self, possible_patrols: list[PatrolEvent]
    ) -> list[PatrolEvent]:
        """
        Check which prey amount we want to allow this clan to get and filter the possible_patrols accordingly to ensure
        they only have patrols where that amount is possible.
        :param possible_patrols: The list of possible patrols
        :returns: The list of possible patrols but filtered to only include those patrols which have the chosen prey
        amount. If there were no patrols with the chosen prey amount, then the original list is returned
        """
        filtered_patrols = []

        # get first what kind of prey size which will be chosen
        biome = (
            game.clan.biome
            if not game.clan.override_biome
            else game.clan.override_biome
        )
        prey_sizes = ["tiny", "small", "medium", "large", "huge"]
        prey_size_random_weights = get_config(
            f"prey.patrol_balance.{biome}.{game.clan.current_season}"
        )

        chosen_prey_size = choices(prey_sizes, weights=prey_size_random_weights)[0]
        print(f"chosen filter prey size: {chosen_prey_size}")

        # filter all possible patrols depending on the needed prey size
        for patrol in possible_patrols:
            # count how many outcomes award each prey size
            prey_size_to_outcome_amounts = {}
            for outcome in patrol.success_outcomes:
                if outcome.supply:
                    for block in outcome.supply:
                        if block["type"] != "freshkill":
                            continue
                        outcome_prey_size = block["adjust"].replace("increase_", "")
                        if outcome_prey_size not in prey_size_to_outcome_amounts:
                            prey_size_to_outcome_amounts[outcome_prey_size] = 0
                        prey_size_to_outcome_amounts[outcome_prey_size] += 1

            # get the prey size with the most outcomes
            most_prey_size = ""
            max_occurrences = 0
            for size, amount in prey_size_to_outcome_amounts.items():
                if amount >= max_occurrences:
                    most_prey_size = size
                    max_occurrences = amount

            # if the most often awarded prey size matches the one we want, then we allow this patrol through
            if chosen_prey_size == most_prey_size:
                filtered_patrols.append(patrol)
            elif self.debug_patrol_id and self.debug_patrol_id == patrol.event_id:
                print(
                    f"DEBUG: requested patrol does not meet constraints (did not have the prey amount required for prey balancing)"
                )
        # if the filtering results in an empty list, don't filter and return whole possible patrols
        if len(filtered_patrols) <= 0:
            print(
                "---- WARNING ---- attempted prey balancing filtering, but there were no patrols with the required prey amount."
            )
            return possible_patrols

        return filtered_patrols

    @staticmethod
    def _balance_herbs(possible_patrols: list[PatrolEvent]) -> list[PatrolEvent]:
        """
        Finds and returns patrols that add herbs the medicine cats are currently looking for
        """
        target_herbs = game.clan.herb_supply.sorted_by_need

        allowed_patrols = []
        for patrol in possible_patrols:
            # if any herb can happen, then we return True
            if "random_herbs" in patrol.herbs_given:
                allowed_patrols.append(patrol)

            # if the patrol is not able to give herbs we need, we return False
            if set(patrol.herbs_given).intersection(set(target_herbs)):
                allowed_patrols.append(patrol)

        return allowed_patrols

    def get_patrol_art(self, outcome: TextPoolEvent = None) -> Optional[pygame.Surface]:
        """Return's patrol art surface"""
        if not self.patrol_event or not isinstance(self.patrol_event.patrol_art, str):
            return pygame.Surface((600, 600), flags=pygame.SRCALPHA)

        root_dir = "resources/images/patrol_art/"

        clean_art = (
            self.patrol_event.patrol_art_clean
            if not outcome
            else outcome.outcome_art_clean
        )
        if not game_setting_get("gore") and clean_art:
            file_name = clean_art
        else:
            file_name = (
                self.patrol_event.patrol_art if not outcome else outcome.outcome_art
            )
            if file_name == "POI":
                file_name = f"backgrounds/poi_{self.chosen_poi}"

        if not isinstance(file_name, str) or not path_exists(
            f"{root_dir}{file_name}.png"
        ):
            if outcome:
                # we return None so that we don't overwrite the patrol's general art.
                # if we got here on an outcome, then the outcome had no attached art and we should just be using
                # the patrol's general art
                return None
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
