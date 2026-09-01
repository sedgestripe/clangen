import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson
import re
from scripts.event_class import Single_Event
from .Screens import Screens
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure import game
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.localization import load_lang_resource
from ..ui.elements.image_button import UIImageButton
from ..ui.elements.surface_image_button import UISurfaceImageButton
from ..ui.elements.sprite_button import UISpriteButton
from scripts.clan_package.settings import get_clan_setting
from scripts.screens.enums import GameScreen

from ..cat.enums import CatRank

from scripts.game_structure import constants

from scripts.ui.theme import get_text_box_theme
from scripts.ui.scale import ui_scale
from scripts.events_module.text_adjust import pronoun_repl
from scripts.clan_package.get_clan_cats import find_alive_cats_with_rank


from ..ui.generate_box import get_box, BoxStyles
from ..ui.generate_button import get_button_dict, ButtonStyles
from ..ui.icon import Icon


class AffairScreen(Screens):
    selected_cat = None
    current_page = 1
    list_frame = None
    apprentice_details = {}
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
        self.affair_screen = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()
            elif event.ui_element == self.confirm_mentor and self.selected_cat:
                if self.selected_cat.status.alive_in_player_clan:
                    self.update_selected_cat()
                    self.change_cat(self.selected_cat)
                    # resetting selected cat so theyre not still in the box when reentering the affair screen next moon
                    self.selected_cat = None
            elif event.ui_element == self.back_button:
                self.change_screen(GameScreen.PROFILE)
            elif event.ui_element == self.next_page_button:
                self.current_page += 1
                self.update_cat_list()
            elif event.ui_element == self.previous_page_button:
                self.current_page -= 1
                self.update_cat_list()

    def screen_switches(self):
        super().screen_switches()
        self.the_cat = game.clan.your_cat

        list_frame = get_box(BoxStyles.ROUNDED_BOX, (650, 226))
        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((75, 360), (650, 226))), list_frame, starting_height=1
        )

        self.heading = pygame_gui.elements.UITextBox(
            "",
            ui_scale(pygame.Rect((150, 25), (500, 40))),
            object_id=get_text_box_theme("#text_box_34_horizcenter"),
            manager=MANAGER,
        )

        self.mentor_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((100, 108), (298, 220))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/affair_select.png"
                ).convert_alpha(),
                (298, 220),
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
        self.confirm_mentor = UIImageButton(
            ui_scale(pygame.Rect((150, 302), (104, 26))),
            "select",
            object_id="#patrol_select_button",
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
        self.affair_screen = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((425, 65), (222, 273))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/affair_screen.png"
                ).convert_alpha(),
                (496, 420),
            ),
            manager=MANAGER,
        )

        self.update_selected_cat()
        self.update_cat_list()

    def exit_screen(self):
        self.current_page = 1

        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for marker in self.fav:
            self.fav[marker].kill()
        self.fav = {}

        for ele in self.apprentice_details:
            self.apprentice_details[ele].kill()
        self.apprentice_details = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        self.heading.kill()
        del self.heading

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

        if self.affair_screen:
            self.affair_screen.kill()

        if self.list_frame:
            self.list_frame.kill()
            del self.list_frame

    def change_cat(self, affair_cat=None):
        game.clan.affair = True
        self.mu_txt = load_lang_resource("events/lifegen_events/affair.json")
        success = self.is_success(affair_cat)
        affair_relationship_chance_lb = constants.CONFIG["lifegen"]["gen"][
            "affair_relationship_change_lb"
        ]
        affair_relationship_chance_ub = constants.CONFIG["lifegen"]["gen"][
            "affair_relationship_change_ub"
        ]
        if success:
            affair_cat.relationships.get(game.clan.your_cat.ID).like += randint(
                affair_relationship_chance_lb, affair_relationship_chance_ub
            )
            affair_cat.relationships.get(game.clan.your_cat.ID).comfort += randint(
                affair_relationship_chance_lb, affair_relationship_chance_ub
            )
            affair_cat.relationships.get(game.clan.your_cat.ID).romance += randint(
                affair_relationship_chance_lb, affair_relationship_chance_ub
            )
            game.clan.your_cat.relationships.get(affair_cat.ID).romance += randint(
                affair_relationship_chance_lb, affair_relationship_chance_ub
            )
            ceremony_txt = self.adjust_txt(choice(self.mu_txt["success"]), affair_cat)
            game.cur_events_list.insert(0, Single_Event(ceremony_txt))
            if (
                randint(
                    1,
                    constants.CONFIG["lifegen"]["gen"][
                        "affair_success_pregnancy_chance"
                    ],
                )
                == 1
            ):
                Pregnancy_Events.handle_zero_moon_pregnant(
                    game.clan.your_cat, affair_cat, game.clan
                )
        else:
            ceremony_txt = self.adjust_txt(choice(self.mu_txt["fail"]), affair_cat)
            game.cur_events_list.insert(0, Single_Event(ceremony_txt))
            if self.get_fail_consequence() == 0:
                ceremony_txt = self.adjust_txt(
                    choice(self.mu_txt["fail breakup"]), affair_cat
                )
                for i in list(game.clan.your_cat.mate):
                    mate = Cat.fetch_cat(i)
                    if mate is None:
                        continue
                    mate.get_ill("heartbroken")
                    mate.unset_mate(game.clan.your_cat)
                    rel = mate.relationships.get(game.clan.your_cat.ID)
                    if rel is None:
                        continue
                    rel.like -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )
                    rel.comfort -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )
                    rel.trust -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )
                    rel.romance -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )
                game.cur_events_list.insert(1, Single_Event(ceremony_txt))
            else:
                ceremony_txt = self.adjust_txt(
                    choice(self.mu_txt["fail none"]), affair_cat
                )
                game.cur_events_list.insert(1, Single_Event(ceremony_txt))
                for i in game.clan.your_cat.mate:
                    mate = Cat.fetch_cat(i)
                    if mate is None:
                        continue
                    rel = mate.relationships.get(game.clan.your_cat.ID)
                    if rel is None:
                        continue
                    rel.like -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )
                    rel.comfort -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )
                    rel.trust -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )
                    rel.romance -= randint(
                        affair_relationship_chance_lb, affair_relationship_chance_ub
                    )

        self.change_screen(GameScreen.EVENTS)

    def is_success(self, affair_cat):
        """Calculates affair success rate based on relationships"""
        chance = constants.CONFIG["lifegen"]["gen"]["affair_success_chance"]
        for i in game.clan.your_cat.mate:
            mate = Cat.fetch_cat(i)
            if mate is None or not mate.status.alive_in_player_clan:
                continue
            rel = mate.relationships.get(game.clan.your_cat.ID)
            if rel is None:
                continue
            if rel.romance > 50:
                chance -= 5
            elif rel.romance < 10:
                chance += 5
            if rel.comfort > 50:
                chance -= 5
            elif rel.comfort < 10:
                chance += 5
            if rel.trust > 50:
                chance -= 5
            elif rel.trust < 10:
                chance += 5
        affair_rel = affair_cat.relationships.get(game.clan.your_cat.ID)
        if affair_rel is not None:
            if affair_rel.like < -10:
                chance += 10
            if affair_rel.romance > 20:
                chance -= 10
            elif affair_rel.romance < 10:
                chance += 10
            if affair_rel.comfort > 20:
                chance -= 10
            elif affair_rel.comfort < 10:
                chance += 10
            if affair_rel.trust > 20:
                chance -= 10
            elif affair_rel.trust < 10:
                chance += 10
        if chance < 1:
            chance = 1
        if randint(1, 100) < randint(0, max(0, chance + randint(-10, 10))):
            return True
        return False

    def get_fail_consequence(self):
        return randint(0, 1)

    def adjust_txt(self, txt, affair_cat):
        mate_options = [
            mate
            for mate in game.clan.your_cat.mate
            if Cat.fetch_cat(mate) and Cat.fetch_cat(mate).status.alive_in_player_clan
        ]
        if not mate_options:
            # fall back to any mate that can still be fetched
            mate_options = [
                mate for mate in game.clan.your_cat.mate if Cat.fetch_cat(mate)
            ]
        random_mate = (
            Cat.fetch_cat(choice(mate_options)) if mate_options else affair_cat
        )

        warriors = find_alive_cats_with_rank(Cat, [CatRank.WARRIOR])
        if warriors:
            random_warrior = Cat.fetch_cat(choice(warriors))

            counter = 0
            while (
                not random_warrior.status.alive_in_player_clan
                or random_warrior.ID == affair_cat.ID
                or random_warrior.ID in game.clan.your_cat.mate
                or random_warrior.ID == game.clan.your_cat.ID
            ):
                random_warrior = Cat.fetch_cat(choice(game.clan.clan_cats))
                counter += 1
                if counter > 30:
                    break

        process_text_dict = {}

        process_text_dict["y_c"] = (
            game.clan.your_cat,
            choice(game.clan.your_cat.pronouns),
        )
        process_text_dict["a_n"] = (affair_cat, choice(affair_cat.pronouns))
        process_text_dict["m_n"] = (random_mate, choice(random_mate.pronouns))
        if random_warrior:
            process_text_dict["r_w"] = (random_warrior, choice(random_warrior.pronouns))

        txt = re.sub(
            r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), txt
        )

        txt = txt.replace("a_n", str(affair_cat.name))
        txt = txt.replace("m_n", str(random_mate.name))
        if random_warrior:
            txt = txt.replace("r_w", str(random_warrior.name))
        return txt

    def update_selected_cat(self):
        """Updates the image and information on the currently selected mentor"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat:
            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((140, 150), (135, 135))),
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
                + self.selected_cat.skills.skill_string(short=True)
            )

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                ui_scale(pygame.Rect((285, 162), (105, 125))),
                object_id="#text_box_22_horizcenter_vertcenter_spacing_95",
                manager=MANAGER,
            )

            name = str(self.selected_cat.name)  # get name
            if 11 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + "..."
            self.selected_details["mentor_name"] = pygame_gui.elements.ui_label.UILabel(
                ui_scale(pygame.Rect((145, 115), (110, 30))),
                name,
                object_id="#text_box_34_horizcenter",
                manager=MANAGER,
            )

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
                    ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))),
                    pygame.transform.scale(
                        pygame.image.load(
                            f"resources/images/fav_marker_{cat.favourite}.png"
                        ).convert_alpha(),
                        (50, 50),
                    ),
                )
                self.fav[str(i)].disable()
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

    def get_valid_cats(self):
        """Get a list of valid mates for the current cat"""

        valid_mates = [
            i
            for i in Cat.all_cats_list
            if not i.faded
            and self.the_cat.is_potential_mate(
                i, for_love_interest=False, age_restriction=False, ignore_no_mates=True
            )
            and i.status.is_outsider == self.the_cat.status.is_outsider
            and i.status.group_ID == self.the_cat.status.group_ID
            and i.ID not in self.the_cat.mate
        ]

        return valid_mates

    def on_use(self):
        super().on_use()

    def chunks(self, L, n):
        return [L[x : x + n] for x in range(0, len(L), n)]
