from random import choice
from re import sub

import i18n
import pygame
import pygame_gui

from scripts.cat.cats import Cat
from scripts.cat.enums import CatSocial, CatGroup
from scripts.game_structure import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.ui.elements.checkbox import UICheckbox
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.screens.enums import GameScreen
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.windows.window_base_class import GameWindow
from scripts.cat.sprites.display_sprites import update_sprite
from scripts.events_module.text_adjust import process_text
from scripts.ui.scale import ui_scale


class LeaveClanWindow(GameWindow):
    """This window allows the user to send the selected cat away from the Clan"""

    def __init__(self, cat: Cat):
        # LG
        # adjusting height based on additional clans
        height = 370
        for clan in game.clan.all_other_clans:
            height += 31
        # ---
        super().__init__(
            ui_scale(pygame.Rect((225, 130), (350, height))),
        )
        self.checkboxes = {}
        self.the_cat = cat
        self.chosen_social = None
        # LG
        self.new_group_ID = None
        self.error = None

        self.heading = pygame_gui.elements.UITextBox(
            "windows.leave_clan",
            ui_scale(pygame.Rect((0, 10), (300, -1))),
            object_id="#text_box_30_horizcenter_spacing_95",
            manager=MANAGER,
            container=self,
            anchors={"centerx": "centerx"},
        )

        prev_element = self.heading
        # LG edits: changes these items to lists to add group IDs
        social_list = [
            (CatSocial.CLANCAT, CatGroup.PLAYER_CLAN_ID, (game.clan.name + "Clan")),
            (CatSocial.LONER, CatGroup.LONER_GROUP_ID, "Loner group"),
            (CatSocial.ROGUE, CatGroup.ROGUE_GROUP_ID, "Rogue group"),
            (CatSocial.KITTYPET, CatGroup.HOUSEHOLD_ID, "Twolegplace"),
        ]
        for other_clan in game.clan.all_other_clans:
            social_list.append(
                (CatSocial.CLANCAT, other_clan.group_ID, (other_clan.name + "Clan"))
            )

        for social in social_list:
            self.checkboxes[social] = UICheckbox(
                position=(-60, 10),
                manager=MANAGER,
                container=self,
                anchors={"top_target": prev_element, "centerx": "centerx"},
            )
            # LG
            if social[1] == cat.status.group_ID:
                self.checkboxes[social].disable()
            else:
                self.checkboxes[social].enable()
            # ---

            self.checkboxes[f"{social[0]}_text"] = pygame_gui.elements.UITextBox(
                i18n.t(social[2], count=1),
                ui_scale(pygame.Rect((0, 10), (200, -1))),
                object_id="#text_box_30_horizleft_spacing_95",
                manager=MANAGER,
                container=self,
                text_kwargs={"count": 1},
                anchors={
                    "top_target": prev_element,
                    "left_target": self.checkboxes[social],
                },
            )
            prev_element = self.checkboxes[social]

        self.done_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, height - 50), (77, 30))),
            "buttons.done_lower",
            get_button_dict(ButtonStyles.SQUOVAL, (77, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
            container=self,
            anchors={"centerx": "centerx"},
        )
        self.error = pygame_gui.elements.UITextBox(
            "You can't join new groups yet!",
            ui_scale(pygame.Rect((0, height - 90), (400, -1))),
            object_id="#text_box_30_horizcenter",
            manager=MANAGER,
            container=self,
            anchors={"centerx": "centerx"},
        )
        if cat == game.clan.your_cat:
            self.done_button.disable()
            self.error.show()
        else:
            self.done_button.enable()
            self.error.hide()

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.done_button:
                # LG edits
                if self.new_group_ID in (
                    CatGroup.ROGUE_GROUP_ID,
                    CatGroup.LONER_GROUP,
                    CatGroup.HOUSEHOLD_ID,
                ):
                    # this cat is becoming a member of an outsider group
                    self.the_cat.leave_clan(
                        self.chosen_social, self.new_group_ID, cat_age=self.the_cat.age
                    )
                elif self.new_group_ID != CatGroup.PLAYER_CLAN_ID:
                    # this cat is joining a non-player clan
                    # TODO: populate clan?
                    self.the_cat.status.add_to_group(str(self.new_group_ID))
                else:
                    # this cat is joining the player clan
                    self.the_cat.add_to_clan()
                # ---
                game.all_screens[GameScreen.PROFILE].exit_screen()
                game.all_screens[GameScreen.PROFILE].screen_switches()
                self.kill()

            for name, button in self.checkboxes.items():
                if event.ui_element == button:
                    for _b in self.checkboxes.values():
                        if isinstance(_b, UICheckbox):
                            _b.uncheck()
                    if button.checked:
                        button.uncheck()
                    else:
                        button.check()
                        self.chosen_social = CatSocial(name[0])
                        self.new_group_ID = name[1]
        return super().process_event(event)
