import pygame.transform
import pygame_gui.elements
from random import choice, randint
import math
import re
import i18n
from scripts.game_structure import constants
from scripts.cat.pelts import Pelt
from ..cat.enums import CatGroup
from scripts.cat.sprites.display_sprites import generate_sprite


from .Screens import Screens

from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale, ui_scale_dimensions
from ..events_module.text_adjust import pronoun_repl

from scripts.cat.cats import Cat
from scripts.cat.sprites.load_sprites import sprites
from scripts.game_structure import image_cache
from scripts.game_structure import game

from ..ui.elements.image_button import UIImageButton
from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.elements.sprite_button import UISpriteButton

from ..ui.generate_box import BoxStyles, get_box
from scripts.game_structure.screen_settings import MANAGER
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon
from scripts.screens.enums import GameScreen
from scripts.game_structure.game.settings import game_setting_get
from scripts.game_structure.localization import load_lang_resource
from scripts.lifegen_utility import get_cluster


ACC_REACTION_TXT = load_lang_resource("events/lifegen_events/gift.json")
ACC_REACTION = load_lang_resource("accessory_preferences.json")


class GiftScreen(Screens):
    selected_cat = None
    current_page = 1
    list_frame = None
    apprentice_details = {}
    selected_details = {}
    selected_acc_details = {}
    cat_list_buttons = {}
    stage = "choose gift cat"

    def __init__(self, name=None):
        super().__init__(name)
        self.list_page = None
        self.next_cat = None
        self.previous_cat = None
        self.next_page_button = None
        self.previous_page_button = None
        self.select_button = None
        self.gift_again_button = None
        self.back_button = None
        self.mentor_frame = None
        self.reaction_box = None
        self.reaction_icon = None
        self.reaction_text = None
        self.reaction = None
        self.info = None
        self.heading = None
        self.the_cat = None
        self.next = None
        self.screen_art = None
        self.page = 0
        self.max_pages = 1
        self.search_bar_image = None
        self.search_bar = None
        self.previous_page_button = None
        self.next_page_button = None
        self.accessory_tab_button = None
        self.previous_search_text = "search"
        self.cat_list_buttons = {}
        self.search_inventory = []
        self.accessory_buttons = {}
        self.selected_accessory = None
        self.cat_sprite = None

        if game_setting_get("lifegen_sprite_changes"):
            self.all_accs = Pelt.all_lifegen_accessories
        else:
            self.all_accs = Pelt.all_clangen_accessories

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()

            elif event.ui_element in self.accessory_buttons.values():
                self.selected_accessory = event.ui_element
                self.update_selected_accessory()

            elif (
                event.ui_element == self.select_button
                and self.selected_cat
                and self.stage == "choose gift cat"
            ):
                if not self.selected_cat.dead:
                    self.exit_screen()
                    self.stage = "choose gift"
                    self.screen_switches()
                    self.update_selected_cat()

            elif (
                event.ui_element == self.select_button
                and self.selected_accessory
                and self.stage == "choose gift"
            ):
                self.exit_screen()
                self.stage = "gift reaction"
                self.screen_switches()
                self.update_selected_cat()

            elif event.ui_element == self.back_button:
                self.change_screen(GameScreen.PROFILE)
                self.stage = "choose gift cat"
            elif (
                event.ui_element == self.gift_again_button
                and self.stage == "gift reaction"
            ):
                self.exit_screen()
                self.stage = "choose gift cat"
                self.screen_switches()
                self.selected_cat = None
                self.selected_accessory = None
                self.cat_sprite = None

            elif event.ui_element == self.next_page_button:
                if self.stage == "choose gift cat":
                    self.current_page += 1
                    self.update_cat_list()
                    self.update_selected_cat()
                elif self.stage == "choose gift":
                    self.page += 1

                    if self.page == 0 and self.max_pages in [0, 1]:
                        self.previous_page_button.disable()
                        self.next_page_button.disable()
                    elif self.page == 0:
                        self.previous_page_button.disable()
                        self.next_page_button.enable()
                    elif self.page == self.max_pages - 1:
                        self.previous_page_button.enable()
                        self.next_page_button.disable()
                    else:
                        self.previous_page_button.enable()
                        self.next_page_button.enable()
                    for i in self.cat_list_buttons:
                        self.cat_list_buttons[i].kill()
                    for i in self.accessory_buttons:
                        self.accessory_buttons[i].kill()
                    self.update_accessory_list()
            elif event.ui_element == self.previous_page_button:
                if self.stage == "choose gift cat":
                    self.current_page -= 1
                    self.update_cat_list()

                elif self.stage == "choose gift":
                    self.page -= 1
                    if self.page == 0 and self.max_pages in [0, 1]:
                        self.previous_page_button.disable()
                        self.next_page_button.disable()
                    elif self.page == 0:
                        self.previous_page_button.disable()
                        self.next_page_button.enable()
                    elif self.page == self.max_pages - 1:
                        self.previous_page_button.enable()
                        self.next_page_button.disable()
                    else:
                        self.previous_page_button.enable()
                        self.next_page_button.enable()
                    for i in self.cat_list_buttons:
                        self.cat_list_buttons[i].kill()
                    for i in self.accessory_buttons:
                        self.accessory_buttons[i].kill()
                    self.update_accessory_list()

    def screen_switches(self):
        super().screen_switches()

        list_frame = get_box(BoxStyles.ROUNDED_BOX, (650, 226))
        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((75, 360), (650, 226))), list_frame, starting_height=1
        )
        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (105, 30))),
            "buttons.back",
            get_button_dict(ButtonStyles.SQUOVAL, (105, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )

        if self.stage == "choose gift cat":
            self.the_cat = game.clan.your_cat
            self.selected_cat = None
            self.selected_accessory = None
            self.screen_art = None
            self.reaction_text = None
            self.reaction = None
            self.reaction_icon = None

            self.heading = pygame_gui.elements.UITextBox(
                "Choose who to gift",
                ui_scale(pygame.Rect((150, 25), (500, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )
            self.mentor_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((90, 90), (172, 200))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_frame.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )

            self.reaction_box = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((280, 245), (250, 75))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_reaction_frame.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )

            self.screen_art = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((550, 95), (170, 197))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_artwork.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )

            self.select_button = UIImageButton(
                ui_scale(pygame.Rect((125, 305), (104, 26))),
                "",
                object_id="#gift_select_button",
            )
            self.gift_again_button = UIImageButton(
                ui_scale(pygame.Rect((580, 305), (104, 26))),
                "",
                object_id="#gift_again_button",
            )

            self.previous_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((315, 579), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )
            self.next_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((451, 579), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                starting_height=0,
            )

            self.update_selected_cat()  # Updates the image and details of selected cat
            self.update_cat_list()
            self.gift_again_button.disable()
        elif self.stage == "choose gift":
            self.selected_accessory = None
            self.the_cat = game.clan.your_cat
            self.screen_art = None
            self.reaction_text = None
            self.reaction = None
            self.reaction_icon = None

            self.heading = pygame_gui.elements.UITextBox(
                "Choose what to gift",
                ui_scale(pygame.Rect((150, 25), (500, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )

            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((90, 90), (172, 200))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_frame.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )

            self.reaction_box = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((280, 245), (250, 75))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_reaction_frame.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )
            self.screen_art = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((550, 95), (170, 197))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_artwork.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )
            self.select_button = UIImageButton(
                ui_scale(pygame.Rect((125, 305), (104, 26))),
                "",
                object_id="#give_gift_button",
            )
            self.gift_again_button = UIImageButton(
                ui_scale(pygame.Rect((580, 305), (104, 26))),
                "",
                object_id="#gift_again_button",
            )
            self.previous_page_button = UIImageButton(
                ui_scale(pygame.Rect((315, 576), (34, 34))),
                "",
                object_id="#relation_list_previous",
                manager=MANAGER,
            )
            self.next_page_button = UIImageButton(
                ui_scale(pygame.Rect((451, 576), (34, 34))),
                "",
                object_id="#relation_list_next",
                manager=MANAGER,
            )
            self.search_bar_image = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((109, 340), (118, 34))),
                pygame.image.load("resources/images/search_bar.png").convert_alpha(),
                manager=MANAGER,
            )
            self.search_bar = pygame_gui.elements.UITextEntryLine(
                ui_scale(pygame.Rect((120, 342), (102, 27))),
                object_id="#search_entry_box",
                initial_text="search",
                manager=MANAGER,
            )

            self.update_selected_cat()  # Updates the image and details of selected cat
            self.update_selected_accessory()
            self.update_accessory_list()
            self.gift_again_button.disable()
        elif self.stage == "gift reaction":
            self.the_cat = game.clan.your_cat

            self.heading = pygame_gui.elements.UITextBox(
                "Choose what to gift",
                ui_scale(pygame.Rect((150, 25), (500, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER,
            )

            self.mentor_frame = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((90, 90), (172, 200))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_frame.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )
            self.screen_art = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((550, 95), (170, 197))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_artwork.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )

            reaction_txt, reaction, acc = self.gift_acc()

            self.reaction_text = pygame_gui.elements.UITextBox(
                self.adjust_txt(reaction_txt),
                ui_scale(pygame.Rect((290, 250), (230, 60))),
                object_id=get_text_box_theme(
                    "#text_box_22_horizcenter_vertcenter_spacing_95"
                ),
                manager=MANAGER,
            )

            icon_png = ""
            pos = False
            neutral = False
            neg = False

            if reaction in ["accept_like", "accept_favourite"]:
                icon_png = "giftreaction_pos"
                pos = True
            elif reaction in ["accept_neutral", "already_have"]:
                icon_png = "giftreaction_neutral"
                neutral = True
            elif reaction in ["accept_dislike"]:
                icon_png = "giftreaction_neg"
                neg = True

            result = self.get_reaction_display(pos, neutral, neg)
            self.relationship_changes(reaction)

            self.reaction_icon = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((325, 327), (20, 20))),
                pygame.transform.scale(
                    image_cache.load_image(
                        f"resources/images/{icon_png}.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )

            self.reaction = pygame_gui.elements.UITextBox(
                result,
                ui_scale(pygame.Rect((350, 325), (230, 25))),
                object_id=get_text_box_theme("#text_box_22_horizleft"),
                manager=MANAGER,
            )

            self.reaction_box = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((280, 245), (250, 75))),
                pygame.transform.scale(
                    image_cache.load_image(
                        "resources/images/gift_reaction_frame.png"
                    ).convert_alpha(),
                    (569, 399),
                ),
                manager=MANAGER,
            )

            self.select_button = UIImageButton(
                ui_scale(pygame.Rect((125, 305), (104, 26))),
                "",
                object_id="#give_gift_button",
            )
            self.gift_again_button = UIImageButton(
                ui_scale(pygame.Rect((580, 305), (104, 26))),
                "",
                object_id="#gift_again_button",
            )
            self.previous_page_button = UIImageButton(
                ui_scale(pygame.Rect((315, 572), (34, 34))),
                "",
                object_id="#relation_list_previous",
                manager=MANAGER,
            )
            self.next_page_button = UIImageButton(
                ui_scale(pygame.Rect((451, 572), (34, 34))),
                "",
                object_id="#relation_list_next",
                manager=MANAGER,
            )
            self.search_bar_image = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((109, 340), (118, 34))),
                pygame.image.load("resources/images/search_bar.png").convert_alpha(),
                manager=MANAGER,
            )
            self.search_bar = pygame_gui.elements.UITextEntryLine(
                ui_scale(pygame.Rect((120, 342), (102, 27))),
                object_id="#search_entry_box",
                initial_text="search",
                manager=MANAGER,
            )

            self.update_selected_accessory()
            self.select_button.disable()
            self.gift_again_button.enable()

    def exit_screen(self):
        # self.selected_accessory = None
        self.previous_search_text = "search"

        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for ele in self.apprentice_details:
            self.apprentice_details[ele].kill()
        self.apprentice_details = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        for ele in self.selected_acc_details:
            self.selected_acc_details[ele].kill()
        self.selected_acc_details = {}

        for ele in self.accessory_buttons:
            self.accessory_buttons[ele].kill()
        self.accessory_buttons = {}

        self.list_frame.kill()

        if self.heading:
            self.heading.kill()
            del self.heading

        if self.screen_art:
            self.screen_art.kill()
            del self.screen_art

        if self.mentor_frame:
            self.mentor_frame.kill()
            del self.mentor_frame

        if self.reaction_box:
            self.reaction_box.kill()
            del self.reaction_box

        if self.reaction_icon:
            self.reaction_icon.kill()
            del self.reaction_icon

        if self.reaction_text:
            self.reaction_text.kill()
            del self.reaction_text

        if self.reaction:
            self.reaction.kill()
            del self.reaction

        if self.back_button:
            self.back_button.kill()
            del self.back_button

        if self.select_button:
            self.select_button.kill()
            del self.select_button

        if self.gift_again_button:
            self.gift_again_button.kill()
            del self.gift_again_button

        if self.previous_page_button:
            self.previous_page_button.kill()
            del self.previous_page_button

        if self.next_page_button:
            self.next_page_button.kill()
            del self.next_page_button

        if self.search_bar_image:
            self.search_bar_image.kill()

        if self.search_bar:
            self.search_bar.kill()

        if self.next:
            self.next.kill()
            del self.next

    def find_next_previous_cats(self):
        """Determines where the previous and next buttons lead"""
        is_instructor = False
        if self.the_cat.dead and game.clan.instructor.ID == self.the_cat.ID:
            is_instructor = True

        self.previous_cat = 0
        self.next_cat = 0
        if self.the_cat.dead and not is_instructor and not self.the_cat.df:
            self.previous_cat = game.clan.instructor.ID

        if is_instructor:
            self.next_cat = 1

        for check_cat in Cat.all_cats_list:
            if check_cat.ID == self.the_cat.ID:
                self.next_cat = 1

            if (
                self.next_cat == 0
                and check_cat.ID != self.the_cat.ID
                and check_cat.dead == self.the_cat.dead
                and check_cat.ID != game.clan.instructor.ID
                and not check_cat.status.is_exiled(CatGroup.PLAYER_CLAN)
                and check_cat.status
                in [
                    "apprentice",
                    "medicine cat apprentice",
                    "mediator apprentice",
                    "queen's apprentice",
                ]
                and check_cat.df == self.the_cat.df
            ):
                self.previous_cat = check_cat.ID

            elif (
                self.next_cat == 1
                and check_cat.ID != self.the_cat.ID
                and check_cat.dead == self.the_cat.dead
                and check_cat.ID != game.clan.instructor.ID
                and not check_cat.status.is_exiled(CatGroup.PLAYER_CLAN)
                and check_cat.status
                in [
                    "apprentice",
                    "medicine cat apprentice",
                    "mediator apprentice",
                    "queen's apprentice",
                ]
                and check_cat.df == self.the_cat.df
            ):
                self.next_cat = check_cat.ID

            elif int(self.next_cat) > 1:
                break

        if self.next_cat == 1:
            self.next_cat = 0

    def relationship_changes(self, reaction):
        """Handles changing the cats' feelings towards you depending on their reaction to the gift."""
        cat = self.selected_cat
        you = game.clan.your_cat
        neutral = False
        pos = False
        neg = False

        # make sure the relationship exists, then apply the reaction to it
        if you.ID not in cat.relationships:
            cat.create_one_relationship(you)

        if reaction == "already_have":
            cat.relationships[you.ID].like += randint(0, 5)
            neutral = True
        elif reaction == "accept_like":
            cat.relationships[you.ID].like += randint(3, 10)
            pos = True
        elif reaction == "accept_dislike":
            cat.relationships[you.ID].like -= randint(3, 8)
            neg = True
        elif reaction == "accept_neutral":
            neutral = True
        elif reaction == "accept_favourite":
            pos = True
            cat.relationships[you.ID].like += randint(10, 30)

    def get_reaction_display(self, pos, neutral, neg):
        """Display text for relationship changes"""
        output = ""
        if pos:
            output = "Gained platonic like!"
        elif neutral:
            output = "Feelings unchanged."
        elif neg:
            output = "Gained dislike!"

        return output

    def gift_acc(self):
        """Gives the accessory!"""
        acc = self.selected_accessory.tool_tip_text
        cluster1, cluster2 = get_cluster(self.selected_cat.personality.trait)
        reaction_txt = ""
        if cluster1 and cluster2:
            cluster = choice([cluster1, cluster2])
        else:
            cluster = cluster1

        reaction = "accept_neutral"
        if acc in self.selected_cat.pelt.inventory:
            reaction = "already_have"
        elif acc in ACC_REACTION[cluster1]["like"] or (
            cluster2 and acc in ACC_REACTION[cluster2]["like"]
        ):
            reaction = "accept_like"
        elif acc in ACC_REACTION[cluster1]["dislike"] or (
            cluster2 and acc in ACC_REACTION[cluster2]["dislike"]
        ):
            reaction = "accept_dislike"

        if self.selected_cat.personality.trait in ACC_REACTION["favourites"]:
            if acc in ACC_REACTION["favourites"][self.selected_cat.personality.trait]:
                reaction = "accept_favourite"

        if reaction != "already_have":
            game.clan.your_cat.pelt.inventory.remove(acc)
            if acc in game.clan.your_cat.pelt.accessory:
                game.clan.your_cat.pelt.accessory = tuple(
                    a for a in game.clan.your_cat.pelt.accessory if a != acc
                )
            self.selected_cat.pelt.inventory.append(acc)
            if (
                acc in ACC_REACTION[cluster1]["like"]
                or (cluster2 and acc in ACC_REACTION[cluster2]["like"])
            ) or reaction == "accept_favourite":
                if len(self.selected_cat.pelt.accessory) <= 4:
                    self.selected_cat.pelt.accessory = (
                        self.selected_cat.pelt.accessory + (acc,)
                    )
                    self.update_selected_cat()

        if (
            acc in ACC_REACTION_TXT["unique_gifts"].keys()
            and reaction in ACC_REACTION_TXT["unique_gifts"][acc].keys()
        ):
            reaction_txt = ACC_REACTION_TXT["unique_gifts"][acc][reaction]
        else:
            reaction_txt = choice(
                ACC_REACTION_TXT["general"][reaction]
                + ACC_REACTION_TXT[cluster][reaction]
            )

        return reaction_txt, reaction, acc

    def get_acc_name(self, acc, count=1):
        acc_name = str(i18n.t(f"cat.accessories.{acc}", count=count))
        if acc in Pelt.collar_accessories:
            for style_type in sprites.COLLAR_DATA["style_data"]:
                for style, color_list in style_type.items():
                    for colour in color_list:
                        if f"{style}_{colour}" == acc:
                            if "colorful" in acc:
                                acc_name = str(
                                    i18n.t(f"cat.accessories.{style}", count=count)
                                )
                            else:
                                acc_name = str(
                                    colour.replace("_", " ")
                                    + " "
                                    + i18n.t(f"cat.accessories.{style}", count=count)
                                )
                            return acc_name
        return acc_name

    def adjust_txt(self, txt):
        process_text_dict = {}

        process_text_dict["y_c"] = (
            game.clan.your_cat,
            choice(game.clan.your_cat.pronouns),
        )
        process_text_dict["t_c"] = (
            self.selected_cat,
            choice(self.selected_cat.pronouns),
        )

        txt = re.sub(
            r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), txt
        )

        txt = txt.replace("y_c", str(game.clan.your_cat.name))
        txt = txt.replace("t_c", str(self.selected_cat.name))
        txt = txt.replace(
            "y_g",
            str(self.get_acc_name(self.selected_accessory.tool_tip_text, count=0)),
        )
        return txt

    def update_selected_cat(self):
        """Updates the image and information on the currently selected cat"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat:
            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((280, 97), (135, 135))),
                pygame.transform.scale(self.selected_cat.sprite, (135, 135)),
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

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((430, 112), (105, 125))),
                object_id=get_text_box_theme("#text_box_22_horizleft"),
                manager=MANAGER,
            )

            name = str(self.selected_cat.name)  # get name
            if 45 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + "..."

            self.selected_details["cat_name"] = pygame_gui.elements.UITextBox(
                name,
                ui_scale(pygame.Rect((150, 65), (500, 40))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
            )

    def update_selected_accessory(self):
        """Updates the image and information on the currently selected accessory"""
        for ele in self.selected_acc_details:
            self.selected_acc_details[ele].kill()

        self.selected_acc_details = {}
        if self.selected_accessory:
            cat = game.clan.your_cat
            accessory = self.selected_accessory.tool_tip_text

            x_pos = 101
            y_pos = 129

            if accessory in self.all_accs:
                acc_sprite = generate_sprite(
                    self.the_cat, only_accessory=True, accessory_to_render=accessory
                )

                self.selected_acc_details[
                    "selected_image"
                ] = pygame_gui.elements.UIImage(
                    ui_scale(pygame.Rect((x_pos, y_pos), (150, 150))),
                    pygame.transform.scale(acc_sprite, ui_scale_dimensions((150, 150))),
                    manager=MANAGER,
                )

            info = ""
            if (
                self.selected_accessory.tool_tip_text
                in game.clan.your_cat.pelt.accessory
            ):
                info = "\ncurrently worn"

            self.selected_acc_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((97, 52), (150, 40))),
                object_id=get_text_box_theme(
                    "#text_box_22_horizcenter_vertcenter_spacing_95"
                ),
                manager=MANAGER,
            )

            accname = self.get_acc_name(self.selected_accessory.tool_tip_text, count=1)
            if 13 <= len(accname):  # check name length
                short_name = str(accname)[0:9]
                accname = short_name + "..."

            self.selected_acc_details["acc name"] = pygame_gui.elements.UITextBox(
                accname,
                ui_scale(pygame.Rect((110, 88), (145, 40))),
                object_id="#text_box_34_horizcenter",
                manager=MANAGER,
            )

    def update_cat_list(self):
        """Updates the cat sprite buttons."""
        valid_cats = self.chunks(self.get_valid_cats(), 30)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_cats):
            self.list_page = len(valid_cats)

        # Handle which next buttons are clickable.
        if len(valid_cats) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_cats):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_cats) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_cats = []
        if valid_cats:
            display_cats = valid_cats[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        pos_x = 0
        pos_y = 20
        i = 0
        for cat in display_cats:
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))),
                cat.sprite,
                cat_object=cat,
                manager=MANAGER,
            )
            pos_x += 60
            if pos_x >= 550:
                pos_x = 0
                pos_y += 60
            i += 1

    def update_accessory_list(self):
        """Updates the cat sprite buttons."""
        cat = self.the_cat
        age = cat.age
        # self.cat_sprite = str(cat.pelt.cat_sprites[cat.age])

        # setting the cat_sprite (bc this makes things much easier)
        # if cat.not_working() and age != 'newborn' and constants.CONFIG['cat_sprites']['sick_sprites']:
        #     if age in ['kitten', 'adolescent']:
        #         self.cat_sprite = str(19)
        #     else:
        #         self.cat_sprite = str(18)
        if cat.pelt.paralyzed and age != "newborn":
            if age in ["kitten", "adolescent"]:
                self.cat_sprite = str(17)
            else:
                if cat.pelt.length == "long":
                    self.cat_sprite = str(16)
                else:
                    self.cat_sprite = str(15)
        else:
            if age == "elder" and not constants.CONFIG["fun"]["all_cats_are_newborn"]:
                age = "senior"

            if constants.CONFIG["fun"]["all_cats_are_newborn"]:
                self.cat_sprite = str(cat.pelt.cat_sprites["newborn"])
            else:
                self.cat_sprite = str(cat.pelt.cat_sprites[age])

        pos_x = 10
        pos_y = 125
        i = 0

        self.cat_list_buttons = {}
        self.accessory_buttons = {}
        self.accessories_list = []
        start_index = self.page * 30
        end_index = start_index + 30

        for acc in cat.pelt.accessory:
            if acc not in cat.pelt.inventory:
                cat.pelt.inventory.append(acc)

        inventory_len = 0
        new_inv = []
        if self.search_bar.get_text() in ["", "search"]:
            inventory_len = len(cat.pelt.inventory)
            new_inv = cat.pelt.inventory
        else:
            for ac in cat.pelt.inventory:
                if self.search_bar.get_text().lower() in ac.lower():
                    inventory_len += 1
                    new_inv.append(ac)
        self.max_pages = math.ceil(inventory_len / 30)

        if self.max_pages == 1 or self.max_pages == 0:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        if self.page == 0:
            self.previous_page_button.disable()
        if cat.pelt.inventory:
            for a, accessory in enumerate(
                new_inv[start_index : min(end_index, inventory_len)], start=start_index
            ):
                try:
                    if (
                        self.search_bar.get_text() in ["", "search"]
                        or self.search_bar.get_text().lower() in accessory.lower()
                    ):
                        self.accessory_buttons[str(i)] = UIImageButton(
                            ui_scale(pygame.Rect((100 + pos_x, 250 + pos_y), (50, 50))),
                            "",
                            tool_tip_text=accessory,
                            object_id="#blank_button",
                        )
                        if accessory in self.all_accs:
                            acc_sprite = generate_sprite(
                                self.the_cat,
                                only_accessory=True,
                                accessory_to_render=accessory,
                            )

                            self.cat_list_buttons[
                                "cat" + str(i)
                            ] = pygame_gui.elements.UIImage(
                                ui_scale(
                                    pygame.Rect((100 + pos_x, 250 + pos_y), (50, 50))
                                ),
                                acc_sprite,
                                manager=MANAGER,
                            )

                        pos_x += 60
                        if pos_x >= 600:
                            pos_x = 0
                            pos_y += 60
                        i += 1
                except:
                    continue

    def get_valid_cats(self):
        valid_cats = []

        for cat in Cat.all_cats_list:
            if (
                not cat.dead
                and not cat.status.is_outsider
                and not cat.ID == game.clan.your_cat.ID
                and not cat.moons == 0
            ):
                valid_cats.append(cat)

        return valid_cats

    def on_use(self):
        super().on_use()
        if self.search_bar and self.stage == "choose gift":
            if self.search_bar.is_focused and self.search_bar.get_text() == "search":
                self.search_bar.set_text("")
                self.page = 0
                if self.page == 0 and (self.max_pages == 1 or self.max_pages == 0):
                    self.previous_page_button.disable()
                    self.next_page_button.disable()
                elif self.page == 0:
                    self.previous_page_button.disable()
                    self.next_page_button.enable()
                elif self.page == self.max_pages - 1:
                    self.previous_page_button.enable()
                    self.next_page_button.disable()
                else:
                    self.previous_page_button.enable()
                    self.next_page_button.enable()
            elif self.search_bar.get_text() != self.previous_search_text:
                self.page = 0
                if self.cat_list_buttons:
                    for i in self.cat_list_buttons:
                        self.cat_list_buttons[i].kill()
                    for i in self.accessory_buttons:
                        self.accessory_buttons[i].kill()

                self.update_accessory_list()

                if self.page == 0 and self.max_pages in [0, 1]:
                    self.previous_page_button.disable()
                    self.next_page_button.disable()
                elif self.page == 0:
                    self.previous_page_button.disable()
                    self.next_page_button.enable()
                elif self.page == self.max_pages - 1:
                    self.previous_page_button.enable()
                    self.next_page_button.disable()
                else:
                    self.previous_page_button.enable()
                    self.next_page_button.enable()
                self.previous_search_text = self.search_bar.get_text()

    def chunks(self, L, n):
        return [L[x : x + n] for x in range(0, len(L), n)]
