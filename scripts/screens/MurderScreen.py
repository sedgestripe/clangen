import pygame.transform
import pygame_gui.elements
from random import choice, randint
import math
import re
from scripts.event_class import Single_Event
from scripts.game_structure import constants

from scripts.screens.enums import GameScreen
from scripts.cat.enums import CatRank
from scripts.game_structure.localization import load_lang_resource

from .Screens import Screens

from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale, ui_scale_dimensions
from ..events_module.text_adjust import pronoun_repl, process_text


from scripts.cat.cats import Cat, INJURIES
from scripts.game_structure import image_cache
from ..ui.elements.image_button import UIImageButton
from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.elements.sprite_button import UISpriteButton
from scripts.game_structure import game
from scripts.cat.skills import SkillPath
from ..ui.generate_box import BoxStyles, get_box
from scripts.game_structure.screen_settings import MANAGER
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon
from ..game_structure.game.switches import (
    switch_set_value,
    Switch,
    switch_append_list_value,
)


class MurderScreen(Screens):
    selected_cat = None
    accomplice_cat = None
    current_page = 1
    list_frame = None
    apprentice_details = {}
    selected_details = {}
    cat_list_buttons = {}
    stage = "choose murder cat"

    def __init__(self, name=None):
        super().__init__(name)
        self.list_page = None
        self.next_cat = None
        self.previous_cat = None
        self.next_page_button = None
        self.previous_page_button = None
        self.current_mentor_warning = None
        self.confirm_mentor = None
        self.randomiser_button = None
        self.back_button = None
        self.next_cat_button = None
        self.mentor_icon = None
        self.app_frame = None
        self.mentor_frame = None
        self.accomplice_frame = None
        self.methodtext = None
        self.locationtext = None
        self.timetext = None
        self.attackmethod = None
        self.poisonmethod = None
        self.accidentmethod = None
        self.predatormethod = None
        self.camplocation = None
        self.territorylocation = None
        self.borderlocation = None
        self.dawntime = None
        self.daytime = None
        self.nighttime = None
        self.current_mentor_text = None
        self.info = None
        self.heading = None
        self.subtitle = None
        self.mentor = None
        self.the_cat = None
        self.murder_cat = None
        self.next = None
        self.prev = None
        self.method = None
        self.location = None
        self.time = None
        self.methodinfo = None
        self.methodheading = None
        self.locationinfo = None
        self.locationheading = None
        self.timeinfo = None
        self.timeheading = None
        self.your_sprite = None
        self.victim_sprite = None
        self.victim_info = None
        self.victim_name = None
        self.chancetext = None
        self.willingnesstext = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if (
                event.ui_element == self.confirm_mentor
                and self.selected_cat
                and self.stage == "choose murder cat"
            ):
                if not self.selected_cat.dead:
                    self.exit_screen()
                    self.cat_to_murder = self.selected_cat

                    self.stage = "choose murder method"

                    self.method = choice(["attack", "poison", "accident", "predator"])
                    self.location = choice(["camp", "territory", "border"])
                    self.time = choice(["dawn", "day", "night"])

                    self.screen_switches()
                    self.print_chances(self.selected_cat, accomplice=None)

            elif event.ui_element in self.cat_list_buttons.values():
                if self.stage == "choose accomplice":
                    self.update_chance_text(
                        self.cat_to_murder, accomplice=self.selected_cat
                    )
                else:
                    self.update_chance_text(self.selected_cat, accomplice=None)
                if event.ui_element.return_cat_object() == self.selected_cat:
                    self.selected_cat = None
                    self.confirm_mentor.disable()
                    if self.willingnesstext:
                        self.willingnesstext.hide()
                    if self.chancetext:
                        self.chancetext.hide()
                else:
                    if self.stage == "choose accomplice":
                        self.update_chance_text(
                            self.cat_to_murder, accomplice=self.selected_cat
                        )
                    else:
                        self.update_chance_text(self.selected_cat, accomplice=None)
                    self.confirm_mentor.enable()
                    self.selected_cat = event.ui_element.return_cat_object()
                    if self.willingnesstext:
                        self.willingnesstext.hide()
                    if self.chancetext:
                        self.chancetext.hide()

                if self.stage == "choose murder cat":
                    self.chancetext = None
                    self.update_selected_cat()
                    self.print_chances(self.selected_cat, accomplice=None)
                elif self.stage == "choose accomplice":
                    self.chancetext = None
                    self.update_selected_cat2()
                    self.print_chances(self.cat_to_murder, accomplice=self.selected_cat)

            elif (
                event.ui_element == self.confirm_mentor
                and self.method
                and self.location
                and self.time
                and self.stage == "choose murder method"
            ):
                if not self.selected_cat.dead:
                    self.exit_screen()
                    self.selected_cat = None
                    self.stage = "choose accomplice"
                    self.screen_switches()
                    self.confirm_mentor.disable()

            elif (
                event.ui_element == self.randomiser_button
                and self.stage == "choose murder method"
            ):
                self.method = choice(["attack", "poison", "accident", "predator"])
                self.location = choice(["camp", "territory", "border"])
                self.time = choice(["dawn", "day", "night"])

                self.update_murder_buttons()
                self.update_method_info()
                self.update_chance_text(self.cat_to_murder, accomplice=None)
                self.print_chances(self.selected_cat, accomplice=None)

            elif event.ui_element == self.confirm_mentor and self.selected_cat:
                r = randint(1, 100)
                accompliced = False
                chance = self.get_accomplice_chance(
                    game.clan.your_cat, self.selected_cat, self.cat_to_murder
                )
                if constants.CONFIG["lifegen"]["gen"]["accomplice_chance"] != -1:
                    try:
                        chance = constants.CONFIG["lifegen"]["gen"]["accomplice_chance"]
                    except:
                        pass
                if r < chance:
                    accompliced = True
                    switch_append_list_value(Switch.accomplices, self.selected_cat.ID)

                self.stage = "choose murder cat"
                self.change_cat(self.murder_cat, self.selected_cat, accompliced)

            elif self.stage == "choose murder method" and event.ui_element == self.next:
                self.stage = "choose murder cat"
                self.change_cat(self.murder_cat, None, None)

            elif self.stage == "choose accomplice" and event.ui_element == self.next:
                self.stage = "choose murder cat"
                self.change_cat(self.murder_cat, None, None)

            elif event.ui_element == self.prev:
                if self.stage == "choose murder method":
                    self.stage = "choose murder cat"
                    self.method = None
                    self.location = None
                    self.time = None
                    self.exit_screen()
                    self.screen_switches()
                elif self.stage == "choose accomplice":
                    self.stage = "choose murder method"
                    self.exit_screen()
                    self.screen_switches()

            elif event.ui_element == self.back_button:
                self.change_screen(GameScreen.PROFILE)
                self.stage = "choose murder cat"

                # reset cats
                self.selected_cat = None
                self.cat_to_murder = None

            # Method buttons
            elif event.ui_element == self.attackmethod:
                self.method = "attack"
                self.attackmethod.disable()
                self.poisonmethod.enable()
                self.accidentmethod.enable()
                self.predatormethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.poisonmethod:
                self.method = "poison"
                self.poisonmethod.disable()
                self.attackmethod.enable()
                self.accidentmethod.enable()
                self.predatormethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.accidentmethod:
                self.method = "accident"
                self.accidentmethod.disable()
                self.poisonmethod.enable()
                self.attackmethod.enable()
                self.predatormethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.predatormethod:
                self.method = "predator"
                self.predatormethod.disable()
                self.poisonmethod.enable()
                self.accidentmethod.enable()
                self.attackmethod.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)

            # Location buttons
            elif event.ui_element == self.camplocation:
                self.location = "camp"
                self.camplocation.disable()
                self.territorylocation.enable()
                self.borderlocation.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.territorylocation:
                self.location = "territory"
                self.territorylocation.disable()
                self.camplocation.enable()
                self.borderlocation.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.borderlocation:
                self.location = "border"
                self.borderlocation.disable()
                self.territorylocation.enable()
                self.camplocation.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)

            # Time buttons
            elif event.ui_element == self.dawntime:
                self.time = "dawn"
                self.dawntime.disable()
                self.daytime.enable()
                self.nighttime.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.daytime:
                self.time = "day"
                self.daytime.disable()
                self.dawntime.enable()
                self.nighttime.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)
            elif event.ui_element == self.nighttime:
                self.time = "night"
                self.nighttime.disable()
                self.daytime.enable()
                self.dawntime.enable()
                self.update_selected_cat()
                self.update_method_info()
                self.print_chances(self.selected_cat, accomplice=None)

            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat):
                    switch_set_value(Switch.cat, self.next_cat)
                    self.update_cat_list()
                    self.update_selected_cat()
                    self.print_chances(self.selected_cat, accomplice=None)
                    # self.update_buttons()
                else:
                    print("invalid next cat", self.next_cat)
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                if self.stage == "choose murder cat":
                    self.update_cat_list()
                else:
                    self.update_cat_list2()
            elif event.ui_element == self.previous_page_button:
                self.current_page = max(1, self.current_page - 1)
                if self.stage == "choose murder cat":
                    self.update_cat_list()
                else:
                    self.update_cat_list2()

    def update_murder_buttons(self):
        """updates the method, location and time buttons for the randomiser to work"""
        if self.method == "attack":
            self.attackmethod.disable()
            self.poisonmethod.enable()
            self.accidentmethod.enable()
            self.predatormethod.enable()
        elif self.method == "poison":
            self.attackmethod.enable()
            self.poisonmethod.disable()
            self.accidentmethod.enable()
            self.predatormethod.enable()
        elif self.method == "accident":
            self.attackmethod.enable()
            self.poisonmethod.enable()
            self.accidentmethod.disable()
            self.predatormethod.enable()
        elif self.method == "predator":
            self.attackmethod.enable()
            self.poisonmethod.enable()
            self.accidentmethod.enable()
            self.predatormethod.disable()

        if self.location == "camp":
            self.camplocation.disable()
            self.territorylocation.enable()
            self.borderlocation.enable()
        elif self.location == "territory":
            self.camplocation.enable()
            self.territorylocation.disable()
            self.borderlocation.enable()
        elif self.location == "border":
            self.camplocation.enable()
            self.territorylocation.enable()
            self.borderlocation.disable()

        if self.time == "dawn":
            self.dawntime.disable()
            self.daytime.enable()
            self.nighttime.enable()
        elif self.time == "day":
            self.dawntime.enable()
            self.daytime.disable()
            self.nighttime.enable()
        elif self.time == "night":
            self.dawntime.enable()
            self.daytime.enable()
            self.nighttime.disable()

    def screen_switches(self):
        super().screen_switches()

        self.heading = None
        self.next = None
        self.prev = None
        self.methodheading = None
        self.methodinfo = None
        self.locationinfo = None
        self.timeinfo = None
        self.timeheading = None
        self.locationheading = None
        self.accomplice_frame = None
        self.victim_sprite = None
        self.victim_info = None
        self.victim_name = None
        self.randomiser_button = None
        self.chancetext = None
        self.willingnesstext = None
        if self.stage == "choose murder cat":
            self.the_cat = game.clan.your_cat

            list_frame = get_box(BoxStyles.ROUNDED_BOX, (650, 226))
            self.list_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((75, 410), (650, 200))),
                list_frame,
                starting_height=1,
            )

            self.heading = pygame_gui.elements.UITextBox(
                "<b>Your target</b>",
                ui_scale(pygame.Rect((150, 25), (500, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )

            self.subtitle = pygame_gui.elements.UITextBox(
                "Who will be your victim?",
                ui_scale(pygame.Rect((150, 45), (500, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((75, 87), (200, 270))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/victim_panel.png"
                    ).convert_alpha(),
                    (200, 270),
                ),
                manager=MANAGER,
            )

            self.your_sprite = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((325, 180), (150, 150))),
                pygame.transform.scale(
                    self.the_cat.sprite, ui_scale_dimensions((150, 150))
                ),
                manager=MANAGER,
            )

            self.methodtext = pygame_gui.elements.UITextBox(
                "Method:",
                ui_scale(pygame.Rect((555, 77), (100, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            self.attackmethod = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((494, 110), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/attackmethod_grey.png"
                    ).convert_alpha(),
                    (55, 55),
                ),
                manager=MANAGER,
            )

            self.poisonmethod = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((552, 110), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/poisonmethod_grey.png"
                    ).convert_alpha(),
                    (55, 55),
                ),
                manager=MANAGER,
            )

            self.accidentmethod = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((610, 110), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/accidentmethod_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )
            self.predatormethod = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((677, 110), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/predatormethod_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )

            self.accidentmethod.disable()
            self.predatormethod.disable()

            self.locationtext = pygame_gui.elements.UITextBox(
                "Location:",
                ui_scale(pygame.Rect((555, 167), (100, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            self.camplocation = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((522, 200), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/camplocation_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )
            self.territorylocation = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((582, 200), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/territorylocation_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )
            self.borderlocation = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((642, 200), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/borderlocation_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )

            self.camplocation.disable()
            self.territorylocation.disable()
            self.borderlocation.disable()

            self.timetext = pygame_gui.elements.UITextBox(
                "Time:",
                ui_scale(pygame.Rect((555, 257), (100, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            self.dawntime = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((522, 290), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/dawntime_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )

            self.daytime = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((582, 290), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/daytime_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )

            self.nighttime = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((642, 290), (55, 55))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/nighttime_grey.png"
                    ).convert_alpha(),
                    (110, 110),
                ),
                manager=MANAGER,
            )

            self.back_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((25, 60), (105, 30))),
                "buttons.back",
                get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
                object_id="@buttonstyles_squoval",
                manager=MANAGER,
            )

            self.confirm_mentor = UISurfaceImageButton(
                ui_scale(pygame.Rect((350, 342), (102, 30))),
                "continue",
                get_button_dict(ButtonStyles.SQUOVAL, (102, 30)),
                object_id="@buttonstyles_squoval",
                starting_height=0,
            )

            self.previous_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((315, 614), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )
            self.next_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((451, 614), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )

            self.prev = UISurfaceImageButton(
                ui_scale(pygame.Rect((295, 340), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                tool_tip_text="Going back a step will re-randomise your plan.",
                starting_height=0,
            )
            self.next = UISurfaceImageButton(
                ui_scale(pygame.Rect((471, 340), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                tool_tip_text="Proceed without an accomplice.",
                starting_height=0,
            )

            self.prev.disable()
            self.next.disable()

            self.update_selected_cat()  # Updates the image and details of selected cat
            self.update_cat_list()

        elif self.stage == "choose murder method":
            self.the_cat = game.clan.your_cat
            self.mentor = Cat.fetch_cat(self.the_cat.mentor)
            self.selected_cat = self.cat_to_murder
            self.next = None
            self.methodinfo = None
            self.locationinfo = None
            self.locationheading = None
            self.methodheading = None
            self.timeinfo = None
            self.timeheading = None
            self.accomplice_frame = None
            self.victim_sprite = None
            self.victim_info = None
            self.victim_name = None
            self.willingnesstext = None
            self.chancetext = None

            self.list_frame = None

            self.heading = pygame_gui.elements.UITextBox(
                "<b>Your plan</b>",
                ui_scale(pygame.Rect((150, 25), (500, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.subtitle = pygame_gui.elements.UITextBox(
                "Choose wisely, or you could end up dead.",
                ui_scale(pygame.Rect((150, 45), (500, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((75, 87), (200, 270))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/victim_panel.png"
                    ).convert_alpha(),
                    (200, 270),
                ),
                manager=MANAGER,
            )

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((105, 95), (185, 135))),
                pygame.transform.scale(
                    self.selected_cat.sprite, ui_scale_dimensions((185, 135))
                ),
                manager=MANAGER,
            )

            self.your_sprite = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((325, 180), (150, 150))),
                pygame.transform.scale(
                    self.the_cat.sprite, ui_scale_dimensions((150, 150))
                ),
                manager=MANAGER,
            )

            self.methodtext = pygame_gui.elements.UITextBox(
                "Method:",
                ui_scale(pygame.Rect((555, 77), (100, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            self.attackmethod = UIImageButton(
                ui_scale(pygame.Rect((494, 110), (55, 55))),
                "",
                tool_tip_text="Attack",
                object_id="#attack_method_button",
                manager=MANAGER,
            )
            self.poisonmethod = UIImageButton(
                ui_scale(pygame.Rect((552, 110), (55, 55))),
                "",
                tool_tip_text="Poison",
                object_id="#poison_method_button",
                manager=MANAGER,
            )
            self.accidentmethod = UIImageButton(
                ui_scale(pygame.Rect((610, 110), (55, 55))),
                "",
                tool_tip_text="Accident",
                object_id="#accident_method_button",
                manager=MANAGER,
            )
            self.predatormethod = UIImageButton(
                ui_scale(pygame.Rect((677, 110), (55, 55))),
                "",
                tool_tip_text="Predator",
                object_id="#predator_method_button",
                manager=MANAGER,
            )

            self.locationtext = pygame_gui.elements.UITextBox(
                "Location:",
                ui_scale(pygame.Rect((555, 167), (100, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            self.camplocation = UIImageButton(
                ui_scale(pygame.Rect((522, 200), (55, 55))),
                "",
                tool_tip_text="Camp",
                object_id="#camp_location_button",
                manager=MANAGER,
            )

            self.territorylocation = UIImageButton(
                ui_scale(pygame.Rect((582, 200), (55, 55))),
                "",
                tool_tip_text="Territory",
                object_id="#territory_location_button",
                manager=MANAGER,
            )

            self.borderlocation = UIImageButton(
                ui_scale(pygame.Rect((642, 200), (55, 55))),
                "",
                tool_tip_text="Border",
                object_id="#border_location_button",
                manager=MANAGER,
            )

            self.timetext = pygame_gui.elements.UITextBox(
                "Time:",
                ui_scale(pygame.Rect((555, 257), (100, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            self.dawntime = UIImageButton(
                ui_scale(pygame.Rect((522, 290), (55, 55))),
                "",
                tool_tip_text="Dawn",
                object_id="#dawntime_button",
                manager=MANAGER,
            )
            self.daytime = UIImageButton(
                ui_scale(pygame.Rect((582, 290), (55, 55))),
                "",
                tool_tip_text="Day",
                object_id="#daytime_button",
                manager=MANAGER,
            )
            self.nighttime = UIImageButton(
                ui_scale(pygame.Rect((642, 290), (55, 55))),
                "",
                tool_tip_text="Night",
                object_id="#nighttime_button",
                manager=MANAGER,
            )

            self.randomiser_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((386, 135), (34, 34))),
                "\u2684",
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                manager=MANAGER,
                sound_id="dice_roll",
            )

            self.back_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((25, 60), (105, 30))),
                "buttons.back",
                get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
                object_id="@buttonstyles_squoval",
                manager=MANAGER,
            )

            self.confirm_mentor = UISurfaceImageButton(
                ui_scale(pygame.Rect((350, 342), (102, 30))),
                "continue",
                get_button_dict(ButtonStyles.SQUOVAL, (102, 30)),
                object_id="@buttonstyles_squoval",
                starting_height=0,
            )

            self.previous_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((315, 614), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )
            self.next_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((451, 614), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )

            self.prev = UISurfaceImageButton(
                ui_scale(pygame.Rect((295, 340), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                tool_tip_text="Going back a step will re-randomise your plan.",
                starting_height=0,
            )
            self.next = UISurfaceImageButton(
                ui_scale(pygame.Rect((471, 340), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                tool_tip_text="Proceed without an accomplice.",
                starting_height=0,
            )

            self.previous_page_button.hide()
            self.next_page_button.hide()

            self.next.disable()

            self.update_method_info()
            self.update_murder_buttons()

            self.update_selected_cat()  # Updates the image and details of selected cat
            # self.update_cat_list()
        else:
            self.the_cat = game.clan.your_cat
            self.mentor = Cat.fetch_cat(self.the_cat.mentor)
            # self.selected_cat = None
            self.methodheading = None
            self.methodinfo = None
            self.locationinfo = None
            self.locationheading = None
            self.timeinfo = None
            self.timeheading = None

            self.methodtext = None

            self.attackmethod = None
            self.poisonmethod = None
            self.accidentmethod = None
            self.predatormethod = None

            self.camplocation = None
            self.territorylocation = None
            self.borderlocation = None

            self.dawntime = None
            self.daytime = None
            self.nighttime = None

            self.methodtext = None
            self.locationtext = None
            self.timetext = None

            self.chancetext = None
            self.willingnesstext = None

            self.randomiser_button = None

            list_frame = get_box(BoxStyles.ROUNDED_BOX, (650, 226))
            self.list_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((75, 410), (650, 200))),
                list_frame,
                starting_height=1,
            )

            self.heading = pygame_gui.elements.UITextBox(
                "<b>Your accomplice</b>",
                ui_scale(pygame.Rect((150, 25), (500, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.subtitle = pygame_gui.elements.UITextBox(
                "Will you need help?",
                ui_scale(pygame.Rect((150, 45), (500, 40))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((75, 87), (200, 270))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/victim_panel.png"
                    ).convert_alpha(),
                    (200, 270),
                ),
                manager=MANAGER,
            )

            self.accomplice_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((525, 87), (200, 270))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/accomplice_panel.png"
                    ).convert_alpha(),
                    (200, 270),
                ),
                manager=MANAGER,
            )
            self.your_sprite = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((325, 180), (150, 150))),
                pygame.transform.scale(
                    self.the_cat.sprite, ui_scale_dimensions((150, 150))
                ),
                manager=MANAGER,
            )
            self.victim_sprite = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((105, 95), (135, 135))),
                pygame.transform.scale(
                    self.cat_to_murder.sprite, ui_scale_dimensions((135, 135))
                ),
                manager=MANAGER,
            )

            info = (
                self.cat_to_murder.status.rank
                + "\n"
                + self.cat_to_murder.genderalign
                + "\n"
                + self.cat_to_murder.personality.trait
                + "\n"
            )

            if self.cat_to_murder.moons < 1:
                info += "???"
            else:
                info += self.cat_to_murder.skills.skill_string(short=True)

            # vicinfo

            self.victim_info = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((102, 237), (150, 125))),
                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                manager=MANAGER,
            )

            name = str(self.cat_to_murder.name)  # get name

            if 17 <= len(name):  # check name length
                short_name = str(name)[0:15]
                name = short_name + "..."

            self.victim_name = pygame_gui.elements.ui_label.UILabel(
                ui_scale(pygame.Rect((102, 236), (150, 30))),
                name,
                object_id="#text_box_34_horizcenter",
                manager=MANAGER,
            )

            self.back_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((25, 60), (105, 30))),
                "buttons.back",
                get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
                object_id="@buttonstyles_squoval",
                manager=MANAGER,
            )

            self.confirm_mentor = UISurfaceImageButton(
                ui_scale(pygame.Rect((350, 342), (102, 30))),
                "kill!",
                get_button_dict(ButtonStyles.SQUOVAL, (102, 30)),
                object_id="@buttonstyles_squoval",
                starting_height=0,
                sound_id="antagonize",
            )

            self.previous_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((315, 614), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )
            self.next_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((451, 614), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )

            self.prev = UISurfaceImageButton(
                ui_scale(pygame.Rect((295, 340), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                tool_tip_text="Going back a step will re-randomise your plan.",
                starting_height=0,
            )
            self.next = UISurfaceImageButton(
                ui_scale(pygame.Rect((471, 340), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                tool_tip_text="Proceed without an accomplice.",
                starting_height=0,
                sound_id="antagonize",
            )

            self.previous_page_button.show()
            self.next_page_button.show()

            self.update_selected_cat2()  # Updates the image and details of selected cat
            # self.update_chance_text(accomplice=None)
            self.update_cat_list2()

    def exit_screen(self):
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for ele in self.apprentice_details:
            self.apprentice_details[ele].kill()
        self.apprentice_details = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        if self.heading:
            self.heading.kill()
            del self.heading

        if self.list_frame:
            self.list_frame.kill()
            del self.list_frame

        if self.subtitle:
            self.subtitle.kill()
            del self.subtitle

        if self.mentor_frame:
            self.mentor_frame.kill()
            del self.mentor_frame

        if self.accomplice_frame:
            self.accomplice_frame.kill()
            del self.accomplice_frame

        if self.your_sprite:
            self.your_sprite.kill()
            del self.your_sprite

        if self.victim_sprite:
            self.victim_sprite.kill()
            del self.victim_sprite

        if self.victim_info:
            self.victim_info.kill()
            del self.victim_info

        if self.victim_name:
            self.victim_name.kill()
            del self.victim_name

        if self.methodinfo:
            self.methodinfo.kill()
            del self.methodinfo

        if self.locationinfo:
            self.locationinfo.kill()
            del self.locationinfo

        if self.timeinfo:
            self.timeinfo.kill()
            del self.timeinfo

        if self.methodheading:
            self.methodheading.kill()
            del self.methodheading

        if self.locationheading:
            self.locationheading.kill()
            del self.locationheading

        if self.timeheading:
            self.timeheading.kill()
            del self.timeheading

        if self.methodtext:
            self.methodtext.kill()
            del self.methodtext

        if self.locationtext:
            self.locationtext.kill()
            del self.locationtext

        if self.timetext:
            self.timetext.kill()
            del self.timetext

        if self.attackmethod:
            self.attackmethod.kill()
            del self.attackmethod

        if self.poisonmethod:
            self.poisonmethod.kill()
            del self.poisonmethod

        if self.accidentmethod:
            self.accidentmethod.kill()
            del self.accidentmethod

        if self.predatormethod:
            self.predatormethod.kill()
            del self.predatormethod

        if self.camplocation:
            self.camplocation.kill()
            del self.camplocation

        if self.territorylocation:
            self.territorylocation.kill()
            del self.territorylocation

        if self.borderlocation:
            self.borderlocation.kill()
            del self.borderlocation

        if self.dawntime:
            self.dawntime.kill()
            del self.dawntime

        if self.daytime:
            self.daytime.kill()
            del self.daytime

        if self.nighttime:
            self.nighttime.kill()
            del self.nighttime

        if self.back_button:
            self.back_button.kill()
            del self.back_button

        if self.chancetext:
            self.chancetext.kill()
            del self.chancetext

        if self.willingnesstext:
            self.willingnesstext.kill()
            del self.willingnesstext

        if self.confirm_mentor:
            self.confirm_mentor.kill()
            del self.confirm_mentor

        if self.randomiser_button:
            self.randomiser_button.kill()
            del self.randomiser_button

        if self.previous_page_button:
            self.previous_page_button.kill()
            del self.previous_page_button

        if self.next_page_button:
            self.next_page_button.kill()
            del self.next_page_button

        if self.next:
            self.next.kill()
            del self.next

        if self.prev:
            self.prev.kill()
            del self.prev

    def print_chances(self, cat_to_murder, accomplice):
        dont_print = True
        if dont_print is True:
            return
        # not deleting the function bc chances will need more tweaking in the future

        if self.selected_cat:
            hypothetical_agree = False
            if accomplice:
                # prints chances when selecting accomplice
                successchance = self.get_kill(
                    game.clan.your_cat,
                    cat_to_murder,
                    accomplice=accomplice,
                    accompliced=False,
                )
                risk_chance = self.get_risk_chance(
                    cat_to_murder, accomplice=accomplice, accompliced=False
                )
                discover_chance = self.get_discover_chance(
                    self.cat_to_murder, accomplice=accomplice, accompliced=False
                )
                death_chance = self.get_death_chance(
                    cat_to_murder, accomplice=accomplice, accompliced=None
                )
                if cat_to_murder.status.rank == CatRank.LEADER:
                    leader_death_chance = self.leader_death_chance(
                        cat_to_murder, accomplice=accomplice, accompliced=False
                    )

                hypothetical_agree = True

                hypsuccesschance = self.get_kill(
                    game.clan.your_cat,
                    cat_to_murder,
                    accomplice=accomplice,
                    accompliced=True,
                )
                hyprisk_chance = self.get_risk_chance(
                    cat_to_murder, accomplice=accomplice, accompliced=True
                )
                hypdiscover_chance = self.get_discover_chance(
                    self.cat_to_murder, accomplice=accomplice, accompliced=True
                )
                hypdeath_chance = self.get_death_chance(
                    cat_to_murder, accomplice=accomplice, accompliced=True
                )
                if cat_to_murder.status.rank == CatRank.LEADER:
                    hypleader_death_chance = self.leader_death_chance(
                        cat_to_murder, accomplice=accomplice, accompliced=None
                    )

                if hypothetical_agree:
                    print("----------------------------")
                    print(f"Victim: {cat_to_murder.name}")
                    print(f"Accomplice: {accomplice.name}")
                    print("IF ACCOMPLICE AGREES:")
                    print("")
                    print(f"Success Chance: {hypsuccesschance}/100")
                    print(f"Discovery Chance: {hypdiscover_chance}/100")
                    print(f"MC Injury Chance: {hyprisk_chance}/100")
                    print(f"MC Death Chance: {hypdeath_chance}/100")

                    if cat_to_murder.status.rank == CatRank.LEADER:
                        print(f"LEADER ALL LIVES CHANCE: {hypleader_death_chance}/100")

            else:
                # prints chances when selecting a victim
                successchance = self.get_kill(
                    game.clan.your_cat, cat_to_murder, accomplice=None, accompliced=None
                )
                risk_chance = self.get_risk_chance(
                    cat_to_murder, accomplice=None, accompliced=None
                )
                discover_chance = self.get_discover_chance(
                    cat_to_murder, accomplice=accomplice, accompliced=None
                )
                death_chance = self.get_death_chance(
                    cat_to_murder, accomplice=None, accompliced=None
                )
                if cat_to_murder.status.rank == CatRank.LEADER:
                    leader_death_chance = self.leader_death_chance(
                        cat_to_murder, accomplice=None, accompliced=None
                    )

                print("----------------------------")
                print(f"Victim: {cat_to_murder.name}")
                print("")
                print(f"Success Chance: {successchance}/100")
                print(f"Discovery Chance: {discover_chance}/100")
                print(f"MC Injury Chance: {risk_chance}/100")
                print(f"MC Death Chance: {death_chance}/100")

                if cat_to_murder.status.rank == CatRank.LEADER:
                    print(f"LEADER ALL LIVES CHANCE: {leader_death_chance}/100")

                print("----------------------------")
                print("IF ACCOMPLICE REFUSES:")
                print("")
                print(f"Success Chance: {successchance}/100")
                print(f"Discovery Chance: {discover_chance}/100")
                print(f"MC Injury Chance: {risk_chance}/100")
                print(f"MC Death Chance: {death_chance}/100")

                if cat_to_murder.status.rank == CatRank.LEADER:
                    print(f"LEADER ALL LIVES CHANCE: {leader_death_chance}/100")

            if cat_to_murder.status.rank == CatRank.LEADER:
                print(
                    "Discovery chances will go up if the leader doesn't lose all of their lives."
                )

    def change_cat(self, new_mentor=None, accomplice=None, accompliced=None):
        self.current_page = 1
        r = randint(0, 100)
        r2 = randint(-10, 10)

        chance = self.get_kill(
            game.clan.your_cat, self.cat_to_murder, accomplice, accompliced
        )
        risk_chance = self.get_risk_chance(
            self.cat_to_murder, accomplice=accomplice, accompliced=accompliced
        )
        discover_chance = self.get_discover_chance(
            self.cat_to_murder, accomplice=accomplice, accompliced=accompliced
        )

        if constants.CONFIG["lifegen"]["gen"]["murder_chance"] != -1:
            try:
                chance = constants.CONFIG["lifegen"]["gen"]["murder_chance"]
            except:
                pass
        murdered = r < max(5, chance + r2)
        you = game.clan.your_cat
        cat_to_murder = self.cat_to_murder

        if murdered:
            self.choose_murder_text(you, cat_to_murder, accomplice, accompliced)
        else:
            self.handle_murder_fail(you, cat_to_murder, accomplice, accompliced)
            # for successes this is done in choose_murder_text
            game.clan.murdered = {
                "moon": game.clan.age,
                "murderer": game.clan.your_cat.ID,
                "victim": cat_to_murder.ID,
                "accomplice": [
                    accomplice.ID if accomplice else None,
                    accompliced if accomplice else False,
                ],
                "success": False,
                "discovered": False,
                "complication": None,
            }
        self.selected_cat = None

        # reset cats
        self.selected_cat = None
        self.cat_to_murder = None

        self.change_screen(GameScreen.EVENTS)

    def get_death_chance(self, cat_to_murder, accomplice, accompliced):
        """chance for mc to bite the dust"""
        # x/100
        you = game.clan.your_cat
        chance = 0

        if self.method == "attack":
            chance += 5
        elif self.method == "poison":
            if you.status.rank not in [
                CatRank.MEDICINE_CAT,
                CatRank.MEDICINE_APPRENTICE,
            ]:
                chance += 1
        elif self.method == "accident":
            chance += 8
        elif self.method == "predator":
            chance += 12

        if self.location == "camp":
            chance += 1
        elif self.location == "territory":
            chance += 5
        elif self.location == "border":
            chance += 10

        if self.time == "dawn":
            chance += 3
        elif self.time == "day":
            chance += 2
        elif self.time == "night":
            chance += 10

        if accomplice and accompliced:
            chance -= 4

        if cat_to_murder.moons > 12:
            chance += 2

        if cat_to_murder.moons < 6 or self.method == "poison":
            chance = math.floor(chance / 2)

        return chance

    def get_risk_chance(self, cat_to_murder, accomplice, accompliced):
        """calculates chance for mc to be injured in the murder. out of 100"""
        you = game.clan.your_cat
        chance = 0

        you_healthy = not you.is_ill() and not you.is_injured()

        cat_healthy = not cat_to_murder.is_ill() and not cat_to_murder.is_injured()

        your_skills = []
        if you.skills.primary:
            your_skills.append(you.skills.primary.skill)
        if you.skills.secondary:
            your_skills.append(you.skills.secondary.skill)

        their_skills = []
        if cat_to_murder.skills.primary:
            their_skills.append(cat_to_murder.skills.primary.skill)
        if cat_to_murder.skills.secondary:
            their_skills.append(cat_to_murder.skills.secondary.skill)

        # GENERAL
        if you.joined_df:
            chance -= 32
        if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
            chance -= 16
        if cat_to_murder.age == "senior":
            chance -= 16
        if you.status.rank == cat_to_murder.status.rank:
            chance -= 16
        if you.experience > cat_to_murder.experience:
            chance -= 16
        if accomplice and accompliced:
            chance -= 24

        if self.location == "camp":
            chance -= 24

        if self.time == "day":
            chance -= 24

        if self.location == "border":
            chance += 22
        if self.time == "night":
            chance += 30

        if cat_to_murder.joined_df:
            chance += 32
        if cat_to_murder.moons >= you.moons + 4:
            chance += 16
        if not you_healthy:
            chance += 16

        if cat_to_murder.status.rank == CatRank.LEADER:
            if game.clan.leader_lives > 1:
                chance += 40
            else:
                chance += 16

        if cat_to_murder.experience > you.experience:
            chance += 16

        victim_skills_lvl1 = [
            "watchful",
            "lives in groups",
            "interested in oddities",
            "fascinated by prophecies",
        ]
        victim_skills_lvl2 = [
            "good guard",
            "good sport",
            "omen seeker",
            "prophecy seeker",
        ]
        victim_skills_lvl3 = [
            "great guard",
            "team player",
            "omen sense",
            "prophecy interpreter",
        ]
        victim_skills_lvl4 = ["guardian", "insider", "omen sight", "prophet"]

        if any(skill in victim_skills_lvl1 for skill in their_skills):
            chance -= 5
        if any(skill in victim_skills_lvl2 for skill in their_skills):
            chance -= 10
        if any(skill in victim_skills_lvl3 for skill in their_skills):
            chance -= 15
        if any(skill in victim_skills_lvl4 for skill in their_skills):
            chance -= 20

        if self.method == "attack":
            if you.joined_df:
                chance -= 35
            if (
                "steps lightly" or "mossball hunter" or "avid play-fighter"
            ) in your_skills:
                chance -= 3
            if ("graceful" or "good hunter" or "good fighter") in your_skills:
                chance -= 7
            if ("elegant" or "great hunter" or "formidable fighter") in your_skills:
                chance -= 11
            if (
                "radiates elegance" or "renowned hunter" or "unusually strong fighter"
            ) in your_skills:
                chance -= 15
            if you.status.rank == CatRank.WARRIOR and you_healthy:
                chance -= 23
            if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
                chance -= 16

            if self.location == "border":
                chance -= 8

            if you.personality.trait == "bloodthirsty":
                chance -= 16

            if cat_to_murder.status.rank == CatRank.WARRIOR and cat_healthy:
                chance += 15
            if not you.status.rank.is_any_adult_warrior_like_rank():
                chance += 10

            if "avid play-fighter" in their_skills:
                chance += 8
            if "good fighter" in their_skills:
                chance += 12
            if "formidable fighter" in their_skills:
                chance += 18
            if "unusually strong fighter" in their_skills:
                chance += 25

            if self.location == "camp":
                chance += 8
            if cat_to_murder.personality.trait == "bloodthirsty":
                chance += 16

        if self.method == "accident":
            acc_skills_lvl_1 = [
                "curious wanderer",
                "good with directions",
                "constantly climbing",
            ]
            acc_skills_lvl_2 = [
                "knowledgeable explorer",
                "good navigator",
                "good climber",
            ]
            acc_skills_lvl_3 = ["brave pathfinder", "great navigator", "great climber"]
            acc_skills_lvl_4 = [
                "master of territories",
                "pathfinder",
                "impressive climber",
            ]

            if any(skill in acc_skills_lvl_1 for skill in your_skills):
                chance -= 5
            if any(skill in acc_skills_lvl_2 for skill in your_skills):
                chance -= 10
            if any(skill in acc_skills_lvl_3 for skill in your_skills):
                chance -= 15
            if any(skill in acc_skills_lvl_4 for skill in your_skills):
                chance -= 20

            if self.location == "camp":
                chance -= 15

            if game.clan.biome == "Mountainous":
                chance += 10
            if (
                cat_to_murder.status.rank.is_any_adult_warrior_like_rank()
                and cat_healthy
            ):
                chance += 11

        if self.method == "predator":
            pred_skills_lvl_1 = ["other-cat-ly whisperer", "mossball hunter"]
            pred_skills_lvl_2 = ["dog-whisperer", "good hunter"]
            pred_skills_lvl_3 = ["multilingual", "great hunter"]
            pred_skills_lvl_4 = ["listener of all voices", "renowned hunter"]

            if any(skill in pred_skills_lvl_1 for skill in your_skills):
                chance += 5
            if any(skill in pred_skills_lvl_2 for skill in your_skills):
                chance += 10
            if any(skill in pred_skills_lvl_3 for skill in your_skills):
                chance += 15
            if any(skill in pred_skills_lvl_4 for skill in your_skills):
                chance += 20

            if self.location == "camp":
                chance -= 35

            if (
                cat_to_murder.status.rank.is_any_adult_warrior_like_rank()
                and cat_healthy
            ):
                chance += 10
            if not you.status.rank.is_any_adult_warrior_like_rank():
                chance += 15

            if "avid play-fighter" in their_skills:
                chance += 8
            if "good fighter" in their_skills:
                chance += 12
            if "formidable fighter" in their_skills:
                chance += 18
            if "unusually strong fighter" in their_skills:
                chance += 25

        if chance >= 95:
            chance = 95
        elif chance <= 5:
            chance = 5

        # lowest possible risk chance for predator is 25, meaning a 1/4 chance, no matter how many other positive factors they have.
        if chance < 25 and self.method == "predator":
            chance = 25

        return chance

    def choose_murder_text(self, you, cat_to_murder, accomplice, accompliced):
        """chooses murder text. nuff said also chooses whether the mc is injured or dies"""

        self.m_txt = load_lang_resource("events/lifegen_events/murder.json")
        self.mu_txt = load_lang_resource(
            "events/lifegen_events/murder_unsuccessful.json"
        )

        leaddeath = randint(1, 100)

        leader_death_chance = self.leader_death_chance(
            cat_to_murder, accomplice=accomplice, accompliced=accompliced
        )

        all_leader_lives = False

        if cat_to_murder.status.rank == CatRank.LEADER:
            if leaddeath < leader_death_chance + 1:
                all_leader_lives = True

        risk = randint(1, 100)
        risk_chance = self.get_risk_chance(
            cat_to_murder, accomplice=accomplice, accompliced=accompliced
        )

        deathrisk = randint(1, 100)
        death_chance = self.get_death_chance(
            cat_to_murder, accomplice=accomplice, accompliced=accompliced
        )

        injury = False
        death = False

        if risk < risk_chance + 1:
            injury = True

        if deathrisk < death_chance + 1 and not injury:
            death = True

        if death and not injury:
            if you.status.rank == CatRank.LEADER:
                game.clan.leader_lives -= 1
            you.die()

        owie = "sore"
        owie2 = "sore"

        if injury and not death:
            if self.method == "attack":
                owie = choice(
                    [
                        "claw-wound",
                        "bite-wound",
                        "torn pelt",
                        "sprain",
                        "sore",
                        "bruises",
                        "scrapes",
                    ]
                )
                owie2 = owie = choice(
                    [
                        "claw-wound",
                        "bite-wound",
                        "torn pelt",
                        "sprain",
                        "sore",
                        "bruises",
                        "scrapes",
                    ]
                )
                # two of em so accomplice and mc dont always get the same injury
            elif self.method == "poison":
                owie = "poisoned"
                owie2 = "poisoned"
            elif self.method == "accident":
                owie = choice(
                    [
                        "broken bone",
                        "broken bone",
                        "broken bone",
                        "sprain",
                        "sore",
                        "bruises",
                        "scrapes",
                        "paralyzed",
                        "head damage",
                        "broken jaw",
                    ]
                )
                owie2 = choice(
                    [
                        "broken bone",
                        "broken bone",
                        "broken bone",
                        "sprain",
                        "sore",
                        "bruises",
                        "scrapes",
                        "paralyzed",
                        "head damage",
                        "broken jaw",
                    ]
                )
            else:
                owie = choice(
                    [
                        "bite-wound",
                        "broken bone",
                        "torn pelt",
                        "mangled leg",
                        "mangled tail",
                    ]
                )
                owie2 = choice(
                    [
                        "bite-wound",
                        "broken bone",
                        "torn pelt",
                        "mangled leg",
                        "mangled tail",
                    ]
                )

            if accomplice and accompliced:
                # accomplice means you have one, accompliced means they agreed
                if randint(1, 4) == 1:
                    accomplice.get_injured(owie2)

        # CHOOSING TEXT
        biome = game.clan.biome.lower()
        camp = game.clan.camp_bg

        ceremony_txt = []
        possible_keys = []

        murder_events = {}

        methods = ["attack", "poison", "accident", "predator"]

        locations = ["camp", "territory", "border"]

        times = ["day", "night", "dawn"]

        camps = ["camp1", "camp2", "camp3", "camp4", "camp5", "camp6"]

        for i in self.m_txt.items():
            key = i[0]
            murder_dict = i[1]

            if "your_status" in murder_dict:
                if "adult" in murder_dict["your_status"]:
                    if you.moons < 12:
                        continue

                elif "no_kit" in murder_dict["your_status"]:
                    if you.moons < 6:
                        continue

                elif "all_apprentices" in murder_dict["your_status"]:
                    if you.moons > 12 or you.moons < 6:
                        continue

                elif "healer_cat" in murder_dict["your_status"]:
                    if you.status.rank not in [
                        CatRank.MEDICINE_CAT,
                        CatRank.MEDICINE_APPRENTICE,
                    ]:
                        continue

                elif you.status.rank not in murder_dict["your_status"]:
                    if "any" not in murder_dict["your_status"]:
                        continue

            if "victim_status" in murder_dict:
                if "adult" in murder_dict["victim_status"]:
                    if cat_to_murder.moons < 12:
                        continue

                elif "no_kit" in murder_dict["victim_status"]:
                    if cat_to_murder.moons < 6:
                        continue

                elif "all_apprentices" in murder_dict["victim_status"]:
                    if cat_to_murder.moons > 12 or cat_to_murder.moons < 6:
                        continue

                elif "healer_cat" in murder_dict["victim_status"]:
                    if cat_to_murder.status.rank not in [
                        CatRank.MEDICINE_APPRENTICE,
                        CatRank.MEDICINE_CAT,
                    ]:
                        continue

                elif cat_to_murder.status.rank not in murder_dict["victim_status"]:
                    if "any" not in murder_dict["victim_status"]:
                        continue

            if "relationship" in murder_dict and murder_dict["relationship"]:
                if "mates" in murder_dict["relationship"]:
                    if cat_to_murder not in you.mate:
                        continue
                if "siblings" in murder_dict["relationship"]:
                    if cat_to_murder.ID not in you.inheritance.get_siblings():
                        continue

                if "your_parent" in murder_dict["relationship"]:
                    if you.parent1:
                        if cat_to_murder.ID != you.parent1:
                            continue
                    if you.parent2:
                        if cat_to_murder.ID != you.parent2:
                            continue
                    if cat_to_murder.ID not in you.inheritance.get_adoptive_parents():
                        continue

                if "your_kit" in murder_dict["relationship"]:
                    if (
                        cat_to_murder.ID not in you.inheritance.get_blood_kits()
                        and cat_to_murder.ID not in you.inheritance.get_not_blood_kits()
                    ):
                        continue

                if "your_apprentice" in murder_dict["relationship"]:
                    if cat_to_murder.mentor != game.clan.your_cat.ID:
                        continue

                if "your_mentor" in murder_dict["relationship"]:
                    if game.clan.your_cat.mentor != cat_to_murder.ID:
                        continue

            if "biome" in murder_dict and murder_dict["biome"]:
                if biome and biome not in murder_dict["biome"]:
                    continue
                if (
                    any(i in murder_dict["biome"] for i in camps)
                    and camp not in murder_dict["biome"]
                ):
                    continue

            if "strategy" in murder_dict and murder_dict["strategy"]:
                tags = [i for i in murder_dict["strategy"]]

                if (
                    any(i in tags for i in methods)
                    and self.method not in murder_dict["strategy"]
                ):
                    continue
                if (
                    any(i in tags for i in locations)
                    and self.location not in murder_dict["strategy"]
                ):
                    continue
                if (
                    any(i in tags for i in times)
                    and self.time not in murder_dict["strategy"]
                ):
                    continue

            # tags!
            # this includes all_lives, accomplice tags, and injury/death tags.
            # perhaps skills and clusters in the future.
            if "tags" in murder_dict and murder_dict["tags"]:
                if (
                    all_leader_lives and cat_to_murder.status.rank == CatRank.LEADER
                ) or (
                    not all_leader_lives
                    and cat_to_murder.status.rank == CatRank.LEADER
                    and game.clan.leader_lives == 1
                ):
                    if "all_lives" not in murder_dict["tags"]:
                        continue
                else:
                    if "all_lives" in murder_dict["tags"]:
                        continue

                if injury:
                    if "injury" not in murder_dict["tags"]:
                        continue
                elif death:
                    if "death" not in murder_dict["tags"]:
                        continue

                if not injury and not death:
                    if "injury" in murder_dict["tags"]:
                        continue
                    if "death" in murder_dict["tags"]:
                        continue

                if accomplice and accompliced:
                    if "alone" in murder_dict["tags"]:
                        continue
                    if "accomplice_refused" in murder_dict["tags"]:
                        continue

                elif accomplice:
                    if "alone" in murder_dict["tags"]:
                        continue
                    if "accomplice_agreed" in murder_dict["tags"]:
                        continue

                elif not accomplice and not accompliced:
                    if "accomplice_refused" in murder_dict["tags"]:
                        continue
                    if "accomplice_agreed" in murder_dict["tags"]:
                        continue

            elif "tags" in murder_dict and not murder_dict["tags"]:
                # injury and death outcomes cannot get events with empty tags
                if injury:
                    continue
                if death:
                    continue

            possible_keys.append(key)

            murder_events.update({key: murder_dict})

        print("POSSIBLE KEYS:", possible_keys)

        options = []
        for i in murder_events.items():
            options.append(i)

        if not options:
            print("No valid murder event found for the current filters.")
            return

        chosen_event = choice(options)

        if "texts" in chosen_event[1]:
            if chosen_event[1]["texts"]:
                for event in chosen_event[1]["texts"]:
                    ceremony_txt.append(event)
            else:
                print("Blank murder text for", chosen_event[0])
                return

        if injury:
            if "tags" in chosen_event[1] and chosen_event[1]["tags"]:
                if injury:
                    for t in chosen_event[1]["tags"]:
                        if any(t in chosen_event[1] for t in INJURIES):
                            if t in INJURIES:
                                you.get_injured(t)
                        else:
                            you.get_injured(owie)

        ceremony_txt = choice(ceremony_txt)

        other_clan = choice(game.clan.all_other_clans)
        ceremony_txt = ceremony_txt.replace("o_c_n", str(other_clan.name) + "Clan")
        ceremony_txt = ceremony_txt.replace("c_n", game.clan.name)

        medcats = []
        for cat in Cat.all_cats_list:
            if (
                cat.status.rank == CatRank.MEDICINE_CAT
                and cat.status.alive_in_player_clan
                and cat.status.rank != you.status.rank
            ):
                medcats.append(cat)

        warriors = []
        for cat in Cat.all_cats_list:
            if (
                cat.status.rank == CatRank.WARRIOR
                and cat.status.alive_in_player_clan
                and cat.status.rank != you.status.rank
            ):
                medcats.append(cat)

        if len(medcats) > 0:
            random_medcat = choice(medcats)
            random_medcat_prns = choice(random_medcat.pronouns)
        elif len(warriors) > 0:
            random_medcat = choice(warriors)
            random_medcat_prns = choice(random_medcat.pronouns)
        elif game.clan.leader and game.clan.leader.ID != you.ID:
            random_medcat = game.clan.leader
            random_medcat_prns = choice(game.clan.leader.pronouns)
        else:
            random_medcat = self.cat_to_murder
            random_medcat_prns = choice(self.cat_to_murder.pronouns)
            # just trying to avoid errors if theres no medcats or anyone else in the clan lol. for that one event that mentions a medcat

        replace_dict = {
            "v_c": (str(self.cat_to_murder.name), choice(self.cat_to_murder.pronouns)),
            "l_n": (str(game.clan.leader.name), choice(game.clan.leader.pronouns)),
            "y_c": (str(game.clan.your_cat.name), choice(game.clan.your_cat.pronouns)),
            "r_m": (str(random_medcat.name), random_medcat_prns),
        }

        if accomplice:
            replace_dict.update(
                {"a_n": (str(accomplice.name), choice(accomplice.pronouns))}
            )

        ceremony_txt = process_text(ceremony_txt, replace_dict)

        if cat_to_murder.status.rank == CatRank.LEADER and all_leader_lives:
            game.clan.leader_lives = 0

        involved_cats = [game.clan.your_cat.ID, cat_to_murder.ID]
        if accomplice:
            involved_cats.append(accomplice.ID)

        game.cur_events_list.insert(
            0, Single_Event(ceremony_txt, ["alert", "birth_death"], involved_cats)
        )

        discover_chance = self.get_discover_chance(
            cat_to_murder, accomplice, accompliced
        )
        discovery_num = randint(1, 10)

        if not all_leader_lives:
            game.clan.leader_lives -= 1
            if discover_chance < 7:
                discover_chance = randint(7, 9)
        # if u kill the leader n they wake up like an hour later Yeah ur probably gonna get caught
        cat_to_murder.die()
        # discover_chance = 3
        # discovery_num = 1
        # ^^ shun debug

        discovered = False
        if discovery_num < (discover_chance + 1):
            discovered = True
        else:
            discovered = False

        game.clan.your_cat.history.add_murder(game.clan.your_cat.ID, cat_to_murder)
        game.clan.your_cat.history.reveal_murder(
            victim=cat_to_murder,
            murderer_id=game.clan.your_cat.ID,
            clan_reveal=discovered,
            aware_individuals=[accomplice] if accomplice else [],
            # shunning is applied in choose_discover_punishment so it matches
            # who the Clan actually blames (you, the accomplice, or both)
            shunned_cat=None,
        )

        if discovered:
            if accomplice and accompliced:
                if game.clan.your_cat.dead:
                    game.cur_events_list.insert(
                        1,
                        Single_Event(
                            "You and "
                            + str(accomplice.name)
                            + " murdered "
                            + str(cat_to_murder.name)
                            + ", but only your accomplice made it out alive.",
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, cat_to_murder.ID, accomplice.ID],
                        ),
                    )
                else:
                    game.cur_events_list.insert(
                        1,
                        Single_Event(
                            "You successfully murdered "
                            + str(cat_to_murder.name)
                            + " with the help of "
                            + str(accomplice.name)
                            + ".",
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, cat_to_murder.ID, accomplice.ID],
                        ),
                    )
                cat_to_murder.history.add_death(
                    f"{you.name} and {accomplice.name} murdered this cat."
                )

                accguiltchance = randint(1, 2)
                if accguiltchance == 1:
                    accomplice.get_injured("guilt")

                youguiltchance = randint(1, 4)
                if youguiltchance == 1:
                    accomplice.get_injured("guilt")

            else:
                if game.clan.your_cat.dead:
                    game.cur_events_list.insert(
                        1,
                        Single_Event(
                            "You successfully murdered "
                            + str(cat_to_murder.name)
                            + " at the cost of your own life.",
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, cat_to_murder.ID],
                        ),
                    )
                else:
                    game.cur_events_list.insert(
                        1,
                        Single_Event(
                            "You successfully murdered "
                            + str(cat_to_murder.name)
                            + ".",
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, cat_to_murder.ID],
                        ),
                    )
                cat_to_murder.history.add_death(f"{you.name} murdered this cat.")
            self.choose_discover_punishment(you, cat_to_murder, accomplice, accompliced)
        else:
            if accomplice:
                if accompliced:
                    cat_to_murder.history.add_death(
                        f"{you.name} and {accomplice.name} murdered this cat."
                    )

                    if game.clan.your_cat.dead:
                        game.cur_events_list.insert(
                            1,
                            Single_Event(
                                "You and "
                                + str(accomplice.name)
                                + " successfully murdered "
                                + str(self.cat_to_murder.name)
                                + " at the cost of your own life. It seems that no cat knows the truth.",
                                ["alert", "birth_death"],
                                [
                                    game.clan.your_cat.ID,
                                    accomplice.ID,
                                    cat_to_murder.ID,
                                ],
                            ),
                        )
                    else:
                        game.cur_events_list.insert(
                            1,
                            Single_Event(
                                "You successfully murdered "
                                + str(cat_to_murder.name)
                                + " along with "
                                + str(accomplice.name)
                                + ". It seems no one is aware of your actions.",
                                ["alert", "birth_death"],
                                [
                                    game.clan.your_cat.ID,
                                    accomplice.ID,
                                    cat_to_murder.ID,
                                ],
                            ),
                        )

                    if game.clan.your_cat.dead:
                        accomplice.get_injured("guilt")
                    else:
                        accguiltchance = randint(1, 4)
                        if accguiltchance == 1:
                            accomplice.get_injured("guilt")

                        youguiltchance = randint(1, 6)
                        if youguiltchance == 1:
                            accomplice.get_injured("guilt")

                else:
                    cat_to_murder.history.add_death(f"{you.name} murdered this cat.")

                    if game.clan.your_cat.dead:
                        game.cur_events_list.insert(
                            1,
                            Single_Event(
                                "You successfully murdered "
                                + str(cat_to_murder.name)
                                + " at the cost of your own life. "
                                + str(accomplice.name)
                                + " chose not to help. It seems that no cat knows the truth.",
                                ["alert", "birth_death"],
                                [
                                    game.clan.your_cat.ID,
                                    accomplice.ID,
                                    cat_to_murder.ID,
                                ],
                            ),
                        )
                    else:
                        game.cur_events_list.insert(
                            1,
                            Single_Event(
                                "You successfully murdered "
                                + str(cat_to_murder.name)
                                + " but "
                                + str(accomplice.name)
                                + " chose not to help. It seems no one is aware of your actions.",
                                ["alert", "birth_death"],
                                [
                                    game.clan.your_cat.ID,
                                    accomplice.ID,
                                    cat_to_murder.ID,
                                ],
                            ),
                        )
            else:
                cat_to_murder.history.add_death(f"{you.name} murdered this cat.")

                if game.clan.your_cat.dead:
                    game.cur_events_list.insert(
                        1,
                        Single_Event(
                            "You successfully murdered "
                            + str(cat_to_murder.name)
                            + " at the cost of your own life. It seems that no cat knows the truth.",
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, cat_to_murder.ID],
                        ),
                    )
                else:
                    game.cur_events_list.insert(
                        1,
                        Single_Event(
                            "You successfully murdered "
                            + str(cat_to_murder.name)
                            + ". It seems no one is aware of your actions.",
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, cat_to_murder.ID],
                        ),
                    )

        self.stage = "choose murder cat"

        if injury:
            comp = "injury"
        elif death:
            comp = "death"
        else:
            comp = None

        game.clan.murdered = {
            "moon": game.clan.age,
            "murderer": game.clan.your_cat.ID,
            "victim": cat_to_murder.ID,
            "accomplice": [
                accomplice.ID if accomplice else None,
                accompliced if accomplice else False,
            ],
            "success": True,
            "discovered": discovered,
            "complication": comp,
        }

    def choose_discover_punishment(self, you, cat_to_murder, accomplice, accompliced):
        """determines punishment text, shunned and guilt outcomes"""
        # 1 = you punished, 2 = accomplice punished, 3 = both punished
        event_text = ""

        if accomplice and accompliced:
            if game.clan.your_cat.dead:
                punishment_chance = 2
            else:
                punishment_chance = randint(1, 3)
        else:
            if game.clan.your_cat.dead:
                # solo murderer who died is still shunned by the Clan
                you.status.shun_from_group()
                return
            punishment_chance = 1

        if not accomplice or not accompliced:
            punishment_chance = 1

        # shun whoever the Clan blames, matching the punishment outcome
        # (1 = you, 2 = accomplice, 3 = both)
        if punishment_chance in (1, 3):
            you.status.shun_from_group()
            demote_text = you.shunned_demotion() if not you.dead else ""
            if demote_text:
                game.cur_events_list.insert(
                    3, Single_Event(demote_text, ["alert", "birth_death"], [you.ID])
                )
        if punishment_chance in (2, 3) and accomplice:
            accomplice.status.shun_from_group()
            demote_text = accomplice.shunned_demotion() if not accomplice.dead else ""
            if demote_text:
                game.cur_events_list.insert(
                    3,
                    Single_Event(
                        demote_text, ["alert", "birth_death"], [accomplice.ID]
                    ),
                )

        if punishment_chance == 1:
            if accomplice and not accompliced:
                a_s = randint(1, 2)
                if (
                    a_s == 1
                    and accomplice.status.rank != CatRank.LEADER
                    and game.clan.leader
                ):
                    game.cur_events_list.insert(
                        2,
                        Single_Event(
                            f"Shocked at your request to be an accomplice to murder, {accomplice.name} reports your actions to the Clan leader.",
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, accomplice.ID, game.clan.leader.ID],
                        ),
                    )
            txt = ""
            if game.clan.your_cat.dead:
                txt = choice(self.mu_txt["murder_discovered dead general"])
            else:
                if game.clan.your_cat.status.rank in [
                    CatRank.KITTEN,
                    CatRank.LEADER,
                    CatRank.DEPUTY,
                    CatRank.MEDICINE_CAT,
                ]:
                    txt = choice(
                        self.mu_txt[
                            "murder_discovered " + game.clan.your_cat.status.rank
                        ]
                    )
                else:
                    txt = choice(self.mu_txt["murder_discovered general"])
            txt = txt.replace("v_c", str(cat_to_murder.name))
            game.cur_events_list.insert(
                2,
                Single_Event(
                    txt,
                    ["alert", "birth_death"],
                    [game.clan.your_cat.ID, cat_to_murder.ID],
                ),
            )
            you.faith -= 0.5
        elif punishment_chance == 2:
            if game.clan.your_cat.dead:
                txt = f"After your and v_c's deaths, {accomplice.name} is blamed for both of them."
            else:
                txt = f"{accomplice.name} is blamed for the murder of v_c. However, you were not caught."
            txt = txt.replace("v_c", str(cat_to_murder.name))
            game.cur_events_list.insert(
                2,
                Single_Event(
                    txt,
                    ["alert", "birth_death"],
                    [game.clan.your_cat.ID, accomplice.ID, cat_to_murder.ID],
                ),
            )
            accomplice.faith -= 0.5
        else:
            txt = f"The unsettling truth of v_c's death is discovered, with you and {accomplice.name} responsible. The Clan decides both of your punishments."
            txt = txt.replace("v_c", str(cat_to_murder.name))
            game.cur_events_list.insert(
                2,
                Single_Event(
                    txt,
                    ["alert", "birth_death"],
                    [game.clan.your_cat.ID, accomplice.ID, cat_to_murder.ID],
                ),
            )
            accomplice.faith -= 0.5

        if punishment_chance == 1 or punishment_chance == 3:
            kit_punishment = [
                "You are assigned counseling by the Clan's medicine cat to help you understand the severity of your actions and to guide you to make better decisions in the future.",
                "You are to be kept in the nursery under the watchful eye of the queens at all times until you become an apprentice.",
            ]
            gen_punishment = [
                "You are assigned counseling by the Clan's medicine cat to help you understand the severity of your actions and to guide you to make better decisions in the future.",
                "You will be required to take meals last and are forced to sleep in a separate den away from your clanmates.",
                "You are assigned to several moons of tasks that include cleaning out nests, checking elders for ticks, and other chores alongside your normal duties.",
                "You are assigned a mentor who will better educate you about the Warrior Code and the sacredness of life.",
            ]
            # demote_leader = ["Your lives will be stripped away and you will be demoted to a warrior, no longer trusted to be the Clan's leader."]
            # demote_deputy = ["The Clan decides that you will be demoted to a warrior, no longer trusting you as their deputy."]
            # demote_medicine_cat = ["The Clan decides that you will be demoted to a warrior, no longer trusting you as their medicine cat."]
            # exiled = ["The Clan decides that they no longer feel safe with you as a Clanmate. You will be exiled from the Clan."]

            if you.status.rank in [CatRank.NEWBORN, CatRank.KITTEN]:
                game.cur_events_list.insert(
                    3,
                    Single_Event(
                        choice(kit_punishment), ["alert"], [game.clan.your_cat.ID]
                    ),
                )
            elif you.status.rank == CatRank.LEADER:
                lead_choice = randint(1, 3)
                if lead_choice == 1:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            choice(gen_punishment), ["alert"], [game.clan.your_cat.ID]
                        ),
                    )
            elif you.status.rank == CatRank.DEPUTY:
                lead_choice = randint(1, 3)
                if lead_choice == 1:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            choice(gen_punishment), ["alert"], [game.clan.your_cat.ID]
                        ),
                    )
            elif you.status.rank == CatRank.MEDICINE_CAT:
                lead_choice = randint(1, 3)
                if lead_choice == 1:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            choice(gen_punishment), ["alert"], [game.clan.your_cat.ID]
                        ),
                    )
            else:
                lead_choice = randint(1, 5)
                if lead_choice in [1, 2, 3, 4]:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            choice(gen_punishment), ["alert"], [game.clan.your_cat.ID]
                        ),
                    )

        if (
            accomplice
            and accompliced
            and (punishment_chance == 2 or punishment_chance == 3)
        ):
            a_n = str(accomplice.name)
            kit_punishment = [
                f"{a_n} is assigned counseling by the Clan's medicine cat to help them understand the severity of their actions and to guide them to make better decisions in the future.",
                f"{a_n} is to be kept in the nursery under the watchful eye of the queens at all times until they become an apprentice.",
            ]
            gen_punishment = [
                f"{a_n} is assigned counseling by the Clan's medicine cat to help them understand the severity of their actions and to guide them to make better decisions in the future.",
                f"{a_n} is required to take meals last and is forced to sleep in a separate den away from their clanmates.",
                f"{a_n} is assigned to several moons of tasks that include cleaning out nests, checking elders for ticks, and other chores alongside their normal duties.",
                f"{a_n} is assigned a mentor who will better educate them about the Warrior Code and the sacredness of life.",
            ]

            # demote_leader = [f"{a_n}'s lives will be stripped away and they will be demoted to a warrior, no longer trusted to be the Clan's leader."]
            # demote_deputy = [f"The Clan decides that {a_n} will be demoted to a warrior, no longer trusting them as their deputy."]
            # demote_medicine_cat = [f"The Clan decides that {a_n} will be demoted to a warrior, no longer trusting them as their medicine cat."]
            # exiled = [f"The Clan decides that they no longer feel safe with {a_n} as a Clanmate. They will be exiled from the Clan."]

            if accomplice.status.rank in [CatRank.NEWBORN, CatRank.KITTEN]:
                game.cur_events_list.insert(
                    3,
                    Single_Event(
                        self.adjust_txt(
                            choice(kit_punishment), accomplice, cat_to_murder
                        ),
                        ["alert", "birth_death"],
                        [game.clan.your_cat.ID, accomplice.ID],
                    ),
                )
            elif accomplice.status.rank == CatRank.LEADER:
                lead_choice = randint(1, 3)
                if lead_choice == 1:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            self.adjust_txt(
                                choice(gen_punishment), accomplice, cat_to_murder
                            ),
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, accomplice.ID],
                        ),
                    )

            elif accomplice.status.rank == CatRank.DEPUTY:
                lead_choice = randint(1, 3)
                if lead_choice == 1:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            self.adjust_txt(
                                choice(gen_punishment), accomplice, cat_to_murder
                            ),
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, accomplice.ID],
                        ),
                    )

            elif accomplice.status.rank == CatRank.MEDICINE_CAT:
                lead_choice = randint(1, 3)
                if lead_choice == 1:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            self.adjust_txt(
                                choice(gen_punishment), accomplice, cat_to_murder
                            ),
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, accomplice.ID],
                        ),
                    )

            else:
                lead_choice = randint(1, 5)
                if lead_choice in [1, 2, 3, 4]:
                    game.cur_events_list.insert(
                        3,
                        Single_Event(
                            self.adjust_txt(
                                choice(gen_punishment), accomplice, cat_to_murder
                            ),
                            ["alert", "birth_death"],
                            [game.clan.your_cat.ID, accomplice.ID],
                        ),
                    )

    def adjust_txt(self, text, accomplice, victim):
        process_text_dict = {}
        process_text_dict["a_n"] = accomplice
        process_text_dict["v_c"] = victim
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))
        text = re.sub(
            r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text
        )
        text = text.replace("a_n", str(accomplice.name))
        text = text.replace("v_c", str(victim.name))
        return text

    def leader_death_chance(self, cat_to_murder, accomplice, accompliced):
        """calculates chance for leader to lose all of their lives if the murder succeeds. out of 100"""
        chance = 50
        if cat_to_murder.status.rank != CatRank.LEADER:
            return

        if game.clan.leader_lives == 1:
            chance = 100
        else:
            add = int(game.clan.leader_lives) * 5
            chance -= add

        if cat_to_murder.is_ill() or cat_to_murder.is_injured():
            chance += 8

        if accomplice and accompliced:
            chance += chance * math.floor(1 / 3)

        return chance

    def get_discover_chance(self, cat_to_murder, accomplice, accompliced):
        """calculates chance for murder discovery out of 100"""
        chance = 5
        # location chances
        if self.location == "camp":
            chance += 8
            if self.method == "attack":
                chance += 8

            if self.method == "poison":
                if game.clan.your_cat.status.rank == CatRank.MEDICINE_CAT:
                    chance += 0
                else:
                    chance += 15
            if self.method == "accident":
                chance += 20
            if self.method == "predator":
                chance += 20

            if self.time == "day":
                chance -= 8

        elif self.location == "territory":
            chance -= 8
            if self.method == "attack":
                chance += 8
            if self.method == "poison":
                if game.clan.your_cat.status.rank == CatRank.MEDICINE_CAT:
                    chance += 15
                else:
                    chance += 20
            if self.method == "accident":
                chance -= 5
            if self.method == "predator":
                chance -= 20

        elif self.location == "border":
            chance -= 20
            if self.method == "attack":
                chance -= 15
            if self.method == "poison":
                chance += 20
            if self.method == "accident":
                chance -= 20
            if self.method == "predator":
                chance -= 25

            if game.clan.war.get("at_war", True):
                chance -= 20

        if self.time == "dawn":
            if self.method == "attack":
                chance += 20
            if self.method == "accident":
                chance += 15
            if self.method == "predator":
                chance -= 15

        if self.time == "day":
            if self.method == "attack":
                chance += 30
            if self.method == "poison":
                if game.clan.your_cat.status.rank == CatRank.MEDICINE_CAT:
                    chance += 20
            if self.method == "accident":
                chance += 8
            if self.method == "predator":
                chance += 8

        if self.time == "night":
            if self.method == "attack":
                chance += 15
            if self.method == "predator":
                chance += 8

        if accomplice and accompliced:
            chance /= 2

        if chance < 5:
            chance = 5
        if chance >= 95:
            chance = 95

        return chance

    def handle_murder_fail(self, you, cat_to_murder, accomplice, accompliced):
        """handles murders failing and victims becoming accidentally injured/sick as a result"""
        c_m = str(cat_to_murder.name)

        victim_injury_chance = 8

        self.print_chances(cat_to_murder, accomplice)

        discover_chance = randint(1, 2)
        fail_texts = []
        if discover_chance == 1:
            fail_texts = [
                "You attempted to murder "
                + c_m
                + ", but were unsuccessful. They were oblivious of your attempt.",
                "You attempted to murder "
                + c_m
                + ", but they sidestepped the peril you'd arranged. They remained oblivious to your intent.",
                "You made an effort to end "
                + c_m
                + "'s life, but fortune favored them. They were none the wiser of your deadly plot.",
                "Your plot to murder "
                + c_m
                + " fell through, and they went about their day, unaware of the fate you'd intended for them.",
                "Despite your best efforts, "
                + c_m
                + " remained unscathed. They continued on, blissfully ignorant of your lethal plan.",
                "Your attempt to kill "
                + c_m
                + " proved futile, and they stayed clueless about your ominous intentions.",
            ]
        else:
            victim_injury_chance = randint(1, 5)
            if accomplice and accompliced:
                fail_texts = [
                    f"You attempted to murder {c_m}, but your plot was unsuccessful. They appear to be slightly wary of you and {accomplice.name} now.",
                    f"Your effort to end {c_m}'s life was thwarted, and they now seem a bit more cautious around you and {accomplice.name}.",
                    f"Despite your intent to murder {c_m}, they remained unscathed. They now look at you and {accomplice.name} with a hint of suspicion.",
                    f"You and {accomplice.name} tried to kill {c_m}, but they survived. They now seem to watch you both with wary eyes.",
                    f"Your plot to murder {c_m} fell through, and they remain alive, now showing signs of mild suspicion towards you and {accomplice.name}.",
                ]
                if you.ID in cat_to_murder.relationships:
                    cat_to_murder.relationships[you.ID].like -= randint(1, 15)
                    cat_to_murder.relationships[you.ID].comfort -= randint(1, 15)
                    cat_to_murder.relationships[you.ID].trust -= randint(1, 15)
                if accomplice.ID in cat_to_murder.relationships:
                    cat_to_murder.relationships[accomplice.ID].like -= randint(1, 15)
                    cat_to_murder.relationships[accomplice.ID].comfort -= randint(1, 15)
                    cat_to_murder.relationships[accomplice.ID].trust -= randint(1, 15)
            else:
                fail_texts = [
                    "You attempted to murder "
                    + c_m
                    + ", but your plot was unsuccessful. They appear to be slightly wary now.",
                    "Your effort to end "
                    + c_m
                    + "'s life was thwarted, and they now seem a bit more cautious around you.",
                    "Despite your intent to murder "
                    + c_m
                    + ", they remained unscathed. They look at you now with a hint of suspicion.",
                    "You tried to kill "
                    + c_m
                    + ", but they survived. They now seem to watch you with wary eyes.",
                    "Your plot to murder "
                    + c_m
                    + " fell through, and they remain alive, now showing signs of mild suspicion towards you.",
                ]
                if you.ID in cat_to_murder.relationships:
                    cat_to_murder.relationships[you.ID].like -= randint(1, 15)
                    cat_to_murder.relationships[you.ID].comfort -= randint(1, 15)
                    cat_to_murder.relationships[you.ID].trust -= randint(1, 15)

        text = choice(fail_texts)
        owie = "torn pelt"

        if victim_injury_chance == 1:
            if self.method == "attack":
                owie = choice(["claw-wound", "torn pelt", "scrapes"])
            elif self.method == "poison":
                owie = choice(["poisoned", "stomachache", "diarrhea"])
            elif self.method == "accident":
                owie = choice(
                    [
                        "broken bone",
                        "broken bone",
                        "sprain",
                        "sore",
                        "bruises",
                        "scrapes",
                    ]
                )
            elif self.method == "predator":
                owie = choice(
                    [
                        "bite-wound",
                        "broken bone",
                        "torn pelt",
                        "mangled leg",
                        "mangled tail",
                    ]
                )

            cat_to_murder.get_injured(owie)

            if self.method == "poison":
                text = text + f" Your attempt on their life has left {c_m} ill."
            else:
                text = text + f" Your attempt on their life has left {c_m} injured."

        game.cur_events_list.insert(
            0, Single_Event(text, ["health"], [game.clan.your_cat.ID, cat_to_murder.ID])
        )

    status_chances = {
        "warrior": 20,
        "medicine cat": 20,
        "mediator": 17,
        "apprentice": 15,
        "medicine cat apprentice": 13,
        "mediator apprentice": 10,
        "queen": 13,
        "queen's apprentice": 13,
        "deputy": 25,
        "leader": 30,
        "elder": 13,
        "kitten": 5,
    }

    skill_chances = {
        "warrior": -5,
        "medicine cat": -5,
        "mediator": 0,
        "apprentice": 5,
        "medicine cat apprentice": 5,
        "mediator apprentice": 5,
        "queen's apprentice": 10,
        "queen": 5,
        "deputy": -10,
        "leader": -15,
        "elder": 5,
        "kitten": 30,
    }

    murder_skills = [
        "quick witted",
        "avid play-fighter",
        "oddly observant",
        "never sits still",
    ]
    good_murder_skills = ["clever", "good fighter", "natural intuition", "fast runner"]
    great_murder_skills = [
        "very clever",
        "formidable fighter",
        "keen eye",
        "incredible runner",
    ]
    best_murder_skills = [
        "incredibly clever",
        "unusually strong fighter",
        "unnatural senses",
        "fast as the wind",
    ]

    def get_kill(self, you, cat_to_murder, accomplice, accompliced):
        chance = self.status_chances.get(you.status.rank, 0)

        you_healthy = not you.is_ill() and not you.is_injured()

        accomplice_healthy = (
            (not accomplice.is_ill() and not accomplice.is_injured())
            if accomplice
            else None
        )

        cat_healthy = not cat_to_murder.is_ill() and not cat_to_murder.is_injured()

        # GENERAL CHANCES
        # skill chances from original murderscreen
        your_skills = []
        if you.skills.primary:
            your_skills.append(you.skills.primary.skill)
        if you.skills.secondary:
            your_skills.append(you.skills.secondary.skill)

        their_skills = []
        if cat_to_murder.skills.primary:
            their_skills.append(cat_to_murder.skills.primary.skill)
        if cat_to_murder.skills.secondary:
            their_skills.append(cat_to_murder.skills.secondary.skill)

        accomp_skills = []
        if accomplice:
            if accomplice.skills.primary:
                accomp_skills.append(accomplice.skills.primary.skill)
            if accomplice.skills.secondary:
                accomp_skills.append(accomplice.skills.secondary.skill)

        if any(skill in self.murder_skills for skill in your_skills):
            chance += 5
        if any(skill in self.good_murder_skills for skill in your_skills):
            chance += 10
        if any(skill in self.great_murder_skills for skill in your_skills):
            chance += 15
        if any(skill in self.best_murder_skills for skill in your_skills):
            chance += 20

        chance += self.skill_chances.get(cat_to_murder.status.rank, 0)

        if any(skill in self.murder_skills for skill in their_skills):
            chance -= 5
        if any(skill in self.good_murder_skills for skill in their_skills):
            chance -= 10
        if any(skill in self.great_murder_skills for skill in their_skills):
            chance -= 15
        if any(skill in self.best_murder_skills for skill in their_skills):
            chance -= 20

        # new stuff
        # raises chances:
        if you.joined_df:
            chance += 15
        if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
            chance += 10
        if cat_to_murder.age == "senior":
            chance += 10
        if you.status.rank == cat_to_murder.status.rank:
            chance += 5
        if not cat_healthy:
            chance += 10
        if you.experience > cat_to_murder.experience:
            chance += 5
        if accomplice and accompliced:
            chance += 15
            if accomplice.personality.trait == "bloodthirsty":
                chance += 10
            if accomplice.status.rank == CatRank.WARRIOR and accomplice_healthy:
                chance += 5
            if (
                accomplice.status.rank in [CatRank.LEADER, CatRank.DEPUTY]
                and accomplice_healthy
            ):
                chance += 15

        if you.history:
            if you.history.murder:
                if "is_murderer" in you.history.murder:
                    if len(you.history.murder["is_murderer"]) > 0:
                        for i in range(len(you.history.murder["is_murderer"])):
                            chance += 5

        if you.ID in cat_to_murder.relationships:
            if (
                cat_to_murder.relationships[you.ID].like > 20
                and cat_to_murder.relationships[you.ID].like < 50
            ):
                chance += 10
            elif cat_to_murder.relationships[you.ID].like >= 50:
                chance += 15

        if self.time == "night":
            chance += 10

        if cat_to_murder.joined_df:
            chance -= 10
        if cat_to_murder.moons >= you.moons + 4:
            chance -= 10
        if not you_healthy:
            chance -= 10

        if (
            cat_to_murder.status.rank == CatRank.LEADER
            and not cat_to_murder.status.is_shunned()
            and cat_healthy
        ):
            chance -= 10

        if cat_to_murder.moons < 6:
            for cat in Cat.all_cats_list:
                if cat.ID != you.ID:
                    if cat.status.rank == CatRank.QUEEN:
                        chance -= 5
                    if (
                        cat.ID == (cat_to_murder.parent1 or cat_to_murder.parent2)
                        or cat.ID in cat_to_murder.adoptive_parents
                    ):
                        chance -= 5

        if cat_to_murder.experience > you.experience:
            chance -= 5

        victim_skills_lvl1 = [
            "watchful",
            "lives in groups",
            "interested in oddities",
            "fascinated by prophecies",
        ]
        victim_skills_lvl2 = [
            "good guard",
            "good sport",
            "omen seeker",
            "prophecy seeker",
        ]
        victim_skills_lvl3 = [
            "great guard",
            "team player",
            "omen sense",
            "prophecy interpreter",
        ]
        victim_skills_lvl4 = ["guardian", "insider", "omen sight", "prophet"]

        if any(skill in victim_skills_lvl1 for skill in their_skills):
            chance -= 5
        if any(skill in victim_skills_lvl2 for skill in their_skills):
            chance -= 10
        if any(skill in victim_skills_lvl3 for skill in their_skills):
            chance -= 15
        if any(skill in victim_skills_lvl4 for skill in their_skills):
            chance -= 20

        if self.location != "camp":
            if "picky nest builder" in their_skills:
                chance -= 3
            if "steady paws" in their_skills:
                chance -= 7
            if "den builder" in their_skills:
                chance -= 11
            if "campkeeper" in their_skills:
                chance -= 15

        if (
            cat_to_murder.status.rank
            in [
                CatRank.QUEEN,
                CatRank.QUEENS_APPRENTICE,
                CatRank.MEDICINE_CAT,
                CatRank.MEDICINE_APPRENTICE,
                CatRank.KITTEN,
            ]
            and self.location != "camp"
        ):
            chance -= 8

        if cat_to_murder.history:
            if cat_to_murder.history.murder:
                if "is_murderer" in cat_to_murder.history.murder:
                    if len(cat_to_murder.history.murder["is_murderer"]) > 0:
                        for i in range(
                            len(cat_to_murder.history.murder["is_murderer"])
                        ):
                            chance -= 5

        if you.ID in cat_to_murder.relationships:
            if (
                cat_to_murder.relationships[you.ID].like < -20
                and cat_to_murder.relationships[you.ID].like >= -50
            ):
                chance -= 10
            elif cat_to_murder.relationships[you.ID].like <= -50:
                chance -= 15

        if self.time == "day":
            chance -= 10

        # METHOD CHANCES
        # ATTACK
        if self.method == "attack":
            # raises chances
            if you.joined_df:
                chance += 15

            if (
                "steps lightly" or "mossball hunter" or "avid play-fighter"
            ) in your_skills:
                chance += 3
            if ("graceful" or "good hunter" or "good fighter") in your_skills:
                chance += 7
            if ("elegant" or "great hunter" or "formidable fighter") in your_skills:
                chance += 11
            if (
                "radiates elegance" or "renowned hunter" or "unusually strong fighter"
            ) in your_skills:
                chance += 15

            if you.status.rank == CatRank.WARRIOR:
                chance += 10
            if you.age != cat_to_murder.age and you.moons > cat_to_murder.moons:
                chance += 10

            if self.location == "border":
                chance += 15

            if you.personality.trait == "bloodthirsty":
                chance += 10

            # lowers chances

            if cat_to_murder.status.rank == CatRank.WARRIOR:
                chance -= 10
            if not you.status.rank.is_any_adult_warrior_like_rank():
                chance -= 10

            if "avid play-fighter" in their_skills:
                chance -= 3
            if "good fighter" in their_skills:
                chance -= 7
            if "formidable fighter" in their_skills:
                chance -= 11
            if "unusually strong fighter" in their_skills:
                chance -= 15

            if self.location == "camp":
                chance -= 15
            if cat_to_murder.personality.trait == "bloodthirsty":
                chance -= 10

        if self.method == "poison":
            # raises chances
            if you.status.rank in [CatRank.MEDICINE_APPRENTICE, CatRank.MEDICINE_CAT]:
                chance += 25
            if cat_to_murder.is_ill() or cat_to_murder.is_injured():
                chance += 15

            if self.location == "camp":
                chance += 10
            if self.location == "territory":
                chance += 15

            # lowers chances
            if cat_to_murder.status.rank in [
                CatRank.MEDICINE_APPRENTICE,
                CatRank.MEDICINE_CAT,
            ]:
                chance -= 15
            if not cat_to_murder.is_ill() and not cat_to_murder.is_injured():
                chance -= 10
            if you.status.rank not in [
                CatRank.MEDICINE_APPRENTICE,
                CatRank.MEDICINE_CAT,
            ]:
                chance -= 20

            if self.location == "border":
                chance -= 10

        if self.method == "accident":
            # raises chances
            if accomplice and accompliced:
                chance += 10

            acc_skills_lvl_1 = [
                "curious wanderer",
                "good with directions",
                "constantly climbing",
            ]
            acc_skills_lvl_2 = [
                "knowledgeable explorer",
                "good navigator",
                "good climber",
            ]
            acc_skills_lvl_3 = ["brave pathfinder", "great navigator", "great climber"]
            acc_skills_lvl_4 = [
                "master of territories",
                "pathfinder",
                "impressive climber",
            ]

            if any(skill in acc_skills_lvl_1 for skill in your_skills):
                chance += 5
            if any(skill in acc_skills_lvl_2 for skill in your_skills):
                chance += 10
            if any(skill in acc_skills_lvl_3 for skill in your_skills):
                chance += 15
            if any(skill in acc_skills_lvl_4 for skill in your_skills):
                chance += 20

            if (
                not cat_to_murder.status.rank.is_any_adult_warrior_like_rank()
                and not cat_to_murder.skills.meets_skill_requirement(SkillPath.EXPLORER)
                and not cat_to_murder.skills.meets_skill_requirement(
                    SkillPath.NAVIGATOR
                )
                and not cat_to_murder.skills.meets_skill_requirement(SkillPath.CLIMBER)
            ):
                chance += 10
            if you.age == cat_to_murder.age and you.age in ["kitten", "adolescent"]:
                chance += 10

            if game.clan.biome == "Mountainous":
                chance += 10

            if self.location == "territory":
                chance += 15

            # lowers chances
            if any(skill in acc_skills_lvl_1 for skill in their_skills):
                chance -= 5
            if any(skill in acc_skills_lvl_2 for skill in their_skills):
                chance -= 10
            if any(skill in acc_skills_lvl_3 for skill in their_skills):
                chance -= 15
            if any(skill in acc_skills_lvl_4 for skill in their_skills):
                chance -= 20

            if cat_to_murder.status.rank.is_any_adult_warrior_like_rank():
                chance -= 15
            if you.moons >= 12 and cat_to_murder.moons >= 12:
                chance -= 10

            if self.location == "camp":
                chance -= 15

        if self.method == "predator":
            # raises chances
            chance += 20
            if accomplice and accompliced:
                chance += 10
                if "other-cat-ly whisperer" in accomp_skills:
                    chance += 5
                if "dog-whisperer" in accomp_skills:
                    chance += 10
                if "multilingual" in accomp_skills:
                    chance += 15
                if "listener of all voices" in accomp_skills:
                    chance += 20

            if cat_to_murder.moons < 6:
                chance += 20
            if self.location in ["territory", "border"]:
                chance += 15

            if "other-cat-ly whisperer" in your_skills:
                chance += 5
            if "dog-whisperer" in your_skills:
                chance += 10
            if "multilingual" in your_skills:
                chance += 15
            if "listener of all voices" in your_skills:
                chance += 20

            # lowers chances
            if cat_to_murder.moons >= 12:
                chance -= 10
            if cat_to_murder.status.rank.is_any_adult_warrior_like_rank():
                chance -= 10
            if not you.status.rank.is_any_adult_warrior_like_rank():
                chance -= 15

            if "watchful" in their_skills:
                chance -= 7
            if "good guard" in their_skills:
                chance -= 11
            if "great guard" in their_skills:
                chance -= 16
            if "guardian" in their_skills:
                chance -= 23

            if "avid play-fighter" in their_skills:
                chance -= 3
            if "good fighter" in their_skills:
                chance -= 8
            if "formidable fighter" in their_skills:
                chance -= 13
            if "unusually strong fighter" in their_skills:
                chance -= 18

            if self.location == "camp":
                chance -= 10

            if "other-cat-ly whisperer" in their_skills:
                chance += 5
            if "dog-whisperer" in their_skills:
                chance += 10
            if "multilingual" in their_skills:
                chance += 15
            if "listener of all voices" in their_skills:
                chance += 20

        if you.moons < 6:
            chance = chance * math.ceil(2 / 3)

        if cat_to_murder.moons < 6:
            chance = chance * math.ceil(4 / 3)

        if accomplice and accompliced:
            chance = chance * math.floor(6 / 5)

        if chance <= 0:
            chance = 5

        if chance > 95:
            chance = 95

        # debug
        # chance = 100

        return chance

    def update_method_info(self):
        if self.methodinfo:
            self.methodinfo.kill()
            del self.methodinfo

        if self.methodheading:
            self.methodheading.kill()
            del self.methodheading

        if self.locationinfo:
            self.locationinfo.kill()
            del self.locationinfo

        if self.locationheading:
            self.locationheading.kill()
            del self.locationheading

        if self.timeinfo:
            self.timeinfo.kill()
            del self.timeinfo

        if self.timeheading:
            self.timeheading.kill()
            del self.timeheading

        # METHOD INFO
        if self.method == "attack":
            self.methodheading = pygame_gui.elements.UITextBox(
                "<b>An Attack</b>",
                ui_scale(pygame.Rect((125, 385), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.methodinfo = pygame_gui.elements.UITextBox(
                "A flashy choice for those who aren't afraid to use their claws.",
                ui_scale(pygame.Rect((125, 410), (550, 150))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )
        elif self.method == "poison":
            self.methodheading = pygame_gui.elements.UITextBox(
                "<b>A Poisoning</b>",
                ui_scale(pygame.Rect((125, 385), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.methodinfo = pygame_gui.elements.UITextBox(
                "A simple, discreet method, as long as you have the knowledge to pull it off.",
                ui_scale(pygame.Rect((125, 410), (550, 50))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

        elif self.method == "accident":
            self.methodheading = pygame_gui.elements.UITextBox(
                '<b>An "Accident"</b>',
                ui_scale(pygame.Rect((125, 385), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.methodinfo = pygame_gui.elements.UITextBox(
                "A rough strategy for those who are great at feigning innocence.",
                ui_scale(pygame.Rect((125, 410), (550, 50))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

        elif self.method == "predator":
            self.methodheading = pygame_gui.elements.UITextBox(
                "<b>Lure a Predator</b>",
                ui_scale(pygame.Rect((125, 385), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.methodinfo = pygame_gui.elements.UITextBox(
                "A risky technique for those who don't want to get their own paws dirty.",
                ui_scale(pygame.Rect((125, 410), (550, 50))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )
        # LOCATION INFO
        if self.location == "camp":
            if self.method == "predator":
                insert = "To"
            else:
                insert = "In"

            self.locationheading = pygame_gui.elements.UITextBox(
                f"<b>{insert} Camp</b>",
                ui_scale(pygame.Rect((125, 455), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.locationinfo = pygame_gui.elements.UITextBox(
                "For a kill closer to home.",
                ui_scale(pygame.Rect((125, 480), (550, 50))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

        elif self.location == "territory":
            if self.method == "predator":
                insert = "To"
            else:
                insert = "In"
            self.locationheading = pygame_gui.elements.UITextBox(
                f"<b>{insert} the Territory</b>",
                ui_scale(pygame.Rect((125, 455), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.locationinfo = pygame_gui.elements.UITextBox(
                "Who knows what could happen out there?",
                ui_scale(pygame.Rect((125, 480), (550, 50))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

        elif self.location == "border":
            if self.method == "predator":
                insert = "To"
            else:
                insert = "At"

            self.locationheading = pygame_gui.elements.UITextBox(
                f"<b>{insert} the Border</b>",
                ui_scale(pygame.Rect((125, 455), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.locationinfo = pygame_gui.elements.UITextBox(
                "The border is a dangerous place.",
                ui_scale(pygame.Rect((125, 480), (550, 50))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )
        # TIME INFO
        if self.time == "dawn":
            self.timeheading = pygame_gui.elements.UITextBox(
                "<b>At Dawn</b>",
                ui_scale(pygame.Rect((125, 535), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.timeinfo = pygame_gui.elements.UITextBox(
                "The early bird gets the worm!",
                ui_scale(pygame.Rect((125, 560), (550, 150))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

        elif self.time == "day":
            self.timeheading = pygame_gui.elements.UITextBox(
                "<b>During the Day</b>",
                ui_scale(pygame.Rect((125, 535), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.timeinfo = pygame_gui.elements.UITextBox(
                "Want to strike in broad daylight?",
                ui_scale(pygame.Rect((125, 560), (550, 150))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

        elif self.time == "night":
            self.timeheading = pygame_gui.elements.UITextBox(
                "<b>At Night</b>",
                ui_scale(pygame.Rect((125, 535), (550, 50))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.timeinfo = pygame_gui.elements.UITextBox(
                "Take advantage of the darkness.",
                ui_scale(pygame.Rect((125, 560), (550, 150))),
                object_id=get_text_box_theme("#text_box_30_horizcenter"),
                manager=MANAGER,
            )

    def update_chance_text(self, cat_to_murder, accomplice):
        if self.chancetext:
            self.chancetext.kill()
            del self.chancetext

        if self.willingnesstext:
            self.willingnesstext.kill()
            del self.willingnesstext

        if self.selected_cat:
            if self.selected_cat.status.alive_in_player_clan:
                if (
                    game.clan.your_cat.skills.meets_skill_requirement(SkillPath.PROPHET)
                    or game.clan.your_cat.skills.meets_skill_requirement(
                        SkillPath.CLEVER
                    )
                    or game.clan.your_cat.skills.meets_skill_requirement(
                        SkillPath.SENSE
                    )
                    or game.clan.your_cat.skills.meets_skill_requirement(SkillPath.OMEN)
                    or game.clan.your_cat.skills.meets_skill_requirement(
                        SkillPath.INSIGHTFUL
                    )
                ):
                    c_text = ""
                    if accomplice:
                        chance = self.get_kill(
                            game.clan.your_cat,
                            self.cat_to_murder,
                            self.selected_cat,
                            True,
                        )
                    else:
                        chance = self.get_kill(
                            game.clan.your_cat, cat_to_murder, None, False
                        )

                    risk_chance = self.get_risk_chance(
                        self.selected_cat, accomplice=None, accompliced=None
                    )
                    discover_chance = self.get_discover_chance(
                        self.selected_cat, accomplice=None, accompliced=False
                    )

                    if chance < 20:
                        c_text = "very low"
                    elif chance < 30:
                        c_text = "low"
                    elif chance < 50:
                        c_text = "average"
                    elif chance < 80:
                        c_text = "high"
                    else:
                        c_text = "very high"

                    insert = ""

                    if accomplice:
                        insert = "possible success chance: "
                    else:
                        insert = "success chance: "

                    self.chancetext = pygame_gui.elements.UITextBox(
                        insert + c_text,
                        ui_scale(pygame.Rect((124, 345), (105, 125))),
                        object_id=get_text_box_theme(
                            "#text_box_22_horizcenter_spacing_95"
                        ),
                        manager=MANAGER,
                    )

                if self.stage == "choose accomplice":
                    if self.selected_cat is not None:
                        a_text = ""
                        chance = self.get_kill(
                            game.clan.your_cat,
                            self.cat_to_murder,
                            accomplice=self.selected_cat,
                            accompliced=False,
                        )

                        chance = self.get_accomplice_chance(
                            game.clan.your_cat, self.selected_cat, self.cat_to_murder
                        )

                        if (
                            constants.CONFIG["lifegen"]["gen"]["accomplice_chance"]
                            != -1
                        ):
                            try:
                                chance = constants.CONFIG["lifegen"]["gen"][
                                    "accomplice_chance"
                                ]
                            except:
                                pass
                        if chance < 20:
                            a_text = "very low"
                        elif chance < 30:
                            a_text = "low"
                        elif chance < 50:
                            a_text = "average"
                        elif chance < 80:
                            a_text = "high"
                        else:
                            a_text = "very high"

                        self.willingnesstext = pygame_gui.elements.UITextBox(
                            "willingness: " + a_text,
                            ui_scale(pygame.Rect((572, 345), (105, 125))),
                            object_id=get_text_box_theme(
                                "#text_box_22_horizcenter_spacing_95"
                            ),
                            manager=MANAGER,
                        )
                else:
                    self.willingnesstext = pygame_gui.elements.UITextBox(
                        "",
                        ui_scale(pygame.Rect((572, 345), (105, 125))),
                        object_id=get_text_box_theme(
                            "#text_box_22_horizcenter_spacing_95"
                        ),
                        manager=MANAGER,
                    )
        else:
            self.willingnesstext = None
            self.chancetext = None

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        if self.selected_cat and not self.selected_cat.dead:
            self.confirm_mentor.enable()

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((105, 95), (135, 135))),
                pygame.transform.scale(
                    self.selected_cat.sprite, ui_scale_dimensions((135, 135))
                ),
                manager=MANAGER,
            )

            info = (
                self.selected_cat.status.rank
                + "\n"
                + self.selected_cat.genderalign
                + "\n"
                + self.selected_cat.personality.trait
                + "\n"
            )

            if self.selected_cat.moons < 1:
                info += "???"
            else:
                info += self.selected_cat.skills.skill_string(short=True)

            # vicinfo

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((102, 237), (150, 125))),
                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                manager=MANAGER,
            )

            name = str(self.selected_cat.name)  # get name
            if 17 <= len(name):  # check name length
                short_name = str(name)[0:15]
                name = short_name + "..."
            self.selected_details["victim_name"] = pygame_gui.elements.ui_label.UILabel(
                ui_scale(pygame.Rect((102, 237), (150, 30))),
                name,
                object_id="#text_box_34_horizcenter",
                manager=MANAGER,
            )

            self.update_chance_text(self.selected_cat, accomplice=None)
        elif self.selected_cat and self.selected_cat.dead:
            self.stage = "choose murder cat"
            self.confirm_mentor.disable()
        else:
            self.confirm_mentor.disable()

    def get_accomplice_chance(self, you, accomplice, cat_to_murder):
        chance = 10
        if accomplice is not None:
            if you.ID in accomplice.relationships:
                if accomplice.relationships[you.ID].like > 10:
                    chance += 10
                if accomplice.relationships[you.ID].like > -10:
                    chance += 10
                if accomplice.relationships[you.ID].romance > 10:
                    chance += 10
                if accomplice.relationships[you.ID].comfort > 10:
                    chance += 10
                if accomplice.relationships[you.ID].trust > 10:
                    chance += 10
            if you.status.rank in [
                CatRank.MEDICINE_CAT,
                CatRank.MEDIATOR,
                CatRank.DEPUTY,
                CatRank.LEADER,
            ]:
                chance += 10
            if accomplice.status.rank in [
                CatRank.MEDICINE_CAT,
                CatRank.MEDIATOR,
                CatRank.DEPUTY,
                CatRank.LEADER,
            ]:
                chance -= 20
            if accomplice.ID in game.clan.your_cat.mate:
                chance += 50
            if game.clan.your_cat.is_related(accomplice, False):
                chance += 30

        return chance

    def update_selected_cat2(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        if (
            self.selected_cat
            and self.selected_cat.ID != self.cat_to_murder.ID
            and not self.selected_cat.dead
        ):
            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((560, 95), (135, 135))),
                pygame.transform.scale(
                    self.selected_cat.sprite, ui_scale_dimensions((135, 135))
                ),
                manager=MANAGER,
            )

            info = (
                self.selected_cat.status.rank
                + "\n"
                + self.selected_cat.genderalign
                + "\n"
                + self.selected_cat.personality.trait
                + "\n"
            )

            if self.selected_cat.moons < 1:
                info += "???"
            else:
                info += self.selected_cat.skills.skill_string(short=True)

            self.selected_details["selected_info_acc"] = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((551, 237), (150, 125))),
                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                manager=MANAGER,
            )

            name = str(self.selected_cat.name)  # get name
            if 17 <= len(name):  # check name length
                short_name = str(name)[0:15]
                name = short_name + "..."
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                ui_scale(pygame.Rect((552, 237), (150, 30))),
                name,
                object_id="#text_box_34_horizcenter",
                manager=MANAGER,
            )

        if self.selected_cat:
            self.update_chance_text(self.cat_to_murder, accomplice=self.selected_cat)

    def update_cat_list(self):
        """Updates the cat sprite buttons."""
        valid_mentors = self.chunks(self.get_valid_cats(), 30)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_mentors):
            self.current_page = max(1, len(valid_mentors))

        # Handle which next buttons are clickable.
        if len(valid_mentors) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_mentors):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_mentors) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_cats = []
        if valid_mentors and len(valid_mentors) > self.current_page - 1:
            display_cats = valid_mentors[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        pos_x = 0
        pos_y = 20
        i = 0
        for cat in display_cats:
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                ui_scale(pygame.Rect((100 + pos_x, 400 + pos_y), (50, 50))),
                cat.sprite,
                cat_object=cat,
                manager=MANAGER,
            )
            pos_x += 60
            if pos_x >= 550:
                pos_x = 0
                pos_y += 60
            i += 1

    def update_cat_list2(self):
        """Updates the cat sprite buttons."""
        valid_mentors = self.chunks(self.get_valid_cats2(), 30)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_mentors):
            self.current_page = max(1, len(valid_mentors))

        # Handle which next buttons are clickable.
        if len(valid_mentors) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_mentors):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_mentors) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_cats = []
        if valid_mentors and len(valid_mentors) > self.current_page - 1:
            display_cats = valid_mentors[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        pos_x = 0
        pos_y = 20
        i = 0
        for cat in display_cats:
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                ui_scale(pygame.Rect((100 + pos_x, 400 + pos_y), (50, 50))),
                cat.sprite,
                cat_object=cat,
                manager=MANAGER,
            )
            pos_x += 60
            if pos_x >= 550:
                pos_x = 0
                pos_y += 60
            i += 1

    def get_valid_cats(self):
        valid_mentors = []

        for cat in Cat.all_cats_list:
            if (
                cat.status.alive_in_player_clan
                and not cat.ID == game.clan.your_cat.ID
                and cat.moons > 0
            ):
                valid_mentors.append(cat)

        return valid_mentors

    def get_valid_cats2(self):
        valid_mentors = []
        for cat in Cat.all_cats_list:
            if (
                cat.status.alive_in_player_clan
                and cat.ID != game.clan.your_cat.ID
                and cat.ID != self.cat_to_murder.ID
                and cat.moons > 0
            ):
                valid_mentors.append(cat)

        return valid_mentors

    def on_use(self):
        # Due to a bug in pygame, any image with buttons over it must be blited
        super().on_use()

    def chunks(self, L, n):
        return [L[x : x + n] for x in range(0, len(L), n)]
