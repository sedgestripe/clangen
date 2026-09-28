import i18n
import pygame
import pygame_gui

from scripts.game_structure import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.elements.checkbox import UICheckbox
from scripts.screens.enums import GameScreen
from scripts.ui.windows.window_base_class import GameWindow
from scripts.ui.scale import ui_scale


class CatToggleWindow(GameWindow):
    """This window allows the user to edit various cat behavior toggles"""

    FAITH_LOCK_ORDER = ["flexible", "starclan", "dark forest", "neutral"]
    cat_toggles = [
        "prevent_fading",
        "prevent_kits",
        "prevent_retirement",
        "prevent_romance",
    ]

    def __init__(self, cat):
        super().__init__(
            ui_scale(pygame.Rect((300, 200), (400, 240))),
        )
        self.the_cat = cat

        self.checkboxes = {}
        self.textbox = {}
        self.refresh_checkboxes()

        prev_element = None
        for text in self.cat_toggles:
            self.textbox[text] = pygame_gui.elements.UITextBox(
                f"windows.{text}",
                ui_scale(pygame.Rect(55, 0 if prev_element else 26, -1, 34)),
                object_id="#text_box_30_horizleft_pad_0_8",
                container=self,
                anchors={"top_target": prev_element} if prev_element else None,
            )
            prev_element = self.textbox[text]

        self.text_5 = pygame_gui.elements.UITextBox(
            "windows.no_faith",
            ui_scale(pygame.Rect(55, 125, -1, 32)),
            object_id="#text_box_30_horizleft_pad_0_8",
            container=self,
        )

        self.faith_lock_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((22, 160), (356, 30))),
            "windows.faith_lock",
            get_button_dict(ButtonStyles.SQUOVAL, (356, 30)),
            object_id="@buttonstyles_squoval",
            text_kwargs=self.faith_lock_kwargs(),
            tool_tip_text="windows.faith_lock_tooltip",
            manager=MANAGER,
            container=self,
        )

    def faith_lock_kwargs(self):
        lock_key = self.the_cat.lock_faith.replace(" ", "_")
        return {"lock": i18n.t(f"windows.faith_lock_{lock_key}")}

    def refresh_faith_lock_button(self):
        self.faith_lock_button.set_text(
            "windows.faith_lock", text_kwargs=self.faith_lock_kwargs()
        )

    def refresh_checkboxes(self):
        for ele in self.checkboxes:
            self.checkboxes[ele].kill()
        self.checkboxes = {}

        self.checkboxes["prevent_fading"] = UICheckbox(
            (22, 25),
            container=self,
            tool_tip_text=f"windows.prevent_fading_tooltip",
            check=self.the_cat.prevent_fading,
        )
        self.checkboxes["prevent_kits"] = UICheckbox(
            (22, 0),
            container=self,
            anchors={
                "top_target": self.checkboxes["prevent_fading"],
            },
            tool_tip_text=f"windows.prevent_kits_tooltip",
            check=self.the_cat.no_kits,
        )

        self.checkboxes["prevent_retirement"] = UICheckbox(
            (22, 0),
            container=self,
            anchors={
                "top_target": self.checkboxes["prevent_kits"],
            },
            tool_tip_text=f"windows.prevent_retirement_tooltip",
            check=self.the_cat.no_retire,
        )

        self.checkboxes["prevent_romance"] = UICheckbox(
            (22, 0),
            container=self,
            anchors={
                "top_target": self.checkboxes["prevent_retirement"],
            },
            tool_tip_text=f"windows.prevent_romance_tooltip",
            check=self.the_cat.no_mates,
        )

        if self.the_cat == game.clan.instructor:
            self.checkboxes["prevent_fading"].set_tooltip(
                "windows.prevent_fading_tooltip_guide"
            )
            self.checkboxes["prevent_fading"].disable()

        # LG
        self.checkboxes["no_faith"] = UICheckbox(
            (22, 0),
            container=self,
            anchors={
                "top_target": self.checkboxes["prevent_romance"],
            },
            tool_tip_text=f"windows.no_faith_tooltip",
            check=self.the_cat.lock_faith,
        )

    def process_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                game.all_screens[GameScreen.PROFILE].exit_screen()
                game.all_screens[GameScreen.PROFILE].screen_switches()
            elif event.ui_element == self.checkboxes["prevent_fading"]:
                if self.checkboxes["prevent_fading"].checked:
                    self.checkboxes["prevent_fading"].uncheck()
                    self.the_cat.prevent_fading = False
                else:
                    self.checkboxes["prevent_fading"].check()
                    self.the_cat.prevent_fading = True
            elif event.ui_element == self.checkboxes["prevent_kits"]:
                if self.checkboxes["prevent_kits"].checked:
                    self.checkboxes["prevent_kits"].uncheck()
                    self.the_cat.no_kits = False
                else:
                    self.checkboxes["prevent_kits"].check()
                    self.the_cat.no_kits = True
            elif event.ui_element == self.checkboxes["prevent_retirement"]:
                if self.checkboxes["prevent_retirement"].checked:
                    self.checkboxes["prevent_retirement"].uncheck()
                    self.the_cat.no_retire = False
                else:
                    self.checkboxes["prevent_retirement"].check()
                    self.the_cat.no_retire = True
            elif event.ui_element == self.checkboxes["prevent_romance"]:
                if self.checkboxes["prevent_romance"].checked:
                    self.checkboxes["prevent_romance"].uncheck()
                    self.the_cat.no_mates = False
                else:
                    self.checkboxes["prevent_romance"].check()
                    self.the_cat.no_mates = True
            elif event.ui_element == self.checkboxes["no_faith"]:
                if self.checkboxes["no_faith"].checked:
                    self.checkboxes["no_faith"].uncheck()
                    self.the_cat.lock_faith = False
                else:
                    self.checkboxes["no_faith"].check()
                    self.the_cat.lock_faith = True

        return super().process_event(event)
