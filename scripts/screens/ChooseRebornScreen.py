import pygame.transform
import pygame_gui.elements

from .Screens import Screens

from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure import game
from scripts.game_structure.screen_settings import MANAGER
from ..cat.enums import CatGroup

from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.elements.sprite_button import UISpriteButton
from scripts.screens.enums import GameScreen

from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale, ui_scale_offset, ui_scale_dimensions

from scripts.clan_package.settings import get_clan_setting
from ..game_structure.game.switches import switch_set_value, Switch

from ..ui.generate_box import get_box, BoxStyles
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon


class ChooseRebornScreen(Screens):
    selected_cat = None
    current_page = 1
    selected_details = {}
    cat_list_buttons = {}

    def __init__(self, name=None):
        super().__init__(name)
        self.fav = {}
        self.list_page = None
        self.list_frame = None
        self.next_page_button = None
        self.previous_page_button = None
        self.confirm_cat = None
        self.back_button = None
        self.selected_cat_frame = None
        self.info = None
        self.heading = None
        self.the_cat = None
        self.dead_tab = None
        self.alive_tab = None
        self.current_list = "alive"
        self.current_sublist = "starclan"

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()
                self.update_tabs()
                # self.update_buttons()
            elif event.ui_element == self.confirm_cat and self.selected_cat:
                self.update_selected_cat()
                self.change_cat(self.selected_cat)
                if not self.selected_cat.dead:
                    switch_set_value(Switch.continue_after_death, False)
                else:
                    switch_set_value(Switch.continue_after_death, True)

                # self.update_buttons()
            elif event.ui_element == self.back_button:
                self.change_screen(GameScreen.PROFILE)
                switch_set_value(Switch.continue_after_death, False)
            elif event.ui_element == self.dead_tab:
                self.selected_cat = None
                self.current_list = "dead"
                self.current_page = 1
                self.alive_tab.enable()
                self.dead_tab.disable()
                self.update_selected_cat()
                self.update_cat_list()
            elif event.ui_element == self.alive_tab:
                self.selected_cat = None
                self.current_list = "alive"
                self.current_page = 1
                self.alive_tab.disable()
                self.dead_tab.enable()
                self.update_selected_cat()
                self.update_cat_list()
            elif event.ui_element == self.darkforest_tab:
                self.selected_cat = None
                self.current_list = "dead"
                self.current_sublist = "darkforest"
                self.current_page = 1
                self.darkforest_tab.disable()
                self.unknown_tab.enable()
                self.starclan_tab.enable()
                self.update_selected_cat()
                self.update_cat_list()
            elif event.ui_element == self.starclan_tab:
                self.selected_cat = None
                self.current_list = "dead"
                self.current_sublist = "starclan"
                self.current_page = 1
                self.starclan_tab.disable()
                self.unknown_tab.enable()
                self.darkforest_tab.enable()
                self.update_selected_cat()
                self.update_cat_list()
            elif event.ui_element == self.unknown_tab:
                self.selected_cat = None
                self.current_list = "dead"
                self.current_sublist = "unknown"
                self.current_page = 1
                self.darkforest_tab.enable()
                self.unknown_tab.disable()
                self.starclan_tab.enable()
                self.update_selected_cat()
                self.update_cat_list()
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                self.update_cat_list()
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                self.update_cat_list()

    def screen_switches(self):
        super().screen_switches()
        self.the_cat = game.clan.your_cat
        self.current_page = 1

        list_frame = get_box(BoxStyles.ROUNDED_BOX, (650, 226))
        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((75, 360), (650, 226))), list_frame, starting_height=1
        )

        self.heading = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((150, 25), (500, 40))),
            object_id=get_text_box_theme("#text_box_34_horizcenter"),
            manager=MANAGER,
        )
        self.selected_cat = None

        self.selected_cat_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((315, 113), (281, 197))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/choosing_cat1_frame_ment.png"
                ).convert_alpha(),
                (281, 197),
            ),
            manager=MANAGER,
        )

        self.cant_switch_warning = pygame_gui.elements.UITextBox(
            "You can't switch to an outside cat yet!",
            ui_scale(pygame.Rect((100, 210), (200, 100))),
            object_id=get_text_box_theme("#text_box_26_horizcenter"),
            manager=MANAGER,
        )
        self.cant_switch_warning.hide()

        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 60), (105, 30))),
            "buttons.back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.confirm_cat = UISurfaceImageButton(
            ui_scale(pygame.Rect((326, 310), (148, 30))),
            "Select Cat",
            get_button_dict(ButtonStyles.SQUOVAL, (148, 30)),
            object_id="@buttonstyles_squoval",
        )
        self.confirm_cat.disable()

        self.previous_page_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((315, 579), (34, 34))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=0,
        )
        self.next_page_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((451, 579), (34, 34))),
            Icon.ARROW_RIGHT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=0,
        )

        self.current_list = "alive"

        button_rect = ui_scale(pygame.Rect((0, 0), (90, 39)))
        button_rect.bottomleft = ui_scale_offset((90, 8))

        self.alive_tab = UISurfaceImageButton(
            button_rect,
            "Alive",
            get_button_dict(ButtonStyles.HORIZONTAL_TAB, (90, 39)),
            object_id="@buttonstyles_horizontal_tab",
            starting_height=2,
            anchors={"bottom": "bottom", "bottom_target": self.list_frame},
        )

        button_rect.bottomleft = ui_scale_offset((15, 8))
        self.dead_tab = UISurfaceImageButton(
            button_rect,
            "Dead",
            get_button_dict(ButtonStyles.HORIZONTAL_TAB, (90, 39)),
            object_id="@buttonstyles_horizontal_tab",
            starting_height=2,
            anchors={
                "bottom": "bottom",
                "bottom_target": self.list_frame,
                "left_target": self.alive_tab,
            },
        )

        button_rect = ui_scale(pygame.Rect((0, 0), (34, 34)))
        button_rect.bottomleft = ui_scale_offset((350, 8))
        self.starclan_tab = UISurfaceImageButton(
            button_rect,
            Icon.STARCLAN,
            get_button_dict(ButtonStyles.HORIZONTAL_TAB, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=2,
            anchors={
                "bottom": "bottom",
                "bottom_target": self.list_frame,
                "left_target": self.alive_tab,
            },
        )
        button_rect.bottomleft = ui_scale_offset((15, 8))
        self.unknown_tab = UISurfaceImageButton(
            button_rect,
            Icon.CLAN_OTHER,
            get_button_dict(ButtonStyles.HORIZONTAL_TAB, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=2,
            anchors={
                "bottom": "bottom",
                "bottom_target": self.list_frame,
                "left_target": self.starclan_tab,
            },
        )
        self.darkforest_tab = UISurfaceImageButton(
            button_rect,
            Icon.DARKFOREST,
            get_button_dict(ButtonStyles.HORIZONTAL_TAB, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=2,
            anchors={
                "bottom": "bottom",
                "bottom_target": self.list_frame,
                "left_target": self.unknown_tab,
            },
        )

        self.alive_tab.disable()
        self.update_selected_cat()  # Updates the image and details of selected cat
        self.update_cat_list()
        # self.update_buttons()

    def exit_screen(self):
        # self.selected_details["selected_image"].kill()
        # self.selected_details["selected_info"].kill()
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for marker in self.fav:
            self.fav[marker].kill()
        self.fav = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        self.heading.kill()
        del self.heading

        self.selected_cat_frame.kill()
        del self.selected_cat_frame

        self.back_button.kill()
        del self.back_button
        self.confirm_cat.kill()
        del self.confirm_cat

        self.previous_page_button.kill()
        del self.previous_page_button
        self.next_page_button.kill()
        del self.next_page_button
        self.alive_tab.kill()
        del self.alive_tab
        self.dead_tab.kill()
        del self.dead_tab

        self.starclan_tab.kill()
        del self.starclan_tab
        self.darkforest_tab.kill()
        del self.darkforest_tab
        self.unknown_tab.kill()
        del self.unknown_tab

        if self.cant_switch_warning:
            self.cant_switch_warning.kill()
            del self.cant_switch_warning

        self.list_frame.kill()

    def change_cat(self, new_mentor=None):
        game.cur_events_list.clear()
        game.clan.your_cat = new_mentor

        # resetting talked_to so the new MC can talk to a cat
        # the old one previously talked to in the same moon
        for cat in Cat.all_cats_list:
            if cat.talked_to is True:
                cat.talked_to = False

        switch_set_value(Switch.attended_half_moon, False)
        if game.clan.your_cat.status.rank.is_any_adult_warrior_like_rank():
            game.clan.your_cat.w_done = True
        switch_set_value(Switch.cat, game.clan.your_cat.ID)
        self.change_screen(GameScreen.PROFILE)

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat:
            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((325, 150), (150, 150))),
                pygame.transform.scale(
                    self.selected_cat.sprite, ui_scale_dimensions((150, 150))
                ),
                manager=MANAGER,
            )

            info = (
                self.selected_cat.status.rank
                + "\n"
                + self.selected_cat.genderalign
                + "\n"
                + self.selected_cat.personality.trait
                + "\n"
            )
            if self.selected_cat.moons < 1:
                info += "???"
            else:
                info += self.selected_cat.skills.skill_string(short=True)

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((482, 162), (105, 125))),
                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                manager=MANAGER,
            )

            name = str(self.selected_cat.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + "..."
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                ui_scale(pygame.Rect((345, 115), (110, 30))),
                name,
                object_id="#text_box_34_horizcenter",
                manager=MANAGER,
            )

    def update_cat_list(self):
        """Updates the cat sprite buttons."""
        valid_mentors = self.chunks(self.get_valid_cats(), 30)

        # clamp current page to a valid page number
        self.current_page = max(1, min(self.current_page, len(valid_mentors)))

        # Handle which next buttons are clickable.
        if len(valid_mentors) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_mentors):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_mentors) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_cats = []
        if valid_mentors:
            display_cats = valid_mentors[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        self.update_tabs()

        for marker in self.fav:
            self.fav[marker].kill()
        self.fav = {}

        pos_x = 0
        pos_y = 20
        i = 0
        for cat in display_cats:
            if get_clan_setting("show fav") and cat.favourite != 0:
                self.fav[str(i)] = pygame_gui.elements.UIImage(
                    ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))),
                    pygame.transform.scale(
                        pygame.image.load(
                            f"resources/images/fav_marker_{cat.favourite}.png"
                        ).convert_alpha(),
                        (50, 50),
                    ),
                )
                self.fav[str(i)].disable()
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))),
                cat.sprite,
                cat_object=cat,
                manager=MANAGER,
            )
            pos_x += 60
            if pos_x >= 550:
                pos_x = 0
                pos_y += 60
            i += 1

    def update_tabs(self):
        if self.selected_cat and self.selected_cat.status.is_outsider:
            self.confirm_cat.disable()
            self.cant_switch_warning.show()
        elif self.selected_cat is None:
            self.confirm_cat.disable()
            self.cant_switch_warning.hide()
        else:
            self.confirm_cat.enable()
            self.cant_switch_warning.hide()

        if self.current_list == "alive":
            self.starclan_tab.hide()
            self.darkforest_tab.hide()
            self.unknown_tab.hide()
        else:
            self.starclan_tab.show()
            self.darkforest_tab.show()
            self.unknown_tab.show()

    def get_valid_cats(self):
        valid_mentors = []

        for cat in Cat.all_cats_list:
            if self.current_list == "alive":
                if (
                    cat.status.alive_in_your_cat_group
                    and not cat.ID == game.clan.your_cat.ID
                ):
                    valid_mentors.append(cat)
            else:
                if self.current_sublist == "darkforest":
                    if (
                        cat.status.group == CatGroup.DARK_FOREST
                        and not cat.ID == game.clan.your_cat.ID
                        and not cat.ID == game.clan.demon.ID
                        and not cat.faded
                    ):
                        valid_mentors.append(cat)
                elif self.current_sublist == "starclan":
                    if (
                        cat.status.group == CatGroup.STARCLAN
                        and not cat.ID == game.clan.your_cat.ID
                        and not cat.ID == game.clan.instructor.ID
                        and not cat.faded
                    ):
                        valid_mentors.append(cat)
                elif self.current_sublist == "unknown":
                    if (
                        cat.status.group == CatGroup.UNKNOWN_RESIDENCE
                        and not cat.ID == game.clan.your_cat.ID
                        and not cat.faded
                    ):
                        valid_mentors.append(cat)

        return valid_mentors

    def on_use(self):
        super().on_use()

    def chunks(self, L, n):
        return [L[x : x + n] for x in range(0, len(L), n)]
