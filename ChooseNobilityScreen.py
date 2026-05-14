#!/usr/bin/env python3
# -*- coding: ascii -*-
import os

import pygame
import pygame_gui

from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.game_structure.ui_elements import (
    UITextBoxTweaked,
    UISurfaceImageButton,
)
from scripts.utility import (
    get_text_box_theme,
    shorten_text_to_fit,
    ui_scale_dimensions,
    ui_scale,
)
from .Screens import Screens
from ..game_structure.screen_settings import MANAGER
from ..ui.generate_box import BoxStyles, get_box
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.get_arrow import get_arrow


class ChooseNobilityScreen(Screens):
    the_cat = None
    selected_cat_elements = {}
    buttons = {}
    next_cat = None
    previous_cat = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.mute_button_pressed(event)

            if event.ui_element == self.back_button:
                self.change_screen("profile screen")
            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat):
                    game.switches["cat"] = self.next_cat
                    self.update_selected_cat()
                else:
                    print("invalid next cat", self.next_cat)
            elif event.ui_element == self.previous_cat_button:
                if isinstance(Cat.fetch_cat(self.previous_cat), Cat):
                    game.switches["cat"] = self.previous_cat
                    self.update_selected_cat()
                else:
                    print("invalid previous cat", self.previous_cat)
            elif event.ui_element == self.ennoble_duke:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 7
                self.update_selected_cat()
            elif event.ui_element == self.ennoble_marquess:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 6
                self.update_selected_cat()
            elif event.ui_element == self.ennoble_earl:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 5
                self.update_selected_cat()
            elif event.ui_element == self.ennoble_viscount:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 4
                self.update_selected_cat()
            elif event.ui_element == self.ennoble_baron:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 3
                self.update_selected_cat()
            elif event.ui_element == self.promote_knight:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 2
                self.update_selected_cat()
            elif event.ui_element == self.demote_marquess:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 6
                self.update_selected_cat()
            elif event.ui_element == self.demote_earl:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 5
                self.update_selected_cat()
            elif event.ui_element == self.demote_viscount:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 4
                self.update_selected_cat()
            elif event.ui_element == self.demote_baron:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 3
                self.update_selected_cat()
            elif event.ui_element == self.demote_knight:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 2
                self.update_selected_cat()
            elif event.ui_element == self.revoke_nobility:
                self.the_cat.former_nobility = self.the_cat.nobility_rank
                self.the_cat.nobility_rank = 1
                self.update_selected_cat()

        elif event.type == pygame.KEYDOWN and game.settings["keybinds"]:
            if event.key == pygame.K_ESCAPE:
                self.change_screen("profile screen")
            elif event.key == pygame.K_RIGHT:
                game.switches["cat"] = self.next_cat
                self.update_selected_cat()
            elif event.key == pygame.K_LEFT:
                game.switches["cat"] = self.previous_cat
                self.update_selected_cat()

    def screen_switches(self):
        super().screen_switches()
        self.show_mute_buttons()

        self.next_cat_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((622, 25), (153, 30))),
            "Next Cat " + get_arrow(3, arrow_left=False),
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            sound_id="page_flip",
            manager=MANAGER,
        )
        self.previous_cat_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (153, 30))),
            get_arrow(2, arrow_left=True) + " Previous Cat",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            sound_id="page_flip",
            manager=MANAGER,
        )
        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 60), (105, 30))),
            get_arrow(2) + " Back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )

        # Create the buttons
        self.bar = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((48, 350), (704, 10))),
            pygame.transform.scale(
                image_cache.load_image("resources/images/bar.png"),
                ui_scale_dimensions((704, 10)),
            ),
            manager=MANAGER,
        )

        self.blurb_background = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((50, 195), (700, 150))),
            get_box(BoxStyles.ROUNDED_BOX, (700, 150)),
        )

        # promote
        
        self.ennoble_duke = UISurfaceImageButton(
            ui_scale(pygame.Rect((48, 0), (172, 36))),
            "ennoble as duke",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_top",
            anchors={"top_target": self.bar},
        )
        self.ennoble_marquess = UISurfaceImageButton(
            ui_scale(pygame.Rect((48, 0), (172, 36))),
            "ennoble as marquess",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.ennoble_duke},
        )
        self.ennoble_earl = UISurfaceImageButton(
            ui_scale(pygame.Rect((225, 0), (172, 36))),
            "ennoble as earl",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.bar},
        )
        self.ennoble_viscount = UISurfaceImageButton(
            ui_scale(pygame.Rect((225, 0), (172, 36))),
            "ennoble as viscount",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.ennoble_earl},
        )
        self.ennoble_baron = UISurfaceImageButton(
            ui_scale(pygame.Rect((402, 0), (172, 36))),
            "ennoble as baron",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.bar},
        )
        self.promote_knight = UISurfaceImageButton(
            ui_scale(pygame.Rect((402, 0), (172, 36))),
            "knight",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.ennoble_baron},
        )
        # LG
        self.revoke_nobility = UISurfaceImageButton(
            ui_scale(pygame.Rect((579, 0), (172, 36))),
            "revoke nobility",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.bar},
        )

        # demote

        self.demote_marquess = UISurfaceImageButton(
            ui_scale(pygame.Rect((48, 0), (172, 36))),
            "denounce to marquess",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.ennoble_duke},
        )
        self.demote_earl = UISurfaceImageButton(
            ui_scale(pygame.Rect((225, 0), (172, 36))),
            "denounce to earl",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.bar},
        )
        self.demote_viscount = UISurfaceImageButton(
            ui_scale(pygame.Rect((225, 0), (172, 36))),
            "denounce to viscount",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.demote_earl},
        )
        self.demote_baron = UISurfaceImageButton(
            ui_scale(pygame.Rect((402, 0), (172, 36))),
            "denounce to baron",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.bar},
        )
        self.demote_knight = UISurfaceImageButton(
            ui_scale(pygame.Rect((402, 0), (172, 36))),
            "denounce to knight",
            get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
            object_id="@buttonstyles_ladder_middle",
            anchors={"top_target": self.demote_baron},
        )
        self.update_selected_cat()

    def update_selected_cat(self):
        for ele in self.selected_cat_elements:
            self.selected_cat_elements[ele].kill()
        self.selected_cat_elements = {}

        self.the_cat = Cat.fetch_cat(game.switches["cat"])
        if not self.the_cat:
            return

        self.selected_cat_elements["cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((245, 40), (150, 150))),
            pygame.transform.scale(
                self.the_cat.sprite, ui_scale_dimensions((150, 150))
            ),
            manager=MANAGER,
        )

        name = str(self.the_cat.name)
        short_name = shorten_text_to_fit(name, 150, 13)
        self.selected_cat_elements["cat_name"] = pygame_gui.elements.UILabel(
            ui_scale(pygame.Rect((387, 70), (175, -1))),
            short_name,
            object_id=get_text_box_theme("#text_box_30"),
        )

        self.the_cat.nobility_str = "commoner"
        if self.the_cat.nobility_rank == 2:
            self.the_cat.nobility_str = "knight"
        elif self.the_cat.nobility_rank == 3:
            self.the_cat.nobility_str = "baron"
        elif self.the_cat.nobility_rank == 4:
            self.the_cat.nobility_str = "viscount"
        elif self.the_cat.nobility_rank == 5:
            self.the_cat.nobility_str = "earl"
        elif self.the_cat.nobility_rank == 6:
            self.the_cat.nobility_str = "marquess"
        elif self.the_cat.nobility_rank == 7:
            self.the_cat.nobility_str = "duke"

        text = f"<b>{self.the_cat.nobility_str}</b>\n{self.the_cat.personality.trait}\n"

        text += f"{self.the_cat.moons} "

        if self.the_cat.moons == 1:
            text += "moon  |  "
        else:
            text += "moons  |  "

        text += self.the_cat.genderalign + "\n"

        self.selected_cat_elements["cat_details"] = UITextBoxTweaked(
            text,
            ui_scale(pygame.Rect((395, 100), (160, 94))),
            object_id=get_text_box_theme("#text_box_22_horizcenter"),
            manager=MANAGER,
            line_spacing=0.95,
        )

        self.selected_cat_elements["nobility_blurb"] = pygame_gui.elements.UITextBox(
            self.get_nobility_blurb(),
            ui_scale(pygame.Rect((170, 200), (560, 135))),
            object_id="#text_box_26_horizcenter_vertcenter_spacing_95",
            manager=MANAGER,
        )

        main_dir = "resources/images/"
        paths = {
            7: "leader_icon.png",
            6: "deputy_icon.png",
            5: "warrior_icon.png",
            4: "medic_icon.png",
            3: "mediator_icon.png",
            2: "elder_icon.png",
            1: "kit_icon.png",
            
        }

        if self.the_cat.nobility_rank in paths:
            icon_path = os.path.join(main_dir, paths[self.the_cat.nobility_rank])
        else:
            icon_path = os.path.join(main_dir, "buttonrank.png")

        self.selected_cat_elements["role_icon"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((82, 231), (78, 78))),
            pygame.transform.scale(
                image_cache.load_image(icon_path),
                ui_scale_dimensions((78, 78)),
            ),
        )

        (
            self.next_cat,
            self.previous_cat,
        ) = self.the_cat.determine_next_and_previous_cats()
        self.update_disabled_buttons()

    def update_disabled_buttons(self):
        # Previous and next cat button
        if self.next_cat == 0:
            self.next_cat_button.disable()
        else:
            self.next_cat_button.enable()

        if self.previous_cat == 0:
            self.previous_cat_button.disable()
        else:
            self.previous_cat_button.enable()

        if self.the_cat.nobility_rank == 7:
            self.revoke_nobility.enable()
            self.ennoble_duke.disable()

            self.ennoble_marquess.hide()
            self.ennoble_earl.hide()
            self.ennoble_baron.hide()
            self.promote_knight.hide()
            self.ennoble_viscount.hide()
            self.demote_marquess.show()
            self.demote_earl.show()
            self.demote_viscount.show()
            self.demote_baron.show()
            self.demote_knight.show()
    
        elif self.the_cat.nobility_rank == 6:
                self.ennoble_duke.enable()
                self.ennoble_duke.show()
                self.ennoble_marquess.disable()
                self.ennoble_marquess.show()
                self.demote_marquess.hide()

                self.ennoble_earl.hide()
                self.ennoble_baron.hide()
                self.promote_knight.hide()
                self.ennoble_viscount.hide()
                self.revoke_nobility.enable()
                self.demote_earl.show()
                self.demote_viscount.show()
                self.demote_baron.show()
                self.demote_knight.show()

        elif self.the_cat.nobility_rank == 5:
                self.ennoble_duke.enable()
                self.ennoble_marquess.enable()
                self.revoke_nobility.enable()

                self.ennoble_duke.show()
                self.ennoble_marquess.show()

                self.ennoble_earl.disable()
                self.ennoble_earl.show()
                self.demote_earl.hide()

                self.ennoble_viscount.hide()
                self.ennoble_baron.hide()
                self.promote_knight.hide()
                
                self.demote_viscount.show()
                self.demote_baron.show()
                self.demote_knight.show()

        elif self.the_cat.nobility_rank == 4:
            self.ennoble_duke.enable()
            self.ennoble_marquess.enable()
            self.ennoble_earl.enable()
            self.revoke_nobility.enable()

            self.ennoble_duke.show()
            self.ennoble_marquess.show()
            self.ennoble_earl.show()
            self.revoke_nobility.show()

            self.ennoble_viscount.disable()
            self.ennoble_viscount.show()
            

            self.ennoble_baron.hide()
            self.promote_knight.hide()
            

            self.demote_baron.show()
            self.demote_knight.show()

            self.demote_viscount.hide()
            self.demote_marquess.hide()
            self.demote_earl.hide()

        elif self.the_cat.nobility_rank == 3:
            self.ennoble_duke.enable()
            self.ennoble_marquess.enable()
            self.ennoble_earl.enable()
            self.ennoble_viscount.enable()
            self.revoke_nobility.enable()

            self.ennoble_duke.show()
            self.ennoble_marquess.show()
            self.ennoble_earl.show()
            self.ennoble_viscount.show()
            self.revoke_nobility.show()

            self.ennoble_baron.disable()
            self.ennoble_baron.show()

            self.demote_baron.hide()
            self.demote_marquess.hide()
            self.demote_earl.hide()
            self.demote_viscount.hide()
            self.promote_knight.hide()
            
            self.demote_knight.show()

        elif self.the_cat.nobility_rank == 2:
                self.ennoble_duke.enable()
                self.ennoble_marquess.enable()
                self.ennoble_earl.enable()
                self.ennoble_baron.enable()
                self.revoke_nobility.enable()
                self.ennoble_viscount.enable()

                self.ennoble_duke.show()
                self.ennoble_marquess.show()
                self.ennoble_earl.show()
                self.ennoble_baron.show()
                self.revoke_nobility.show()
                self.ennoble_viscount.show()

                self.demote_marquess.hide()
                self.demote_earl.hide()
                self.demote_viscount.hide()
                self.demote_baron.hide()

                self.promote_knight.disable()
                self.promote_knight.show()
                self.demote_knight.hide()

        elif self.the_cat.nobility_rank == 1:
                self.ennoble_duke.show()
                self.ennoble_marquess.show()
                self.ennoble_earl.show()
                self.ennoble_baron.show()
                self.promote_knight.show()
                self.ennoble_viscount.show()

                self.ennoble_duke.enable()
                self.ennoble_marquess.enable()
                self.ennoble_earl.enable()
                self.ennoble_viscount.enable()
                self.ennoble_baron.enable()
                self.promote_knight.enable()
                self.promote_knight.enable()

                self.revoke_nobility.disable()

                self.demote_marquess.hide()
                self.demote_earl.hide()
                self.demote_viscount.hide()
                self.demote_baron.hide()
                self.demote_knight.hide()


    def get_nobility_blurb(self):
        if self.the_cat.nobility_rank == 7:
            output = (
                f"{self.the_cat.name} is a <b>duke</b>. Dukes are the highest order of nobility. "
                f"Dukes are responsible for a large amount of land and citizens."
            )
        elif self.the_cat.nobility_rank == 6:
            output = (
                f"{self.the_cat.name} is a <b>marquess</b>. Marquesses are responsible "
                f"for border lands and external threats. Marquesses usually have "
                f"military power."
            )
        elif self.the_cat.nobility_rank == 5:
            output = (
                f"{self.the_cat.name} is an <b>earl</b>. Earls are responsible "
                f"for a small area within a duke's land. Earls rank below "
                f"dukes and marquesses."
            )
        elif self.the_cat.nobility_rank == 4:
            output = (
                f"{self.the_cat.name} is a <b>viscount</b>. Viscounts are "
                f"responsible for an area within the land of an earl. "
                f"Viscounts rank below earls, marquesses and dukes."
            )
        elif self.the_cat.nobility_rank == 3:
            output = (
                f"{self.the_cat.name} is a <b>baron</b>. Barons are responsible "
                f"for a an area within the land of a viscount. Barons rank "
                f"below viscounts, earls, marquesses and dukes."
            )
        elif self.the_cat.nobility_rank == 2:
            output = (
                    f"{self.the_cat.name} is a <b>knight</b>. Knights are given "
                    f"their rank to symbolize their contribution to the clan. Traditionally "
                    f"knights were elite fighters, however that has changed. Knights may have "
                    f"an area of land to rule, however not all do."
                    )
        elif self.the_cat.nobility_rank == 1:
            output = (
                f"{self.the_cat.name} is a <b>commoner</b>. Commoners are the "
                f"cats in your clan which do not have a title. Commoners make up "
                f"the bulk of your clan."
            )
        else:
            output = f"{self.the_cat.name} has an unknown title. I guess they want to make their own way in life! "

        return output

    def exit_screen(self):
        self.back_button.kill()
        del self.back_button
        self.next_cat_button.kill()
        del self.next_cat_button
        self.previous_cat_button.kill()
        del self.previous_cat_button
        self.bar.kill()
        del self.bar
        self.ennoble_duke.kill()
        del self.ennoble_duke
        self.ennoble_marquess.kill()
        del self.ennoble_marquess
        self.ennoble_earl.kill()
        del self.ennoble_earl
        self.ennoble_baron.kill()
        del self.ennoble_baron
        self.promote_knight.kill()
        del self.promote_knight
        self.revoke_nobility.kill()
        del self.revoke_nobility
        self.ennoble_viscount.kill()
        del self.ennoble_viscount
        self.demote_marquess.kill()
        del self.demote_marquess
        self.demote_earl.kill()
        del self.demote_earl
        self.demote_viscount.kill()
        del self.demote_viscount
        self.demote_baron.kill()
        del self.demote_baron
        self.demote_knight.kill()
        del self.demote_knight
        self.blurb_background.kill()
        del self.blurb_background

        for ele in self.selected_cat_elements:
            self.selected_cat_elements[ele].kill()
        self.selected_cat_elements = {}