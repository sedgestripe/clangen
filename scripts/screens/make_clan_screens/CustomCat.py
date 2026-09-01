import pygame
import pygame_gui
from scripts.screens.make_clan_screens.MakeClanScreenBase import MakeClanScreenBase
from scripts.screens.enums import GameScreen
import copy

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
from scripts.cat.enums import CatRank, CatAge
from scripts.cat.pelts import Pelt
from scripts.cat.factories.new_cat_factory import NewCatFactory


class CustomCatScreen(MakeClanScreenBase):
    def __init__(self, name="custom_cat_screen"):
        super().__init__(name)
        # your edited cat
        self.custom_cat = None
        # the cat you started with
        self.starting_cat = None

        self.current_page = 1
        self.total_page_num = 2

    def screen_switches(self):
        super().screen_switches()
        self.starting_cat = Cat.all_cats.get(switch_get_value(Switch.cat))
        # dummy cat
        self.custom_cat = NewCatFactory.create_cat(rank=CatRank.KITTEN, moons=1)

        if self.starting_cat and not self.clan_info.your_cat:
            self.reset_custom_cat(copycat=self.starting_cat)
        elif self.clan_info.your_cat:
            self.custom_cat = self.clan_info.your_cat
        else:
            self.starting_cat = switch_get_value(Switch.possible_cats)[0]
            self.reset_custom_cat(copycat=self.starting_cat)

        self.elements["previous_step"].set_relative_position(
            ui_scale_dimensions((253, 630))
        )
        self.elements["next_step"].set_relative_position(ui_scale_dimensions((0, 630)))
        self.elements["next_step"].enable()

        self.elements["random_cat"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((-65, 50), (130, 34))),
            Icon.DICE + " Random Cat",
            get_button_dict(ButtonStyles.PROFILE_LEFT, (130, 34)),
            object_id="@buttonstyles_profile_left",
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )
        self.elements["reset_cat"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((65, 50), (130, 34))),
            "Reset Cat",
            get_button_dict(ButtonStyles.PROFILE_RIGHT, (130, 34)),
            object_id="@buttonstyles_profile_right",
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        self.elements["previous_page"] = UIImageButton(
            ui_scale(pygame.Rect((50, 275), (38, 50))),
            "",
            object_id="#arrow_right_fancy",
            starting_height=2,
        )
        self.elements["next_page"] = UIImageButton(
            ui_scale(pygame.Rect((712, 275), (38, 50))),
            "",
            object_id="#arrow_left_fancy",
            starting_height=2,
        )

        self.load_page()
        self.update_sprite()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.elements["previous_step"]:
                self.change_screen(GameScreen.MAKE_CLAN_CHOOSE_CATS)
            elif event.ui_element == self.elements["next_step"]:
                self._assign_cat()
                self.change_screen(GameScreen.MAKE_CLAN_YOUR_NAME)
            elif event.ui_element == self.elements["random_cat"]:
                self.custom_cat = NewCatFactory.create_cat(rank=CatRank.KITTEN, moons=1)
                self.update_sprite()
            elif event.ui_element == self.elements["reset_cat"]:
                self.reset_custom_cat()
                self.update_sprite()
            elif event.ui_element == self.elements["previous_page"]:
                self.current_page -= 1
                self.load_page()
            elif event.ui_element == self.elements["next_page"]:
                self.current_page += 1
                self.load_page()

        return super().handle_event(event)

    def _assign_cat(self):
        self.clan_info.your_cat = self.custom_cat

    # SPRITE UPDATING
    def update_sprite(self):
        self.custom_cat.pelt.rebuild_sprite = True
        if "your_cat_image" in self.elements:
            self.elements["your_cat_image"].kill()

        self.elements["your_cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((0, -50), (160, 160))),
            pygame.transform.scale(
                self.custom_cat.sprite, ui_scale_dimensions((160, 160))
            ),
            starting_height=1,
            manager=MANAGER,
            anchors={"centerx": "centerx", "centery": "centery"},
        )

    def reset_custom_cat(self, copycat=None):
        self.custom_cat.pelt.name = copycat.pelt.name if copycat else "SingleColour"
        self.custom_cat.pelt.colour = copycat.pelt.colour if copycat else "WHITE"
        self.custom_cat.pelt.white_patches = (
            copycat.pelt.white_patches if copycat else None
        )
        self.custom_cat.pelt.tortie_base = copycat.pelt.tortie_base if copycat else None
        self.custom_cat.pelt.tortie_colour = (
            copycat.pelt.tortie_colour if copycat else None
        )
        self.custom_cat.pelt.tortie_marking = (
            copycat.pelt.tortie_marking if copycat else None
        )
        self.custom_cat.pelt.tortie_patches = (
            copycat.pelt.tortie_patches if copycat else None
        )
        self.custom_cat.pelt.tint = copycat.pelt.tint if copycat else None
        self.custom_cat.pelt.white_patches_tint = (
            copycat.pelt.white_patches_tint if copycat else None
        )
        self.custom_cat.pelt.eye_colour = copycat.pelt.eye_colour if copycat else "BLUE"
        self.custom_cat.pelt.eye_colour2 = copycat.pelt.eye_colour2 if copycat else None
        self.custom_cat.pelt.length = copycat.pelt.length if copycat else "short"

        self.custom_cat.pelt.skin = copycat.pelt.skin if copycat else "PINK"
        self.custom_cat.pelt.reverse = copycat.pelt.reverse if copycat else False

        self.custom_cat.pelt.cat_sprites = (
            copycat.pelt.cat_sprites
            if copycat
            else {
                "newborn": "newborn0",
                "kitten": "kitten0",
                "adolescent": f"adolescent_{self.custom_cat.pelt.length}0",
                "adult": f"adult_{self.custom_cat.pelt.length}0",
                "para_adult": f"para_adult_{self.custom_cat.pelt.length}0",
                "senior": "senior0",
            }
        )
        self.custom_cat.pelt.cat_sprites[
            "young adult"
        ] = self.custom_cat.pelt.cat_sprites["adult"]
        self.custom_cat.pelt.cat_sprites[
            "senior adult"
        ] = self.custom_cat.pelt.cat_sprites["adult"]

    def load_page(self):
        self.update_buttons()
        if self.current_page == 1:
            self.open_page_1()
        elif self.current_page == 2:
            self.open_page_2()

    def open_page_1(self):
        print("Page 1!")

    def open_page_2(self):
        print("Page 2!")

    def update_buttons(self):
        if self.current_page >= self.total_page_num:
            self.elements["next_page"].disable()
        else:
            self.elements["next_page"].enable()
        if self.current_page <= 1:
            self.elements["previous_page"].disable()
        else:
            self.elements["previous_page"].enable()

    def exit_screen(self):
        super().exit_screen()
