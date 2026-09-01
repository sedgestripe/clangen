import pygame
import pygame_gui

from scripts.game_structure import game
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.elements.text_box_tweaked import UITextBoxTweaked
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.windows.window_base_class import GameWindow
from scripts.game_structure.game.switches import (
    Switch,
    switch_get_value,
    switch_set_value,
)
from scripts.ui.scale import ui_scale
from scripts.screens.enums import GameScreen
from scripts.cat.enums import CatRank


class ChooseDeputyWindow(GameWindow):
    def __init__(self, last_screen):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 180))),
        )
        self.set_blocking(True)
        switch_set_value(Switch.window_open, True)

        self.clan_name = str(game.clan.name + "Clan")
        self.last_screen = last_screen
        self.pick_path_message = UITextBoxTweaked(
            f"<b>You need to choose a deputy.</b>\nWho will it be?",
            ui_scale(pygame.Rect((20, 20), (250, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((55, 95), (80, 30))),
            "skip",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.mediator_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((160, 95), (80, 30))),
            "choose",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.begin_anew_button.enable()
        self.mediator_button.enable()

    def process_event(self, event):
        super().process_event(event)
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.begin_anew_button:
                game.last_screen_forupdate = None
                switch_set_value(Switch.window_open, False)

                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.kill()
            elif event.ui_element == self.mediator_button:
                game.last_screen_forupdate = None
                if game.clan.deputy:
                    game.clan.deputy.rank_change(CatRank.WARRIOR)
                switch_set_value(Switch.window_open, False)

                game.last_screen_forupdate = switch_get_value(Switch.cur_screen)
                switch_set_value(Switch.cur_screen, GameScreen.CHOOSE_DEPUTY)
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.mediator_button.kill()
                self.kill()
