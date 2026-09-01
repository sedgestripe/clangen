from random import randrange

import i18n
import pygame
import pygame_gui
from pygame_gui.core import UIContainer

from scripts.game_structure.screen_settings import MANAGER
from scripts.screens.enums import GameScreen
from scripts.ui.elements.image_button import UIImageButton
from scripts.ui.elements.surface_image_button import UISurfaceImageButton
from scripts.ui.generate_box import BoxStyles, get_box
from scripts.ui.generate_button import ButtonStyles, get_button_dict
from scripts.ui.icon import Icon
from scripts.ui.scale import ui_scale, ui_scale_dimensions, ui_scale_offset


from scripts.screens.make_clan_screens.MakeClanScreenBase import MakeClanScreenBase
from scripts.ui.windows.cruel_locked_action import CruelLockedAction
from scripts.cat.enums import CatSocial


class ChooseCampScreen(MakeClanScreenBase):
    def __init__(self, name="choose_camp_screen"):
        super().__init__(name)
        self.tabs = {}
        self.selected_camp_tab = 1

    def screen_switches(self):
        super().screen_switches()
        self.selected_camp_tab = 1

        self.elements["previous_step"].show()
        self.elements["next_step"].show()

        # return step buttons to their default position
        self.elements["previous_step"].set_relative_position(
            ui_scale_dimensions((253, 620))
        )
        self.elements["next_step"].set_relative_position(ui_scale_dimensions((0, 620)))

        # Biome buttons
        self.elements["biome_container"] = UIContainer(
            ui_scale(pygame.Rect(((0, 100), (500, 100)))),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        prev_element = None
        for biome in ("forest", "mountainous", "plains", "beach"):
            self.elements[f"{biome}_biome"] = UIImageButton(
                ui_scale(pygame.Rect((20, 0), (100, 46))),
                f"screens.make_clan.{biome.capitalize()}",
                object_id=f"#{biome}_biome_button",
                container=self.elements["biome_container"],
                anchors={"left_target": prev_element} if prev_element else None,
                manager=MANAGER,
            )
            prev_element = self.elements[f"{biome}_biome"]

        # Camp Art Choosing Tabs, Dummy buttons, will be overridden.
        for i in range(1, 11):
            self.tabs[f"tab{i}"] = UIImageButton(
                ui_scale(pygame.Rect((0, 0), (0, 0))),
                "",
                visible=False,
                manager=MANAGER,
            )

        self.elements["season_container"] = UIContainer(
            ui_scale(pygame.Rect((625, 225), (39, 400))),
            manager=MANAGER,
        )
        season_icon_map = {
            "newleaf": Icon.NEWLEAF,
            "greenleaf": Icon.GREENLEAF,
            "leaf-fall": Icon.LEAFFALL,
            "leaf-bare": Icon.LEAFBARE,
        }
        prev_element = None
        for season, icon in season_icon_map.items():
            self.tabs[f"{season}_tab"] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, 30), (39, 34))),
                icon,
                get_button_dict(ButtonStyles.ICON_TAB_LEFT, (39, 36)),
                object_id="@buttonstyles_icon_tab_left",
                manager=MANAGER,
                tool_tip_text="screens.make_clan.season_tooltip",
                container=self.elements["season_container"],
                tool_tip_text_kwargs={
                    "season": i18n.t(f"general.{season.capitalize()}")
                },
                anchors={"top_target": prev_element} if prev_element else None,
            )
            prev_element = self.tabs[f"{season}_tab"]

        # Random background
        self.elements["random_background"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((255, 580), (290, 30))),
            "screens.make_clan.choose_random_background",
            get_button_dict(ButtonStyles.SQUOVAL, (290, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )

        # art frame
        self.draw_art_frame()
        self.refresh_text_and_buttons()

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.elements["previous_step"]:
                self.set_bg(None)
                self.change_screen(GameScreen.MAKE_CLAN_CHOOSE_CATS)
            elif event.ui_element == self.elements["forest_biome"]:
                self.clan_info.biome = "Forest"
                self.selected_camp_tab = 1
                self.refresh_text_and_buttons()
            elif event.ui_element == self.elements["mountainous_biome"]:
                self.clan_info.biome = "Mountainous"
                self.selected_camp_tab = 1
                self.refresh_text_and_buttons()
            elif event.ui_element == self.elements["plains_biome"]:
                self.clan_info.biome = "Plains"
                self.selected_camp_tab = 1
                self.refresh_text_and_buttons()
            elif event.ui_element == self.elements["beach_biome"]:
                self.clan_info.biome = "Beach"
                self.selected_camp_tab = 1
                self.refresh_text_and_buttons()
            elif event.ui_element == self.tabs["newleaf_tab"]:
                if self.get_config_during_creation("seasons.lock_season"):
                    CruelLockedAction()
                    return True
                self.clan_info.starting_season = "Newleaf"
                self.refresh_text_and_buttons()
            elif event.ui_element == self.tabs["greenleaf_tab"]:
                if self.get_config_during_creation("seasons.lock_season"):
                    CruelLockedAction()
                    return True
                self.clan_info.starting_season = "Greenleaf"
                self.refresh_text_and_buttons()
            elif event.ui_element == self.tabs["leaf-fall_tab"]:
                if self.get_config_during_creation("seasons.lock_season"):
                    CruelLockedAction()
                    return True
                self.clan_info.starting_season = "Leaf-fall"
                self.refresh_text_and_buttons()
            elif event.ui_element == self.tabs["leaf-bare_tab"]:
                if self.get_config_during_creation("seasons.lock_season"):
                    CruelLockedAction()
                    return True
                self.clan_info.starting_season = "Leaf-bare"
                self.refresh_text_and_buttons()
            elif event.ui_element == self.elements["random_background"]:
                # Select a random biome and background
                self.clan_info.biome = self.random_biome_selection()
                max_camps = len(
                    (self.get_possible_camps()[self.clan_info.biome]).keys()
                )
                self.selected_camp_tab = randrange(1, max_camps)
                self.clan_info.camp_bg = f"camp{self.selected_camp_tab}"
                self.refresh_selected_camp()
                self.refresh_text_and_buttons()
            elif event.ui_element == self.elements["next_step"]:
                self.clan_info.camp_bg = f"camp{self.selected_camp_tab}"
                self.change_screen(GameScreen.MAKE_CLAN_CHOOSE_SYMBOL)

            for tab_id, button in self.tabs.items():
                if event.ui_element == button:
                    tabnum = tab_id.replace("tab", "")
                    if "_" in tabnum:
                        # its a season tab
                        continue
                    self.selected_camp_tab = int(tabnum)
                    self.refresh_selected_camp()

        return super().handle_event(event)

    def exit_screen(self):
        for ele in self.tabs.values():
            ele.kill()

        super().exit_screen()

    def draw_art_frame(self):
        if "art_frame" in self.elements:
            return
        self.elements["art_frame"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect(((0, 10), (466, 416)))),
            get_box(BoxStyles.FRAME, (466, 416)),
            manager=MANAGER,
            starting_height=2,
            anchors={"center": "center"},
        )

    def refresh_text_and_buttons(self):
        # Enable/disable biome buttons
        self.elements["forest_biome"].enable()
        self.elements["mountainous_biome"].enable()
        self.elements["plains_biome"].enable()
        self.elements["beach_biome"].enable()

        if self.clan_info.biome == "Forest":
            self.elements["forest_biome"].disable()
        elif self.clan_info.biome == "Mountainous":
            self.elements["mountainous_biome"].disable()
        elif self.clan_info.biome == "Plains":
            self.elements["plains_biome"].disable()
        elif self.clan_info.biome == "Beach":
            self.elements["beach_biome"].disable()

        config_season = self.get_config_during_creation("seasons.force_starting_season")
        if config_season:
            self.clan_info.starting_season = config_season

        # enable/disable season buttons
        self.tabs["newleaf_tab"].enable()
        self.tabs["greenleaf_tab"].enable()
        self.tabs["leaf-fall_tab"].enable()
        self.tabs["leaf-bare_tab"].enable()
        self.tabs[f"{self.clan_info.starting_season.lower()}_tab"].disable()

        if self.clan_info.biome and self.selected_camp_tab:
            self.elements["next_step"].enable()

        # Deal with tab and shown camp image:
        self.refresh_selected_camp()

    def refresh_selected_camp(self):
        """Updates selected camp image and tabs"""
        self.tabs["tab1"].kill()
        self.tabs["tab2"].kill()
        self.tabs["tab3"].kill()
        self.tabs["tab4"].kill()
        self.tabs["tab5"].kill()
        self.tabs["tab6"].kill()
        self.tabs["tab7"].kill()
        self.tabs["tab8"].kill()
        self.tabs["tab9"].kill()
        self.tabs["tab10"].kill()

        # this is all edited for lg
        camp_dict = self.get_possible_camps()

        for camp_num, camp_info in camp_dict[self.clan_info.biome].items():
            tab_rect = ui_scale(pygame.Rect((0, 0), (camp_info["button_width"], 30)))
            tab_rect.topright = (
                ui_scale_offset((5, 180))
                if int(camp_num) == 1
                else ui_scale_offset((5, 5))
            )

            self.tabs[f"tab{camp_num}"] = UISurfaceImageButton(
                tab_rect,
                f"screens.make_clan.{camp_info['camp_name']}",
                get_button_dict(
                    ButtonStyles.VERTICAL_TAB, (camp_info["button_width"], 30)
                ),
                object_id="@buttonstyles_vertical_tab",
                manager=MANAGER,
                anchors=(
                    {
                        "right": "right",
                        "right_target": self.elements["art_frame"],
                        "top_target": self.tabs[f"tab{int(camp_num) - 1}"],
                    }
                    if int(camp_num) > 1
                    else {"right": "right", "right_target": self.elements["art_frame"]}
                ),
            )

        tab_num = 10
        # how many camp tabs u need

        for num in range(tab_num + 1):
            if num == 0:
                continue
            (
                self.tabs[f"tab{num}"].disable()
                if self.selected_camp_tab == num
                else self.tabs[f"tab{num}"].enable()
            )

        # I have to do this for proper layering.
        if "camp_art" in self.elements:
            self.elements["camp_art"].kill()
        if self.clan_info.biome:
            src = pygame.image.load(
                self.get_camp_art_path(self.selected_camp_tab)
            ).convert_alpha()
            self.elements["camp_art"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((175, 160), (450, 400))),
                pygame.transform.scale(
                    src.copy(),
                    ui_scale_dimensions((450, 400)),
                ),
                manager=MANAGER,
            )
            self.get_camp_bg(src)

        self.draw_art_frame()

    # LG
    def get_possible_camps(self):
        """
        LG: returns a dict of all possible camps based on selected biome and social
        """
        # this dict makes tab generation waaaaay easier
        # even if the dict itself is pretty uggo
        if self.clan_info.your_cat.status.social == CatSocial.CLANCAT:
            camp_dict = {
                "Forest": {
                    "1": {"camp_name": "camp_classic", "button_width": 85},
                    "2": {"camp_name": "camp_gully", "button_width": 70},
                    "3": {"camp_name": "camp_grotto", "button_width": 85},
                    "4": {"camp_name": "camp_lakeside", "button_width": 100},
                    "5": {"camp_name": "camp_pine", "button_width": 100},
                    "6": {"camp_name": "camp_birch", "button_width": 85},
                },
                "Mountainous": {
                    "1": {"camp_name": "camp_cliff", "button_width": 70},
                    "2": {"camp_name": "camp_cavern", "button_width": 90},
                    "3": {"camp_name": "camp_crystal_river", "button_width": 130},
                    "4": {"camp_name": "camp_rocky_slope", "button_width": 135},
                    "5": {"camp_name": "camp_quarry", "button_width": 85},
                    "6": {"camp_name": "camp_ruins", "button_width": 85},
                },
                "Plains": {
                    "1": {"camp_name": "camp_grasslands", "button_width": 115},
                    "2": {"camp_name": "camp_tunnels", "button_width": 90},
                    "3": {"camp_name": "camp_wastelands", "button_width": 115},
                    "4": {"camp_name": "camp_taiga", "button_width": 100},
                    "5": {"camp_name": "camp_desert", "button_width": 100},
                    "6": {"camp_name": "camp_city", "button_width": 85},
                    "7": {"camp_name": "camp_farm", "button_width": 85},
                    "8": {"camp_name": "camp_bushland", "button_width": 105},
                    "9": {"camp_name": "camp_castle", "button_width": 95},
                    "10": {"camp_name": "camp_bridge", "button_width": 85},
                },
                "Beach": {
                    "1": {"camp_name": "camp_tidepools", "button_width": 110},
                    "2": {"camp_name": "camp_tidal_cave", "button_width": 110},
                    "3": {"camp_name": "camp_shipwreck", "button_width": 110},
                    "4": {"camp_name": "camp_fjord", "button_width": 80},
                    "5": {"camp_name": "camp_tropical_island", "button_width": 140},
                    "6": {"camp_name": "camp_quay", "button_width": 75},
                },
            }
        elif self.clan_info.your_cat.status.social == CatSocial.ROGUE:
            camp_dict = {
                "Forest": {"1": {"camp_name": "rogue_forest", "button_width": 110}},
                "Mountainous": {
                    "1": {"camp_name": "rogue_mountainous", "button_width": 110}
                },
                "Plains": {"1": {"camp_name": "rogue_plains", "button_width": 110}},
                "Beach": {"1": {"camp_name": "rogue_beach", "button_width": 110}},
            }
        elif self.clan_info.your_cat.status.social == CatSocial.LONER:
            camp_dict = {
                "Forest": {"1": {"camp_name": "loner_forest", "button_width": 110}},
                "Mountainous": {
                    "1": {"camp_name": "loner_mountainous", "button_width": 110}
                },
                "Plains": {"1": {"camp_name": "loner_plains", "button_width": 110}},
                "Beach": {"1": {"camp_name": "loner_beach", "button_width": 110}},
            }
        elif self.clan_info.your_cat.status.social == CatSocial.KITTYPET:
            camp_dict = {
                "Forest": {"1": {"camp_name": "household_forest", "button_width": 110}},
                "Mountainous": {
                    "1": {"camp_name": "household_mountainous", "button_width": 110}
                },
                "Plains": {"1": {"camp_name": "household_plains", "button_width": 110}},
                "Beach": {"1": {"camp_name": "household_beach", "button_width": 110}},
            }
        else:
            camp_dict = {
                "Forest": {"1": {"camp_name": "no_group_forest", "button_width": 110}},
                "Mountainous": {
                    "1": {"camp_name": "no_group_mountainous", "button_width": 110}
                },
                "Plains": {"1": {"camp_name": "no_group_plains", "button_width": 110}},
                "Beach": {"1": {"camp_name": "no_group_beach", "button_width": 110}},
            }
        return camp_dict
