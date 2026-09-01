from random import choice, randint
import pygame
import ujson
import re
from .Screens import Screens
import random

from ..ui.scale import ui_scale, ui_scale_dimensions
from scripts.cat.sprites.display_sprites import generate_sprite
from scripts.clan_package.get_clan_cats import find_alive_cats_with_rank
from scripts.game_structure.localization import load_lang_resource
from scripts.cat.factories.new_cat_factory import NewCatFactory
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from ..game_structure.game.switches import (
    switch_set_value,
    switch_get_value,
    Switch,
    switch_append_list_value,
    switch_remove_list_value,
)
from scripts.screens.enums import GameScreen

from scripts.cat.enums import CatRank, CatGroup
from ..game_structure.game.settings import game_setting_get

import pygame_gui
from scripts.game_structure import game
from enum import Enum  # pylint: disable=no-name-in-module
from scripts.cat.names import Name
from scripts.game_structure.screen_settings import MANAGER
from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.generate_button import ButtonStyles, get_button_dict
from scripts.events_module.text_adjust import (
    pronoun_repl,
    event_text_adjust,
    process_text,
)


class RelationType(Enum):
    """An enum representing the possible age groups of a cat"""

    BLOOD = ""  # direct blood related - do not need a special print
    ADOPTIVE = "adoptive"  # not blood related but close (parents, kits, siblings)
    HALF_BLOOD = "half sibling"  # only one blood parent is the same (siblings only)
    NOT_BLOOD = "not blood related"  # not blood related for parent siblings
    RELATED = "blood related"  # related by blood (different mates only)


BLOOD_RELATIVE_TYPES = [
    RelationType.BLOOD,
    RelationType.HALF_BLOOD,
    RelationType.RELATED,
]


