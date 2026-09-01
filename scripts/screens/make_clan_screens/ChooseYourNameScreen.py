import pygame
import pygame_gui
from scripts.screens.make_clan_screens.MakeClanScreenBase import MakeClanScreenBase
from scripts.screens.enums import GameScreen
from scripts.game_structure import game

from scripts.game_structure.game import Switch, switch_get_value
from scripts.game_structure.game.switches import switch_set_value
from scripts.game_structure.screen_settings import MANAGER
from scripts.screens.enums import GameScreen
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.elements.modified_image import UIModifiedImage
from scripts.ui.elements.sprite_button import UISpriteButton
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.generate_button import ButtonStyles, get_button_dict
from scripts.ui.icon import Icon
from scripts.ui.scale import ui_scale, ui_scale_dimensions
from scripts.ui.theme import get_text_box_theme
from scripts.cat.cats import Cat
from scripts.cat.names import names


class ChooseYourNameScreen(MakeClanScreenBase):
    path = "resources/images/pick_clan_screen"
    ui_images = {
        "screen_art": pygame.image.load(f"{path}/your_name_screen.png").convert_alpha(),
    }

    def __init__(self, name="custom_cat_screen"):
        super().__init__(name)
        self.prefixes = names.names_dict["clan_prefixes"]

    def screen_switches(self):
        super().screen_switches()

        # decorative image
        self.elements["background"] = UIModifiedImage(
            ui_scale(pygame.Rect((0, 0), (800, 700))),
            pygame.transform.scale(
                self.ui_images["screen_art"],
                ui_scale_dimensions((800, 700)),
            ),
            manager=MANAGER,
        )
        self.elements["background"].disable()

        self.elements["previous_step"].set_relative_position(
            ui_scale_dimensions((253, 500))
        )
        self.elements["next_step"].set_relative_position(ui_scale_dimensions((0, 500)))

        self.elements["your_cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((0, -50), (160, 160))),
            pygame.transform.scale(
                self.clan_info.your_cat.sprite, ui_scale_dimensions((160, 160))
            ),
            starting_height=1,
            manager=MANAGER,
            anchors={"centerx": "centerx", "centery": "centery"},
        )

        # NAME
        self.elements["random_name"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((285, 398), (34, 34))),
            Icon.DICE,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            manager=MANAGER,
            sound_id="dice_roll",
        )

        self.elements["name_entry"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((330, 400), (140, 29))),
            manager=MANAGER,
            initial_text=self.clan_info.your_cat.name.prefix,
        )
        self.elements["name_entry"].set_forbidden_characters("forbidden_file_path")
        self.elements["name_entry"].set_text_length_limit(15)

        self.elements["suffix"] = pygame_gui.elements.UITextBox(
            "kit",
            ui_scale(pygame.Rect((470, 400), (100, 29))),
            object_id=get_text_box_theme("#text_box_30"),
            manager=MANAGER,
        )

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.elements["next_step"]:
                self.set_your_name()
                if switch_get_value(Switch.customise_new_life):
                    self.change_screen(GameScreen.MAKE_CLAN_CLAN_CREATED)
                else:
                    self.change_screen(GameScreen.MAKE_CLAN_CHOOSE_CAMP)
            if event.ui_element == self.elements["previous_step"]:
                self.change_screen(game.last_screen_forupdate)
            if event.ui_element == self.elements["random_name"]:
                self.elements["name_entry"].set_text(self.random_mc_name())
        return super().handle_event(event)

    def set_your_name(self):
        self.clan_info.your_cat.name.prefix = (
            self.elements["name_entry"].get_text().strip()
        )
        if switch_get_value(Switch.customise_new_life):
            game.clan.your_cat = self.clan_info.your_cat
            game.clan.your_cat.moons = -1
            switch_set_value(Switch.possible_cats, [])

    def update_buttons(self):
        if self.elements["name_entry"].get_text().strip():
            self.elements["next_step"].enable()
        else:
            self.elements["next_step"].disable()

    def on_use(self):
        super().on_use()
        self.update_buttons()

    def exit_screen(self):
        super().exit_screen()
