import pygame
import pygame_gui
from random import choice

from scripts.game_structure import game, constants
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.elements.text_box_tweaked import UITextBoxTweaked
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.windows.window_base_class import GameWindow
from scripts.game_structure.game.switches import (
    Switch,
    switch_get_value,
    switch_set_value,
)
from scripts.ui.icon import Icon
from scripts.ui.scale import ui_scale
from scripts.screens.enums import GameScreen
from scripts.event_class import Single_Event
from scripts.game_structure.localization import load_lang_resource


class DeathScreen(GameWindow):
    def __init__(self, last_screen):
        super().__init__(
            ui_scale(pygame.Rect((155, 175), (490, 250))),
        )
        switch_set_value(Switch.window_open, True)

        self.clan_name = str(game.clan.name + "Clan")
        self.last_screen = last_screen
        self.pick_path_message = UITextBoxTweaked(
            f"<b>You are dead.</b>\nWhat will you do now?",
            ui_scale(pygame.Rect((20, 10), (435, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.begin_anew_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((35, 75), (210, 30))),
            Icon.DICE + " Start a new Clan",
            get_button_dict(ButtonStyles.SQUOVAL, (210, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.switch_cats_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((35, 115), (170, 30))),
            Icon.CAT_HEAD + " Switch cats",
            get_button_dict(ButtonStyles.SQUOVAL, (170, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.revive_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((265, 75), (170, 30))),
            Icon.STARCLAN + " Revive",
            get_button_dict(ButtonStyles.SQUOVAL, (170, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.new_life_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((225, 115), (210, 30))),
            Icon.PAW + " Start a new life",
            get_button_dict(ButtonStyles.SQUOVAL, (210, 30)),
            container=self,
            object_id="@buttonstyles_squoval",
        )

        self.continue_dead_button = UIImageButton(
            ui_scale(pygame.Rect((115, 165), (249, 48))),
            "",
            object_id="#continue_dead_button",
            container=self,
        )

        self.begin_anew_button.enable()
        self.switch_cats_button.enable()

        self.revive_button.enable()
        if (
            (game.clan.your_cat.dead_for >= constants.CONFIG["fading"]["age_to_fade"])
            and not game.clan.your_cat.prevent_fading
        ) or game.clan.your_cat.revives > 5:
            self.revive_button.disable()

        self.continue_dead_button.enable()
        self.new_life_button.enable()

    def process_event(self, event):
        super().process_event(event)

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.begin_anew_button:
                game.last_screen_forupdate = switch_get_value(Switch.cur_screen)
                switch_set_value(Switch.cur_screen, GameScreen.START)
                game.switch_screens = True

                switch_set_value(Switch.continue_after_death, False)

                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.switch_cats_button.kill()
                self.revive_button.kill()
                self.continue_dead_button.kill()
                self.new_life_button.kill()
                self.kill()
            elif event.ui_element == self.switch_cats_button:
                switch_set_value(Switch.window_open, False)

                game.last_screen_forupdate = switch_get_value(Switch.cur_screen)
                switch_set_value(Switch.cur_screen, GameScreen.CHOOSE_REBORN)
                game.switch_screens = True
                self.kill()

                switch_set_value(Switch.continue_after_death, False)
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.switch_cats_button.kill()
                self.revive_button.kill()
                self.continue_dead_button.kill()
                self.new_life_button.kill()
                self.kill()
            elif event.ui_element == self.revive_button:
                game.clan.your_cat.revive()
                switch_set_value(Switch.continue_after_death, False)
                switch_set_value(Switch.window_open, False)

                game.last_screen_forupdate = switch_get_value(Switch.cur_screen)
                switch_set_value(Switch.cur_screen, GameScreen.EVENTS)
                game.switch_screens = True

                revival_json = load_lang_resource("events/lifegen_events/revival.json")

                game.cur_events_list.append(Single_Event(choice(revival_json), "alert"))
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.switch_cats_button.kill()
                self.revive_button.kill()
                self.continue_dead_button.kill()
                self.new_life_button.kill()
                self.kill()
            elif event.ui_element == self.continue_dead_button:
                switch_set_value(Switch.window_open, False)
                switch_set_value(Switch.continue_after_death, True)
                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.switch_cats_button.kill()
                self.revive_button.kill()
                self.continue_dead_button.kill()
                self.new_life_button.kill()
                self.kill()
            elif event.ui_element == self.new_life_button:
                switch_set_value(Switch.window_open, False)
                switch_set_value(Switch.customise_new_life, True)
                switch_set_value(Switch.continue_after_death, False)
                game.last_screen_forupdate = switch_get_value(Switch.cur_screen)
                switch_set_value(Switch.cur_screen, GameScreen.MAKE_CLAN_CHOOSE_CATS)
                game.switch_screens = True

                self.begin_anew_button.kill()
                self.pick_path_message.kill()
                self.switch_cats_button.kill()
                self.revive_button.kill()
                self.continue_dead_button.kill()
                self.new_life_button.kill()
                self.kill()
