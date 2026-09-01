from math import ceil
from random import choice

import pygame.transform
import pygame_gui.elements

# pylint: disable=consider-using-dict-items

from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure import game
from ..ui.elements.image_button import UIImageButton
from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.elements.sprite_button import UISpriteButton
from ..ui.elements.text_box_tweaked import UITextBoxTweaked
from ..ui.elements.modified_scrolling_container import UIModifiedScrollingContainer

from scripts.screens.enums import GameScreen
from ..cat.enums import CatRank
from ..game_structure.game.settings import game_setting_get

from ..game_structure.game.switches import switch_set_value, switch_get_value, Switch

from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale, ui_scale_dimensions
from ..events_module.text_adjust import shorten_text_to_fit

from scripts.clan_package.settings import get_clan_setting
from .Screens import Screens
from ..game_structure.screen_settings import MANAGER
from ..ui.generate_box import get_box, BoxStyles
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon


class ElderStoryScreen(Screens):
    def __init__(self, name=None):
        super().__init__(name)
        self.back_button = None
        self.selected_elder = 0
        self.search_bar = None
        self.search_bar_image = None
        self.elder_elements = {}
        self.elders = []
        self.cat_buttons = []
        self.page = 1
        self.selected_cat_elements = {}
        self.allow_romantic = True
        self.current_listed_cats = None
        self.previous_search_text = ""
        self.selected_story = ""
        self.selected_cats = []
        self.selected_cat_containers = {}
        self.story_container = None
        self.elements = {}

        self.stage = "cats"

        # the cat currently being chosen for
        self.selected_cat_sprites = {}
        self.selected_cat_sprite_buttons = {}
        self.cat_selection = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.stage = "cats"
                self.selected_cats = []
                self.cat_selection = None
                self.change_screen(GameScreen.PROFILE)
            elif event.ui_element == self.last_med:
                self.selected_elder -= 1
                self.update_elder_info()
            elif event.ui_element == self.next_med:
                self.selected_elder += 1
                self.update_elder_info()
            elif event.ui_element == self.next_page:
                self.page += 1
                self.update_page()
            elif event.ui_element == self.previous_page:
                self.page -= 1
                self.update_page()
            elif event.ui_element == self.starclan_story_button:
                self.selected_story = "starclan"
                self.update_buttons()
            elif event.ui_element == self.df_story_button:
                self.selected_story = "darkforest"
                self.update_buttons()
            elif event.ui_element == self.ur_story_button:
                self.selected_story = "neutral"
                self.update_buttons()
            elif event.ui_element == self.tell_story_button:
                if self.stage == "cats":
                    self.stage = "story"
                    self.exit_screen()
                    self.screen_switches()
                    game.patrolled.append(self.elders[self.selected_elder].ID)
                    game.told_story.extend([cat.ID for cat in self.selected_cats])
                    output = Cat.elder_story(
                        self.elders[self.selected_elder],
                        self.selected_cats,
                        chosen_story=self.selected_story,
                    )
                    self.results_heading.set_text(output[0])

                    story_text = []
                    for string in output[1]:
                        story_text.append(string)

                    joined_story_text = "<br><br>".join(story_text)

                    self.results.set_text(joined_story_text)
                    faith_changes = output[2]
                    self.update_selected_cats(faith_changes)
                else:
                    self.stage = "cats"
                    self.selected_cats = []
                    self.cat_selection = None
                    self.selected_story = ""
                    self.exit_screen()
                    self.screen_switches()
                    self.update_selected_cats()
            elif event.ui_element == self.random1:
                self.selected_cats = []
                for i in [0, 1, 2, 3, 4]:
                    try:
                        new_cat = self.random_cat()
                        self.selected_cats.append(new_cat)
                    except:
                        print("No random cats available.")
                self.update_selected_cats()
                self.update_elder_info()
            elif event.ui_element == self.elements["randomise_cat"]:
                if self.cat_selection is not None:
                    try:
                        new_cat = self.random_cat()
                    except:
                        print("No random cats available.")
                    self.selected_cats[self.cat_selection] = new_cat
                    self.update_selected_cats()
            elif event.ui_element == self.elements["remove_cat"]:
                if self.cat_selection is not None:
                    self.selected_cats.remove(self.selected_cats[self.cat_selection])
                    if self.cat_selection > 0:
                        self.cat_selection -= 1
                    if self.cat_selection == 0:
                        self.cat_selection = None
                    self.update_selected_cats()
            elif event.ui_element in self.cat_buttons:
                cat_object = event.ui_element.return_cat_object()
                if cat_object in self.selected_cats:
                    if self.cat_selection == self.selected_cats.index(cat_object):
                        if self.cat_selection is not None:
                            self.cat_selection = (
                                (self.selected_cats.index(cat_object)) - 1
                                if self.selected_cats.index(cat_object) > 0
                                else None
                            )
                    self.selected_cats.remove(cat_object)
                    if self.cat_selection is not None:
                        if self.cat_selection > 0:
                            self.cat_selection -= 1
                        if self.cat_selection == 0:
                            self.cat_selection = None
                else:
                    if self.cat_selection is not None:
                        print(self.selected_cats)
                        print(self.cat_selection)
                        self.selected_cats[self.cat_selection] = cat_object
                    else:
                        if len(self.selected_cats) < 5:
                            self.selected_cats.append(cat_object)
                            # self.cat_selection = self.selected_cats.index(cat_object)
                if self.cat_selection is not None and self.cat_selection > len(
                    self.selected_cats
                ):
                    self.cat_selection = (
                        len(self.selected_cats) if len(self.selected_cats) > 0 else None
                    )

                self.update_selected_cats()
            for item in self.selected_cat_sprite_buttons:
                if event.ui_element == self.selected_cat_sprite_buttons[item]:
                    if self.cat_selection == item:
                        self.cat_selection = None
                    else:
                        self.cat_selection = item
                    self.update_selected_cats()

            for item in self.selected_cat_sprite_buttons:
                if event.ui_element == item:
                    self.cat_selection = item

    def screen_switches(self):
        super().screen_switches()
        self.show_mute_buttons()
        # Gather the elders:
        self.elders = []
        for cat in Cat.all_cats_list:
            if cat.status.rank == CatRank.ELDER and (
                cat.status.alive_in_player_clan and cat.moons > 0
            ):
                self.elders.append(cat)

        self.page = 1

        if self.elders:
            if Cat.fetch_cat(switch_get_value(Switch.cat)) in self.elders:
                self.selected_elder = self.elders.index(
                    Cat.fetch_cat(switch_get_value(Switch.cat))
                )
            else:
                self.selected_elder = 0
        else:
            self.selected_elder = None

        # SIDEBAR
        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (105, 30))),
            "buttons.back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )

        # for the cat list
        self.next_page = UISurfaceImageButton(
            ui_scale(pygame.Rect((245, 180), (34, 34))),
            Icon.ARROW_RIGHT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            manager=MANAGER,
        )
        self.previous_page = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 180), (34, 34))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            manager=MANAGER,
        )

        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((53, 80), (200, 270))),
            get_box(BoxStyles.ROUNDED_BOX, (200, 250)),
        )
        self.list_frame.disable()

        self.random1 = UISurfaceImageButton(
            ui_scale(pygame.Rect((200, 360), (34, 34))),
            "\u2684",
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            manager=MANAGER,
            tool_tip_text="Randomise all cats",
            sound_id="dice_roll",
        )

        self.search_bar_image = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((60, 360), (118, 34))),
            pygame.image.load("resources/images/search_bar.png").convert_alpha(),
            manager=MANAGER,
        )
        self.search_bar = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((67, 363), (115, 27))),
            object_id="#search_entry_box",
            initial_text="name search",
            manager=MANAGER,
        )

        self.elements["randomise_cat"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((64, 405), (34, 34))),
            Icon.DICE,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            tool_tip_text="Randomise selected cat",
            sound_id="dice_roll",
        )
        self.elements["remove_cat"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((105, 405), (135, 34))),
            "Remove cat",
            get_button_dict(ButtonStyles.SQUOVAL, (135, 34)),
            object_id="@buttonstyles_squoval",
        )

        self.buttons_bg = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((53, 450), (200, 160))),
            get_box(BoxStyles.ROUNDED_BOX, (200, 160)),
        )
        self.buttons_bg.disable()

        self.starclan_story_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((73, 475), (160, 30))),
            "StarClan",
            get_button_dict(ButtonStyles.ROUNDED_RECT, (160, 30)),
            object_id="@buttonstyles_rounded_rect",
            manager=MANAGER,
        )
        self.df_story_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((73, 515), (160, 30))),
            "Dark Forest",
            get_button_dict(ButtonStyles.ROUNDED_RECT, (160, 30)),
            object_id="@buttonstyles_rounded_rect",
            manager=MANAGER,
        )
        self.ur_story_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((73, 555), (160, 30))),
            "Neutral",
            get_button_dict(ButtonStyles.ROUNDED_RECT, (160, 30)),
            object_id="@buttonstyles_rounded_rect",
            manager=MANAGER,
        )

        self.story_container = pygame_gui.core.UIContainer(
            ui_scale(pygame.Rect((290, 70), (476, 620))),
            starting_height=1,
            manager=MANAGER,
        )

        # CATS STAGE
        if self.stage == "cats":
            self.results = None
            self.results_heading = None
            self.results_container = None
            self.tell_story_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((53, 630), (200, 30))),
                "tell a story",
                get_button_dict(ButtonStyles.ROUNDED_RECT, (200, 30)),
                object_id="@buttonstyles_rounded_rect",
                manager=MANAGER,
            )
            # SELECTED CAT CONTAINERS
            self.selected_cat_containers[0] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((0, 184), (150, 180))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
            )
            self.selected_cat_containers[1] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((34, 34), (150, 180))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
            )
            self.selected_cat_containers[2] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((0, 0), (150, 180))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
                anchors={"centerx": "centerx"},
            )
            self.selected_cat_containers[3] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((-184, 34), (150, 180))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
                anchors={"right": "right"},
            )
            self.selected_cat_containers[4] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((-150, 184), (150, 180))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
                anchors={"right": "right"},
            )

            self.next_med = UISurfaceImageButton(
                ui_scale(pygame.Rect((530, 482), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
            )
            self.last_med = UISurfaceImageButton(
                ui_scale(pygame.Rect((490, 482), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
            )
            self.error = pygame_gui.elements.UITextBox(
                "",
                ui_scale(pygame.Rect((0, 361), (380, 60))),
                object_id=get_text_box_theme("#text_box_22_horizcenter_spacing_95"),
                manager=MANAGER,
                container=self.story_container,
                anchors={"centerx": "centerx"},
            )
        elif self.stage == "story":
            self.next_med = None
            self.last_med = None
            self.error = None

            for ele in self.selected_cat_containers:
                self.selected_cat_containers[ele].kill()
            self.selected_cat_containers = {}

            self.tell_story_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((53, 630), (200, 30))),
                "reset",
                get_button_dict(ButtonStyles.ROUNDED_RECT, (200, 30)),
                object_id="@buttonstyles_rounded_rect",
                manager=MANAGER,
            )

            self.elements["banner_img"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 10), (460, 70))),
                pygame.image.load(
                    f"resources/images/elder_banner_{self.selected_story}.png"
                ).convert_alpha(),
                container=self.story_container,
                anchors={"centerx": "centerx"},
                manager=MANAGER,
            )

            self.selected_cat_containers[0] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((70, 400), (75, 165))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
            )
            self.selected_cat_containers[1] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((150, 400), (75, 165))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
            )
            self.selected_cat_containers[2] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((230, 400), (75, 165))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
            )
            self.selected_cat_containers[3] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((310, 400), (75, 165))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
            )
            self.selected_cat_containers[4] = pygame_gui.core.UIContainer(
                ui_scale(pygame.Rect((390, 400), (75, 165))),
                starting_height=1,
                container=self.story_container,
                manager=MANAGER,
            )

            self.results_heading = pygame_gui.elements.UITextBox(
                "",
                ui_scale(pygame.Rect((0, 90), (420, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
                container=self.story_container,
                anchors={"centerx": "centerx"},
            )
            self.results_container = UIModifiedScrollingContainer(
                ui_scale(pygame.Rect((0, 140), (450, 250))),
                starting_height=3,
                manager=MANAGER,
                allow_scroll_y=True,
                container=self.story_container,
                anchors={"centerx": "centerx"},
            )
            self.results = UITextBoxTweaked(
                "",
                ui_scale(pygame.Rect((0, 0), (390, -1))),
                object_id=get_text_box_theme("#text_box_26_horizcenter"),
                manager=MANAGER,
                container=self.results_container,
                anchors={"centerx": "centerx"},
            )

        self.update_buttons()
        self.update_elder_info()

    def random_cat(self):
        try:
            random_list = [
                i
                for i in Cat.all_cats_list
                if (
                    i not in self.selected_cats
                    and i.status.alive_in_player_clan
                    and (i.ID != self.elders[self.selected_elder].ID)
                    and i.ID not in game.mediated
                    and i.ID not in game.told_story
                    and i.moons > 0
                )
            ]
        except:
            random_list = [
                i
                for i in Cat.all_cats_list
                if (
                    i not in self.selected_cats
                    and i.status.alive_in_player_clan
                    and (i.ID != self.elders[self.selected_elder].ID)
                    and i.moons > 0
                )
            ]

        return choice(random_list)

    def update_elder_info(self):
        for ele in self.elder_elements:
            self.elder_elements[ele].kill()
        self.elder_elements = {}

        if self.selected_elder is None:
            if self.stage == "cats":
                self.last_med.disable()
                self.next_med.disable()
        else:
            elder = self.elders[self.selected_elder]

            # Clear elder as selected cat
            if elder in self.selected_cats:
                self.selected_cats.remove(elder)
                self.update_selected_cats()

            if self.stage == "cats":
                switch_set_value(Switch.cat, elder.ID)
                self.elder_elements["elder_container"] = pygame_gui.core.UIContainer(
                    ui_scale(pygame.Rect((0, 160), (150, 230))),
                    starting_height=1,
                    manager=MANAGER,
                    container=self.story_container,
                    anchors={"centerx": "centerx"},
                )

                self.elder_elements["elder_image"] = pygame_gui.elements.UIImage(
                    ui_scale(pygame.Rect((0, 0), (130, 130))),
                    pygame.transform.scale(
                        elder.sprite, ui_scale_dimensions((130, 130))
                    ),
                    anchors={"centerx": "centerx"},
                    container=self.elder_elements["elder_container"],
                )

                name = str(elder.name)
                short_name = shorten_text_to_fit(name, 120, 11)
                self.elder_elements["name"] = pygame_gui.elements.UILabel(
                    ui_scale(pygame.Rect((0, 130), (130, 25))),
                    short_name,
                    object_id=get_text_box_theme("#text_box_30_horizcenter"),
                    manager=MANAGER,
                    anchors={"centerx": "centerx"},
                    container=self.elder_elements["elder_container"],
                )

                text = elder.personality.trait + "\n" + elder.experience_level

                if elder.not_working():
                    text += "\nThis cat isn't able to work"
                    self.starclan_story_button.disable()
                    self.df_story_button.disable()
                    self.ur_story_button.disable()
                else:
                    text += "\nThis cat can work"
                    self.starclan_story_button.enable()
                    self.df_story_button.enable()
                    self.ur_story_button.enable()

                self.elder_elements["details"] = pygame_gui.elements.UITextBox(
                    text,
                    ui_scale(pygame.Rect((0, 160), (130, 80))),
                    object_id=get_text_box_theme("#text_box_22_horizcenter_spacing_95"),
                    manager=MANAGER,
                    anchors={"centerx": "centerx"},
                    container=self.elder_elements["elder_container"],
                )

                elder_number = len(self.elders)
                if self.selected_elder < elder_number - 1:
                    self.next_med.enable()
                else:
                    self.next_med.disable()

                if self.selected_elder > 0:
                    self.last_med.enable()
                else:
                    self.last_med.disable()
            elif self.stage == "story":
                self.elder_elements["elder_container"] = pygame_gui.core.UIContainer(
                    ui_scale(pygame.Rect((-20, 400), (100, 150))),
                    starting_height=1,
                    manager=MANAGER,
                    container=self.story_container,
                )

                self.elder_elements["elder_image"] = pygame_gui.elements.UIImage(
                    ui_scale(pygame.Rect((0, 0), (75, 75))),
                    pygame.transform.scale(elder.sprite, ui_scale_dimensions((75, 75))),
                    anchors={"centerx": "centerx"},
                    container=self.elder_elements["elder_container"],
                )

                name = str(elder.name)
                short_name = shorten_text_to_fit(name, 75, 14)
                self.elder_elements["name"] = pygame_gui.elements.UILabel(
                    ui_scale(pygame.Rect((0, 80), (75, 30))),
                    short_name,
                    object_id=get_text_box_theme("#text_box_22_horizcenter"),
                    manager=MANAGER,
                    anchors={"centerx": "centerx"},
                    container=self.elder_elements["elder_container"],
                )

        self.update_buttons()
        self.update_list_cats()

    def update_list_cats(self):
        self.all_cats_list = [
            i
            for i in Cat.all_cats_list
            if (i.ID != self.elders[self.selected_elder].ID)
            and i.status.alive_in_player_clan
            and i.moons > 0
            and i.ID not in game.told_story
        ]
        self.all_cats = self.chunks(self.all_cats_list, 12)
        self.current_listed_cats = self.all_cats_list
        self.all_pages = (
            int(ceil(len(self.current_listed_cats) / 12.0))
            if len(self.current_listed_cats) > 12
            else 1
        )
        self.update_page()

    def update_page(self):
        for cat in self.cat_buttons:
            cat.kill()
        self.cat_buttons = []
        if self.page > self.all_pages:
            self.page = self.all_pages
        elif self.page < 1:
            self.page = 1

        if self.page >= self.all_pages:
            self.next_page.disable()
        else:
            self.next_page.enable()

        if self.page <= 1:
            self.previous_page.disable()
        else:
            self.previous_page.enable()

        x = 75
        y = 97
        chunked_cats = self.chunks(self.current_listed_cats, 12)
        if chunked_cats:
            for cat in chunked_cats[self.page - 1]:
                if get_clan_setting("show fav") and cat.favourite != 0:
                    _temp = pygame.transform.scale(
                        pygame.image.load(
                            f"resources/images/fav_marker_{cat.favourite}.png"
                        ).convert_alpha(),
                        (50, 50),
                    )

                    self.cat_buttons.append(
                        pygame_gui.elements.UIImage(
                            ui_scale(pygame.Rect((x, y), (50, 50))), _temp
                        )
                    )
                    self.cat_buttons[-1].disable()

                self.cat_buttons.append(
                    UISpriteButton(
                        ui_scale(pygame.Rect((x, y), (50, 50))),
                        cat.sprite,
                        cat_object=cat,
                    )
                )
                x += 55
                if x > 190:
                    y += 55
                    x = 75

    def update_selected_cats(self, faith_changes={}):
        for ele in self.selected_cat_elements:
            self.selected_cat_elements[ele].kill()
        self.selected_cat_elements = {}
        for ele in self.selected_cat_sprites:
            self.selected_cat_sprites[ele].kill()
        self.selected_cat_sprites = {}
        for ele in self.selected_cat_sprite_buttons:
            self.selected_cat_sprite_buttons[ele].kill()
        self.selected_cat_sprite_buttons = {}

        for cat in self.selected_cats:
            self.draw_info_block(self.selected_cats.index(cat), cat, faith_changes)

        if self.cat_selection is not None and self.stage == "cats":
            self.selected_cat_elements["outline"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 0), (130, 170))),
                get_box(BoxStyles.FRAME, (130, 170)),
                container=self.selected_cat_containers[self.cat_selection],
                starting_height=1,
                anchors={"centerx": "centerx"},
                manager=MANAGER,
            )
            self.selected_cat_elements["outline"].show()
        else:
            self.selected_cat_elements["outline"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 0), (130, 170))),
                get_box(BoxStyles.FRAME, (130, 170)),
                container=self.selected_cat_containers[0],
                starting_height=1,
                anchors={"centerx": "centerx"},
                manager=MANAGER,
            )
            self.selected_cat_elements["outline"].hide()

        self.update_buttons()

    def draw_info_block(self, index, cat, faith_changes):
        if not cat:
            return

        other_cat = [Cat.fetch_cat(i) for i in self.selected_cat_list() if i != cat.ID]
        if other_cat:
            other_cat = other_cat[0]
        else:
            other_cat = None

        if self.stage == "cats":
            self.selected_cat_sprites["cat_", index] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 0), (120, 120))),
                pygame.transform.scale(cat.sprite, ui_scale_dimensions((120, 120))),
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
            )

            name = str(cat.name)
            short_name = shorten_text_to_fit(name, 130, 15)
            self.selected_cat_elements[
                "name" + str(index)
            ] = pygame_gui.elements.UILabel(
                ui_scale(pygame.Rect((0, 110), (130, 30))),
                short_name,
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
            )

            cat_faith = round(cat.faith)

            if cat_faith < 0:
                cat_faith *= -1
                image_path = "resources/images/faith_bar_df.png"
            elif cat_faith > 0:
                image_path = "resources/images/faith_bar_sc.png"
            else:
                image_path = "resources/images/relation_bar.png"

            self.selected_cat_elements[
                "faith_bar_bg_" + str(index)
            ] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 140), (124, 25))),
                pygame.image.load("resources/images/search_bar.png").convert_alpha(),
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
                manager=MANAGER,
            )
            if cat.moons > 5:
                x_pos = 22
                for i in range(cat_faith):
                    self.selected_cat_elements[
                        str(index) + "_faith_bars_" + str(i)
                    ] = pygame_gui.elements.UIImage(
                        ui_scale(pygame.Rect((x_pos, 148), (8, 9))),
                        image_cache.load_image(image_path).convert_alpha(),
                        container=self.selected_cat_containers[index],
                        anchors={"left": "left"},
                    )
                    x_pos += 12
            self.selected_cat_sprite_buttons[index] = UIImageButton(
                ui_scale(pygame.Rect((0, 0), (150, 150))),
                "",
                object_id="#blank_button",
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
            )
        elif self.stage == "story":
            self.selected_cat_sprites["cat_", index] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 0), (75, 75))),
                pygame.transform.scale(cat.sprite, ui_scale_dimensions((75, 75))),
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
            )

            name = str(cat.name)
            short_name = shorten_text_to_fit(name, 75, 15)
            self.selected_cat_elements[
                "name" + str(index)
            ] = pygame_gui.elements.UILabel(
                ui_scale(pygame.Rect((0, 80), (75, 25))),
                short_name,
                object_id=get_text_box_theme("#text_box_22_horizcenter"),
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
            )

            cat_faith = round(cat.faith)

            if cat_faith < 0:
                cat_faith *= -1
                image_path = "resources/images/faith_bar_df.png"
            elif cat_faith > 0:
                image_path = "resources/images/faith_bar_sc.png"
            else:
                image_path = "resources/images/relation_bar.png"

            self.selected_cat_elements[
                "faith_bar_bg_" + str(index)
            ] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((0, 108), (75, 25))),
                pygame.image.load("resources/images/search_bar.png").convert_alpha(),
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
                manager=MANAGER,
            )
            if cat.moons > 5:
                x_pos = 6
                for i in range(cat_faith):
                    self.selected_cat_elements[
                        str(index) + "_faith_bars_" + str(i)
                    ] = pygame_gui.elements.UIImage(
                        ui_scale(pygame.Rect((x_pos, 115), (6, 11))),
                        image_cache.load_image(image_path).convert_alpha(),
                        container=self.selected_cat_containers[index],
                        anchors={"left": "left"},
                    )
                    x_pos += 7

            if cat in faith_changes:
                change = faith_changes[cat]
            else:
                print(cat.name, "not in faith_changes")
                print(faith_changes)
                change = 0

            # font colours
            if game_setting_get("dark mode"):
                sc_colour = "#A8BBFF"
                df_colour = "#FF9999"
                neut_colour = "#CE9DFF"
            else:
                sc_colour = "#2B3DC3"
                df_colour = "#950000"
                neut_colour = "#450E7B"

            if cat.moons > 5:
                if change < 0:
                    if cat.faith > 0:
                        faith_text = f"<font color = '{sc_colour}'>decreased</font>"
                    elif cat.faith < 0:
                        faith_text = f"<font color = '{df_colour}'>increased</font>"
                    else:
                        faith_text = f"<font color = '{neut_colour}'>unchanged</font>"
                elif change > 0:
                    if cat.faith > 0:
                        faith_text = f"<font color = '{sc_colour}'>increased</font>"
                    elif cat.faith < 0:
                        faith_text = f"<font color = '{df_colour}'>decreased</font>"
                    else:
                        faith_text = f"<font color = '{neut_colour}'>unchanged</font>"
                else:
                    faith_text = f"<font color = '{neut_colour}'>unchanged</font>"
            else:
                faith_text = "???"

            self.selected_cat_elements["faith_change_" + str(index)] = UITextBoxTweaked(
                faith_text,
                ui_scale(pygame.Rect((0, 130), (75, 25))),
                object_id=get_text_box_theme("#text_box_22_horizcenter"),
                container=self.selected_cat_containers[index],
                anchors={"centerx": "centerx"},
                manager=MANAGER,
            )

    def selected_cat_list(self):
        return self.selected_cats

    def update_buttons(self):
        error_message = ""

        invalid_elder = False
        if self.selected_elder is not None:
            if self.elders[self.selected_elder].not_working():
                invalid_elder = True
            elif self.elders[self.selected_elder].ID in game.patrolled:
                invalid_elder = True
                error_message += "This elder has already worked this moon. <br>"
        else:
            invalid_elder = True

        no_cats = False
        invalid_cats = []
        if self.selected_cats:
            for x in self.selected_cats:
                if x.ID in game.told_story:
                    invalid_cats.append(x)
            if invalid_cats:
                error_message += (
                    "These cats have already been told a story this moon:<br>"
                )
                error_message += f"{', '.join(str(x.name) for x in invalid_cats)}"
        else:
            no_cats = True

        if self.error:
            self.error.set_text(error_message)

        if self.selected_story == "" or not self.selected_cats or invalid_cats:
            self.tell_story_button.disable()
        else:
            self.tell_story_button.enable()

        if self.stage == "cats":
            self.next_page.enable()
            self.previous_page.enable()
            self.random1.enable()
            self.search_bar.show()

            if invalid_elder or no_cats or invalid_cats:
                self.starclan_story_button.disable()
                self.df_story_button.disable()
                self.tell_story_button.disable()
                self.ur_story_button.disable()
            else:
                self.starclan_story_button.enable()
                self.df_story_button.enable()
                self.ur_story_button.enable()

            if self.selected_story:
                self.tell_story_button.enable()
            else:
                self.tell_story_button.disable()

            if self.selected_story == "starclan":
                self.starclan_story_button.disable()
                self.df_story_button.enable()
                self.ur_story_button.enable()
            elif self.selected_story == "darkforest":
                self.starclan_story_button.enable()
                self.df_story_button.disable()
                self.ur_story_button.enable()
            elif self.selected_story == "neutral":
                self.ur_story_button.disable()
                self.starclan_story_button.enable()
                self.df_story_button.enable()
            for btn in self.cat_buttons:
                btn.enable()
        else:
            self.next_page.disable()
            self.previous_page.disable()
            self.random1.disable()
            self.search_bar.hide()
            self.df_story_button.disable()
            self.ur_story_button.disable()
            self.starclan_story_button.disable()
            self.tell_story_button.enable()

            for btn in self.cat_buttons:
                btn.disable()

        if self.cat_selection is None:
            self.elements["randomise_cat"].disable()
            self.elements["remove_cat"].disable()
        else:
            self.elements["randomise_cat"].enable()
            self.elements["remove_cat"].enable()

        for btn in self.selected_cat_sprite_buttons:
            if len(self.selected_cats) < btn:
                self.selected_cat_sprite_buttons[btn].disable()
            else:
                self.selected_cat_sprite_buttons[btn].enable()

    def update_search_cats(self, search_text):
        """Run this function when the search text changes, or when the screen is switched to."""
        self.current_listed_cats = []
        Cat.sort_cats(self.all_cats_list)

        search_text = search_text.strip()
        if search_text not in ["", "name search"]:
            for cat in self.all_cats_list:
                if search_text.lower() in str(cat.name).lower():
                    self.current_listed_cats.append(cat)
        else:
            self.current_listed_cats = self.all_cats_list.copy()

        self.all_pages = (
            int(ceil(len(self.current_listed_cats) / 12.0))
            if len(self.current_listed_cats) > 12
            else 1
        )

        Cat.ordered_cat_list = self.current_listed_cats
        self.update_page()

    def exit_screen(self):
        for ele in self.elder_elements:
            self.elder_elements[ele].kill()
        self.elder_elements = {}

        for cat in self.cat_buttons:
            cat.kill()
        self.cat_buttons = []

        for ele in self.selected_cat_elements:
            self.selected_cat_elements[ele].kill()
        self.selected_cat_elements = {}

        for ele in self.selected_cat_sprite_buttons:
            self.selected_cat_sprite_buttons[ele].kill()
        self.selected_cat_sprite_buttons = {}

        for ele in self.selected_cat_sprites:
            self.selected_cat_sprites[ele].kill()
        self.selected_cat_sprites = {}

        for ele in self.selected_cat_containers:
            self.selected_cat_containers[ele].kill()
        self.selected_cat_containers = {}

        for ele in self.elements:
            self.elements[ele].kill()
        self.elements = {}

        self.elders = []
        self.back_button.kill()
        del self.back_button
        self.buttons_bg.kill()
        del self.buttons_bg
        self.list_frame.kill()
        del self.list_frame
        self.tell_story_button.kill()
        del self.tell_story_button
        self.starclan_story_button.kill()
        del self.starclan_story_button
        self.df_story_button.kill()
        del self.df_story_button
        self.ur_story_button.kill()
        del self.ur_story_button
        if self.last_med:
            self.last_med.kill()
            del self.last_med
        if self.next_med:
            self.next_med.kill()
            del self.next_med
        self.next_page.kill()
        del self.next_page
        self.previous_page.kill()
        del self.previous_page
        if self.results:
            self.results.kill()
            del self.results
        if self.results_heading:
            self.results_heading.kill()
            del self.results_heading
        if self.results_container:
            self.results_container.kill()
            del self.results_container
        self.random1.kill()
        del self.random1
        if self.error:
            self.error.kill()
            del self.error
        self.search_bar_image.kill()
        del self.search_bar_image
        self.search_bar.kill()
        del self.search_bar
        self.story_container.kill()
        del self.story_container

    def chunks(self, L, n):
        return [L[x : x + n] for x in range(0, len(L), n)]

    def on_use(self):
        super().on_use()
        # Only update the positions if the search text changes
        if self.search_bar.is_focused and self.search_bar.get_text() == "name search":
            self.search_bar.set_text("")
        if self.search_bar.get_text() != self.previous_search_text:
            self.update_search_cats(self.search_bar.get_text())
        self.previous_search_text = self.search_bar.get_text()
