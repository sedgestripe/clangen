import pygame
from scripts.game_structure.screen_settings import MANAGER
from scripts.ui.elements.text_box_tweaked import UITextBoxTweaked
from scripts.housekeeping.game_version import get_version_info
from scripts.ui.windows.window_base_class import GameWindow
from scripts.ui.scale import ui_scale


class ChangelogWindow(GameWindow):
    def __init__(self):
        super().__init__(
            ui_scale(pygame.Rect((150, 150), (500, 400))),
        )

        self.changelog_popup_title = UITextBoxTweaked(
            "windows.whats_new",
            ui_scale(pygame.Rect((0, 10), (500, -1))),
            line_spacing=1,
            object_id="#changelog_popup_title",
            container=self,
            anchors={"centerx": "centerx"},
        )

        current_version_number = "{:.16}".format(get_version_info().version_number)

        self.changelog_popup_subtitle = UITextBoxTweaked(
            "windows.version_title",
            ui_scale(pygame.Rect((0, 35), (500, -1))),
            line_spacing=1,
            object_id="#changelog_popup_subtitle",
            container=self,
            anchors={"centerx": "centerx"},
            text_kwargs={"ver": current_version_number},
        )

        with open("changelog.txt", "r", encoding="utf-8") as read_file:
            file_cont = read_file.read()

        self.changelog_text = UITextBoxTweaked(
            file_cont,
            ui_scale(pygame.Rect((10, 65), (480, 325))),
            object_id="#text_box_30",
            line_spacing=0.95,
            starting_height=2,
            container=self,
            manager=MANAGER,
        )
