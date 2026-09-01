import pygame
import pygame_gui

from scripts.game_structure import game
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.elements.text_box_tweaked import UITextBoxTweaked
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.windows.window_base_class import GameWindow
from scripts.ui.scale import ui_scale
from scripts.game_structure.game.switches import Switch, switch_set_value


class RetireWindow(GameWindow):
    def __init__(self, last_screen):
        super().__init__(
            ui_scale(pygame.Rect((250, 200), (300, 150))),
        )
        self.set_blocking(True)
        switch_set_value(Switch.window_open, True)

        self.clan_name = str(game.clan.name + "Clan")
        self.last_screen = last_screen
        switch_set_value(Switch.retire, False)
        switch_set_value(Switch.retire_reject, False)
        self.pick_path_message = UITextBoxTweaked(
            f"You're asked if you would like to retire.",
            ui_scale(pygame.Rect((20, 20), (260, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((55, 95), (80, 30))),
            "accept",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )
        self.mediator_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((160, 95), (80, 30))),
            "reject",
            get_button_dict(ButtonStyles.SQUOVAL, (80, 30)),
            object_id="@buttonstyles_squoval",
            container=self,
        )

        self.begin_anew_button.enable()
        self.mediator_button.enable()

    def process_event(self, event):
        super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            try:
                if event.ui_element == self.begin_anew_button:
                    game.last_screen_forupdate = None
                    switch_set_value(Switch.window_open, False)

                    # game.switch_screens = True
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                    switch_set_value(Switch.retire, True)
                    game.clan.your_cat.status_change("elder")
                elif event.ui_element == self.mediator_button:
                    game.last_screen_forupdate = None
                    switch_set_value(Switch.window_open, False)

                    # game.switch_screens = True
                    self.begin_anew_button.kill()
                    self.pick_path_message.kill()
                    self.mediator_button.kill()
                    self.kill()
                    switch_set_value(Switch.retire_reject, True)
            except:
                print("error with retire screen")
