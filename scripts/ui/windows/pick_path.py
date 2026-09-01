import pygame
import pygame_gui
from random import choice

from scripts.game_structure import game
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.elements.text_box_tweaked import UITextBoxTweaked
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.windows.window_base_class import GameWindow
from scripts.game_structure.game.switches import Switch, switch_set_value
from scripts.ui.scale import ui_scale
from scripts.screens.enums import GameScreen
from scripts.ui.icon import Icon
from scripts.cat.enums import CatRank


class PickPath(GameWindow):
    def __init__(self, last_screen):
        super().__init__(
            ui_scale(pygame.Rect((220, 175), (400, 250))),
        )
        self.set_blocking(True)
        switch_set_value(Switch.window_open, True)

        self.clan_name = str(game.clan.name + "Clan")
        self.last_screen = last_screen
        self.pick_path_message = UITextBoxTweaked(
            f"You have an important decision to make...",
            ui_scale(pygame.Rect((20, 20), (360, -1))),
            line_spacing=1,
            object_id="#text_box_30_horizcenter",
            container=self,
        )

        self.begin_anew_button = UIImageButton(
            ui_scale(pygame.Rect((15, 80), (75, 75))),
            "",
            object_id="#med",
            container=self,
            tool_tip_text="Choose to become a medicine cat apprentice",
        )
        self.not_yet_button = UIImageButton(
            ui_scale(pygame.Rect((110, 80), (75, 75))),
            "",
            object_id="#warrior",
            container=self,
            tool_tip_text="Choose to become a warrior apprentice",
        )
        self.mediator_button = UIImageButton(
            ui_scale(pygame.Rect((205, 80), (75, 75))),
            "",
            object_id="#mediator",
            container=self,
            tool_tip_text="Choose to become a mediator apprentice",
        )
        self.queen_button = UIImageButton(
            ui_scale(pygame.Rect((300, 80), (75, 75))),
            "",
            object_id="#queen",
            container=self,
            tool_tip_text="Choose to become a queen's apprentice",
        )
        self.random_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((170, 175), (50, 50))),
            Icon.DICE,
            get_button_dict(ButtonStyles.ICON, (50, 50)),
            object_id="@buttonstyles_icon",
            container=self,
            tool_tip_text="Random",
        )

        self.not_yet_button.enable()
        self.begin_anew_button.enable()
        self.mediator_button.enable()
        self.random_button.enable()

    def process_event(self, event):
        super().process_event(event)

        try:
            status = ""
            if event.type == pygame_gui.UI_BUTTON_START_PRESS:
                if event.ui_element == self.begin_anew_button:
                    switch_set_value(Switch.window_open, False)

                    if game.clan.your_cat.moons < 12:
                        status = CatRank.MEDICINE_APPRENTICE
                    else:
                        status = CatRank.MEDICINE_CAT
                elif event.ui_element == self.not_yet_button:
                    switch_set_value(Switch.window_open, False)

                    if game.clan.your_cat.moons < 12:
                        status = CatRank.APPRENTICE
                    else:
                        status = CatRank.WARRIOR
                elif event.ui_element == self.mediator_button:
                    switch_set_value(Switch.window_open, False)

                    if game.clan.your_cat.moons < 12:
                        status = CatRank.MEDIATOR_APPRENTICE
                    else:
                        status = CatRank.MEDIATOR
                elif event.ui_element == self.queen_button:
                    switch_set_value(Switch.window_open, False)

                    if game.clan.your_cat.moons < 12:
                        status = CatRank.QUEENS_APPRENTICE
                    else:
                        status = CatRank.QUEEN
                elif event.ui_element == self.random_button:
                    switch_set_value(Switch.window_open, False)

                    if game.clan.your_cat.moons < 12:
                        status = choice(
                            [
                                CatRank.APPRENTICE,
                                CatRank.MEDIATOR_APPRENTICE,
                                CatRank.MEDICINE_APPRENTICE,
                                CatRank.QUEENS_APPRENTICE,
                            ]
                        )
                    else:
                        status = choice(
                            [
                                CatRank.WARRIOR,
                                CatRank.MEDICINE_CAT,
                                CatRank.MEDIATOR,
                                CatRank.QUEEN,
                            ]
                        )

                if status:
                    game.clan.your_cat.rank_change(status)
                    self.kill()
        except Exception as e:
            print("Error with PickPath window!")
            print(e)
