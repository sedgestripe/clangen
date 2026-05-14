#!/usr/bin/env python3
# -*- coding: ascii -*-
import os
from random import choice, randint

import pygame

from ..cat.history import History
from ..housekeeping.datadir import get_save_dir
from ..game_structure.windows import ChangeCatName, KillCat, ChangeCatToggles
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events

import ujson

from scripts.utility import event_text_adjust, ACC_DISPLAY, process_text, chunks, get_cluster

from .Screens import Screens

from scripts.utility import get_text_box_theme, shorten_text_to_fit
from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.pelts import Pelt
from scripts.game_structure import image_cache
import pygame_gui
from re import sub
from scripts.cat.skills import SkillPath

import math
from scripts.cat.sprites import sprites
from scripts.game_structure.game_essentials import game
from random import choice
from re import sub

import pygame
import pygame_gui
import ujson

from scripts.cat.cats import Cat, BACKSTORIES
from scripts.cat.pelts import Pelt
from scripts.clan_resources.freshkill import FRESHKILL_ACTIVE
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UITextBoxTweaked,
    UISurfaceImageButton,
)
from scripts.utility import (
    event_text_adjust,
    ui_scale,
    ACC_DISPLAY,
    process_text,
    chunks,
    get_text_box_theme,
    ui_scale_dimensions,
    shorten_text_to_fit,
    ui_scale_offset,
    adjust_list_text,
    pronoun_repl,
    get_alive_cats
)
from .Screens import Screens
from ..cat.history import History
from ..game_structure.screen_settings import MANAGER
from ..game_structure.windows import ChangeCatName, KillCat, ChangeCatToggles
from ..housekeeping.datadir import get_save_dir
from ..ui.generate_box import get_box, BoxStyles
from ..ui.generate_button import ButtonStyles, get_button_dict
from ..ui.get_arrow import get_arrow
from ..ui.icon import Icon


# ---------------------------------------------------------------------------- #
#             change how accessory info displays on cat profiles               #
# ---------------------------------------------------------------------------- #
def accessory_display_name(cat):
    accessory = cat.pelt.accessory

    if accessory is None:
        return ""
    acc_display = accessory.lower()

    if accessory in Pelt.collars:
        collar_colors = {
            "crimson": "red",
            "blue": "blue",
            "yellow": "yellow",
            "cyan": "cyan",
            "red": "orange",
            "lime": "lime",
            "green": "green",
            "rainbow": "rainbow",
            "black": "black",
            "spikes": "spiky",
            "white": "white",
            "pink": "pink",
            "purple": "purple",
            "multi": "multi",
            "indigo": "indigo",
        }
        collar_color = next(
            (color for color in collar_colors if acc_display.startswith(color)), None
        )

        if collar_color:
            if acc_display.endswith("bow") and not collar_color == "rainbow":
                acc_display = collar_colors[collar_color] + " bow"
            elif acc_display.endswith("bell"):
                acc_display = collar_colors[collar_color] + " bell collar"
            else:
                acc_display = collar_colors[collar_color] + " collar"

    elif accessory in Pelt.wild_accessories:
        if acc_display == "blue feathers":
            acc_display = "crow feathers"
        elif acc_display == "red feathers":
            acc_display = "cardinal feathers"

    return acc_display


# ---------------------------------------------------------------------------- #
#               assigns backstory blurbs to the backstory                      #
# ---------------------------------------------------------------------------- #
def bs_blurb_text(cat):
    backstory = cat.backstory
    backstory_text = BACKSTORIES["backstories"][backstory]

    if cat.status in ["kittypet", "loner", "rogue", "former Clancat"]:
        return f"This cat is a {cat.status} and currently resides outside of the Clans."

    return backstory_text


# ---------------------------------------------------------------------------- #
#             change how backstory info displays on cat profiles               #
# ---------------------------------------------------------------------------- #
def backstory_text(cat):
    backstory = cat.backstory
    if backstory is None:
        return ""
    bs_category = None

    for category in BACKSTORIES["backstory_categories"]:
        if backstory in category:
            bs_category = category
            break
    bs_display = BACKSTORIES["backstory_display"][bs_category]

    return bs_display