class MoonplaceScreen(Screens):
    def __init__(self, name=None):
        super().__init__(name)
        self.back_button = None
        self.texts = ""
        self.text_frames = [
            [text[: i + 1] for i in range(len(text))] for text in self.texts
        ]
        self.scroll_container = None
        self.life_text = None
        self.header = None
        self.the_cat = None
        self.text_index = 0
        self.frame_index = 0
        self.typing_delay = 20
        self.next_frame_time = pygame.time.get_ticks() + self.typing_delay
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.text = None
        self.profile_elements = {}
        self.talk_box_img = None
        self.possible_texts = {}
        self.chosen_text_key = ""
        self.choice_buttons = {}
        self.text_choices = {}
        self.option_bgs = {}
        self.current_scene = ""
        self.created_choice_buttons = False
        self.choicepanel = False
        self.textbox_graphic = None
        self.starclan_cats = []

    def screen_switches(self):
        super().screen_switches()
        switch_set_value(Switch.attended_half_moon, True)
        self.update_camp_bg()
        self.hide_menu_buttons()
        self.handle_other_med()
        self.text_index = 0
        self.frame_index = 0
        self.choicepanel = False
        self.created_choice_buttons = False
        self.profile_elements = {}

        self.starclan_cats = [
            cat
            for cat in Cat.all_cats_list
            if (cat.dead and cat.status.group == CatGroup.STARCLAN)
        ]
        self.the_cat = choice(self.starclan_cats)

        self.clan_name_bg = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((115, 438), (190, 35))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/clan_name_bg.png"
                ).convert_alpha(),
                (500, 870),
            ),
            manager=MANAGER,
        )
        self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(
            str(self.the_cat.name),
            ui_scale(pygame.Rect((150, 437), (-1, 40))),
            object_id="#text_box_34_horizcenter_light",
            manager=MANAGER,
        )

        self.text_type = ""
        self.texts = self.load_texts(self.the_cat)
        self.text_frames = [
            [text[: i + 1] for i in range(len(text))] for text in self.texts
        ]
        self.talk_box_img = image_cache.load_image(
            "resources/images/talk_box.png"
        ).convert_alpha()

        self.talk_box = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((90, 470), (624, 151))), self.talk_box_img
        )

        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (105, 30))),
            "buttons.back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(
            ui_scale(pygame.Rect((250, 475), (450, 150)))
        )
        self.text = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((0, 10), (450, -100))),
            object_id="#text_box_30_horizleft",
            container=self.scroll_container,
            manager=MANAGER,
        )

        self.textbox_graphic = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((90, 471), (163, 150))),
            image_cache.load_image(
                "resources/images/textbox_graphic.png"
            ).convert_alpha(),
        )
        # self.textbox_graphic.hide()

        self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((35, 450), (200, 200))),
            pygame.transform.scale(generate_sprite(self.the_cat), (200, 200)),
            manager=MANAGER,
        )
        self.paw = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((685, 590), (15, 15))),
            image_cache.load_image("resources/images/cursor.png").convert_alpha(),
        )
        self.paw.visible = False

    def exit_screen(self):
        self.text.kill()
        del self.text
        self.scroll_container.kill()
        del self.scroll_container
        self.back_button.kill()
        del self.back_button
        self.profile_elements["cat_image"].kill()
        self.profile_elements["cat_name"].kill()
        del self.profile_elements
        self.clan_name_bg.kill()
        del self.clan_name_bg
        self.talk_box.kill()
        del self.talk_box
        self.textbox_graphic.kill()
        del self.textbox_graphic
        self.paw.kill()
        del self.paw
        for button in self.choice_buttons:
            self.choice_buttons[button].kill()
        self.choice_buttons = {}
        for option in self.text_choices:
            self.text_choices[option].kill()
        self.text_choices = {}
        for option_bg in self.option_bgs:
            self.option_bgs[option_bg].kill()
        self.option_bgs = {}

    def update_camp_bg(self):
        light_dark = "dark" if game_setting_get("dark mode") else "light"

        camp_bg_base_dir = "resources/images/moonplace/"
        leaves = ["newleaf", "greenleaf", "leafbare", "leaffall"]

        img_dict = {
            "mountainous": "moonstone.png",
            "forest": "moonhollow.png",
            "plains": "moonplace1.png",
            "beach": "moonstone.png",
        }
        platform_dir = camp_bg_base_dir + img_dict[game.clan.biome.lower()]

        self.add_bgs(
            {
                "Newleaf": pygame.transform.scale(
                    pygame.image.load(platform_dir).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
                "Greenleaf": pygame.transform.scale(
                    pygame.image.load(platform_dir).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
                "Leaf-bare": pygame.transform.scale(
                    pygame.image.load(platform_dir).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
                "Leaf-fall": pygame.transform.scale(
                    pygame.image.load(platform_dir).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
            },
            {
                "Newleaf": None,
                "Greenleaf": None,
                "Leaf-bare": None,
                "Leaf-fall": None,
            },
        )

        self.set_bg(game.clan.current_season)

    def on_use(self):
        super().on_use()
        now = pygame.time.get_ticks()
        try:
            if (
                self.texts[self.text_index][0] == "["
                and self.texts[self.text_index][-1] == "]"
            ):
                self.profile_elements["cat_image"].hide()
                self.clan_name_bg.hide()
                self.profile_elements["cat_name"].hide()
                # self.textbox_graphic.show()
            else:
                self.profile_elements["cat_image"].show()
                self.clan_name_bg.show()
                self.profile_elements["cat_name"].show()
                # self.textbox_graphic.hide()
        except:
            print("Moonplace screen error")
        if self.text_index < len(self.text_frames):
            if (
                now >= self.next_frame_time
                and self.frame_index < len(self.text_frames[self.text_index]) - 1
            ):
                self.frame_index += 1
                self.next_frame_time = now + self.typing_delay
        try:
            if self.text_index == len(self.text_frames) - 1:
                if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                    self.paw.visible = True

        except:
            pass

        # Always render the current frame
        try:
            self.text.html_text = self.text_frames[self.text_index][self.frame_index]
        except:
            pass
        self.text.rebuild()
        self.clock.tick(60)

    def handle_event(self, event):
        if switch_get_value(Switch.window_open):
            pass
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen(GameScreen.PROFILE)
        elif event.type == pygame.KEYDOWN and game_setting_get("keybinds"):
            if event.key == pygame.K_ESCAPE:
                self.change_screen(GameScreen.PROFILE)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            try:
                if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                    if self.text_index < len(self.texts) - 1:
                        self.text_index += 1
                        self.frame_index = 0
                else:
                    self.frame_index = (
                        len(self.text_frames[self.text_index]) - 1
                    )  # Go to the last frame
            except:
                pass
        return

    def get_cluster_list(self):
        return [
            "assertive",
            "brooding",
            "cool",
            "upstanding",
            "introspective",
            "neurotic",
            "silly",
            "stable",
            "sweet",
            "unabashed",
            "unlawful",
        ]

    def get_cluster_list_you(self):
        return [
            "you_assertive",
            "you_brooding",
            "you_cool",
            "you_upstanding",
            "you_introspective",
            "you_neurotic",
            "you_silly",
            "you_stable",
            "you_sweet",
            "you_unabashed",
            "you_unlawful",
        ]

    def relationship_check(self, talk, cat_relationship):
        relationship_conditions = {
            "hate": 50,
            "romantic_like": 30,
            "platonic_like": 30,
            "jealousy": 30,
            "dislike": 30,
            "comfort": 30,
            "respect": 30,
            "trust": 30,
        }
        tags = talk["intro"] if "intro" in talk else talk[0]
        for key, value in relationship_conditions.items():
            if key in tags and cat_relationship < value:
                return True
        return False

    def handle_random_cat(self, cat):
        random_cat = Cat.all_cats.get(choice(game.clan.clan_cats))
        counter = 0
        while (
            random_cat.status.is_outsider
            or random_cat.dead
            or random_cat.ID in [game.clan.your_cat.ID, cat.ID]
        ):
            counter += 1
            if counter == 15:
                break
            random_cat = Cat.all_cats.get(choice(game.clan.clan_cats))
        return random_cat

    def get_med_type(self, you):
        med_type = "you_single_med"

        if you.status.rank == CatRank.MEDICINE_APPRENTICE and not you.mentor:
            med_type = "you_app_mentorless"
        elif you.status.rank == CatRank.MEDICINE_APPRENTICE:
            med_type = "you_app_mentor"
        elif (
            you.status.rank == CatRank.MEDICINE_CAT
            and len(
                find_alive_cats_with_rank(
                    Cat,
                    [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE],
                    working=False,
                )
            )
            == 2
        ):
            med_type = "two_meds"
        elif (
            you.status.rank == CatRank.MEDICINE_CAT
            and len(
                find_alive_cats_with_rank(
                    Cat,
                    [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE],
                    working=False,
                )
            )
            > 2
        ):
            med_type = "multi_meds"

        return med_type

    def load_texts(self, cat):
        you = game.clan.your_cat

        resource_dir = "events/lifegen_events/moonplace/moonplace.json"

        possible_texts = load_lang_resource(resource_dir)

        if you.status.rank.is_any_apprentice_rank():
            return self.get_adjusted_txt(
                choice(possible_texts["apprentice_halfmoon"]), cat
            )

        med_type = self.get_med_type(you)

        other_med_greeting = self.get_other_med_greeting(possible_texts)

        if randint(1, 2) == 1:
            # No message
            return self.get_adjusted_txt(
                choice(possible_texts["intros"][med_type])
                + other_med_greeting
                + choice(possible_texts["moonplace"]["starclan_no_message"]),
                cat,
            )

        possible_texts2 = load_lang_resource(
            "events/lifegen_events/moonplace/prophecies.json"
        )

        switch_set_value(
            Switch.next_possible_disaster, choice(list(possible_texts2.keys()))
        )

        prophecy = choice(
            possible_texts2[switch_get_value(Switch.next_possible_disaster)]["text"]
        )

        return self.get_adjusted_txt(
            choice(possible_texts["intros"][med_type])
            + other_med_greeting
            + choice(possible_texts["moonplace"]["starclan_general"])
            + prophecy,
            cat,
        )

    def get_adjusted_txt(self, text, cat):
        you = game.clan.your_cat

        process_text_dict = {}
        process_text_dict["t_c"] = cat
        process_text_dict["y_c"] = you

        healthy_meds = find_alive_cats_with_rank(
            Cat,
            ranks=[CatRank.MEDICINE_CAT],
            working=True,
        )
        if any("med_name" in line for line in text):
            if not healthy_meds:
                return ""
            process_text_dict["med_name"] = random.choice(healthy_meds)

        if any("mentor_name" in line for line in text):
            if not you.mentor:
                return ""
            process_text_dict["mentor_name"] = Cat.fetch_cat(you.mentor)

        for abbrev, abbrev_cat in process_text_dict.items():
            process_text_dict[abbrev] = (
                str(abbrev_cat.name),
                choice(abbrev_cat.pronouns),
            )

        text = [t1.replace("c_n", game.clan.name + "Clan") for t1 in text]

        new_text_list = []
        for line in text:
            new_line = process_text(line, process_text_dict)
            newer_line = self.replace_moonplace_name(new_line)
            if newer_line == "":
                return ""
            new_text_list.append(newer_line)

        return new_text_list

    def get_living_cats(self):
        living_cats = []
        for the_cat in Cat.all_cats_list:
            if (
                not the_cat.dead
                and not the_cat.status.is_outsider
                and not the_cat.moons == -1
            ):
                living_cats.append(the_cat)
        return living_cats

    def replace_moonplace_name(self, text):
        """
        Replaces the moonplace name
        """

        if "moonplace" in text or "Moonplace" in text:
            moonplace_dict = {
                "Beach": "Mooncove",
                "Mountainous": "Moonfalls",
                "Forest": "Moonhollow",
                "Plains": "Moongrove",
            }
            moonplace = moonplace_dict.get(game.clan.biome, "Moonplace")
            text = text.replace("moonplace_name", moonplace)

        return text

    def get_other_med_greeting(self, possible_texts):
        """Handles other medicine cat greetings at the Moonplace."""

        def format_greeting(template, clan_name, med_names):
            formatted_names = (
                ", ".join(med_names[:-1]) + f", and {med_names[-1]}"
                if len(med_names) > 2
                else " and ".join(med_names)
                if len(med_names) == 2
                else med_names[0]
            )
            return template.replace("o_cn", f"{clan_name}Clan").replace(
                "o_c_m", formatted_names
            )

        other_clan = choice(game.clan.all_other_clans)
        med_cats = []
        for cat in switch_get_value(Switch.other_meds):
            if Cat.fetch_cat(cat).status.group_ID == other_clan.group_ID:
                med_cats.append(Cat.fetch_cat(cat).name)

        med_count_key = "one_med" if len(med_cats) == 1 else "multi_med"
        temperament_key = f"general_greeting_{other_clan.temperament}_{med_count_key}"
        general_key = f"general_greeting_{med_count_key}"

        greeting_pool = []
        greeting_pool.extend(possible_texts["med_cat_greetings"].get(general_key, []))
        greeting_pool.extend(
            possible_texts["med_cat_greetings"].get(temperament_key, [])
        )

        if game.clan.war.get("at_war", True) and other_clan.name == game.clan.war.get(
            "enemy"
        ):
            greeting_pool.extend(
                possible_texts["med_cat_greetings"].get(
                    f"general_greeting_war_{med_count_key}", []
                )
            )

        if other_clan.relations > 16:
            greeting_pool.extend(
                possible_texts["med_cat_greetings"].get(
                    f"general_greeting_friendly_{med_count_key}", []
                )
            )
        elif other_clan.relations < 7:
            greeting_pool.extend(
                possible_texts["med_cat_greetings"].get(
                    f"general_greeting_unfriendly_{med_count_key}", []
                )
            )

        if greeting_pool:
            chosen = choice(greeting_pool)
            formatted = format_greeting(
                chosen, other_clan.name, [str(m) for m in med_cats]
            )
            return [formatted]
        return []

    def handle_other_med(self):
        """Updates other Clans' medicine cats for the Moonplace."""

        def generate_other_meds(clan, num):
            """Generates cats for specified clan (mostly full names, some apprentices)."""
            for _ in range(num):
                is_apprentice = randint(1, 4) == 1
                # give an age that fits the role
                moons = randint(6, 11) if is_apprentice else randint(20, 120)
                cat = NewCatFactory.create_cat(name=Name(), moons=moons)
                if is_apprentice:
                    cat.rank_change(CatRank.MEDICINE_APPRENTICE)
                else:
                    cat.rank_change(CatRank.MEDICINE_CAT)
                cat.status.add_to_group(clan.group_ID)
                if cat.mentor:
                    mentor = Cat.fetch_cat(cat.mentor)
                    if mentor and cat.ID in mentor.apprentice:
                        mentor.apprentice.remove(cat.ID)
                    cat.mentor = None
                switch_append_list_value(Switch.other_meds, cat.ID)

        def simulate_death_other_meds(clan):
            """Randomly removes a medicine cat from the specified clan."""
            clan_meds = [
                cat_id
                for cat_id in switch_get_value(Switch.other_meds)
                if Cat.fetch_cat(cat_id).status.group_ID == clan.group_ID
            ]

            if clan_meds and randint(1, 3) == 1:
                rand_med_cat = choice(clan_meds)
                switch_remove_list_value(Switch.other_meds, rand_med_cat)

        def check_number_other_meds(clan):
            """Count and replenish medicine cats for a clan."""
            num_other_meds = 0
            for cat in switch_get_value(Switch.other_meds):
                if Cat.fetch_cat(cat).status.group_ID == clan.group_ID:
                    num_other_meds += 1

            if num_other_meds < 1:
                generate_other_meds(clan, randint(1, 3))
            elif num_other_meds == 1 and randint(1, 2) == 1:
                generate_other_meds(clan, 1)

        # initialize on first call
        if not switch_get_value(Switch.other_meds):
            switch_set_value(Switch.other_meds, [])
            for clan in game.clan.all_other_clans:
                generate_other_meds(clan, randint(1, 3))
        else:
            for clan in game.clan.all_other_clans:
                check_number_other_meds(clan)
                simulate_death_other_meds(clan)
                check_number_other_meds(clan)
