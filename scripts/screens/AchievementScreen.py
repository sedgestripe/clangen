# pylint: disable=line-too-long
"""

This file contains:
  The start screen,
  The switch clan screen,
  The settings screen,
  And the statistics screen.



"""  # pylint: enable=line-too-long

import logging
from ..game_structure.game.settings import game_setting_get

import pygame
import pygame_gui

from scripts.cat.cats import Cat
from scripts.game_structure import game
from .Screens import Screens
from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale
from scripts.game_structure.localization import load_lang_resource
from scripts.game_structure.screen_settings import MANAGER

from scripts.lifegen_utility import check_achievements


logger = logging.getLogger(__name__)
has_checked_for_update = False
update_available = False


class AchievementScreen(Screens):
    """
    TODO: DOCS
    """

    def screen_switches(self):
        """
        TODO: DOCS
        """
        super().screen_switches()

        self.show_menu_buttons()
        self.show_mute_buttons()
        # self.set_disabled_menu_buttons(["achievements"])
        # LG EDIT
        self.update_heading_text(game.clan.your_cat.status.get_group_heading_text())
        # ---

        a_txt = load_lang_resource("achievements.json")

        check_achievements(Cat)

        # Determine stats
        self.heading = pygame_gui.elements.UITextBox(
            "<u>Achievements</u>",
            ui_scale(pygame.Rect((0, 140), (600, 500))),
            manager=MANAGER,
            object_id=get_text_box_theme("#text_box_40_horizcenter"),
            anchors={"centerx": "centerx"},
        )

        catname_colour = "#B5A17B" if game_setting_get("dark mode") else "#605546"
        stats_text = ""
        for i in game.clan.achievements:
            stats_text += (
                f"\n <b>{a_txt[i[0]][0]}</b> - "
                + f"{a_txt[i[0]][1]} "
                # + f"<font color='{catname_colour}'>({Cat.fetch_cat(i[1]).name})</font>"
            )

        self.stats_box = pygame_gui.elements.UITextBox(
            stats_text,
            ui_scale(pygame.Rect((0, 170), (600, 500))),
            manager=MANAGER,
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            anchors={"centerx": "centerx"},
        )

    def exit_screen(self):
        """
        TODO: DOCS
        """
        self.stats_box.kill()
        del self.stats_box
        self.heading.kill()
        del self.heading

    def handle_event(self, event):
        """
        TODO: DOCS
        """
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.menu_button_pressed(event)

    def on_use(self):
        """
        TODO: DOCS
        """
        super().on_use()
