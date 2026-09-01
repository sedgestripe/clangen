import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson
import re
from .Screens import Screens

from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale
from ..events_module.text_adjust import pronoun_repl

from scripts.events_module.event_filters import get_personality_compatibility

from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.elements.sprite_button import UISpriteButton
from ..ui.generate_box import BoxStyles, get_box
from scripts.game_structure.screen_settings import MANAGER
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon
from ..game_structure.game.switches import switch_get_value, Switch
from scripts.screens.enums import GameScreen
from scripts.clan_package.settings import get_clan_setting
from scripts.game_structure.localization import load_lang_resource


class QueenScreen(Screens):
    selected_cat = None
    current_page = 1
    list_frame = None
    queen_img = pygame.transform.scale(
        image_cache.load_image("resources/images/queenart.png").convert_alpha(),
        (250, 250),
    )
    selected_details = {}
    cat_list_buttons = {}

    def __init__(self, name=None):
        super().__init__(name)
        self.fav = {}
        self.list_page = None
        self.next_page_button = None
        self.previous_page_button = None
        self.current_mentor_warning = None
        self.confirm_mentor = None
        self.back_button = None
        self.mentor_icon = None
        self.app_frame = None
        self.mentor_frame = None
        self.current_mentor_text = None
        self.info = None
        self.heading = None
        self.mentor = None
        self.the_cat = None
        self.activity = "mossball"
        self.queen_art = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()
            elif event.ui_element == self.confirm_mentor and self.selected_cat:
                if not self.selected_cat.dead:
                    self.update_selected_cat()
                    self.change_cat()
            elif event.ui_element == self.back_button:
                self.change_screen(GameScreen.PROFILE)
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                self.update_cat_list()
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                self.update_cat_list()
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            self.activity = event.text

    def screen_switches(self):
        super().screen_switches()
        self.the_cat = Cat.all_cats.get(switch_get_value(Switch.cat))

        list_frame = get_box(BoxStyles.ROUNDED_BOX, (330, 194))
        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((75, 360), (330, 194))), list_frame, starting_height=1
        )

        self.queen_art = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((450, 360), (250, 250))),
            self.queen_img,
            starting_height=1,
        )

        self.activity = "mossball"
        self.heading = pygame_gui.elements.UITextBox(
            f"{self.the_cat.name}'s Nursery Activities",
            ui_scale(pygame.Rect((150, 25), (500, 40))),
            object_id=get_text_box_theme("#text_box_34_horizcenter"),
            manager=MANAGER,
        )

        if self.the_cat.did_activity:
            self.heading2 = pygame_gui.elements.UITextBox(
                "This queen already worked this moon.",
                ui_scale(pygame.Rect((0, 55), (500, 80))),
                object_id=get_text_box_theme("#text_box_26_horizcenter"),
                manager=MANAGER,
                anchors={"centerx": "centerx"},
            )
        else:
            self.heading2 = pygame_gui.elements.UITextBox(
                "Nursery activities can impact a kit's stats.\n"
                + "Stats may affect the kit's future role and personality.",
                ui_scale(pygame.Rect((0, 55), (500, 80))),
                object_id=get_text_box_theme("#text_box_26_horizcenter"),
                manager=MANAGER,
                anchors={"centerx": "centerx"},
            )

        self.mentor_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((415, 113), (281, 197))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/choosing_cat1_frame_ment.png"
                ).convert_alpha(),
                (281, 197),
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

        self.previous_page_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((125, 579), (34, 34))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=0,
        )
        self.next_page_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((291, 579), (34, 34))),
            Icon.ARROW_RIGHT,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
            starting_height=0,
        )

        self.activity_text = pygame_gui.elements.UITextBox(
            "Choose an activity!",
            ui_scale(pygame.Rect((55, 110), (400, 40))),
            object_id=get_text_box_theme("#text_box_34_horizcenter"),
            manager=MANAGER,
        )

        self.activities = pygame_gui.elements.UIDropDownMenu(
            [
                "mossball",
                "playfight",
                "lecture",
                "clean",
                "tell story",
                "scavenger hunt",
            ],
            "mossball",
            ui_scale(pygame.Rect((100, 150), (150, 35))),
            manager=MANAGER,
        )

        # CHECKMERGE redo. this screen lol

        # self.activities = UIDropDown(
        #     pygame.Rect((60, 150), (150, 35)),
        #     parent_text=self.activity,
        #     item_list=["mossball", "playfight", "lecture", "clean", "tell story", "scavenger hunt"],
        #     manager=MANAGER,
        #     starting_selection=["mossball"]
        # )

        self.confirm_mentor = UISurfaceImageButton(
            ui_scale(pygame.Rect((290, 150), (104, 34))),
            "Play!",
            get_button_dict(ButtonStyles.SQUOVAL, (104, 34)),
            object_id="@buttonstyles_squoval",
            starting_height=0,
        )

        if self.the_cat.did_activity:
            self.confirm_mentor.disable()

        self.activity_box = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((100, 180), (300, 200))),
            object_id=get_text_box_theme("#text_box_26"),
            manager=MANAGER,
        )

        self.selected_cat = None
        self.update_selected_cat()  # Updates the image and details of selected cat
        self.update_cat_list()

    def exit_screen(self):
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for marker in self.fav:
            self.fav[marker].kill()
        self.fav = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        self.queen_art.kill()
        del self.queen_art
        self.heading.kill()
        del self.heading
        self.heading2.kill()
        del self.heading2
        self.mentor_frame.kill()
        del self.mentor_frame

        self.back_button.kill()
        del self.back_button
        self.confirm_mentor.kill()
        del self.confirm_mentor

        self.previous_page_button.kill()
        del self.previous_page_button
        self.next_page_button.kill()
        del self.next_page_button

        self.activity_box.kill()
        self.activity_text.kill()
        self.activities.kill()

        self.list_frame.kill()
        del self.list_frame

    def change_cat(self):
        display_events = load_lang_resource(
            "events/lifegen_events/nursery_activities.json"
        )
        display_events = display_events[self.activity]

        success = self.get_success()
        stat_change = choice(display_events["stat_change"])
        while (success and "down" in stat_change) or (
            not success and "up" in stat_change
        ):
            stat_change = choice(display_events["stat_change"])
        self.activity_box.kill()
        self.activity_box = pygame_gui.elements.UITextBox(
            self.adjust_txt(choice(display_events[stat_change])),
            ui_scale(pygame.Rect((100, 210), (300, 170))),
            object_id=get_text_box_theme("#text_box_26"),
            manager=MANAGER,
        )
        if stat_change == "courage up":
            self.selected_cat.courage += 1
        elif stat_change == "courage down":
            self.selected_cat.courage -= 1
        elif stat_change == "empathy up":
            self.selected_cat.empathy += 1
        elif stat_change == "empathy down":
            self.selected_cat.empathy -= 1
        elif stat_change == "compassion up":
            self.selected_cat.compassion += 1
        elif stat_change == "compassion down":
            self.selected_cat.compassion -= 1
        elif stat_change == "intelligence up":
            self.selected_cat.intelligence += 1
        elif stat_change == "intelligence down":
            self.selected_cat.intelligence -= 1

        if success:
            exp_gain = randint(5, 20)
            self.the_cat.experience += exp_gain
        self.update_selected_cat()
        self.the_cat.did_activity = True
        self.confirm_mentor.disable()

    def get_success(self):
        queen = self.the_cat
        kit = self.selected_cat

        # influences on success chances: exp, relationship, skill

        chance = 50

        if queen.experience_level == "untrained":
            chance = 40
        elif queen.experience_level == "trainee":
            chance = 50
        elif queen.experience_level == "prepared":
            chance = 60
        elif queen.experience_level == "proficient":
            chance = 70
        elif queen.experience_level == "expert":
            chance = 80
        elif queen.experience_level == "master":
            chance = 90

        if queen.ID in kit.relationships:
            rel1 = queen.relationships[kit.ID]
        else:
            rel1 = queen.create_one_relationship(kit)

        if kit.ID in queen.relationships:
            rel2 = kit.relationships[queen.ID]
        else:
            rel2 = kit.create_one_relationship(queen)

        compat = get_personality_compatibility(queen, kit)
        if compat is True:
            chance += 10
        elif compat is False:
            chance -= 5

        if rel1.like > 30:
            chance += 5
        if rel1.like < -10:
            chance -= 5
        if rel2.like > 30:
            chance += 5
        if rel2.like < -10:
            chance -= 5

        return randint(0, 100) < min(chance, 95)

    def adjust_txt(self, text):
        process_text_dict = {}
        process_text_dict["t_k"] = self.selected_cat
        process_text_dict["t_q"] = self.the_cat
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))
        text = re.sub(
            r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text
        )
        text = text.replace("t_k", str(self.selected_cat.name))
        text = text.replace("t_q", str(self.the_cat.name))
        return text

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat is None or self.the_cat.did_activity:
            self.confirm_mentor.disable()
        else:
            self.confirm_mentor.enable()

        if self.selected_cat:
            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((425, 150), (150, 150))),
                pygame.transform.scale(self.selected_cat.sprite, (150, 150)),
                manager=MANAGER,
            )

            stats = f"Courage: {self.selected_cat.courage}\nCompassion: {self.selected_cat.compassion} \nIntelligence: {self.selected_cat.intelligence} \nEmpathy: {self.selected_cat.empathy}"

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(
                stats,
                ui_scale(pygame.Rect((580, 162), (105, 125))),
                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                manager=MANAGER,
            )

            name = str(self.selected_cat.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + "..."
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                ui_scale(pygame.Rect((445, 115), (110, 30))),
                name,
                object_id="#text_box_34_horizcenter",
                manager=MANAGER,
            )

    def update_cat_list(self):
        """Updates the cat sprite buttons."""
        valid_mentors = self.chunks(self.get_valid_cats(), 15)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_mentors):
            self.list_page = len(valid_mentors)

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
        if valid_mentors:
            display_cats = valid_mentors[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for marker in self.fav:
            self.fav[marker].kill()
        self.fav = {}

        pos_x = 0
        pos_y = 20
        i = 0
        for cat in display_cats:
            if get_clan_setting("show fav") and cat.favourite != 0:
                self.fav[str(i)] = pygame_gui.elements.UIImage(
                    ui_scale(pygame.Rect((100 + pos_x, 350 + pos_y), (50, 50))),
                    pygame.transform.scale(
                        pygame.image.load(
                            f"resources/images/fav_marker_{cat.favourite}.png"
                        ).convert_alpha(),
                        (50, 50),
                    ),
                )
                self.fav[str(i)].disable()
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                ui_scale(pygame.Rect((100 + pos_x, 350 + pos_y), (50, 50))),
                cat.sprite,
                cat_object=cat,
                manager=MANAGER,
            )
            pos_x += 60
            if pos_x >= 262:
                pos_x = 0
                pos_y += 60
            i += 1

    def get_valid_cats(self):
        """Get a list of valid mates for the current cat"""

        # Behold! The uglest list comprehension ever created!
        valid_mates = [
            i
            for i in Cat.all_cats_list
            if not i.faded
            and i.moons >= 1
            and i.moons < 6
            and i.status.alive_in_player_clan
        ]

        return valid_mates

    def on_use(self):
        super().on_use()

    def chunks(self, L, n):
        return [L[x : x + n] for x in range(0, len(L), n)]