# ---------------------------------------------------------------------------- #
#                               Profile Screen                                 #
# ---------------------------------------------------------------------------- #
class ProfileScreen(Screens):
    # UI Images
    conditions_tab = image_cache.load_image(
        "resources/images/conditions_tab_backdrop.png"
    ).convert_alpha()

    # Keep track of current tabs open. Can be used to keep tabs open when pages are switched, and
    # helps with exiting the screen
    open_tab = None

    def __init__(self, name=None):
        super().__init__(name)
        self.condition_data = {}
        self.show_moons = None
        self.no_moons = None
        self.help_button = None
        self.open_sub_tab = None
        self.editing_notes = False
        self.user_notes = None
        self.save_text = None
        self.not_fav_tab = None
        self.fav_tab = None
        self.edit_text = None
        self.sub_tab_4 = None
        self.sub_tab_3 = None
        self.sub_tab_2 = None
        self.sub_tab_1 = None
        self.backstory_background = None
        self.history_text_box = None
        self.conditions_tab_button = None
        self.condition_container = None
        self.left_conditions_arrow = None
        self.right_conditions_arrow = None
        self.conditions_background = None
        self.previous_cat = None
        self.next_cat = None
        self.cat_image = None
        self.background = None
        self.cat_info_column2 = None
        self.cat_info_column1 = None
        self.cat_thought = None
        self.cat_name = None
        self.placeholder_tab_4 = None
        self.placeholder_tab_3 = None
        self.placeholder_tab_2 = None
        self.faith_bar = None
        self.your_tab = None
        self.backstory_tab_button = None
        self.dangerous_tab_button = None
        self.personal_tab_button = None
        self.roles_tab_button = None
        self.relations_tab_button = None
        self.back_button = None
        self.previous_cat_button = None
        self.next_cat_button = None
        self.the_cat = None
        self.prevent_fading_text = None
        self.checkboxes = {}
        self.profile_elements = {}
        self.join_df_button = None
        self.exit_df_button = None
        self.accessories_tab_button = None
        self.exile_return_button = None
        self.page = 0
        self.max_pages = 1
        self.clear_accessories = None
        self.delete_accessory = None
        self.search_bar_image = None
        self.search_bar = None
        self.previous_page_button = None
        self.next_page_button = None
        self.accessory_tab_button = None
        self.previous_search_text = "search"
        self.cat_list_buttons = None
        self.search_inventory = []
        self.faith_text = None

        # LG: all accs
        self.cat_inventory = []

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:

            if game.switches["window_open"]:
                pass
            elif event.ui_element == self.exile_return_button:
                game.clan.exile_return = True
                Cat.return_home(self)
                self.change_screen('events screen')
                # self.exit_screen()
                # game.switches['cur_screen'] = "events screen"
            elif event.ui_element == self.back_button:
                self.close_current_tab()
                self.change_screen(game.last_screen_forProfile)
            elif event.ui_element == self.previous_cat_button:
                if isinstance(Cat.fetch_cat(self.previous_cat), Cat) and Cat.fetch_cat(self.previous_cat).moons >= 0:
                    self.clear_profile()
                    game.switches["cat"] = self.previous_cat
                    self.build_profile()
                    self.page = 0
                    if self.previous_page_button:

                        inventory_len = 0
                        if self.search_bar.get_text() in ["", "search"]:
                            inventory_len = len(self.cat_inventory)
                        else:
                            for ac in self.cat_inventory:
                                if self.search_bar.get_text().lower() in ac.lower():
                                    inventory_len+=1
                        self.max_pages = math.ceil(inventory_len/18)
                        if self.page == 0 and self.max_pages == 1:
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
                    self.update_disabled_buttons_and_text()
                else:
                    print("invalid previous cat", self.previous_cat)
            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat) and Cat.fetch_cat(self.next_cat).moons >= 0:
                    self.clear_profile()
                    game.switches["cat"] = self.next_cat
                    self.build_profile()
                    self.page = 0
                    if self.previous_page_button:
                        self.previous_page_button.enable()
                        self.next_page_button.enable()
                        inventory_len = 0
                        if self.search_bar.get_text() in ["", "search"]:
                            inventory_len = len(self.cat_inventory)
                        else:
                            for ac in self.cat_inventory:
                                if self.search_bar.get_text().lower() in ac.lower():
                                    inventory_len+=1
                        self.max_pages = math.ceil(inventory_len/18)
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
                    self.update_disabled_buttons_and_text()
                else:
                    print("invalid next cat", self.previous_cat)
            elif event.ui_element == self.inspect_button:
                self.close_current_tab()
                self.change_screen("sprite inspect screen")
            elif self.the_cat.ID == game.clan.your_cat.ID and event.ui_element == self.profile_elements["change_cat"]:
                self.close_current_tab()
                self.change_screen("choose reborn screen")
            elif event.ui_element == self.relations_tab_button:
                self.toggle_relations_tab()
            elif event.ui_element == self.roles_tab_button:
                self.toggle_roles_tab()
            elif event.ui_element == self.personal_tab_button:
                self.toggle_personal_tab()
            elif event.ui_element == self.your_tab:
                self.toggle_your_tab()
            elif event.ui_element == self.dangerous_tab_button:
                self.toggle_dangerous_tab()
            elif event.ui_element == self.backstory_tab_button:
                if self.open_sub_tab is None:
                    if game.switches["favorite_sub_tab"] is None:
                        self.open_sub_tab = "life events"
                    else:
                        self.open_sub_tab = game.switches["favorite_sub_tab"]

                self.toggle_history_tab()
            elif event.ui_element == self.conditions_tab_button:
                self.toggle_conditions_tab()
            elif event.ui_element == self.accessories_tab_button:
                self.toggle_accessories_tab()
            elif event.ui_element == self.placeholder_tab_3:
                self.toggle_faith_tab()
            elif event.ui_element == self.previous_page_button:
                if self.page > 0:
                    self.page -= 1
                if self.page == 0:
                    self.previous_page_button.disable()
                    self.next_page_button.enable()
                elif self.page == self.max_pages - 1:
                    self.previous_page_button.enable()
                    self.next_page_button.disable()
                else:
                    self.previous_page_button.enable()
                    self.next_page_button.enable()
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.next_page_button:
                if self.page < self.max_pages - 1:
                    self.page += 1

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
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.delete_accessory:
                for acc in self.the_cat.pelt.accessories:
                    self.the_cat.pelt.inventory.remove(acc)
                    self.the_cat.pelt.accessories.remove(acc)
                self.close_current_tab()
                self.clear_profile()
                self.build_profile()
                self.toggle_accessories_tab()
            elif event.ui_element == self.clear_accessories:
                self.the_cat.pelt.accessories.clear()
                self.build_inventory(event)
                self.update_disabled_buttons_and_text()
            elif "leader_ceremony" in self.profile_elements and \
                    event.ui_element == self.profile_elements["leader_ceremony"]:
                self.change_screen('ceremony screen')
            elif "talk" in self.profile_elements and \
                    event.ui_element == self.profile_elements["talk"]:
                self.the_cat.talked_to = True
                if not self.the_cat.dead and not game.clan.your_cat.dead and game.clan.your_cat.ID in self.the_cat.relationships and self.the_cat.ID in game.clan.your_cat.relationships and game.clan.your_cat.shunned == 0:
                    self.the_cat.relationships[game.clan.your_cat.ID].platonic_like += randint(0,5)
                    game.clan.your_cat.relationships[self.the_cat.ID].platonic_like += randint(0,5)
                game.switches["talk_category"] = "talk"
                self.change_screen('talk screen')
            elif "insult" in self.profile_elements and \
                    event.ui_element == self.profile_elements["insult"]:
                self.the_cat.insulted = True
                if game.clan.your_cat.status != "kitten":
                    self.the_cat.relationships[game.clan.your_cat.ID].dislike += randint(1,10)
                    self.the_cat.relationships[game.clan.your_cat.ID].platonic_like -= randint(1,5)
                    self.the_cat.relationships[game.clan.your_cat.ID].comfortable -= randint(1,5)
                    self.the_cat.relationships[game.clan.your_cat.ID].trust -= randint(1,5)
                    self.the_cat.relationships[game.clan.your_cat.ID].admiration -= randint(1,5)
                    game.clan.your_cat.relationships[self.the_cat.ID].dislike += randint(1,10)
                    game.clan.your_cat.relationships[self.the_cat.ID].platonic_like -= randint(1,5)
                    game.clan.your_cat.relationships[self.the_cat.ID].comfortable -= randint(1,5)
                    game.clan.your_cat.relationships[self.the_cat.ID].trust -= randint(1,5)
                    game.clan.your_cat.relationships[self.the_cat.ID].admiration -= randint(1,5)
                game.switches["talk_category"] = "insult"
                self.change_screen('talk screen')
            elif "flirt" in self.profile_elements and \
                    event.ui_element == self.profile_elements["flirt"]:
                self.the_cat.flirted = True
                game.switches["talk_category"] = "flirt"
                self.change_screen('talk screen')
            elif event.ui_element == self.profile_elements["med_den"]:
                self.change_screen('med den screen')
            elif "mediation" in self.profile_elements and event.ui_element == self.profile_elements["mediation"]:
                self.change_screen('mediation screen')
            elif "queen" in self.profile_elements and event.ui_element == self.profile_elements["queen"]:
                self.change_screen('queen screen')
            elif "halfmoon" in self.profile_elements and event.ui_element == self.profile_elements["halfmoon"]:
                self.change_screen('moonplace screen')
            elif "story" in self.profile_elements and event.ui_element == self.profile_elements["story"]:
                self.change_screen('elder story screen')
            elif event.ui_element == self.profile_elements["favourite_button"]:
                if self.the_cat.favourite == 3:
                    self.the_cat.favourite = 0
                else:
                    self.the_cat.favourite += 1
                self.clear_profile()
                self.build_profile()
            else:
                self.handle_tab_events(event)

        elif event.type == pygame.KEYDOWN and game.settings["keybinds"]:
            if event.key == pygame.K_LEFT:
                if isinstance(Cat.fetch_cat(self.previous_cat), Cat) and Cat.fetch_cat(self.previous_cat).moons >= 0:
                    self.clear_profile()
                    game.switches["cat"] = self.previous_cat
                    self.build_profile()
                    self.update_disabled_buttons_and_text()
                else:
                    print("invalid previous cat", self.previous_cat)
            elif event.key == pygame.K_RIGHT:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat) and Cat.fetch_cat(self.next_cat).moons >= 0:
                    self.clear_profile()
                    game.switches["cat"] = self.next_cat
                    self.build_profile()
                    self.update_disabled_buttons_and_text()
                else:
                    print("invalid next cat", self.previous_cat)

            elif event.key == pygame.K_ESCAPE:
                self.close_current_tab()
                self.change_screen(game.last_screen_forProfile)

    def handle_tab_events(self, event):
        # Relations Tab
        if self.open_tab == "relations":
            if event.ui_element == self.family_tree_button:
                self.change_screen("family tree screen")
            elif event.ui_element == self.see_relationships_button:
                self.change_screen("relationship screen")
            elif event.ui_element == self.choose_mate_button:
                self.change_screen("choose mate screen")
            elif event.ui_element == self.change_adoptive_parent_button:
                self.change_screen("choose adoptive parent screen")

        # Roles Tab
        elif self.open_tab == "roles":
            if event.ui_element == self.manage_roles:
                self.change_screen("role screen")
            elif event.ui_element == self.change_mentor_button:
                self.change_screen("choose mentor screen")
            elif event.ui_element == self.manage_nobility:
                self.change_screen("choose nobility screen")
        # Personal Tab
        elif self.open_tab == "personal":
            if event.ui_element == self.change_name_button:
                ChangeCatName(self.the_cat)
            elif event.ui_element == self.specify_gender_button:
                self.change_screen("change gender screen")
            # when button is pressed...
            elif event.ui_element == self.cis_trans_button:
                # if the cat is anything besides m/f/transm/transf then turn them back to cis
                if self.the_cat.genderalign not in [
                    "female",
                    "trans female",
                    "male",
                    "trans male",
                ]:
                    self.the_cat.genderalign = self.the_cat.gender
                elif (
                    self.the_cat.gender == "male"
                    and self.the_cat.genderalign == "female"
                ):
                    self.the_cat.genderalign = self.the_cat.gender
                elif (
                    self.the_cat.gender == "female"
                    and self.the_cat.genderalign == "male"
                ):
                    self.the_cat.genderalign = self.the_cat.gender

                # if the cat is cis (gender & gender align are the same) then set them to trans
                # cis males -> trans female first
                elif (
                    self.the_cat.gender == "male" and self.the_cat.genderalign == "male"
                ):
                    self.the_cat.genderalign = "trans female"
                # cis females -> trans male
                elif (
                    self.the_cat.gender == "female"
                    and self.the_cat.genderalign == "female"
                ):
                    self.the_cat.genderalign = "trans male"
                # if the cat is trans then set them to nonbinary
                elif self.the_cat.genderalign in ["trans female", "trans male"]:
                    self.the_cat.genderalign = "nonbinary"
                # pronoun handler
                if self.the_cat.genderalign in ["female", "trans female"]:
                    self.the_cat.pronouns = [self.the_cat.default_pronouns[1].copy()]
                elif self.the_cat.genderalign in ["male", "trans male"]:
                    self.the_cat.pronouns = [self.the_cat.default_pronouns[2].copy()]
                elif self.the_cat.genderalign in ["nonbinary"]:
                    self.the_cat.pronouns = [self.the_cat.default_pronouns[0].copy()]
                elif self.the_cat.genderalign not in [
                    "female",
                    "trans female",
                    "male",
                    "trans male",
                ]:
                    self.the_cat.pronouns = [self.the_cat.default_pronouns[0].copy()]
                self.clear_profile()
                self.build_profile()
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.cat_toggles_button:
                ChangeCatToggles(self.the_cat)
        elif self.open_tab == 'your tab':
            if event.ui_element == self.have_kits_button:
                if 'have kits' not in game.switches:
                    game.switches['have kits'] = True
                if game.switches.get('have kits'):
                    game.clan.your_cat.no_kits = False
                    relation = Pregnancy_Events()
                    relation.handle_having_kits(game.clan.your_cat, game.clan)
                    game.switches['have kits'] = False
                    self.have_kits_button.disable()
            elif event.ui_element == self.request_apprentice_button:
                if 'request apprentice' not in game.switches:
                    game.switches['request apprentice'] = False
                if not game.switches['request apprentice']:
                    game.switches['request apprentice'] = True
                    self.request_apprentice_button.disable()
            elif event.ui_element == self.gift_accessory_button:
                self.change_screen("gift screen")
            elif event.ui_element == self.your_faith_button:
                self.toggle_faith_tab()
        # Dangerous Tab
        elif self.open_tab == "dangerous":
            if event.ui_element == self.kill_cat_button:
                KillCat(self.the_cat)
            elif event.ui_element == self.murder_cat_button:
                self.change_screen('murder screen')
            elif event.ui_element == self.join_df_button:
                game.clan.your_cat.joined_df = True
                game.clan.your_cat.df_join_moon = game.clan.age
                game.clan.your_cat.faith -=1
                game.clan.your_cat.update_df_mentor()
                self.join_df_button.disable()
                self.clear_profile()
                self.build_profile()
            elif event.ui_element == self.exit_df_button:
                game.clan.your_cat.joined_df = False
                game.clan.your_cat.faith += 1
                try:
                    Cat.all_cats[game.clan.your_cat.df_mentor].df_apprentices.remove(game.clan.your_cat.ID)
                except:
                    print("ERROR: removing df apprentice")
                game.clan.your_cat.df_mentor = None
                self.exit_df_button.disable()
                self.clear_profile()
                self.build_profile()
            elif event.ui_element == self.affair_button:
                self.change_screen('affair screen')
            elif event.ui_element == self.exile_cat_button:
                if not self.the_cat.dead and not self.the_cat.exiled:
                    Cat.exile(self.the_cat)
                    self.clear_profile()
                    self.build_profile()
                    self.update_disabled_buttons_and_text()
                if self.the_cat.dead:
                #     elif self.the_cat.dead:
                # if not self.the_cat.outside and not self.the_cat.df:
                #     object_id = "#exile_df_button"
                # elif self.the_cat.df and not self.the_cat.outside:
                #     object_id = "#send_ur_button"
                # else:
                #     object_id = "#guide_sc_button"
                    if self.the_cat.ID != game.clan.instructor.ID and self.the_cat.ID != game.clan.demon.ID:
                        if event.ui_object_id == "#guide_sc_button":
                            self.the_cat.outside, self.the_cat.exiled = False, False
                            self.the_cat.df = False
                            game.clan.add_to_starclan(self.the_cat)
                            self.the_cat.thought = "Is relieved to once again hunt in StarClan"
                        elif event.ui_object_id == "#exile_df_button":
                            self.the_cat.outside, self.the_cat.exiled = False, False
                            self.the_cat.df = True
                            game.clan.add_to_darkforest(self.the_cat)
                            self.the_cat.thought = "Is distraught after being sent to the Place of No Stars"
                        elif event.ui_object_id == "#send_ur_button":
                            self.the_cat.outside, self.the_cat.exiled = True, False
                            self.the_cat.df = False
                            game.clan.add_to_unknown(self.the_cat)
                            self.the_cat.thought = "Is wandering the Unknown Residence"


                    if self.the_cat.ID == game.clan.demon.ID and game.clan.followingsc == True:
                        game.clan.followingsc = False
                        for i in game.clan.clan_cats:
                            clan_cat = Cat.fetch_cat(i)
                            if clan_cat:
                                clan_cat.faith-=1

                    elif self.the_cat.ID == game.clan.instructor.ID and not game.clan.followingsc:
                        game.clan.followingsc = True
                        for i in game.clan.clan_cats:
                            clan_cat = Cat.fetch_cat(i)
                            if clan_cat:
                                clan_cat.faith+=1



                self.clear_profile()
                self.build_profile()
                self.update_disabled_buttons_and_text()
        # History Tab
        elif self.open_tab == "history":
            if event.ui_element == self.sub_tab_1:
                if self.open_sub_tab == "user notes":
                    self.notes_entry.kill()
                    self.display_notes.kill()
                    if self.edit_text:
                        self.edit_text.kill()
                    if self.save_text:
                        self.save_text.kill()
                    self.help_button.kill()
                self.open_sub_tab = "life events"
                self.toggle_history_sub_tab()
            elif event.ui_element == self.sub_tab_2:
                if self.open_sub_tab == "life events":
                    self.history_text_box.kill()
                self.open_sub_tab = "user notes"
                self.toggle_history_sub_tab()
            elif event.ui_element == self.fav_tab:
                game.switches["favorite_sub_tab"] = None
                self.fav_tab.hide()
                self.not_fav_tab.show()
            elif event.ui_element == self.not_fav_tab:
                game.switches["favorite_sub_tab"] = self.open_sub_tab
                self.fav_tab.show()
                self.not_fav_tab.hide()
            elif event.ui_element == self.save_text:
                self.user_notes = sub(
                    r"[^A-Za-z0-9<->/.()*'&#!?,| _+=@~:;[]{}%$^`]+",
                    "",
                    self.notes_entry.get_text(),
                )
                self.save_user_notes()
                self.editing_notes = False
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.edit_text:
                self.editing_notes = True
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.no_moons:
                game.switches["show_history_moons"] = True
                self.update_disabled_buttons_and_text()
            elif event.ui_element == self.show_moons:
                game.switches["show_history_moons"] = False
                self.update_disabled_buttons_and_text()

        # Conditions Tab
        elif self.open_tab == "conditions":
            if event.ui_element == self.right_conditions_arrow:
                self.conditions_page += 1
                self.display_conditions_page()
            if event.ui_element == self.left_conditions_arrow:
                self.conditions_page -= 1
                self.display_conditions_page()

        elif self.open_tab == 'accessories':
            self.build_inventory(event)

    def screen_switches(self):
        super().screen_switches()
        self.the_cat = Cat.all_cats.get(game.switches['cat'])
        self.page = 0

        # Set up the menu buttons, which appear on all cat profile images.
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
        self.inspect_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((741, 60), (34, 34))),
            Icon.MAGNIFY,
            get_button_dict(ButtonStyles.ICON, (34, 34)),
            object_id="@buttonstyles_icon",
        )
        
        self.exile_return_button = UIImageButton(ui_scale(pygame.Rect((383, 119), (34, 34))), "",
                                                object_id="#exile_return_button",  tool_tip_text='Ask your Clan for your nest back.', manager=MANAGER)
        
        self.relations_tab_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((48, 420), (176, 30))),
            "relations",
            get_button_dict(ButtonStyles.PROFILE_LEFT, (176, 30)),
            object_id="@buttonstyles_profile_left",
            manager=MANAGER,
        )
        self.roles_tab_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((224, 420), (176, 30))),
            "roles",
            get_button_dict(ButtonStyles.PROFILE_MIDDLE, (176, 30)),
            object_id="@buttonstyles_profile_middle",
            manager=MANAGER,
        )
        self.personal_tab_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((400, 420), (176, 30))),
            "personal",
            get_button_dict(ButtonStyles.PROFILE_MIDDLE, (176, 30)),
            object_id="@buttonstyles_profile_middle",
            manager=MANAGER,
        )
        self.dangerous_tab_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((576, 420), (176, 30))),
            "dangerous",
            get_button_dict(ButtonStyles.PROFILE_RIGHT, (176, 30)),
            object_id="@buttonstyles_profile_right",
            manager=MANAGER,
        )

        self.backstory_tab_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((48, 622), (176, 30))),
            "history",
            get_button_dict(ButtonStyles.PROFILE_LEFT, (176, 30)),
            object_id="@buttonstyles_profile_left",
            manager=MANAGER,
        )

        self.conditions_tab_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((224, 622), (176, 30))),
            "conditions",
            get_button_dict(ButtonStyles.PROFILE_MIDDLE, (176, 30)),
            object_id="@buttonstyles_profile_middle",
            manager=MANAGER,
        )

        self.placeholder_tab_3 = UISurfaceImageButton(
            ui_scale(pygame.Rect((400, 622), (176, 30))),
            "faith",
            get_button_dict(ButtonStyles.PROFILE_MIDDLE, (176, 30)),
            object_id="@buttonstyles_profile_middle",
            manager=MANAGER,
        )

        self.accessories_tab_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((576, 622), (176, 30))),
            "accessories",
            get_button_dict(ButtonStyles.PROFILE_RIGHT, (176, 30)),
            object_id="@buttonstyles_profile_right",
            manager=MANAGER,
        )

        if self.the_cat.moons == 0:
            self.accessories_tab_button.disable()
        else:
            self.accessories_tab_button.enable()
        self.build_profile()

        self.hide_mute_buttons()  # no space for mute button on this screen
        self.hide_menu_buttons()  # Menu buttons don't appear on the profile screen
        if game.last_screen_forProfile == "med den screen":
            self.toggle_conditions_tab()
        # game.clan.load_accessories()

        self.set_cat_location_bg(self.the_cat)

    def clear_profile(self):
        """Clears all profile objects."""
        for ele in self.profile_elements:
            self.profile_elements[ele].kill()
        self.profile_elements = {}

        if self.your_tab:
            self.your_tab.kill()

        if self.user_notes:
            self.user_notes = "Click the check mark to enter notes about your cat!"

        for box in self.checkboxes:
            self.checkboxes[box].kill()
        self.checkboxes = {}

    def exit_screen(self):
        self.clear_profile()
        self.back_button.kill()
        self.next_cat_button.kill()
        self.previous_cat_button.kill()
        if self.exile_return_button:
            self.exile_return_button.kill()
        self.relations_tab_button.kill()
        self.roles_tab_button.kill()
        self.personal_tab_button.kill()
        self.dangerous_tab_button.kill()
        self.backstory_tab_button.kill()
        self.conditions_tab_button.kill()
        if self.your_tab:
            self.your_tab.kill()
        self.placeholder_tab_3.kill()
        self.accessories_tab_button.kill()
        self.inspect_button.kill()
        self.close_current_tab()

    def build_profile(self):
        """Rebuild builds the cat profile. Run when you switch cats
        or for changes in the profile."""
        self.the_cat = Cat.all_cats.get(game.switches["cat"])

        # LG: accessory bull shit
        if game.clan.clan_settings['all accessories']:
            self.cat_inventory = game.clan.load_accessories()
        else:
            self.cat_inventory = self.the_cat.pelt.inventory
        
        if self.the_cat.pelt.accessory:
            if self.the_cat.pelt.accessory not in self.the_cat.pelt.inventory:
                self.the_cat.pelt.inventory.append(self.the_cat.pelt.accessory)

        for acc in self.the_cat.pelt.accessories:
            if acc not in self.the_cat.pelt.inventory:
                self.the_cat.pelt.inventory.append(acc)
        # ---

        if self.the_cat.dead and game.clan.demon.ID == self.the_cat.ID:
            self.the_cat.df = True

        # use these attributes to create differing profiles for StarClan cats etc.
        is_sc_instructor = False
        is_df_instructor = False
        if self.the_cat is None:
            return
        if (
            self.the_cat.dead
            and game.clan.instructor.ID == self.the_cat.ID
            and self.the_cat.df is False
        ):
            is_sc_instructor = True
        elif self.the_cat.dead and game.clan.demon.ID == self.the_cat.ID and self.the_cat.df is True:
            is_df_instructor = True

        # Info in string
        cat_name = str(self.the_cat.name)
        cat_name = shorten_text_to_fit(cat_name, 500, 20)
        if self.the_cat.dead:
            cat_name += " (dead)"  # A dead cat will have the (dead) sign next to their name


        if is_sc_instructor:

            if game.clan.followingsc == True:
                self.the_cat.thought = "Hello. I will be guiding the cats of " + game.clan.name + "Clan into StarClan."
            else:
                self.the_cat.thought = "Misses watching over " + game.clan.name + "Clan"

        if is_df_instructor:
            if game.clan.followingsc == True:
                self.the_cat.thought = "Hello. I am here to drag the cats of " + game.clan.name + "Clan into the Dark Forest"
                self.the_cat.df
            else:
                self.the_cat.thought = "Is picking more " + game.clan.name + "Clan cats to join them"

        self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(cat_name,
                                                                        ui_scale(pygame.Rect((50, 280), (-1, 105))),
                                                                        object_id=get_text_box_theme(
                                                                            "#text_box_40_horizcenter"),
                                                                        manager=MANAGER)
        name_text_size = self.profile_elements["cat_name"].get_relative_rect()
        self.profile_elements["cat_name"].kill()

        self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(
            cat_name,
            ui_scale(pygame.Rect((0, 0), (-1, 40))),
            manager=MANAGER,
            object_id=get_text_box_theme("#text_box_40_horizcenter"),
            anchors={"centerx": "centerx"},
        )
        self.profile_elements["cat_name"].set_relative_position(
            ui_scale_offset((0, 140))
        )

        # Write cat thought
        self.profile_elements["cat_thought"] = pygame_gui.elements.UITextBox(
            self.the_cat.thought,
            ui_scale(pygame.Rect((0, 170), (600, -1))),
            wrap_to_height=True,
            object_id=get_text_box_theme("#text_box_30_horizcenter"),
            manager=MANAGER,
            anchors={"centerx": "centerx"},
        )

        self.profile_elements["cat_info_column1"] = UITextBoxTweaked(
            self.generate_column1(self.the_cat),
            ui_scale(pygame.Rect((300, 220), (180, 200))),
            object_id=get_text_box_theme("#text_box_22_horizleft"),
            line_spacing=1,
            manager=MANAGER,
        )
    
        self.profile_elements["cat_info_column2"] = UITextBoxTweaked(
            self.generate_column2(self.the_cat),
            ui_scale(pygame.Rect((490, 220), (250, 200))),
            object_id=get_text_box_theme("#text_box_22_horizleft"),
            line_spacing=1,
            manager=MANAGER,
        )

        # Set the cat backgrounds.
        if game.clan.clan_settings["backgrounds"]:
            self.profile_elements["background"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((55, 200), (240, 210))),
                pygame.transform.scale(
                    self.get_platform(), ui_scale_dimensions((240, 210))
                ),
                manager=MANAGER,
            )
            self.profile_elements["background"].disable()

        # Create cat image object
        self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((100, 200), (150, 150))),
            pygame.transform.scale(
                self.the_cat.sprite, ui_scale_dimensions((150, 150))
            ),
            manager=MANAGER,
        )
        self.profile_elements["cat_image"].disable()

        # if cat is a med or med app, show button for their den
        self.profile_elements["med_den"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((100, 380), (151, 28))),
            "medicine cat den",
            get_button_dict(ButtonStyles.ROUNDED_RECT, (151, 28)),
            object_id="@buttonstyles_rounded_rect",
            manager=MANAGER,
            starting_height=2,
        )
        if not (self.the_cat.dead or self.the_cat.outside) and (
            self.the_cat.status in ["medicine cat", "medicine cat apprentice"]
            or self.the_cat.is_ill()
            or self.the_cat.is_injured()
        ):
            self.profile_elements["med_den"].show()
        else:
            self.profile_elements["med_den"].hide()

        favorite_button_rect = ui_scale(pygame.Rect((0, 0), (28, 28)))
        favorite_button_rect.topright = ui_scale_offset((-5, 146))

        # LG changes
        if self.the_cat.favourite != 0:
            if self.the_cat.favourite == 1:
                fav_star_id = "#fav_star"
            else:
                fav_star_id = f"#fav_star_{str(self.the_cat.favourite)}"
        else:
            fav_star_id = "#not_fav_star"

        self.profile_elements["favourite_button"] = UIImageButton(
            favorite_button_rect,
            "",
            object_id=fav_star_id,
            manager=MANAGER,
            tool_tip_text=f"Move to {self.the_cat.favourite + 1}" if self.the_cat.favourite < 3 else "Remove favourite"
            if self.the_cat.favourite != 0
            else "Mark as favorite",
            starting_height=2,
            anchors={
                "right": "right",
                "right_target": self.profile_elements["cat_name"],
            },
        )
        self.profile_elements["favourite_button"].rebuild()
        del favorite_button_rect


        if self.accessory_tab_button:
            if self.the_cat.moons == 0:
                self.accessory_tab_button.disable()
            else:
                self.accessory_tab_button.enable()

        # Determine where the next and previous cat buttons lead
        (
            self.next_cat,
            self.previous_cat,
        ) = self.the_cat.determine_next_and_previous_cats()

        # Disable and enable next and previous cat buttons as needed.
        if self.next_cat == 0:
            self.next_cat_button.disable()
        else:
            self.next_cat_button.enable()

        if self.previous_cat == 0:
            self.previous_cat_button.disable()
        else:
            self.previous_cat_button.enable()

        if self.open_tab == "history" and self.open_sub_tab == "user notes":
            self.load_user_notes()

        if not game.clan.your_cat:
            print("Are you playing a normal ClanGen save? Switch to a LifeGen save or create a new cat!")
            print("Choosing random cat to play...")
            game.clan.your_cat = choice(get_alive_cats(Cat))
            print("Chose " + str(game.clan.your_cat.name))

        if self.the_cat.ID == game.clan.your_cat.ID:
            self.profile_elements["change_cat"] = UISurfaceImageButton(
                ui_scale(pygame.Rect((701, 60), (34, 34))),
                Icon.DICE,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                tool_tip_text="Switch MC",
                object_id="@buttonstyles_icon",
            )
            
        # TALK BUTTONS

        if self.the_cat.ID != game.clan.your_cat.ID:

            # TALK
            cant_talk = False
            dead_talk = self.get_dead_cat_talk()

            if (
                (not self.the_cat.dead and self.the_cat.outside) or
                (not self.the_cat.dead and not self.the_cat.outside and game.clan.your_cat.outside and not game.clan.your_cat.dead) or 
                game.clan.your_cat.moons < 0 or
                self.the_cat.ID == game.clan.your_cat.ID or
                ((game.clan.your_cat.dead or self.the_cat.dead) and dead_talk is False)
            ):
                cant_talk = True
                
            self.profile_elements["talk"] = UIImageButton(ui_scale(pygame.Rect(
                (383, 105), (34, 34))),
                "",
                object_id="#talk_button",
                tool_tip_text="Talk to this Cat",
                manager=MANAGER
            )
            if self.the_cat.talked_to or cant_talk is True:
                self.profile_elements["talk"].disable()
            else:
                self.profile_elements["talk"].enable()

            # INSULT
            cant_insult = False
            if (
                self.the_cat.outside or
                (not self.the_cat.dead and not self.the_cat.outside and game.clan.your_cat.outside and not game.clan.your_cat.dead) or 
                game.clan.your_cat.moons < 0 or
                self.the_cat.ID == game.clan.your_cat.ID or
                (game.clan.your_cat.dead is True or self.the_cat.dead is True and
                dead_talk is False) or

                game.clan.your_cat.dead or
                self.the_cat.dead
                # when/if dead insulting is added, these two lines can just be removed
            ):
                cant_insult = True

            self.profile_elements["insult"] = UIImageButton(ui_scale(pygame.Rect(
                (423, 105), (34, 34))),
                "",
                object_id="#insult_button",
                tool_tip_text="Insult this Cat", manager=MANAGER
            )
            if self.the_cat.insulted or cant_insult:
                self.profile_elements["insult"].disable()
            else:
                self.profile_elements["insult"].enable()

            # FLIRT
            cant_flirt = False
            if (
                self.the_cat.outside or
                game.clan.your_cat.moons < 0 or
                self.the_cat.ID == game.clan.your_cat.ID or
                (not self.the_cat.dead and not self.the_cat.outside and game.clan.your_cat.outside and not game.clan.your_cat.dead) or 
                (game.clan.your_cat.dead is True or self.the_cat.dead is True and
                dead_talk is False) or
                not self.the_cat.is_dateable(game.clan.your_cat) or

                game.clan.your_cat.dead or
                self.the_cat.dead
                # when/if dead flirting is added, these two lines can just be removed
            ):
                cant_flirt = True

            self.profile_elements["flirt"] = UIImageButton(ui_scale(pygame.Rect(
                (343, 105), (34, 34))),
                "",
                object_id="#flirt_button",
                tool_tip_text="Flirt with this Cat", manager=MANAGER
            )
            if self.the_cat.flirted:
                self.profile_elements["flirt"].disable()
            elif cant_flirt:
                self.profile_elements["flirt"].kill()

                self.profile_elements["flirt"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((343, 105), (34, 34))), image_cache.load_image(
                    "resources/images/flirt_impossible.png").convert_alpha())

                self.profile_elements["flirt"].disable()
            else:
                self.profile_elements["flirt"].enable()

        # WORK BUTTONS
        # leader, mediator, queen, moonplace

        if self.the_cat.ID == game.clan.your_cat.ID:
            y_pos = 105
        else:
            y_pos = 65

        if self.the_cat.status == 'leader' and not self.the_cat.dead:
            self.profile_elements["leader_ceremony"] = UIImageButton(ui_scale(pygame.Rect(
                (383, y_pos), (34, 34))),
                "",
                object_id="#leader_ceremony_button",
                tool_tip_text="Leader Ceremony",
                manager=MANAGER,
            )
        elif self.the_cat.status in ["mediator", "mediator apprentice"] and self.the_cat.moons >= 6:
            self.profile_elements["mediation"] = UIImageButton(
                ui_scale(pygame.Rect((383, y_pos), (34, 34))),
                "",
                object_id="#mediation_button",
                manager=MANAGER,
            )
            if self.the_cat.dead or self.the_cat.outside or self.the_cat.shunned > 0:
                self.profile_elements["mediation"].disable()
        elif self.the_cat.status in ["queen", "queen's apprentice"] and self.the_cat.moons >= 6:
            self.profile_elements["queen"] = UIImageButton(ui_scale(pygame.Rect(
                (383, y_pos), (34, 34))),
                "",
                object_id="#queen_activity_button", manager=MANAGER
            )
            if self.the_cat.dead or self.the_cat.outside or self.the_cat.shunned > 0 or self.the_cat.not_working():
                # check for not working because the queen screen doesnt have the "this cat is unable to work" thing
                # like the mediator screen does
                self.profile_elements["queen"].disable()
        if self.the_cat.status in ["medicine cat", "medicine cat apprentice"] and self.the_cat.ID == game.clan.your_cat.ID and self.the_cat.moons >= 6:
            self.profile_elements["halfmoon"] = UIImageButton(ui_scale(pygame.Rect(
                (383, y_pos), (34, 34))),
                "",
                object_id="#half_moon_button", 
                tool_tip_text= "You may attend the half-moon gathering every six moons",
                manager=MANAGER
            )
            if self.the_cat.dead or self.the_cat.outside or (game.clan.age % 6 != 0) or self.the_cat.shunned > 0:
                self.profile_elements["halfmoon"].disable()
            elif "attended half-moon" in game.switches and game.switches["attended half-moon"]:
                self.profile_elements["halfmoon"].disable()
        elif (
            self.the_cat.status in [
                "queen's apprentice",
                "mediator apprentice",
                "apprentice"
                ] and
                self.the_cat.ID == game.clan.your_cat.ID and
                self.the_cat.moons >= 6
                ):
            if self.the_cat.status == "apprentice":
                self.profile_elements["halfmoon"] = UIImageButton(ui_scale(pygame.Rect(
                    (383, y_pos), (34, 34))),
                    "",
                    object_id="#half_moon_button", 
                    tool_tip_text= "You may visit the Moonplace once during your apprenticeship.",
                    manager=MANAGER
                )
            else:
                self.profile_elements["halfmoon"] = UIImageButton(ui_scale(pygame.Rect(
                (323, y_pos), (34, 34))),
                "",
                object_id="#half_moon_button", 
                tool_tip_text= "You may visit the Moonplace once during your apprenticeship.",
                manager=MANAGER
            )
            if self.the_cat.dead or self.the_cat.outside or self.the_cat.shunned > 0:
                self.profile_elements["halfmoon"].disable()
            elif "attended half-moon" in game.switches and game.switches["attended half-moon"]:
                self.profile_elements["halfmoon"].disable()
        elif self.the_cat.status == "elder":
            self.profile_elements["story"] = UISurfaceImageButton(
                ui_scale(pygame.Rect((383, y_pos), (34, 34))),
                Icon.NOTEPAD,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                manager=MANAGER,
                tool_tip_text="Tell a story",
                object_id="@buttonstyles_icon",
                starting_height=2,
            )
           
            if self.the_cat.dead or self.the_cat.outside or self.the_cat.shunned > 0:
                self.profile_elements["story"].disable()
        
        if self.the_cat.ID == game.clan.your_cat.ID and not game.clan.your_cat.dead:
            if self.open_tab == "faith":
                self.close_current_tab()
            self.placeholder_tab_3.kill()

            self.your_tab = UISurfaceImageButton(
                ui_scale(pygame.Rect((400, 622), (176, 30))),
                "your tab",
                get_button_dict(ButtonStyles.PROFILE_MIDDLE, (176, 30)),
                object_id="@buttonstyles_profile_middle",
                manager=MANAGER,
            )
            
        else:
            if self.open_tab == 'your tab':
                self.close_current_tab()
            if self.open_tab == "faith" and (self.the_cat.dead or self.the_cat.outside or self.the_cat.moons < 6):
                self.close_current_tab()
            self.placeholder_tab_3.kill()
            self.placeholder_tab_3 = None

            self.placeholder_tab_3 = UISurfaceImageButton(
                ui_scale(pygame.Rect((400, 622), (176, 30))),
                "faith",
                get_button_dict(ButtonStyles.PROFILE_MIDDLE, (176, 30)),
                object_id="@buttonstyles_profile_middle",
                manager=MANAGER,
            )
            if self.the_cat.dead or self.the_cat.outside or self.the_cat.moons < 6:
                self.placeholder_tab_3.disable()
            else:
                self.placeholder_tab_3.enable()

        if self.the_cat.ID == game.clan.your_cat.ID:
            if not self.the_cat.dead and self.the_cat.exiled or self.the_cat.status == 'former_Clancat':
                if game.clan.exile_return:
                    self.exile_return_button.disable()
                else:
                    self.exile_return_button.show()
            else:
                self.exile_return_button.hide()
        else:
            self.exile_return_button.hide()

        # if self.the_cat.shunned == 0 and self.the_cat.revealed > 0 and not self.the_cat.outside and not self.the_cat.exiled:
        #     print("This cat has been forgiven for murder.")

    def generate_column1(self, the_cat):
        """Generate the left column information"""
        output = ""
        # SEX/GENDER
        if the_cat.genderalign is None or the_cat.genderalign == the_cat.gender:
            output += str(the_cat.gender)
        else:
            output += str(the_cat.genderalign)
        # NEWLINE ----------
        output += "\n"

        # AGE
        if the_cat.age == "kitten":
            output += "young"
        elif the_cat.age == "senior":
            output += "senior"
        else:
            output += the_cat.age
        # NEWLINE ----------
        output += "\n"

        # EYE COLOR
        output += "eyes: " + str(the_cat.describe_eyes())
        # NEWLINE ----------
        output += "\n"

        # PELT TYPE
        output += "pelt: " + the_cat.pelt.name.lower()
        # NEWLINE ----------
        output += "\n"

        # PELT LENGTH
        output += "fur length: " + the_cat.pelt.length
        # NEWLINE ----------

        # ACCESSORY
        if the_cat.pelt.accessories:
            if len(the_cat.pelt.accessories) > 0:
                if the_cat.pelt.accessories[0]:
                    try:
                        output += "\n"
                        output += 'accessories: ' + str(ACC_DISPLAY[the_cat.pelt.accessories[0]]["default"])
                        if len(the_cat.pelt.accessories) > 1:
                            output += ' and ' + str(len(the_cat.pelt.accessories) - 1) + ' more'
                    except:
                        print("error with column1")

        elif the_cat.pelt.accessory and the_cat.pelt.accessory in the_cat.pelt.accessories:
            output += "\n"
            output += "accessory: " + str(
                ACC_DISPLAY[the_cat.pelt.accessory]["default"]
            )
            # NEWLINE ----------

        # PARENTS
        all_parents = [Cat.fetch_cat(i) for i in the_cat.get_parents()]
        if all_parents:
            output += "\n"
            if len(all_parents) == 1:
                output += "parent: " + str(all_parents[0].name)
            elif len(all_parents) > 2:
                output += (
                    "parents: "
                    + ", ".join([str(i.name) for i in all_parents[:2]])
                    + f", and {len(all_parents) - 2} "
                )
                if len(all_parents) - 2 == 1:
                    output += "other"
                else:
                    output += "others"
            else:
                output += "parents: " + ", ".join([str(i.name) for i in all_parents if i])


        # MOONS
        output += "\n"
        if the_cat.dead:
            output += str(the_cat.moons)
            if the_cat.moons == 1:
                output += " moon (in life)\n"
            elif the_cat.moons != 1:
                output += " moons (in life)\n"

            output += str(the_cat.dead_for)
            if the_cat.dead_for == 1:
                output += " moon (in death)"
            elif the_cat.dead_for != 1:
                output += " moons (in death)"
        else:
            if the_cat.moons == -1:
                output += 'Unborn'
            else:
                output += str(the_cat.moons)
                if the_cat.moons == 1:
                    output += ' moon'
                elif the_cat.moons != 1:
                    output += ' moons'

        # MATE
        if len(the_cat.mates) > 0:
            output += "\n"

            mate_names = []
            # Grab the names of only the first two, since that's all we will display
            for _m in the_cat.mates[:2]:
                mate_ob = Cat.fetch_cat(_m)
                if not isinstance(mate_ob, Cat):
                    continue
                if mate_ob.dead != self.the_cat.dead:
                    if the_cat.dead:
                        former_indicate = "(living)"
                    else:
                        former_indicate = "(dead)"

                    mate_names.append(f"{str(mate_ob.name)} {former_indicate}")
                elif mate_ob.outside != self.the_cat.outside:
                    mate_names.append(f"{str(mate_ob.name)} (away)")
                else:
                    mate_names.append(f"{str(mate_ob.name)}")

            if len(the_cat.mates) == 1:
                output += "mate: "
            else:
                output += "mates: "

            output += ", ".join(mate_names)

            if len(the_cat.mates) > 2:
                output += f", and {len(the_cat.mates) - 2}"
                if len(the_cat.mates) - 2 > 1:
                    output += " others"
                else:
                    output += " other"

        if not the_cat.dead:
            # NEWLINE ----------
            output += "\n"

        return output

    def generate_column2(self, the_cat):
        """Generate the right column information"""
        output = ""

        # STATUS
        if the_cat.outside and not (the_cat.exiled or the_cat.df) and the_cat.status not in ['kittypet', 'loner', 'rogue',
            'former Clancat'] and not the_cat.dead:
            output += "<font color='#FF0000'>lost</font>"
        elif the_cat.exiled:
            output += "<font color='#FF0000'>exiled</font>"
        elif the_cat.shunned > 0 and not the_cat.dead:
            if not the_cat.outside:

                # grabbing demoted statuses
                murder_history = History.get_murders(the_cat)
                history = None
                status = the_cat.status
                if "is_murderer" in murder_history:
                    history = murder_history["is_murderer"]
                if history:
                    if "demoted_from" in history[-1] and history[-1]["demoted_from"]:
                        status = history[-1]["demoted_from"]

                if game.settings['dark mode']:
                    output += "<font color='#FF9999'>shunned " + status+ "</font>"
                else:
                    output += "<font color='#950000'>shunned " + status + "</font>"
            else:
                output += the_cat.status
        elif the_cat.df:
            if game.settings['dark mode']:
                output += "<font color='#FF9999' >" + "Dark Forest "+ the_cat.status + "</font>"
            else:
                output += "<font color='#950000' >" + "Dark Forest "+ the_cat.status + "</font>"
        elif the_cat.dead and not the_cat.df and not the_cat.outside:
            if game.settings['dark mode']:
                output += "<font color ='#A8BBFF'>" + "StarClan " + the_cat.status + "</font>"
            else:
                output += "<font color ='#2B3DC3'>" + "StarClan " + the_cat.status + "</font>"
        elif the_cat.dead and not the_cat.df and the_cat.outside:
            if game.settings['dark mode']:
                output += "<font color ='#CE9DFF'>" + "ghost " + the_cat.status + "</font>"
            else:
                output += "<font color ='#450E7B'>" + "ghost " + the_cat.status + "</font>"
        else:
            output += the_cat.status

        # NEWLINE ----------
        output += "\n"

        # LEADER LIVES:
        # Optional - Only shows up for leaders
        if not the_cat.dead and "leader" in the_cat.status:
            output += "remaining lives: " + str(game.clan.leader_lives)
            # NEWLINE ----------
            output += "\n"

        # NOBILITY
        if the_cat.nobility_rank == 1:
            output += "commoner"
        if the_cat.nobility_rank == 2:
            output += "knight"
        if the_cat.nobility_rank == 3:
            output += "baron"
        if the_cat.nobility_rank == 4:
            output += "viscount"
        if the_cat.nobility_rank == 5:
            output += "earl"
        if the_cat.nobility_rank == 6:
            output += "marquess"
        if the_cat.nobility_rank == 7:
            output += "duke"

        # NEWLINE
        output += "\n"

        # MENTOR
        # Only shows up if the cat has a mentor.
        if the_cat.mentor:
            mentor_ob = Cat.fetch_cat(the_cat.mentor)
            if mentor_ob:
                output += "mentor: " + str(mentor_ob.name) + "\n"
        
        if the_cat.df_mentor and not the_cat.dead:
            mentor_ob = Cat.fetch_cat(the_cat.df_mentor)
            if mentor_ob:
                output += "dark forest mentor: " + str(mentor_ob.name) + "\n"

        # CURRENT APPRENTICES
        # Optional - only shows up if the cat has an apprentice currently
        if the_cat.apprentice:
            app_count = len(the_cat.apprentice)
            if app_count == 1 and Cat.fetch_cat(the_cat.apprentice[0]):
                output += "apprentice: " + str(
                    Cat.fetch_cat(the_cat.apprentice[0]).name
                )
            elif app_count > 1:
                output += "apprentice: " + ", ".join(
                    [
                        str(Cat.fetch_cat(i).name)
                        for i in the_cat.apprentice
                        if Cat.fetch_cat(i)
                    ]
                )
            # NEWLINE ----------
            output += "\n"

        # FORMER APPRENTICES
        # Optional - Only shows up if the cat has previous apprentice(s)
        if the_cat.former_apprentices:
            apprentices = [
                Cat.fetch_cat(i)
                for i in the_cat.former_apprentices
                if isinstance(Cat.fetch_cat(i), Cat)
            ]

            if len(apprentices) > 2:
                output += (
                    "former apprentices: "
                    + ", ".join([str(i.name) for i in apprentices[:2]])
                    + ", and "
                    + str(len(apprentices) - 2)
                )
                if len(apprentices) - 2 > 1:
                    output += " others"
                else:
                    output += " other"
            else:
                if len(apprentices) > 1:
                    output += "former apprentices: "
                else:
                    output += "former apprentice: "
                output += ", ".join(str(i.name) for i in apprentices)

            # NEWLINE ----------
            output += "\n"
        
        if the_cat.df_apprentices and the_cat.dead:
            app_count = len(the_cat.df_apprentices)
            if app_count == 1 and Cat.fetch_cat(the_cat.df_apprentices[0]) and not Cat.fetch_cat(the_cat.df_apprentices[0]).dead:
                output += 'dark forest apprentice: ' + str(Cat.fetch_cat(the_cat.df_apprentices[0]).name)

                # NEWLINE ----------
                output += "\n"
            elif app_count > 1:
                output += 'dark forest apprentices: ' + ", ".join([str(Cat.fetch_cat(i).name) for i in the_cat.df_apprentices if Cat.fetch_cat(i) and not Cat.fetch_cat(i).dead])

                # NEWLINE ----------
                output += "\n"

        # CHARACTER TRAIT
        output += the_cat.personality.trait
        # NEWLINE ----------
        output += "\n"
        # CAT SKILLS

        if the_cat.moons < 1:
            output += "???"
        else:
            output += the_cat.skills.skill_string()
        # NEWLINE ----------
        output += "\n"

        # EXPERIENCE
        output += "experience: " + str(the_cat.experience_level)

        if game.clan.clan_settings["showxp"]:
            output += " (" + str(the_cat.experience) + ")"
        # NEWLINE ----------
        output += "\n"

        # BACKSTORY
        bs_text = "this should not appear"
        if the_cat.status in ["kittypet", "loner", "rogue", "former Clancat"]:
            bs_text = the_cat.status
        else:
            if the_cat.backstory:
                for category in BACKSTORIES["backstory_categories"]:
                    if (
                        the_cat.backstory
                        in BACKSTORIES["backstory_categories"][category]
                    ):
                        bs_text = BACKSTORIES["backstory_display"][category]
                        break
            else:
                bs_text = "Clanborn"
        output += f"backstory: {bs_text}"
        # NEWLINE ----------
        output += "\n"

        # NUTRITION INFO (if the game is in the correct mode)
        if (
            game.clan.game_mode in ["expanded", "cruel season"]
            and the_cat.is_alive()
            and FRESHKILL_ACTIVE
        ):
            # Check to only show nutrition for clan cats
            if str(the_cat.status) not in [
                "loner",
                "kittypet",
                "rogue",
                "former Clancat",
                "exiled",
            ]:
                nutr = None
                if the_cat.ID in game.clan.freshkill_pile.nutrition_info:
                    nutr = game.clan.freshkill_pile.nutrition_info[the_cat.ID]
                if not nutr:
                    game.clan.freshkill_pile.add_cat_to_nutrition(the_cat)
                    nutr = game.clan.freshkill_pile.nutrition_info[the_cat.ID]
                output += "nutrition: " + nutr.nutrition_text
                if game.clan.clan_settings["showxp"]:
                    output += " (" + str(int(nutr.percentage)) + ")"
                output += "\n"

        if the_cat.is_disabled():
            for condition in the_cat.permanent_condition:
                if (
                    the_cat.permanent_condition[condition]["born_with"] is True
                    and the_cat.permanent_condition[condition]["moons_until"] != -2
                ):
                    continue
                output += "has a permanent condition"

                # NEWLINE ----------
                output += "\n"
                break

        if the_cat.is_injured():
            if "recovering from birth" in the_cat.injuries:
                output += "recovering from birth!"
            elif "pregnant" in the_cat.injuries:
                output += 'pregnant!'
            elif "guilt" in the_cat.injuries:
                output += "guilty!"
            else:
                output += "injured!"
        elif the_cat.is_ill():
            if "grief stricken" in the_cat.illnesses:
                output += "grieving!"
            elif "fleas" in the_cat.illnesses:
                output += "flea-ridden!"
            else:
                output += "sick!"

        return output

    def toggle_history_tab(self, sub_tab_switch=False):
        """Opens the history tab
        param sub_tab_switch should be set to True if switching between sub tabs within the History tab
        """
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open at a time
        self.close_current_tab()

        if previous_open_tab == "history" and sub_tab_switch is False:
            """If the current open tab is history and we aren't switching between sub tabs,
            just close the tab and do nothing else."""
            pass
        else:
            self.open_tab = "history"
            rect = ui_scale(pygame.Rect((0, 0), (620, 157)))
            rect.bottomleft = ui_scale_offset((89, 0))
            self.backstory_background = pygame_gui.elements.UIImage(
                rect,
                get_box(
                    BoxStyles.ROUNDED_BOX, (620, 157), sides=(True, True, False, True)
                ),
                anchors={
                    "bottom": "bottom",
                    "bottom_target": self.conditions_tab_button,
                },
            )
            self.backstory_background.disable()
            self.sub_tab_1 = UIImageButton(
                ui_scale(pygame.Rect((709, 475), (42, 30))),
                "",
                object_id="#sub_tab_1_button",
                manager=MANAGER,
            )
            self.sub_tab_1.disable()
            self.sub_tab_2 = UIImageButton(
                ui_scale(pygame.Rect((709, 512), (42, 30))),
                "",
                object_id="#sub_tab_2_button",
                manager=MANAGER,
            )
            self.sub_tab_2.disable()
            self.sub_tab_3 = UIImageButton(
                ui_scale(pygame.Rect((709, 549), (42, 30))),
                "",
                object_id="#sub_tab_3_button",
                manager=MANAGER,
            )
            self.sub_tab_3.disable()
            self.sub_tab_4 = UIImageButton(
                ui_scale(pygame.Rect((709, 586), (42, 30))),
                "",
                object_id="#sub_tab_4_button",
                manager=MANAGER,
            )
            self.sub_tab_4.disable()
            self.fav_tab = UIImageButton(
                ui_scale(pygame.Rect((55, 480), (28, 28))),
                "",
                object_id="#fav_star",
                tool_tip_text="un-favorite this sub tab",
                manager=MANAGER,
            )
            self.not_fav_tab = UIImageButton(
                ui_scale(pygame.Rect((55, 480), (28, 28))),
                "",
                object_id="#not_fav_star",
                tool_tip_text="favorite this sub tab - it will be the default sub tab displayed when History is viewed",
                manager=MANAGER,
            )

            if self.open_sub_tab != "life events":
                self.toggle_history_sub_tab()
            else:
                # This will be overwritten in update_disabled_buttons_and_text()
                self.history_text_box = pygame_gui.elements.UITextBox(
                    "", ui_scale(pygame.Rect((40, 240), (307, 71))), manager=MANAGER
                )
                self.no_moons = UIImageButton(
                    ui_scale(pygame.Rect((52, 514), (34, 34))),
                    "",
                    object_id="@unchecked_checkbox",
                    tool_tip_text="Show the Moon that certain history events occurred on",
                    manager=MANAGER,
                )
                self.show_moons = UIImageButton(
                    ui_scale(pygame.Rect((52, 514), (34, 34))),
                    "",
                    object_id="@checked_checkbox",
                    tool_tip_text="Stop showing the Moon that certain history events occurred on",
                    manager=MANAGER,
                )

                self.update_disabled_buttons_and_text()

    def toggle_user_notes_tab(self):
        """Opens the User Notes portion of the History Tab"""
        self.load_user_notes()
        if self.user_notes is None:
            self.user_notes = "Click the check mark to enter notes about your cat!"

        self.notes_entry = pygame_gui.elements.UITextEntryBox(
            ui_scale(pygame.Rect((100, 473), (600, 149))),
            initial_text=self.user_notes,
            object_id="#text_box_26_horizleft_pad_10_14",
            manager=MANAGER,
        )

        self.display_notes = UITextBoxTweaked(
            self.user_notes,
            ui_scale(pygame.Rect((100, 473), (60, 149))),
            object_id="#text_box_26_horizleft_pad_10_14",
            line_spacing=1,
            manager=MANAGER,
        )

        self.update_disabled_buttons_and_text()

    def save_user_notes(self):
        """Saves user-entered notes."""
        clanname = game.clan.name

        notes = self.user_notes

        notes_directory = get_save_dir() + "/" + clanname + "/notes"
        notes_file_path = notes_directory + "/" + self.the_cat.ID + "_notes.json"

        if not os.path.exists(notes_directory):
            os.makedirs(notes_directory)

        if (
            notes is None
            or notes == "Click the check mark to enter notes about your cat!"
        ):
            return

        new_notes = {str(self.the_cat.ID): notes}

        game.safe_save(notes_file_path, new_notes)

    def load_user_notes(self):
        """Loads user-entered notes."""
        clanname = game.clan.name

        notes_directory = get_save_dir() + "/" + clanname + "/notes"
        notes_file_path = notes_directory + "/" + self.the_cat.ID + "_notes.json"

        if not os.path.exists(notes_file_path):
            return

        try:
            with open(notes_file_path, "r") as read_file:
                rel_data = ujson.loads(read_file.read())
                self.user_notes = "Click the check mark to enter notes about your cat!"
                if str(self.the_cat.ID) in rel_data:
                    self.user_notes = rel_data.get(str(self.the_cat.ID))
        except Exception as e:
            print(
                f"ERROR: there was an error reading the Notes file of cat #{self.the_cat.ID}.\n",
                e,
            )

    def toggle_history_sub_tab(self):
        """To toggle the history-sub-tab"""

        if self.open_sub_tab == "life events":
            self.toggle_history_tab(sub_tab_switch=True)

        elif self.open_sub_tab == "user notes":
            self.toggle_user_notes_tab()

    def get_all_history_text(self):
        """Generates a string with all important history information."""
        output = ""
        if self.open_sub_tab == "life events":
            # start our history with the backstory, since all cats get one
            life_history = [str(self.get_backstory_text())]

            # now get apprenticeship history and add that if any exists
            app_history = self.get_apprenticeship_text()
            if app_history:
                life_history.append(app_history)

            # Get mentorship text if it exists
            mentor_history = self.get_mentorship_text()
            if mentor_history:
                life_history.append(mentor_history)

            # now go get the scar history and add that if any exists
            body_history = []
            scar_history = self.get_scar_text()
            if scar_history:
                body_history.append(scar_history)
            death_history = self.get_death_text()
            if death_history:
                body_history.append(death_history)
            # join scar and death into one paragraph
            if body_history:
                life_history.append(" ".join(body_history))

            murder = self.get_murder_text()
            if murder:
                life_history.append(murder)

            # join together history list with line breaks
            output = "\n\n".join(life_history)
        return output

    def get_living_cats(self):
        living_cats = []
        for the_cat in Cat.all_cats_list:
            if not the_cat.dead and not the_cat.outside and not the_cat.moons == -1:
                living_cats.append(the_cat)
        return living_cats

    def get_backstory_text(self):
        """
        returns the backstory blurb
        """
        cat_dict = {"m_c": (str(self.the_cat.name), choice(self.the_cat.pronouns))}
        bs_blurb = None
        if self.the_cat.backstory:
            bs_blurb = BACKSTORIES["backstories"][self.the_cat.backstory]
        if (
            self.the_cat.status in ["kittypet", "loner", "rogue", "former Clancat"]
            and self.the_cat.dead
        ):
            bs_blurb = f"This cat was a {self.the_cat.status} in life."
        elif self.the_cat.status in ["kittypet", "loner", "rogue", "former Clancat"]:
            bs_blurb = f"This cat is a {self.the_cat.status} and currently resides outside of the Clans."

        if bs_blurb is not None:
            adjust_text = str(bs_blurb).replace("This cat", str(self.the_cat.name))
            text = adjust_text
        else:
            text = str(self.the_cat.name) + "'s past history is unknown."

        beginning = History.get_beginning(self.the_cat)
        if beginning:
            if (
                ("encountered" in beginning and beginning['encountered'] is False)
                or "encountered" not in beginning
                ):
                if 'clan_born' in beginning and beginning['clan_born']:
                    text += " {PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} born on Moon " + str(
                        beginning['moon']) + " during " + str(beginning['birth_season']) + "."
                elif 'age' in beginning and beginning['age'] and not self.the_cat.outside:
                    text += " {PRONOUN/m_c/subject/CAP} joined the Clan on Moon " + str(
                        beginning['moon']) + " at the age of " + str(beginning['age']) + " Moons."
                else:
                    text += "<br>You met {PRONOUN/m_c/object} on Moon " + str(beginning['moon']) + "."
            else:
                text += "<br>You encountered {PRONOUN/m_c/object} on Moon " + str(beginning['moon']) + "."

        if self.the_cat.history and self.the_cat.history.wrong_placement and self.the_cat.dead and not self.the_cat.outside:
            if self.the_cat.df:
                text += f"<br>{self.the_cat.name} was wrongly placed in the Dark Forest."
            else:
                text += f"<br>{self.the_cat.name} was wrongly placed in StarClan."

        text = process_text(text, cat_dict)
        if "o_c_n" in text:
            if self.the_cat.backstory_str:
                text = text.replace("o_c_n", self.the_cat.backstory_str)
            else:
                other_clan = "a different Clan"
                if game.clan.all_clans:
                    other_clan = str(choice(game.clan.all_clans).name) + "Clan"
                self.the_cat.backstory_str = other_clan
                text = text.replace("o_c_n", other_clan)
        if "c_n" in text:
            text = text.replace("c_n", str(game.clan.name) + "Clan")
        if "r_c" in text:
            if self.the_cat.backstory_str:
                text = text.replace("r_c", self.the_cat.backstory_str)
            else:
                random_cat = choice(self.get_living_cats())
                counter = 0
                while random_cat.moons < self.the_cat.moons or random_cat.ID == self.the_cat.ID:
                    if counter == 30:
                        break
                    random_cat = choice(self.get_living_cats())
                    counter+=1
                self.the_cat.backstory_str = str(random_cat.name)
                text = text.replace("r_c", str(random_cat.name))
        return text

    def get_scar_text(self):
        """
        returns the adjusted scar text
        """
        scar_text = []
        scar_history = History.get_death_or_scars(self.the_cat, scar=True)
        if game.switches["show_history_moons"]:
            moons = True
        else:
            moons = False

        if scar_history:
            i = 0
            for scar in scar_history:
                # base adjustment to get the cat's name and moons if needed
                new_text = event_text_adjust(
                    Cat,
                    scar["text"],
                    main_cat=self.the_cat,
                    random_cat=Cat.fetch_cat(scar["involved"]),
                )

                if moons:
                    new_text += f" (Moon {scar['moon']})"

                # checking to see if we can throw out a duplicate
                if new_text in scar_text:
                    i += 1
                    continue

                # the first event keeps the cat's name, consecutive events get to switch it up a bit
                if i != 0:
                    sentence_beginners = [
                        "This cat",
                        "Then {PRONOUN/m_c/subject} {VERB/m_c/were/was}",
                        "{PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} also",
                        "Also, {PRONOUN/m_c/subject} {VERB/m_c/were/was}",
                        "As well as",
                        "{PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} then",
                    ]
                    chosen = choice(sentence_beginners)
                    if chosen == "This cat":
                        new_text = new_text.replace(str(self.the_cat.name), chosen, 1)
                    else:
                        new_text = new_text.replace(
                            f"{self.the_cat.name} was", f"{chosen}", 1
                        )
                cat_dict = {
                    "m_c": (str(self.the_cat.name), choice(self.the_cat.pronouns))
                }
                new_text = process_text(new_text, cat_dict)
                scar_text.append(new_text)
                i += 1

            scar_history = " ".join(scar_text)

        return scar_history

    def get_apprenticeship_text(self):
        """
        returns adjusted apprenticeship history text (mentor influence and app ceremony)
        """
        if self.the_cat.status in ["kittypet", "loner", "rogue", "former Clancat"]:
            return ""

        mentor_influence = History.get_mentor_influence(self.the_cat)
        influence_history = ""

        #First, just list the mentors:
        if self.the_cat.status in ['kitten', 'newborn']:
                influence_history = 'This cat has not begun training.'
        elif self.the_cat.status in ['apprentice', 'medicine cat apprentice', 'mediator apprentice', "queen's apprentice"]:
            influence_history = 'This cat has not finished training.'
        else:
            valid_formor_mentors = [
                Cat.fetch_cat(i)
                for i in self.the_cat.former_mentor
                if isinstance(Cat.fetch_cat(i), Cat)
            ]
            if valid_formor_mentors:
                influence_history += (
                    "{PRONOUN/m_c/subject/CAP} {VERB/m_c/were/was} mentored by "
                )
                if len(valid_formor_mentors) > 1:
                    influence_history += (
                        ", ".join([str(i.name) for i in valid_formor_mentors[:-1]])
                        + " and "
                        + str(valid_formor_mentors[-1].name)
                        + ". "
                    )
                else:
                    influence_history += str(valid_formor_mentors[0].name) + ". "
            else:
                influence_history += "This cat either did not have a mentor, or {PRONOUN/m_c/poss} mentor is unknown. "

            # Second, do the facet/personality effect
            trait_influence = []
            if "trait" in mentor_influence and isinstance(
                mentor_influence["trait"], dict
            ):
                for _mentor in mentor_influence["trait"]:
                    # If the strings are not set (empty list), continue.
                    if not mentor_influence["trait"][_mentor].get("strings"):
                        continue

                    ment_obj = Cat.fetch_cat(_mentor)
                    # Continue of the mentor is invalid too.
                    if not isinstance(ment_obj, Cat):
                        continue

                    if len(mentor_influence["trait"][_mentor].get("strings")) > 1:
                        string_snippet = (
                            ", ".join(
                                mentor_influence["trait"][_mentor].get("strings")[:-1]
                            )
                            + " and "
                            + mentor_influence["trait"][_mentor].get("strings")[-1]
                        )
                    else:
                        string_snippet = mentor_influence["trait"][_mentor].get(
                            "strings"
                        )[0]

                    trait_influence.append(
                        str(ment_obj.name)
                        + " influenced {PRONOUN/m_c/object} to be more likely to "
                        + string_snippet
                        + ". "
                    )

            influence_history += " ".join(trait_influence)

            skill_influence = []
            if "skill" in mentor_influence and isinstance(
                mentor_influence["skill"], dict
            ):
                for _mentor in mentor_influence["skill"]:
                    # If the strings are not set (empty list), continue.
                    if not mentor_influence["skill"][_mentor].get("strings"):
                        continue

                    ment_obj = Cat.fetch_cat(_mentor)
                    # Continue of the mentor is invalid too.
                    if not isinstance(ment_obj, Cat):
                        continue

                    if len(mentor_influence["skill"][_mentor].get("strings")) > 1:
                        string_snippet = (
                            ", ".join(
                                mentor_influence["skill"][_mentor].get("strings")[:-1]
                            )
                            + " and "
                            + mentor_influence["skill"][_mentor].get("strings")[-1]
                        )
                    else:
                        string_snippet = mentor_influence["skill"][_mentor].get(
                            "strings"
                        )[0]

                    skill_influence.append(
                        str(ment_obj.name)
                        + " helped {PRONOUN/m_c/object} become better at "
                        + string_snippet
                        + ". "
                    )

            influence_history += " ".join(skill_influence)

        app_ceremony = History.get_app_ceremony(self.the_cat)

        graduation_history = ""
        if app_ceremony:
            graduation_history = (
                "When {PRONOUN/m_c/subject} graduated, {PRONOUN/m_c/subject} {VERB/m_c/were/was} honored for {PRONOUN/m_c/poss} "
                + app_ceremony["honor"]
                + "."
            )

            grad_age = app_ceremony["graduation_age"]
            if int(grad_age) < 11:
                graduation_history += (
                    " {PRONOUN/m_c/poss/CAP} training went so well that {PRONOUN/m_c/subject} graduated early at "
                    + str(grad_age)
                    + " moons old."
                )
            elif int(grad_age) > 13:
                graduation_history += (
                    " {PRONOUN/m_c/subject/CAP} graduated late at "
                    + str(grad_age)
                    + " moons old."
                )
            else:
                graduation_history += (
                    " {PRONOUN/m_c/subject/CAP} graduated at "
                    + str(grad_age)
                    + " moons old."
                )

            if game.switches["show_history_moons"]:
                graduation_history += f" (Moon {app_ceremony['moon']})"
        cat_dict = {"m_c": (str(self.the_cat.name), choice(self.the_cat.pronouns))}
        apprenticeship_history = influence_history + " " + graduation_history
        apprenticeship_history = process_text(apprenticeship_history, cat_dict)
        return apprenticeship_history

    def get_mentorship_text(self):
        """

        returns full list of previously mentored apprentices.

        """

        text = ""
        # Doing this is two steps
        all_real_apprentices = [
            Cat.fetch_cat(i)
            for i in self.the_cat.former_apprentices
            if isinstance(Cat.fetch_cat(i), Cat)
        ]
        if all_real_apprentices:
            text = "{PRONOUN/m_c/subject/CAP} mentored "
            if len(all_real_apprentices) > 2:
                text += (
                    ", ".join([str(i.name) for i in all_real_apprentices[:-1]])
                    + ", and "
                    + str(all_real_apprentices[-1].name)
                    + "."
                )
            elif len(all_real_apprentices) == 2:
                text += (
                    str(all_real_apprentices[0].name)
                    + " and "
                    + str(all_real_apprentices[1].name)
                    + "."
                )
            elif len(all_real_apprentices) == 1:
                text += str(all_real_apprentices[0].name) + "."

            cat_dict = {"m_c": (str(self.the_cat.name), choice(self.the_cat.pronouns))}

            text = process_text(text, cat_dict)

        return text

    def get_text_for_murder_event(self, event, death):
        """Returns the adjusted murder history text for the victim"""

        if game.switches["show_history_moons"]:
            moons = True
        else:
            moons = False

        if event["text"] == death["text"] and event["moon"] == death["moon"]:
            if event["revealed"] is True:
                final_text = event_text_adjust(
                    Cat,
                    event["text"],
                    main_cat=self.the_cat,
                    random_cat=Cat.fetch_cat(death["involved"]),
                )

                if event.get("revelation_text"):
                    final_text = f"{final_text} {event['revelation_text']}"
                if moons:
                    if event.get("revelation_moon"):
                        final_text = f"{final_text} (Moon {event['revelation_moon']})."
                return final_text
            else:
                return event_text_adjust(
                    Cat,
                    event["text"],
                    main_cat=self.the_cat,
                    random_cat=Cat.fetch_cat(death["involved"]),
                )

        return None

    def get_death_text(self):
        """
        returns adjusted death history text
        """
        text = None
        death_history = self.the_cat.history.get_death_or_scars(
            self.the_cat, death=True
        )
        murder_history = self.the_cat.history.get_murders(self.the_cat)
        if game.switches["show_history_moons"]:
            moons = True
        else:
            moons = False

        if death_history:
            all_deaths = []
            death_number = len(death_history)
            multi_life_count = 0
            for index, death in enumerate(death_history):
                found_murder = (
                    False  # Add this line to track if a matching murder event is found
                )
                if "is_victim" in murder_history:
                    for event in murder_history["is_victim"]:
                        text = None
                        # text = self.get_text_for_murder_event(event, death)
                        if text is not None:
                            found_murder = True  # Update the flag if a matching murder event is found
                            break

                        if found_murder and text is not None and not event["revealed"]:
                            text = event_text_adjust(
                                Cat,
                                event["text"],
                                main_cat=self.the_cat,
                                random_cat=Cat.fetch_cat(death["involved"]),
                            )
                if not found_murder:
                    text = event_text_adjust(
                        Cat,
                        death["text"],
                        main_cat=self.the_cat,
                        random_cat=Cat.fetch_cat(death["involved"]),
                    )

                if self.the_cat.status == "leader":
                    if text == "multi_lives":
                        multi_life_count += 1
                        continue
                    if index == death_number - 1 and self.the_cat.dead:
                        if death_number == 9:
                            life_text = "lost {PRONOUN/m_c/poss} final life"
                        elif death_number == 1:
                            life_text = "lost all of {PRONOUN/m_c/poss} lives"
                        else:
                            life_text = "lost the rest of {PRONOUN/m_c/poss} lives"
                    else:
                        life_names = [
                            "first",
                            "second",
                            "third",
                            "fourth",
                            "fifth",
                            "sixth",
                            "seventh",
                            "eighth",
                        ]
                        if multi_life_count != 0:
                            temp_index = index - multi_life_count
                            lives = [life_names[temp_index]]
                            while multi_life_count != 0:
                                multi_life_count -= 1
                                temp_index += 1
                                lives.append(life_names[temp_index])
                        else:
                            lives = [life_names[index]]
                        life_text = (
                            "lost {PRONOUN/m_c/poss} "
                            + adjust_list_text(lives)
                            + (" life" if len(lives) == 1 else " lives")
                        )
                elif death_number > 1:
                    # for retired leaders
                    if index == death_number - 1 and self.the_cat.dead:
                        life_text = "lost {PRONOUN/m_c/poss} last remaining life"
                        # added code
                        if "This cat was" in text:
                            text = text.replace("This cat was", "{VERB/m_c/were/was}")
                        else:
                            text = text[0].lower() + text[1:]
                    else:
                        life_text = "lost a life"
                else:
                    life_text = ""

                if text:
                    if life_text:
                        text = f"{life_text} when {{PRONOUN/m_c/subject}} {text}"
                    else:
                        text = f"{text}"

                    if moons:
                        text += f" (Moon {death['moon']})"
                    all_deaths.append(text)

            if self.the_cat.status == "leader" or death_number > 1:
                if death_number > 1:
                    deaths = str("\n" + str(self.the_cat.name) + " ").join(all_deaths)
                else:
                    deaths = all_deaths[0]

                if not deaths.endswith("."):
                    deaths += "."

                text = str(self.the_cat.name) + " " + deaths

            else:
                text = all_deaths[0]

            cat_dict = {"m_c": (str(self.the_cat.name), choice(self.the_cat.pronouns))}
            text = process_text(text, cat_dict)

        return text

    def get_murder_text(self):
        """
        returns adjusted murder history text FOR THE MURDERER

        """
        murder_history = History.get_murders(self.the_cat)
        victim_text = ""

        if game.switches["show_history_moons"]:
            moons = True
        else:
            moons = False
        victims = []
        if murder_history:
            if "is_murderer" in murder_history:
                victims = murder_history["is_murderer"]

        if len(victims) > 0:
            victim_names = {}
            name_list = []
            reveal_text = None

            for victim in victims:
                if not Cat.fetch_cat(victim["victim"]):
                    continue
                name = str(Cat.fetch_cat(victim["victim"]).name)

                if victim["revealed"]:
                    victim_names[name] = []
                    if victim.get("revelation_text"):
                        reveal_text = victim["revelation_text"]
                    if moons:
                        victim_names[name].append(victim["moon"])
                        if victim.get("revelation_moon"):
                            reveal_text = (
                                f"{reveal_text} (Moon {victim['revelation_moon']})"
                            )

            if victim_names:
                for name in victim_names:
                    if not moons:
                        name_list.append(name)
                    else:
                        name_list.append(f"{name} (Moon {victim_names[name][0]})")

                if len(name_list) == 1:
                    victim_text = f"{self.the_cat.name} murdered {name_list[0]}."
                elif len(victim_names) == 2:
                    victim_text = (
                        f"{self.the_cat.name} murdered {' and '.join(name_list)}."
                    )
                else:
                    victim_text = f"{self.the_cat.name} murdered {', '.join(name_list[:-1])}, and {name_list[-1]}."

            if reveal_text:
                cat_dict = {
                    "m_c": (str(self.the_cat.name), choice(self.the_cat.pronouns))
                }
                victim_text = f"{victim_text} {process_text(reveal_text, cat_dict)}"

        return victim_text

    def toggle_conditions_tab(self):
        """Opens the conditions tab"""
        previous_open_tab = self.open_tab
        # This closes the current tab, so only one can be open at a time
        self.close_current_tab()

        if previous_open_tab == "conditions":
            """If the current open tab is conditions, just close the tab and do nothing else."""
            pass
        else:
            self.open_tab = "conditions"
            self.conditions_page = 0

            rect = ui_scale(pygame.Rect((0, 0), (624, 151)))
            rect.bottomleft = ui_scale_offset((0, 0))
            self.conditions_background = pygame_gui.elements.UIImage(
                rect,
                self.conditions_tab,
                starting_height=2,
                anchors={
                    "bottom": "bottom",
                    "bottom_target": self.conditions_tab_button,
                    "centerx": "centerx",
                },
            )
            del rect

            rect = ui_scale(pygame.Rect((-5, 537), (34, 34)))
            self.right_conditions_arrow = UISurfaceImageButton(
                rect,
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                manager=MANAGER,
                anchors={"left_target": self.conditions_background},
            )
            del rect

            rect = ui_scale(pygame.Rect((0, 0), (34, 34)))
            rect.topright = ui_scale_offset((5, 537))
            self.left_conditions_arrow = UISurfaceImageButton(
                rect,
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                anchors={"right": "right", "right_target": self.conditions_background},
            )
            del rect

            # This will be overwritten in update_disabled_buttons_and_text()
            self.update_disabled_buttons_and_text()

    def display_conditions_page(self):
        # tracks the position of the detail boxes
        if self.condition_container:
            self.condition_container.kill()

        self.condition_container = pygame_gui.core.UIContainer(
            ui_scale(pygame.Rect((89, 471), (624, 151))), MANAGER
        )

        # gather a list of all the conditions and info needed.
        all_illness_injuries = [
            (i, self.get_condition_details(i))
            for i in self.the_cat.permanent_condition
            if not (
                self.the_cat.permanent_condition[i]["born_with"]
                and self.the_cat.permanent_condition[i]["moons_until"] != -2
            )
        ]
        all_illness_injuries.extend(
            [(i, self.get_condition_details(i)) for i in self.the_cat.injuries]
        )
        all_illness_injuries.extend(
            [
                (i, self.get_condition_details(i))
                for i in self.the_cat.illnesses
                if i not in ("an infected wound", "a festering wound")
            ]
        )
        all_illness_injuries = chunks(all_illness_injuries, 4)

        if not all_illness_injuries:
            self.conditions_page = 0
            self.right_conditions_arrow.disable()
            self.left_conditions_arrow.disable()
            return

        # Adjust the page number if it somehow goes out of range.
        if self.conditions_page < 0:
            self.conditions_page = 0
        elif self.conditions_page > len(all_illness_injuries) - 1:
            self.conditions_page = len(all_illness_injuries) - 1

        # Disable the arrow buttons
        if self.conditions_page == 0:
            self.left_conditions_arrow.disable()
        else:
            self.left_conditions_arrow.enable()

        if self.conditions_page >= len(all_illness_injuries) - 1:
            self.right_conditions_arrow.disable()
        else:
            self.right_conditions_arrow.enable()

        x_pos = 13
        for x in self.condition_data.values():
            x.kill()
        self.condition_data = {}
        for con in all_illness_injuries[self.conditions_page]:
            # Background Box
            self.condition_data[f"bg_{con}"] = pygame_gui.elements.UIPanel(
                ui_scale(pygame.Rect((x_pos, 13), (142, 142))),
                manager=MANAGER,
                container=self.condition_container,
                object_id="#profile_condition_panel",
                margins={"left": 0, "right": 0, "top": 0, "bottom": 0},
            )

            self.condition_data[f"name_{con}"] = UITextBoxTweaked(
                con[0],
                ui_scale(pygame.Rect((0, 0), (120, -1))),
                line_spacing=0.90,
                object_id="#text_box_30_horizcenter",
                container=self.condition_data[f"bg_{con}"],
                manager=MANAGER,
                anchors={"centerx": "centerx"},
            )

            y_adjust = self.condition_data[f"name_{con}"].get_relative_rect().height
            details_rect = ui_scale(pygame.Rect((0, 0), (142, 100)))
            details_rect.bottomleft = (0, 0)

            self.condition_data[f"desc_{con}"] = UITextBoxTweaked(
                con[1],
                details_rect,
                line_spacing=0.75,
                object_id="#text_box_22_horizcenter",
                container=self.condition_data[f"bg_{con}"],
                manager=MANAGER,
                anchors={"bottom": "bottom", "centerx": "centerx"},
            )

            x_pos += 152
        return

    def get_condition_details(self, name):
        """returns the relevant condition details as one string with line breaks"""
        text_list = []
        cat_name = self.the_cat.name

        # collect details for perm conditions
        if name in self.the_cat.permanent_condition:
            # display if the cat was born with it
            if self.the_cat.permanent_condition[name]["born_with"] is True:
                text_list.append(f"born with this condition")
            else:
                # moons with the condition if not born with condition
                moons_with = (
                    game.clan.age - self.the_cat.permanent_condition[name]["moon_start"]
                )
                if moons_with != 1:
                    text_list.append(f"has had this condition for {moons_with} moons")
                else:
                    text_list.append(f"has had this condition for 1 moon")

            # is permanent
            text_list.append("permanent condition")

            # infected or festering
            complication = self.the_cat.permanent_condition[name].get(
                "complication", None
            )
            if complication is not None:
                if "a festering wound" in self.the_cat.illnesses:
                    complication = "festering"
                text_list.append(f"is {complication}!")

        # collect details for injuries
        if name in self.the_cat.injuries:
            # moons with condition
            keys = self.the_cat.injuries[name].keys()
            moons_with = game.clan.age - self.the_cat.injuries[name]["moon_start"]
            insert = "has been hurt for"

            if name == 'recovering from birth':
                insert = 'has been recovering for'
            elif name == 'pregnant':
                insert = 'has been pregnant for'
            elif name == 'guilt':
                insert = 'has been troubled for'
            
            if moons_with != 1:
                text_list.append(f"{insert} {moons_with} moons")
            else:
                text_list.append(f"{insert} 1 moon")

            # infected or festering
            if "complication" in keys:
                complication = self.the_cat.injuries[name]["complication"]
                if complication is not None:
                    if "a festering wound" in self.the_cat.illnesses:
                        complication = "festering"
                    text_list.append(f"is {complication}!")

            # can or can't patrol
            if self.the_cat.injuries[name]["severity"] != "minor":
                text_list.append("Can't work with this condition")

        # collect details for illnesses
        if name in self.the_cat.illnesses:
            # moons with condition
            moons_with = game.clan.age - self.the_cat.illnesses[name]["moon_start"]
            insert = "has been sick for"

            if name == "grief stricken":
                insert = "has been grieving for"

            if moons_with != 1:
                text_list.append(f"{insert} {moons_with} moons")
            else:
                text_list.append(f"{insert} 1 moon")

            if self.the_cat.illnesses[name]["infectiousness"] != 0:
                text_list.append("infectious!")

            # can or can't patrol
            if self.the_cat.illnesses[name]["severity"] != "minor":
                text_list.append("Can't work with this condition")

        text = "<br><br>".join(text_list)
        return text
    
    def toggle_faith_tab(self):
        """Opens faith tab"""
        previous_open_tab = self.open_tab
        self.close_current_tab()

        if previous_open_tab == 'faith':
            pass
        else:
            self.open_tab = "faith"
            rect = ui_scale(pygame.Rect((0, 0), (620, 157)))
            rect.bottomleft = ui_scale_offset((89, 0))
            self.backstory_background = pygame_gui.elements.UIImage(
                rect,
                get_box(
                    BoxStyles.ROUNDED_BOX, (620, 157), sides=(True, True, False, True)
                ),
                anchors={
                    "bottom": "bottom",
                    "bottom_target": self.conditions_tab_button,
                },
            )
            self.backstory_background.disable()
            self.open_faith_tab()
            self.update_disabled_buttons_and_text()

    def open_faith_tab(self):
        if self.faith_bar and self.faith_text:
            self.faith_bar.kill()
            self.faith_text.kill()
        if self.the_cat.no_faith:
            self.the_cat.faith = 0
        cat_faith = round(self.the_cat.faith)
        if self.the_cat.lock_faith == "flexible":
            if cat_faith > 9:
                cat_faith = 9
            elif cat_faith < -9:
                cat_faith = -9
        elif self.the_cat.lock_faith == "starclan":
            if cat_faith > 9:
                cat_faith = 9
            elif cat_faith < 1:
                cat_faith = 1
        elif self.the_cat.lock_faith == "dark forest":
            if cat_faith > -1:
                cat_faith = -1
            elif cat_faith < -9:
                cat_faith = 9
        elif self.the_cat.lock_faith == "neutral":
            if cat_faith > 3:
                cat_faith = 3
            elif cat_faith < -3:
                cat_faith = -3
        self.faith_bar = pygame_gui.elements.UIImage(ui_scale(pygame.Rect((175, 500), (421, 39))),
                                                                image_cache.load_image(f"resources/images/faith{cat_faith}.png").convert_alpha())
        self.faith_bar.disable()
        self.faith_text = UITextBoxTweaked(self.get_faith_text(cat_faith),
                                                        ui_scale(pygame.Rect((175, 535), (425,75))),
                                                        object_id="#text_box_26_horizleft_pad_10_14",
                                                        line_spacing=1, manager=MANAGER)
        
    def get_faith_text(self, faith):
        faith_dict = {}
        with open("resources/dicts/faith_display.json", "r") as read_file:
            faith_dict = ujson.loads(read_file.read())
            cluster1, cluster2 = get_cluster(self.the_cat.personality.trait)

        faith_text = ""
        if faith == 0:
            faith_text = faith_dict[str(faith)]["All"]
        else:
            faith_text = faith_dict[str(faith)][str(cluster1)]

        process_text_dict = {}
        process_text_dict["m_c"] = self.the_cat
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))
        faith_text = sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), faith_text)
        
        return faith_text
    
    def toggle_accessories_tab(self):
        """Opens accessories tab"""

        previous_open_tab = self.open_tab

        self.close_current_tab()
        self.page = 0


        if previous_open_tab == 'accessories':
            pass
        else:
            self.open_tab = "accessories"
            rect = ui_scale(pygame.Rect((0, 0), (620, 157)))
            rect.bottomleft = ui_scale_offset((89, 0))
            self.backstory_background = pygame_gui.elements.UIImage(
                rect,
                get_box(
                    BoxStyles.ROUNDED_BOX, (620, 157), sides=(True, True, False, True)
                ),
                anchors={
                    "bottom": "bottom",
                    "bottom_target": self.conditions_tab_button,
                },
            )
            self.backstory_background.disable()

            self.clear_accessories = UIImageButton(
                ui_scale(pygame.Rect((709, 580), (34, 34))),
                "",
                object_id="#exit_window_button",
                tool_tip_text="Take off all worn accessories",
                manager=MANAGER
                )

            self.delete_accessory = UIImageButton(
                ui_scale(pygame.Rect((709, 542), (34, 34))),
                "",
                object_id="#exit_window_button",
                tool_tip_text="Remove worn accessories from inventory",
                manager=MANAGER
                )
            
            self.next_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((709, 500), (34, 34))),
                Icon.ARROW_RIGHT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                manager=MANAGER,
            )
            self.previous_page_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((55, 500), (34, 34))),
                Icon.ARROW_LEFT,
                get_button_dict(ButtonStyles.ICON, (34, 34)),
                object_id="@buttonstyles_icon",
                manager=MANAGER,
            )

            self.search_bar_image = pygame_gui.elements.UIImage(ui_scale(pygame.Rect((119, 455), (118, 34))),
                                                            pygame.image.load(
                                                                "resources/images/search_bar.png").convert_alpha(),
                                                            manager=MANAGER)
            self.search_bar = pygame_gui.elements.UITextEntryLine(ui_scale(pygame.Rect((129, 457), (102, 27))),
                                                              object_id="#search_entry_box",
                                                              initial_text="search",
                                                              manager=MANAGER)
            self.open_accessories()
            self.update_disabled_buttons_and_text()

    # def update_accessories(self):


    def open_accessories(self):

        cat = self.the_cat
        age = cat.age
        cat_sprite = str(cat.pelt.cat_sprites[cat.age])

        # setting the cat_sprite (bc this makes things much easier)
        if cat.not_working() and age != 'newborn' and game.config['cat_sprites']['sick_sprites']:
            if age in ['kitten', 'adolescent']:
                cat_sprite = str(19)
            else:
                cat_sprite = str(18)
        elif cat.pelt.paralyzed and age != 'newborn':
            if age in ['kitten', 'adolescent']:
                cat_sprite = str(17)
            else:
                if cat.pelt.length == 'long':
                    cat_sprite = str(16)
                else:
                    cat_sprite = str(15)
        else:
            if age == 'elder' and not game.config['fun']['all_cats_are_newborn']:
                age = 'senior'

            if game.config['fun']['all_cats_are_newborn']:
                cat_sprite = str(cat.pelt.cat_sprites['newborn'])
            else:
                cat_sprite = str(cat.pelt.cat_sprites[age])

        pos_x = 10
        pos_y = 125
        i = 0

        self.cat_list_buttons = {}
        self.accessory_buttons = {}
        self.accessories_list = []
        start_index = self.page * 18
        end_index = start_index + 18

        # correcting duplicates
        acc_list = []
        for acc in self.the_cat.pelt.inventory:
            if acc not in acc_list:
                acc_list.append(acc)
            else:
                # print("Removing duplicate", acc, "from", self.the_cat.name, "'s inventory.")
                self.the_cat.pelt.inventory.remove(acc)

        inventory_len = 0
        new_inv = []
        if self.search_bar.get_text() in ["", "search"]:
            inventory_len = len(self.cat_inventory)
            new_inv = self.cat_inventory
        else:
            for ac in self.cat_inventory:
                if ac and self.search_bar.get_text() and self.search_bar.get_text().lower() in ac.lower():
                    inventory_len+=1
                    new_inv.append(ac)
        self.max_pages = math.ceil(inventory_len/18)
        
        if (self.max_pages == 1 or self.max_pages == 0):
            self.previous_page_button.disable()
            self.next_page_button.disable()
        if self.page == 0:
            self.previous_page_button.disable()
        if self.cat_inventory:
            for a, accessory in enumerate(new_inv[start_index:min(end_index, inventory_len)], start = start_index):
                if self.search_bar.get_text() in ["", "search"] or self.search_bar.get_text().lower() in accessory.lower():
                    self.inventory_display(cat, cat_sprite, accessory, pos_x, pos_y)
                    self.accessories_list.append(accessory)
                    pos_x += 60
                    if pos_x >= 550:
                        pos_x = 0
                        pos_y += 60

    def toggle_relations_tab(self):
        """Opens relations tab"""
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == "relations":
            """If the current open tab is relations, just close the tab and do nothing else."""
            pass
        else:
            self.open_tab = "relations"
            self.family_tree_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((50, 450), (172, 36))),
                "family tree",
                get_button_dict(ButtonStyles.LADDER_TOP, (172, 36)),
                object_id="@buttonstyles_ladder_top",
                starting_height=2,
                manager=MANAGER,
            )
            self.change_adoptive_parent_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((50, 486), (172, 36))),
                "adoptive parents",
                get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
                object_id="@buttonstyles_ladder_middle",
                starting_height=2,
                manager=MANAGER,
            )
            self.see_relationships_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((50, 522), (172, 36))),
                "see relationships",
                get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
                object_id="@buttonstyles_ladder_middle",
                starting_height=2,
                manager=MANAGER,
            )
            self.choose_mate_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((50, 558), (172, 36))),
                "choose mate",
                get_button_dict(ButtonStyles.LADDER_BOTTOM, (172, 36)),
                object_id="@buttonstyles_ladder_bottom",
                starting_height=2,
                manager=MANAGER,
            )
            self.update_disabled_buttons_and_text()

    def toggle_your_tab(self):
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == 'your tab':
            '''If the current open tab is relations, just close the tab and do nothing else. '''
            pass
        else:
            self.open_tab = 'your tab'
            self.have_kits_button = None
            self.request_apprentice_button = None
            self.gift_accessory_button = None
            self.your_faith_button = None
            self.update_disabled_buttons_and_text()

    def toggle_roles_tab(self):
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == "roles":
            """If the current open tab is roles, just close the tab and do nothing else."""
            pass
        else:
            self.open_tab = "roles"

            self.manage_roles = UISurfaceImageButton(
                ui_scale(pygame.Rect((226, 450), (172, 36))),
                "manage roles",
                get_button_dict(ButtonStyles.LADDER_TOP, (172, 36)),
                object_id="@buttonstyles_ladder_top",
                starting_height=2,
                manager=MANAGER,
            )
            self.change_mentor_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((226, 486), (172, 36))),
                "change mentor",
                get_button_dict(ButtonStyles.LADDER_BOTTOM, (172, 36)),
                object_id="@buttonstyles_ladder_bottom",
                starting_height=2,
                manager=MANAGER,
            )
            self.manage_nobility = UISurfaceImageButton(
                ui_scale(pygame.Rect((226, 522), (172, 36))),
                "manage nobility",
                get_button_dict(ButtonStyles.LADDER_BOTTOM, (172, 36)),
                object_id="@buttonstyles_ladder_bottom",
                starting_height=2,
                manager=MANAGER,
            )
            self.update_disabled_buttons_and_text()

    def toggle_personal_tab(self):
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == "personal":
            """If the current open tab is personal, just close the tab and do nothing else."""
            pass
        else:
            self.open_tab = "personal"
            self.change_name_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((402, 450), (172, 36))),
                "change name",
                get_button_dict(ButtonStyles.LADDER_TOP, (172, 36)),
                object_id="@buttonstyles_ladder_top",
                starting_height=2,
                manager=MANAGER,
            )
            self.cis_trans_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((402, 0), (172, 52))),
                "debug\nuwu",
                get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 52)),
                object_id="@buttonstyles_ladder_middle",
                text_layer_object_id="@buttonstyles_ladder_multiline",
                starting_height=2,
                manager=MANAGER,
                anchors={"top_target": self.change_name_button},
                text_is_multiline=True,
            )
            self.specify_gender_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((402, 0), (172, 36))),
                "specify gender",
                get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
                object_id="@buttonstyles_ladder_middle",
                starting_height=2,
                manager=MANAGER,
                anchors={"top_target": self.cis_trans_button},
            )
            self.cat_toggles_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((402, 0), (172, 36))),
                "cat toggles",
                get_button_dict(ButtonStyles.LADDER_BOTTOM, (172, 36)),
                object_id="@buttonstyles_ladder_bottom",
                starting_height=2,
                manager=MANAGER,
                anchors={"top_target": self.specify_gender_button},
            )

            self.update_disabled_buttons_and_text()

    def toggle_dangerous_tab(self):
        # Save what is previously open, for toggle purposes.
        previous_open_tab = self.open_tab

        # This closes the current tab, so only one can be open as a time
        self.close_current_tab()

        if previous_open_tab == "dangerous":
            """If the current open tab is dangerous, just close the tab and do nothing else."""
            pass
        else:
            self.open_tab = "dangerous"
            self.exile_cat_button = UIImageButton(
                ui_scale(pygame.Rect((578, 450), (172, 36))),
                "",
                object_id="#exile_cat_button",
                tool_tip_text="This cannot be reversed.",
                starting_height=2,
                manager=MANAGER,
            )
            self.kill_cat_button = UIImageButton(
                ui_scale(pygame.Rect((578, 486), (172, 36))),
                "",
                object_id="#kill_cat_button",
                tool_tip_text="This will open a confirmation window and allow you to input a death reason",
                starting_height=2,
                manager=MANAGER,
            )
            self.murder_cat_button = UIImageButton(
                ui_scale(pygame.Rect((578, 522), (172, 36))),
                "",
                object_id="#murder_button",
                tool_tip_text='Choose to murder one of your clanmates',
                starting_height=2, manager=MANAGER
            )
            if game.clan.your_cat.moons == 0:
                self.murder_cat_button.disable()
            
            if "moon" in game.clan.murdered and game.clan.murdered["moon"] == game.clan.age:
                self.murder_cat_button.disable()
                
            if game.clan.your_cat.joined_df:
                self.exit_df_button = UIImageButton(
                ui_scale(pygame.Rect((578, 558), (172, 36))),
                "",
                object_id="#exit_df_button",
                tool_tip_text='Leave the Dark Forest',
                starting_height=2, manager=MANAGER
                )
            else:
                self.join_df_button = UIImageButton(
                ui_scale(pygame.Rect((578, 558), (172, 36))),
                "",
                object_id="#join_df_button",
                tool_tip_text='Join the Dark Forest',
                starting_height=2, manager=MANAGER
            )
            if game.clan.your_cat.moons < 6:
                self.join_df_button.disable()
            self.affair_button = UIImageButton(
                ui_scale(pygame.Rect((578, 594), (172, 36))),
                "",
                object_id="#affair_button",
                tool_tip_text='Have an affair with one of your clanmates',
                starting_height=2, manager=MANAGER
            )
            if len(game.clan.your_cat.mates) == 0 or game.clan.affair:
                self.affair_button.disable()
            if game.clan.your_cat.mates:
                alive_mate = False
                for m in game.clan.your_cat.mates:
                    if Cat.all_cats.get(m).dead == False:
                        alive_mate = True
                if not alive_mate:
                    self.affair_button.disable()

            # These are a placeholders, to be killed and recreated in self.update_disabled_buttons_and_text().
            #   This it due to the image switch depending on the cat's status, and the location switch the close button
            #    If you can think of a better way to do this, please fix!
            self.update_disabled_buttons_and_text()

    def update_disabled_buttons_and_text(self):
        """Sets which tab buttons should be disabled. This is run when the cat is switched. """
        if self.the_cat.moons == 0:
            self.accessories_tab_button.disable()
        else:
            self.accessories_tab_button.enable()
        if self.open_tab is None:
            pass
        elif self.open_tab == "relations":
            if self.the_cat.dead:
                self.see_relationships_button.disable()
                self.change_adoptive_parent_button.disable()
            else:
                self.see_relationships_button.enable()
                self.change_adoptive_parent_button.enable()

            if (
                self.the_cat.age
                not in ["young adult", "adult", "senior adult", "senior"]
                or self.the_cat.exiled
                or self.the_cat.outside
            ):
                self.choose_mate_button.disable()
            else:
                self.choose_mate_button.enable()

        # Roles Tab
        elif self.open_tab == "roles":
            if self.the_cat.dead or self.the_cat.outside:
                self.manage_roles.disable()
                self.manage_nobility.disable()
            else:
                self.manage_roles.enable()
                self.manage_nobility.enable()
            if self.the_cat.status not in ['apprentice', 'medicine cat apprentice', 'mediator apprentice', "queen's apprentice"] \
                                            or self.the_cat.dead or self.the_cat.outside:
                self.change_mentor_button.disable()
            else:
                self.change_mentor_button.enable()

        elif self.open_tab == "personal":
            # Button to trans or cis the cats.
            if self.the_cat.gender == "male" and self.the_cat.genderalign == "male":
                self.cis_trans_button.set_text("change to trans\nfemale")
            elif (
                self.the_cat.gender == "female" and self.the_cat.genderalign == "female"
            ):
                self.cis_trans_button.set_text("change to trans\nmale")
            elif self.the_cat.genderalign in ["trans female", "trans male"]:
                self.cis_trans_button.set_text("change to\nnonbinary")
            elif self.the_cat.genderalign not in [
                "female",
                "trans female",
                "male",
                "trans male",
            ]:
                self.cis_trans_button.set_text("change to \ncisgender")
            elif self.the_cat.gender == "male" and self.the_cat.genderalign == "female":
                self.cis_trans_button.set_text("change to \ncisgender")
            elif self.the_cat.gender == "female" and self.the_cat.genderalign == "male":
                self.cis_trans_button.set_text("change to \ncisgender")
            elif self.the_cat.genderalign:
                self.cis_trans_button.set_text("change to \ncisgender")
            else:
                self.cis_trans_button.set_text("change to \ncisgender")
                self.cis_trans_button.disable()

        elif self.open_tab == 'your tab':
            if 'have kits' not in game.switches:
                    game.switches['have kits'] = True
            self.have_kits_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((402, 580), (172, 36))),
                "have kits",
                get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
                object_id="@buttonstyles_ladder_middle",
                starting_height=2,
                tool_tip_text='You will be more likely to have kits the next moon.',
                manager=MANAGER,
                anchors={
                    "bottom_target": self.your_tab},
            )
            if self.the_cat.age in ['young adult', 'adult', 'senior adult', 'senior'] and not self.the_cat.dead and not self.the_cat.outside and game.switches['have kits']:
                self.have_kits_button.enable()
            else:
                self.have_kits_button.disable()

            self.request_apprentice_button = UISurfaceImageButton(
                    ui_scale(pygame.Rect((402, 544), (172, 36))),
                    "request apprentice",
                    get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
                    object_id="@buttonstyles_ladder_middle",
                    starting_height=2,
                    tool_tip_text='You will be more likely to receive an apprentice.', 
                    manager=MANAGER,
                    anchors={
                        "bottom_target": self.have_kits_button},
                )
            
            if self.the_cat.status in ['leader', 'deputy', 'medicine cat', 'mediator', 'queen', 'warrior'] and not self.the_cat.dead and not self.the_cat.outside:
                self.request_apprentice_button.enable()
            else:
                self.request_apprentice_button.disable()
            
            self.gift_accessory_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((402, 508), (172, 36))),
                "give a gift",
                get_button_dict(ButtonStyles.LADDER_MIDDLE, (172, 36)),
                object_id="@buttonstyles_ladder_middle",
                starting_height=2,
                manager=MANAGER,
                anchors={
                    "bottom_target": self.request_apprentice_button},
            )
            if (
                self.the_cat.moons > 0
                and not self.the_cat.dead
                and not self.the_cat.outside
                and len(self.cat_inventory) > 0
                ):
               
                self.gift_accessory_button.enable()
            else:
                self.gift_accessory_button.disable()

            self.your_faith_button = UISurfaceImageButton(
                ui_scale(pygame.Rect((402, 472), (172, 36))),
                "faith",
                get_button_dict(ButtonStyles.LADDER_TOP, (172, 36)),
                object_id="@buttonstyles_ladder_top",
                starting_height=2,
                manager=MANAGER,
                anchors={
                    "bottom_target": self.gift_accessory_button},
            )
            if self.the_cat.status not in ["newborn", "kitten"] and not self.the_cat.dead and not self.the_cat.outside:
                self.your_faith_button.enable()
            else:
                self.your_faith_button.disable()
            

            if 'request apprentice' in game.switches:
                if game.switches['request apprentice']:
                    self.request_apprentice_button.disable()

        # Dangerous Tab
        elif self.open_tab == "dangerous":
            # Button to exile cat
            if self.exile_cat_button:
                self.exile_cat_button.kill()
            if not self.the_cat.dead:
                self.exile_cat_button = UIImageButton(
                    ui_scale(pygame.Rect((578, 450), (172, 36))),
                    "",
                    object_id="#exile_cat_button",
                    tool_tip_text="This cannot be reversed.",
                    starting_height=2,
                    manager=MANAGER,
                )
                if self.the_cat.exiled or self.the_cat.outside:
                    self.exile_cat_button.disable()

            elif self.the_cat.dead:
                if not self.the_cat.outside and not self.the_cat.df:
                    dead_button = "#exile_df_button"
                elif self.the_cat.df and not self.the_cat.outside:
                    dead_button = "#send_ur_button"
                else:
                    dead_button = "#guide_sc_button"

                if game.clan.instructor.ID == self.the_cat.ID:
                    self.exile_cat_button = UIImageButton(ui_scale(pygame.Rect((578, 450), (172, 46))),
                                                            "",
                                                          object_id= "#follow_sc_button",
                                                           tool_tip_text='Your Clan will go to StarClan'
                                                                         ' after death.',

                                                          starting_height=2, manager=MANAGER)

                    if game.clan.followingsc:
                        self.exile_cat_button.disable()

                elif game.clan.demon.ID == self.the_cat.ID:
                    self.exile_cat_button = UIImageButton(ui_scale(pygame.Rect((578, 450), (172, 46))),
                                                            "",
                                                          object_id= "#follow_df_button",
                                                          tool_tip_text='Your Clan will go to the Dark'
                                                                         ' forest after death.',
                                                          starting_height=2, manager=MANAGER)
                    if not game.clan.followingsc:
                        self.exile_cat_button.disable()

                else:
                    self.exile_cat_button = UIImageButton(ui_scale(pygame.Rect((578, 450), (172, 46))),
                                                          "",
                                                          object_id=dead_button,
                                                          starting_height=2, manager=MANAGER)

            if not self.the_cat.dead:
                self.kill_cat_button.enable()
            else:
                self.kill_cat_button.disable()

            if self.the_cat.ID != game.clan.your_cat.ID:
                self.murder_cat_button.hide()
                if self.join_df_button:
                    self.join_df_button.hide()
                if self.exit_df_button:
                    self.exit_df_button.hide()
                self.affair_button.hide()
            else:
                self.murder_cat_button.show()
                if self.join_df_button:
                    self.join_df_button.show()
                if self.exit_df_button:
                    self.exit_df_button.show()
                if game.clan.your_cat.dead or game.clan.your_cat.outside:
                    self.murder_cat_button.disable()
                    if self.join_df_button:
                        self.join_df_button.disable()
                    if self.exit_df_button:
                        self.exit_df_button.disable()
                self.affair_button.show()

            if game.clan.your_cat.status == 'kitten':
                if self.join_df_button:
                    self.join_df_button.hide()
                elif self.exit_df_button:
                    self.exit_df_button.hide()
                if self.affair_button:
                    self.affair_button.hide()
        elif self.open_tab == "accessories":
            for i in self.cat_list_buttons:
                self.cat_list_buttons[i].kill()
            for i in self.accessory_buttons:
                self.accessory_buttons[i].kill()

            if game.clan.clan_settings['all accessories']:
                self.delete_accessory.disable()
            else:
                self.delete_accessory.enable()
            
            self.open_accessories()
        elif self.open_tab == "faith":
            self.open_faith_tab()
        # History Tab:
        elif self.open_tab == "history":
            # show/hide fav tab star
            if self.open_sub_tab == game.switches["favorite_sub_tab"]:
                self.fav_tab.show()
                self.not_fav_tab.hide()
            else:
                self.fav_tab.hide()
                self.not_fav_tab.show()

            if self.open_sub_tab == "life events":
                self.sub_tab_1.disable()
                self.sub_tab_2.enable()
                self.history_text_box.kill()
                self.history_text_box = UITextBoxTweaked(
                    self.get_all_history_text(),
                    ui_scale(pygame.Rect((100, 473), (600, 149))),
                    object_id="#text_box_26_horizleft_pad_10_14",
                    line_spacing=1,
                    manager=MANAGER,
                )

                self.no_moons.kill()
                self.show_moons.kill()
                self.no_moons = UIImageButton(
                    ui_scale(pygame.Rect((52, 514), (34, 34))),
                    "",
                    object_id="@unchecked_checkbox",
                    tool_tip_text="Show the Moon that certain history events occurred on",
                    manager=MANAGER,
                )
                self.show_moons = UIImageButton(
                    ui_scale(pygame.Rect((52, 514), (34, 34))),
                    "",
                    object_id="@checked_checkbox",
                    tool_tip_text="Stop showing the Moon that certain history events occurred on",
                    manager=MANAGER,
                )
                if game.switches["show_history_moons"]:
                    self.no_moons.kill()
                else:
                    self.show_moons.kill()
            elif self.open_sub_tab == "user notes":
                self.sub_tab_1.enable()
                self.sub_tab_2.disable()
                if self.history_text_box:
                    self.history_text_box.kill()
                    self.no_moons.kill()
                    self.show_moons.kill()
                if self.save_text:
                    self.save_text.kill()
                if self.notes_entry:
                    self.notes_entry.kill()
                if self.edit_text:
                    self.edit_text.kill()
                if self.display_notes:
                    self.display_notes.kill()
                if self.help_button:
                    self.help_button.kill()

                self.help_button = UIImageButton(
                    ui_scale(pygame.Rect((52, 584), (34, 34))),
                    "",
                    object_id="#help_button",
                    manager=MANAGER,
                    tool_tip_text="The notes section has limited html capabilities.<br>"
                    "Use the following commands with < and > in place of the apostrophes.<br>"
                    "-'br' to start a new line.<br>"
                    "-Encase text between 'b' and '/b' to bold.<br>"
                    "-Encase text between 'i' and '/i' to italicize.<br>"
                    "-Encase text between 'u' and '/u' to underline.<br><br>"
                    "The following font related codes can be used, "
                    "but keep in mind that not all font faces will work.<br>"
                    "-Encase text between 'font face = name of font you wish to use' and '/font' to change the font face.<br>"
                    "-Encase text between 'font color= #hex code of the color' and '/font' to change the color of the text.<br>"
                    "-Encase text between 'font size=number of size' and '/font' to change the text size.",
                )
                if self.editing_notes is True:
                    self.save_text = UIImageButton(
                        ui_scale(pygame.Rect((52, 514), (34, 34))),
                        "",
                        object_id="@unchecked_checkbox",
                        tool_tip_text="lock and save text",
                        manager=MANAGER,
                    )

                    self.notes_entry = pygame_gui.elements.UITextEntryBox(
                        ui_scale(pygame.Rect((100, 473), (600, 149))),
                        initial_text=self.user_notes,
                        object_id="#text_box_26_horizleft_pad_10_14",
                        manager=MANAGER,
                    )
                else:
                    self.edit_text = UIImageButton(
                        ui_scale(pygame.Rect((52, 514), (34, 34))),
                        "",
                        object_id="@checked_checkbox_smalltooltip",
                        tool_tip_text="edit text",
                        manager=MANAGER,
                    )

                    self.display_notes = UITextBoxTweaked(
                        self.user_notes,
                        ui_scale(pygame.Rect((100, 473), (600, 149))),
                        object_id="#text_box_26_horizleft_pad_10_14",
                        line_spacing=1,
                        manager=MANAGER,
                    )

        # Conditions Tab
        elif self.open_tab == "conditions":
            self.display_conditions_page()

    def close_current_tab(self):
        """Closes current tab."""
        if self.open_tab is None:
            pass
        elif self.open_tab == "relations":
            self.family_tree_button.kill()
            self.see_relationships_button.kill()
            self.choose_mate_button.kill()
            self.change_adoptive_parent_button.kill()
        elif self.open_tab == "roles":
            self.manage_roles.kill()
            self.change_mentor_button.kill()
            self.manage_nobility.kill()
        elif self.open_tab == "personal":
            self.change_name_button.kill()
            self.cat_toggles_button.kill()
            self.specify_gender_button.kill()
            if self.cis_trans_button:
                self.cis_trans_button.kill()
        elif self.open_tab == "dangerous":
            self.kill_cat_button.kill()
            self.exile_cat_button.kill()
            self.murder_cat_button.kill()
            if self.join_df_button:
                self.join_df_button.kill()
            if self.exit_df_button:
                self.exit_df_button.kill()
            self.affair_button.kill()
        elif self.open_tab == 'history':
            self.backstory_background.kill()
            self.sub_tab_1.kill()
            self.sub_tab_2.kill()
            self.sub_tab_3.kill()
            self.sub_tab_4.kill()
            self.fav_tab.kill()
            self.not_fav_tab.kill()
            if self.open_sub_tab == "user notes":
                if self.edit_text:
                    self.edit_text.kill()
                if self.save_text:
                    self.save_text.kill()
                if self.notes_entry:
                    self.notes_entry.kill()
                if self.display_notes:
                    self.display_notes.kill()
                self.help_button.kill()
            elif self.open_sub_tab == "life events":
                if self.history_text_box:
                    self.history_text_box.kill()
                self.show_moons.kill()
                self.no_moons.kill()
        elif self.open_tab == "accessories":
            self.backstory_background.kill()
            for i in self.cat_list_buttons:
                self.cat_list_buttons[i].kill()
            for i in self.accessory_buttons:
                self.accessory_buttons[i].kill()
            self.next_page_button.kill()
            self.previous_page_button.kill()
            self.clear_accessories.kill()
            self.delete_accessory.kill()
            self.search_bar_image.kill()
            self.search_bar.kill()
        elif self.open_tab == "faith":
            self.backstory_background.kill()
            self.faith_bar.kill()
            self.faith_text.kill()
        elif self.open_tab == 'your tab':
            if self.have_kits_button:
                self.have_kits_button.kill()
            if self.request_apprentice_button:
                self.request_apprentice_button.kill()
            if self.gift_accessory_button:
                self.gift_accessory_button.kill()
            if self.your_faith_button:
                self.your_faith_button.kill()
        elif self.open_tab == 'conditions':
            self.left_conditions_arrow.kill()
            self.right_conditions_arrow.kill()
            self.conditions_background.kill()
            self.condition_container.kill()
            for data in self.condition_data.values():
                data.kill()
            self.condition_data = {}

        self.open_tab = None



    # ---------------------------------------------------------------------------- #
    #                               cat platforms                                  #
    # ---------------------------------------------------------------------------- #
    def get_platform(self):
        the_cat = Cat.all_cats.get(game.switches["cat"], game.clan.instructor)

        light_dark = "light"
        if game.settings["dark mode"]:
            light_dark = "dark"

        available_biome = ["Forest", "Mountainous", "Plains", "Beach"]
        biome = game.clan.biome

        if biome not in available_biome:
            biome = available_biome[0]
        if the_cat.age == "newborn" or the_cat.not_working():
            biome = "nest"

        biome = biome.lower()

        platformsheet = pygame.image.load(
            "resources/images/platforms.png"
        ).convert_alpha()

        order = ["beach", "forest", "mountainous", "nest", "plains", "SC/DF"]

        biome_platforms = platformsheet.subsurface(
            pygame.Rect(0, order.index(biome) * 70, 640, 70)
        ).convert_alpha()

        biome_platforms = platformsheet.subsurface(
            pygame.Rect(0, order.index(biome) * 70, 640, 70)
        ).convert_alpha()

        offset = 0
        if light_dark == "light":
            offset = 80

        if the_cat.df:
            biome_platforms = platformsheet.subsurface(
                pygame.Rect(0, order.index("SC/DF") * 70, 640, 70)
            )
            return pygame.transform.scale(
                biome_platforms.subsurface(pygame.Rect(0 + offset, 0, 80, 70)),
                (240, 210),
            )
        elif the_cat.dead or game.clan.instructor.ID == the_cat.ID:
            biome_platforms = platformsheet.subsurface(
                pygame.Rect(0, order.index("SC/DF") * 70, 640, 70)
            )
            return pygame.transform.scale(
                biome_platforms.subsurface(pygame.Rect(160 + offset, 0, 80, 70)),
                (240, 210),
            )
        else:
            biome_platforms = platformsheet.subsurface(
                pygame.Rect(0, order.index(biome) * 70, 640, 70)
            ).convert_alpha()
            season_x = {
                "greenleaf": 0 + offset,
                "leaf-bare": 160 + offset,
                "leaf-fall": 320 + offset,
                "newleaf": 480 + offset,
            }

            return pygame.transform.scale(
                biome_platforms.subsurface(
                    pygame.Rect(
                        season_x.get(
                            game.clan.current_season.lower(), season_x["greenleaf"]
                        ),
                        0,
                        80,
                        70,
                    )
                ),
                (240, 210),
            )
        
    def get_dead_cat_talk(self):
        """ determining placing the talk button for dead cats """
        # They SC
        cat_dead_condition_sc = (
            self.the_cat.dead and
            not self.the_cat.df and
            not self.the_cat.outside and
            (game.clan.your_cat.dead or
            (game.clan.your_cat.skills.meets_skill_requirement(SkillPath.STAR)
            and game.clan.your_cat.moons >=1))
            )

        # They DF
        cat_dead_condition_df = (
            self.the_cat.dead and
            self.the_cat.df and
            (game.clan.your_cat.dead or
            (game.clan.your_cat.skills.meets_skill_requirement(SkillPath.DARK)
            and game.clan.your_cat.moons >=1) or
            game.clan.your_cat.joined_df)
            )

        # They UR
        cat_dead_condition_ur = (
            self.the_cat.dead and
            self.the_cat.ID in game.clan.unknown_cats and
            (game.clan.your_cat.dead or
            (game.clan.your_cat.skills.meets_skill_requirement(SkillPath.GHOST) and
            game.clan.your_cat.moons >=1))
            )

        # you SC
        cat_alive_condition_sc = (
            game.clan.your_cat.dead and
            not game.clan.your_cat.df and
            game.clan.your_cat.ID in game.clan.starclan_cats and
            (self.the_cat.dead or
            (self.the_cat.skills.meets_skill_requirement(SkillPath.STAR) and
            self.the_cat.moons >= 1))
            )

        # you DF
        cat_alive_condition_df = (
            game.clan.your_cat.dead and
            game.clan.your_cat.df and
            (self.the_cat.dead or
            (self.the_cat.skills.meets_skill_requirement(SkillPath.DARK) and
            self.the_cat.moons >= 1) or
            self.the_cat.joined_df)
            )

        # You UR
        cat_alive_condition_ur = (
            game.clan.your_cat.dead and
            game.clan.your_cat.ID in game.clan.unknown_cats and
            (self.the_cat.dead or
            (self.the_cat.skills.meets_skill_requirement(SkillPath.GHOST) and
            self.the_cat.moons >= 1))
            )

        if self.the_cat.dead and not self.the_cat.outside and not self.the_cat.df:
            if not cat_dead_condition_sc:
                return False
            else:
                return True
            
        if self.the_cat.dead and self.the_cat.outside and not self.the_cat.df:
            if not cat_dead_condition_ur:
                return False
            else:
                return True
            
        if self.the_cat.dead and not self.the_cat.outside and self.the_cat.df:
            if not cat_dead_condition_df:
                return False
            else:
                return True
            
        if game.clan.your_cat.dead:
            if game.clan.your_cat.df:
                if not cat_alive_condition_df:
                    return False
                else:
                    return True
            elif game.clan.your_cat.outside:
                if not cat_alive_condition_ur:
                    return False
                else:
                    return True
            else:
                if not cat_alive_condition_sc:
                    return False
                else:
                    return True
    
    def build_inventory(self, event):
        """
        Puts together the accessory inventory
        """
        b_data = event.ui_element.blit_data[1]
        b_2data = []
        pos_x = 10
        pos_y = 125

        for b in self.accessory_buttons.values():
            b_2data.append(b.blit_data[1])
        if b_data in b_2data:
            value = b_2data.index(b_data)
            self.generate_inventory(value, pos_x, pos_y)

        self.profile_elements["cat_image"].kill()
        self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((100, 200), (150, 150))),
            pygame.transform.scale(
                self.the_cat.sprite, ui_scale_dimensions((150, 150))
            ),
            manager=MANAGER,
        )
        self.profile_elements["cat_image"].disable()

        self.profile_elements["cat_info_column1"].kill()
        self.profile_elements["cat_info_column1"] = UITextBoxTweaked(
            self.generate_column1(self.the_cat),
            ui_scale(pygame.Rect((300, 220), (180, 200))),
            object_id=get_text_box_theme("#text_box_22_horizleft"),
            line_spacing=1,
            manager=MANAGER,
        )
    
    def inventory_display(self, cat, cat_sprite, accessory, pos_x, pos_y):
        """
        Creates the individual accessory buttons
        """
        
        if accessory in cat.pelt.accessories:
            button_id = "#fav_marker"
        else:
            button_id = "#blank_button"
        
        self.accessory_buttons[str(accessory) + "_select"] = UIImageButton(
            ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))),
            "",
            tool_tip_text=accessory,
            object_id=button_id
            )

        acc_dict = {
            "acc_herbs": cat.pelt.plant_accessories,
            "acc_wild": cat.pelt.wild_accessories,
            "collars": cat.pelt.collars,
            "acc_flower": cat.pelt.flower_accessories,
            "acc_plant2": cat.pelt.plant2_accessories,
            "acc_snake": cat.pelt.snake_accessories,
            "acc_smallAnimal": cat.pelt.smallAnimal_accessories,
            "acc_deadInsect": cat.pelt.deadInsect_accessories,
            "acc_aliveInsect": cat.pelt.aliveInsect_accessories,
            "acc_fruit": cat.pelt.fruit_accessories,
            "acc_crafted": cat.pelt.crafted_accessories,
            "acc_tail2": cat.pelt.tail2_accessories
        }

        for acc_string, acc_list in acc_dict.items():
            if accessory in acc_list:
                self.cat_list_buttons[str(cat) + str(accessory) + "_sprite"] = pygame_gui.elements.UIImage(ui_scale(pygame.Rect((100 + pos_x, 365 + pos_y), (50, 50))), sprites.sprites[acc_string + accessory + cat_sprite], manager=MANAGER)
                break
    
    def generate_inventory(self, value, pos_x, pos_y):
        """
        Puts together the inventory structure. Button locations, cat_sprite
        """

        # CAT SPRITE
        cat = self.the_cat
        age = cat.age
        cat_sprite = str(cat.pelt.cat_sprites[cat.age])

        # setting the cat_sprite (bc this makes things much easier)
        if cat.not_working() and age != 'newborn' and game.config['cat_sprites']['sick_sprites']:
            if age in ['kitten', 'adolescent']:
                cat_sprite = str(19)
            else:
                cat_sprite = str(18)
        elif cat.pelt.paralyzed and age != 'newborn':
            if age in ['kitten', 'adolescent']:
                cat_sprite = str(17)
            else:
                if cat.pelt.length == 'long':
                    cat_sprite = str(16)
                else:
                    cat_sprite = str(15)
        else:
            if age == 'elder' and not game.config['fun']['all_cats_are_newborn']:
                age = 'senior'

            if game.config['fun']['all_cats_are_newborn']:
                cat_sprite = str(cat.pelt.cat_sprites['newborn'])
            else:
                cat_sprite = str(cat.pelt.cat_sprites[age])
        
        # Preparing buttons
        n = value
        if self.accessories_list[n] == self.the_cat.pelt.accessory:
            self.the_cat.pelt.accessory = None
        if self.accessories_list[n] in self.the_cat.pelt.accessories:
            self.the_cat.pelt.accessories.remove(self.accessories_list[n])
        else:
            self.the_cat.pelt.accessories.append(self.accessories_list[n])
        for acc in self.accessory_buttons:
            self.accessory_buttons[acc].kill()
        for acc in self.cat_list_buttons:
            self.cat_list_buttons[acc].kill()
        start_index = self.page * 18
        end_index = start_index + 18
        inventory_len = 0
        new_inv = []
        if self.search_bar.get_text() in ["", "search"]:
            inventory_len = len(self.cat_inventory)
            new_inv = self.cat_inventory
        else:
            for ac in self.cat_inventory:
                if self.search_bar.get_text().lower() in ac.lower():
                    inventory_len+=1
                    new_inv.append(ac)
        self.max_pages = math.ceil(inventory_len/18)
        if (self.max_pages == 1 or self.max_pages == 0):
            self.previous_page_button.disable()
            self.next_page_button.disable()
        if self.page == 0:
            self.previous_page_button.disable()
        
        if self.cat_inventory:
            for a, accessory in enumerate(new_inv[start_index:min(end_index, inventory_len + start_index)], start = start_index):
                if self.search_bar.get_text() in ["", "search"] or self.search_bar.get_text().lower() in accessory.lower():
                    self.inventory_display(cat, cat_sprite, accessory, pos_x, pos_y)
                    pos_x += 60
                    if pos_x >= 550:
                        pos_x = 0
                        pos_y += 60

    def on_use(self):
        super().on_use()
        if self.search_bar:
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
                self.open_accessories()

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
