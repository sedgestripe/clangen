import random

from scripts.game_structure import game, constants
from scripts.special_dates import get_special_date
from scripts.game_structure.game.switches import switch_get_value, Switch
from scripts.game_structure.localization import load_lang_resource
from scripts.cat.enums import CatRank, CatAge
from scripts.cat.cats import Cat
from scripts.cat.pelts import Pelt
from scripts.events_module.consequences import unpack_rel_block


from scripts.events_module.filter_random_cats import choose_random_cats

# pylint: disable=consider-using-dict-items


class Dialogue:
    def __init__(self, cat: Cat, you: Cat):
        self.cat = cat
        self.you = you
        self.debug = constants.CONFIG["lifegen"]["debug"]["debug_ensure_dialogue"]
        self.cat_dict = {}

        # holds a cat dict for each dialogue key
        self.dialogue_cat_dict = {}

    def load_texts(self):
        """
        Loads dialogue depending on rank, group, age
        """

        resource_dir = "lifegen_talk"
        possible_texts = {}

        special_date = get_special_date()

        if switch_get_value(Switch.talk_category) == "insult":
            possible_texts.update(load_lang_resource(f"{resource_dir}/insults.json"))
        elif switch_get_value(Switch.talk_category) == "flirt":
            possible_texts.update(load_lang_resource(f"{resource_dir}/flirt.json"))
        else:
            possible_texts.update(
                load_lang_resource(
                    f"{resource_dir}/{self.cat.status.rank.replace(' ', '_')}.json"
                )
            )
            if self.cat.status.is_outsider:
                possible_texts.update(
                    load_lang_resource(f"{resource_dir}/general_outsider.json")
                )
            else:
                if self.cat.status.rank != CatRank.NEWBORN:
                    # newborns will no longer participate in nuanced discussion

                    if (
                        not self.cat.status.rank.is_baby()
                        and not self.you.status.rank.is_baby()
                    ):
                        possible_texts.update(
                            load_lang_resource(f"{resource_dir}/general_no_kit.json")
                        )
                    if (
                        self.cat.age != CatAge.NEWBORN
                        and self.you.age != CatAge.NEWBORN
                    ):
                        possible_texts.update(
                            load_lang_resource(
                                f"{resource_dir}/general_no_newborn.json"
                            )
                        )
                    if (
                        not self.cat.status.rank.is_baby()
                        and self.you.status.rank.is_baby()
                    ):
                        possible_texts.update(
                            load_lang_resource(f"{resource_dir}/general_you_kit.json")
                        )
                    if game.clan.focus:
                        possible_texts.update(
                            load_lang_resource(
                                f"{resource_dir}/focuses/{game.clan.focus}.json"
                            )
                        )
                    if special_date:
                        possible_texts.update(
                            load_lang_resource(
                                f"{resource_dir}/focuses/{special_date.patrol_tag}.json"
                            )
                        )
                    if constants.CONFIG["fun"]["april_fools"]:
                        possible_texts.update(
                            load_lang_resource(
                                f"{resource_dir}/focuses/aprilfools.json"
                            )
                        )

        # uncomment below to limit dialogue range
        # this can cut down on dialogue delay, but also cause some meow errors

        # dialogue_range = 200
        # shuffled_dict = dict(random.sample(list(possible_texts.items()), len(possible_texts)))
        # new_dict = {}
        # count = 0
        # for key, dialogue in shuffled_dict.items():
        #     if count >= dialogue_range:
        #         break
        #     new_dict[key] = dialogue
        #     count += 1
        # possible_texts = new_dict

        # DEBUG
        # possible_texts = load_lang_resource("lifegen_talk/TEST.json")
        return possible_texts

    def filter_dialogue(self, possible_texts, flirt):
        """
        Filters possible dialogue for selection.
        Season, biome, camp, and frequency are addressed here. Cats are validated later.
        """

        flirt_success = self.get_flirt_success()

        possible_dialogue = {}
        for key, block in possible_texts.items():
            if "season" in block:
                if (
                    game.clan.current_season not in block["season"]
                    and game.clan.current_season.lower() not in block["season"]
                ):
                    continue
            if "biome" in block:
                if (
                    block["biome"]
                    and game.clan.biome not in block["biome"]
                    and game.clan.biome.lower() not in block["biome"]
                ):
                    continue
            if "camp" in block:
                if block["camp"] and game.clan.camp_bg not in block["camp"]:
                    continue

            if "frequency" in block:
                count = block["frequency"]
                for other_block in block:
                    if other_block in ["season", "biome", "camp", "relationships"]:
                        count += 1
                for i in range(count):
                    possible_dialogue.update({key: block})
            else:
                print("Warning: Dialogue", key, "has no frequency.")
                possible_dialogue.update({key: block})

            if flirt:
                if "tags" in block:
                    if "reject" in block["tags"] and flirt_success:
                        continue
                    elif "accept" in block["tags"] and not flirt_success:
                        continue
                else:
                    if not flirt_success:
                        continue

        return possible_dialogue

    def get_cat_dict(self):
        """
        Returns the cat dict for use in TalkScreen
        """
        return self.cat_dict

    def choose_dialogue(self, possible_dialogue, flirt=False):
        """
        Makes a final selection.
        Returns the key and the dict object.
        """
        possible_dialogue = self.filter_dialogue(possible_dialogue, flirt)

        if not possible_dialogue:
            possible_dialogue = load_lang_resource("lifegen_talk/general.json")

        possible_dialogue_keys = list(possible_dialogue.keys())

        debug_dict = {}
        for key in possible_dialogue_keys.copy():
            if len(possible_dialogue_keys) > 2:
                if key in game.clan.talks and key != self.debug:
                    possible_dialogue_keys.remove(key)
            if key not in debug_dict:
                debug_dict[key] = 1
            else:
                debug_dict[key] += 1

        # debug print
        # print()
        # print("DIALOGUE WEIGHTS")
        # for key, value in debug_dict.items():
        #     print(f"{key}: {value}")

        debug_valid = False
        chosen_key = None
        chosen_cat_dict = {}
        if self.debug:
            if constants.CONFIG["lifegen"]["debug"][
                "debug_dialogue_override_filtering"
            ]:
                print(f"Debug: Dialogue set to {self.debug} with overridden filtering.")
                chosen_key = self.debug

                # assembling a new "cats" block with empty constraints for purely random cats
                debugged_cats_block = {}
                for cat in possible_dialogue[chosen_key]["cats"]:
                    debugged_cats_block[cat] = {}

                # pick cats
                chosen_cat_dict = choose_random_cats(
                    cats_block=debugged_cats_block,
                    rel_block=[],
                    your_cat=self.you,
                    the_cat=self.cat,
                    cat_dict=self.cat_dict,
                )
                debug_valid = True
            elif self.debug in possible_dialogue_keys:
                print(f"Debug: Dialogue set to {self.debug}")
                chosen_key = self.debug

                chosen_cat_dict = choose_random_cats(
                    cats_block=possible_dialogue[chosen_key]["cats"],
                    rel_block=(
                        possible_dialogue[chosen_key]["relationships"]
                        if "relationships" in possible_dialogue[chosen_key]
                        else []
                    ),
                    your_cat=self.you,
                    the_cat=self.cat,
                    cat_dict=self.cat_dict,
                )
                if chosen_cat_dict:
                    debug_valid = True

            if debug_valid:
                self._populate_cat_dict(chosen_key, chosen_cat_dict)

        if not debug_valid:
            # if the debug dialogue failed OR debug isnt set at all
            # so, normal dialogue
            if self.debug:
                print(
                    f"Debugged Dialogue ID ({self.debug}) is not in possible dialogue options."
                    + " Set debug_dialogue_override_filtering to true to override filtering."
                )
            # shuffle dialogue
            possible_dialogue = dict(
                random.sample(list(possible_dialogue.items()), len(possible_dialogue))
            )
            # check possible dialogue for valid cat constraints
            for key, dialogue_block in possible_dialogue.items():
                chosen_cat_dict = choose_random_cats(
                    cats_block=dialogue_block["cats"],
                    rel_block=dialogue_block["relationships"]
                    if "relationships" in dialogue_block
                    else [],
                    your_cat=self.you,
                    the_cat=self.cat,
                    cat_dict=self.cat_dict,
                )
                if not chosen_cat_dict:
                    continue
                else:
                    chosen_key = key
                    # print("Choosing key:", chosen_key)
                    # print()
                    self._populate_cat_dict(chosen_key, chosen_cat_dict)
                    break
            if not chosen_key:
                # none possible within the attempt range :(
                possible_dialogue = load_lang_resource("lifegen_talk/general.json")
                chosen_key = "general"

        if chosen_key != "general":
            self.cat_dict = self.dialogue_cat_dict[chosen_key]
            game.clan.talks.append(chosen_key)
        else:
            self.cat_dict = {"t_c": self.cat, "y_c": self.you}

        return chosen_key, possible_dialogue[chosen_key]

    # ---------------------------------------------------------------------- #
    #                                HELPERS                                 #
    # ---------------------------------------------------------------------- #

    def _populate_cat_dict(self, key, possible_cats_dict):
        self.dialogue_cat_dict[key] = possible_cats_dict

    def get_flirt_success(self):
        if self.you.ID not in self.cat.relationships:
            return False
        if self.cat.relationships[self.you.ID].romance < 20:
            return False
        return True

    # ---------------------------------------------------------------------- #
    #                            SCENE EFFECTS                               #
    # ---------------------------------------------------------------------- #

    def handle_scene_effects(self, current_scene, dialogue_object, cat_dict):
        """
        Handles scene effects such as accessories, relationship changes, and more.
        """
        if f"{current_scene}_scene_effects" not in dialogue_object:
            return
        scene_effects = dialogue_object[f"{current_scene}_scene_effects"]

        inventory_block = (
            scene_effects["inventory"] if "inventory" in scene_effects else {}
        )
        relationship_block = (
            scene_effects["relationships"] if "relationships" in scene_effects else {}
        )
        dark_forest_block = (
            scene_effects["dark_forest"] if "dark_forest" in scene_effects else {}
        )

        # inventory
        # try:
        if inventory_block:
            for cat_abbrev in inventory_block["cats_to"]:
                cat_to_object = cat_dict[cat_abbrev] if cat_abbrev in cat_dict else None
                if not cat_to_object:
                    return
                if inventory_block["addition"] == "choice":
                    chosen_accessory = random.choice(inventory_block["accessory"])
                    if chosen_accessory in Pelt.lifegen_acc_categories:
                        cat_to_object.pelt.inventory.append(
                            random.choice(Pelt.lifegen_acc_categories[chosen_accessory])
                        )
                    else:
                        cat_to_object.pelt.inventory.append(
                            random.choice(chosen_accessory)
                        )
                elif inventory_block["addition"] == "all":
                    for acc in inventory_block["accessory"]:
                        if acc in Pelt.lifegen_acc_categories:
                            cat_to_object.pelt.inventory.append(
                                random.choice(Pelt.lifegen_acc_categories[acc])
                            )
                        else:
                            cat_to_object.pelt.inventory.append(acc)

        if relationship_block:
            unpack_rel_block(Cat, relationship_block, self, dialogue_dict=cat_dict)

        if dark_forest_block:
            if "join" in dark_forest_block:
                for abbrev in dark_forest_block["join"]:
                    cat_dict[abbrev].join_df()
            if "leave" in dark_forest_block:
                for abbrev in dark_forest_block["leave"]:
                    cat_dict[abbrev].leave_df()

        # except Exception as e:
        #     print("ERROR with dialogue scene effects:", e)
        #     return
