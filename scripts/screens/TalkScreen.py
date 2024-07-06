from random import choice, choices, randint
import pygame
import ujson
import re

from scripts.utility import scale

from .Screens import Screens

from scripts.utility import generate_sprite, get_cluster, get_alive_kits, get_alive_cats, get_alive_apps, get_alive_meds, get_alive_mediators, get_alive_queens, get_alive_elders, get_alive_warriors, pronoun_repl
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
import pygame_gui
from scripts.game_structure.image_button import UIImageButton
from scripts.game_structure.game_essentials import game, screen_x, screen_y, MANAGER, screen
from enum import Enum  # pylint: disable=no-name-in-module
from scripts.housekeeping.version import VERSION_NAME
# pylint: disable=consider-using-dict-items
# pylint: disable=consider-using-enumerate

class RelationType(Enum):
    """An enum representing the possible age groups of a cat"""

    BLOOD = ''                      # direct blood related - do not need a special print
    ADOPTIVE = 'adoptive'       	# not blood related but close (parents, kits, siblings)
    HALF_BLOOD = 'half sibling'   	# only one blood parent is the same (siblings only)
    NOT_BLOOD = 'not blood related'	# not blood related for parent siblings
    RELATED = 'blood related'   	# related by blood (different mates only)

BLOOD_RELATIVE_TYPES = [RelationType.BLOOD, RelationType.HALF_BLOOD, RelationType.RELATED, RelationType.ADOPTIVE]

class TalkScreen(Screens):

    def __init__(self, name=None):
        super().__init__(name)
        self.back_button = None
        self.resource_dir = "resources/dicts/lifegen_talk/"
        self.texts = ""
        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in self.texts]
        self.scroll_container = None
        self.life_text = None
        self.header = None
        self.the_cat = None
        self.text_index = 0
        self.frame_index = 0
        self.typing_delay = 20
        self.next_frame_time = pygame.time.get_ticks() + self.typing_delay
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.text = None
        self.profile_elements = {}
        self.talk_box_img = None
        self.possible_texts = {}
        self.chosen_text_key = ""
        self.choice_buttons = {}
        self.text_choices = {}
        self.option_bgs = {}
        self.current_scene = ""
        self.created_choice_buttons = False
        self.choicepanel = False
        self.textbox_graphic = None
        self.cat_dict = {}
        self.replaced_index = (False, 0)
        self.other_dict = {}

    def screen_switches(self):
        self.the_cat = Cat.all_cats.get(game.switches['cat'])
        self.cat_dict.clear()
        self.other_dict.clear()
        self.update_camp_bg()
        self.hide_menu_buttons()
        self.text_index = 0
        self.frame_index = 0
        self.choicepanel = False
        self.created_choice_buttons = False
        self.profile_elements = {}
        self.clan_name_bg = pygame_gui.elements.UIImage(
            scale(pygame.Rect((230, 875), (380, 70))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/clan_name_bg.png").convert_alpha(),
                (500, 870)),
            manager=MANAGER)
        self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(str(self.the_cat.name),
                                                                    scale(pygame.Rect((300, 870), (-1, 80))),
                                                                        object_id="#text_box_34_horizcenter_light",
                                                                        manager=MANAGER)

        self.text_type = ""
        self.texts = self.load_texts(self.the_cat)
        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in self.texts]
        self.talk_box_img = image_cache.load_image("resources/images/talk_box.png").convert_alpha()

        self.talk_box = pygame_gui.elements.UIImage(
                scale(pygame.Rect((178, 942), (1248, 302))),
                self.talk_box_img
            )

        self.back_button = UIImageButton(scale(pygame.Rect((50, 50), (210, 60))), "",
                                        object_id="#back_button", manager=MANAGER)
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(scale(pygame.Rect((500, 970), (900, 300))))
        self.text = pygame_gui.elements.UITextBox("",
                                                scale(pygame.Rect((0, 0), (900, -100))),
                                                object_id="#text_box_30_horizleft",
                                                container=self.scroll_container,
                                                manager=MANAGER)

        self.textbox_graphic = pygame_gui.elements.UIImage(
                scale(pygame.Rect((170, 942), (346, 302))),
                image_cache.load_image("resources/images/textbox_graphic.png").convert_alpha()
            )
        # self.textbox_graphic.hide()

        self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((70, 900), (400, 400))),
                                                                        pygame.transform.scale(
                                                                            generate_sprite(self.the_cat),
                                                                            (400, 400)), manager=MANAGER)
        self.paw = pygame_gui.elements.UIImage(
                scale(pygame.Rect((1370, 1180), (30, 30))),
                image_cache.load_image("resources/images/cursor.png").convert_alpha()
            )
        self.paw.visible = False


    def exit_screen(self):
        self.text.kill()
        del self.text
        self.scroll_container.kill()
        del self.scroll_container
        self.back_button.kill()
        del self.back_button
        self.profile_elements["cat_image"].kill()
        self.profile_elements["cat_name"].kill()
        del self.profile_elements
        self.clan_name_bg.kill()
        del self.clan_name_bg
        self.talk_box.kill()
        del self.talk_box
        self.textbox_graphic.kill()
        del self.textbox_graphic
        self.paw.kill()
        del self.paw
        for button in self.choice_buttons:
            self.choice_buttons[button].kill()
        self.choice_buttons = {}
        for option in self.text_choices:
            self.text_choices[option].kill()
        self.text_choices = {}
        for option_bg in self.option_bgs:
            self.option_bgs[option_bg].kill()
        self.option_bgs = {}

    def update_camp_bg(self):
        light_dark = "light"
        if game.settings["dark mode"]:
            light_dark = "dark"

        camp_bg_base_dir = 'resources/images/camp_bg/'
        leaves = ["newleaf", "greenleaf", "leafbare", "leaffall"]
        camp_nr = game.clan.camp_bg

        if camp_nr is None:
            camp_nr = 'camp1'
            game.clan.camp_bg = camp_nr

        available_biome = ['Forest', 'Mountainous', 'Plains', 'Beach']
        biome = game.clan.biome
        if biome not in available_biome:
            biome = available_biome[0]
            game.clan.biome = biome
        biome = biome.lower()

        all_backgrounds = []
        for leaf in leaves:

            platform_dir = ""
            if self.the_cat.dead and self.the_cat.outside and not self.the_cat.df:
                platform_dir = "resources/images/urbg.png"
            elif self.the_cat.dead and not self.the_cat.outside and not self.the_cat.df:
                if game.clan.biome == "Forest":
                    platform_dir = "resources/images/dead_camps/sunsetclouds.png"
                else:
                    platform_dir = "resources/images/starclanbg.png"
            elif self.the_cat.dead and not self.the_cat.outside and self.the_cat.df:
                platform_dir = "resources/images/df camp ecpilse.png"
            else:
                platform_dir = f'{camp_bg_base_dir}/{biome}/{leaf}_{camp_nr}_{light_dark}.png'
            all_backgrounds.append(platform_dir)

        self.newleaf_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[0]).convert(), (screen_x, screen_y))
        self.greenleaf_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[1]).convert(), (screen_x, screen_y))
        self.leafbare_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[2]).convert(), (screen_x, screen_y))
        self.leaffall_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[3]).convert(), (screen_x, screen_y))

    def on_use(self):
        if game.clan.clan_settings['backgrounds']:
            if game.clan.current_season == 'Newleaf':
                screen.blit(self.newleaf_bg, (0, 0))
            elif game.clan.current_season == 'Greenleaf':
                screen.blit(self.greenleaf_bg, (0, 0))
            elif game.clan.current_season == 'Leaf-bare':
                screen.blit(self.leafbare_bg, (0, 0))
            elif game.clan.current_season == 'Leaf-fall':
                screen.blit(self.leaffall_bg, (0, 0))
        now = pygame.time.get_ticks()
        if self.texts:
            if self.texts[self.text_index][0] == "[" and self.texts[self.text_index][-1] == "]":
                self.profile_elements["cat_image"].hide()
                # self.textbox_graphic.show()
            else:
                self.profile_elements["cat_image"].show()
                # self.textbox_graphic.hide()
            if "|r_c|" in self.texts[self.text_index] and not self.replaced_index[0]:
                random_cat = self.cat_dict["r_c"]
                self.profile_elements["cat_name"].kill()
                self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(str(random_cat.name),
                                                                    scale(pygame.Rect((300, 870), (-1, 80))),
                                                                        object_id="#text_box_34_horizcenter_light",
                                                                        manager=MANAGER)
                self.profile_elements["cat_image"].kill()
                self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((70, 900), (400, 400))),
                                                                        pygame.transform.scale(
                                                                            generate_sprite(random_cat),
                                                                            (400, 400)), manager=MANAGER)
                self.texts[self.text_index] = self.texts[self.text_index].replace("|r_c|", "")
                self.replaced_index = (True,self.text_index)
            elif self.replaced_index[0] and self.text_index != self.replaced_index[1]:
                self.profile_elements["cat_name"].kill()
                self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(str(self.the_cat.name),
                                                                    scale(pygame.Rect((300, 870), (-1, 80))),
                                                                        object_id="#text_box_34_horizcenter_light",
                                                                        manager=MANAGER)
                self.profile_elements["cat_image"].kill()
                self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((70, 900), (400, 400))),
                                                                        pygame.transform.scale(
                                                                            generate_sprite(self.the_cat),
                                                                            (400, 400)), manager=MANAGER)
                self.replaced_index = (False, self.text_index)

        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in self.texts]
        if self.text_index < len(self.text_frames):
            if now >= self.next_frame_time and self.frame_index < len(self.text_frames[self.text_index]) - 1:
                self.frame_index += 1
                self.next_frame_time = now + self.typing_delay
        if self.text_index == len(self.text_frames) - 1:
            if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                if self.text_type != "choices":
                    self.paw.visible = True
                if not self.created_choice_buttons and self.text_type == "choices":
                    self.create_choice_buttons()
                    self.created_choice_buttons = True


        # Always render the current frame
        if self.text_frames:
            self.text.html_text = self.text_frames[self.text_index][self.frame_index]

        self.text.rebuild()
        self.clock.tick(60)

    def handle_event(self, event):
        if game.switches['window_open']:
            pass
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen('profile screen')
            else:
                for key, button in self.choice_buttons.items():
                    if event.ui_element == button and self.chosen_text_key:
                        self.current_scene = self.possible_texts[self.chosen_text_key][f"{self.current_scene}_choices"][key]["next_scene"]
                        self.handle_choice(self.the_cat)
        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if event.key == pygame.K_ESCAPE:
                self.change_screen('profile screen')
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.text_frames:
                if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                    if self.text_index < len(self.texts) - 1:
                        self.text_index += 1
                        self.frame_index = 0
                else:
                    self.frame_index = len(self.text_frames[self.text_index]) - 1  # Go to the last frame
            
        return

    def get_cluster_list(self):
        return ["assertive", "brooding", "cool", "upstanding", "introspective", "neurotic", "silly", "stable", "sweet", "unabashed", "unlawful"]

    def get_cluster_list_you(self):
        return ["you_assertive", "you_brooding", "you_cool", "you_upstanding", "you_introspective", "you_neurotic", "you_silly", "you_stable", "you_sweet", "you_unabashed", "you_unlawful"]


    def relationship_check(self, talk, cat_relationship):
        relationship_conditions = {
            'hate': 50,
            'romantic_like': 30,
            'platonic_like': 30,
            'jealousy': 30,
            'dislike': 30,
            'comfort': 30,
            'respect': 30,
            'trust': 30
        }
        tags = talk["intro"] if "intro" in talk else talk[0]
        for key, value in relationship_conditions.items():
            if key in tags and cat_relationship < value:
                return True
        return False

    def handle_random_cat(self, cat):
        random_cat = Cat.all_cats.get(choice(game.clan.clan_cats))
        counter = 0
        while random_cat.outside or random_cat.dead or random_cat.ID in [game.clan.your_cat.ID, cat.ID]:
            counter += 1
            if counter == 15:
                break
            random_cat = Cat.all_cats.get(choice(game.clan.clan_cats))
        return random_cat

    def display_intro(self, cat, texts_list, texts_chosen_key):
        chosen_text_intro = texts_list[texts_chosen_key]["intro"]
        chosen_text_intro = self.get_adjusted_txt(chosen_text_intro, cat)
        self.current_scene = "intro"
        self.possible_texts = texts_list
        self.chosen_text_key = texts_chosen_key
        return chosen_text_intro

    def create_choice_buttons(self):
        y_pos = 0
        if f"{self.current_scene}_choices" not in self.possible_texts[self.chosen_text_key]:
            self.paw.visible = True

            return
        for c in self.possible_texts[self.chosen_text_key][f"{self.current_scene}_choices"]:
            text = self.possible_texts[self.chosen_text_key][f"{self.current_scene}_choices"][c]['text']
            text = self.get_adjusted_txt([text], self.the_cat)
            text = text[0]

            #the background image for the text
            option_bg = pygame_gui.elements.UIImage(scale(pygame.Rect((860, 855 + y_pos), (540, 70))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/option_bg.png").convert_alpha(),
                                                                (540, 60)), manager=MANAGER)
            self.option_bgs[c] = option_bg

            #the button for dialogue choices
            button = UIImageButton(scale(pygame.Rect((780, 855 + y_pos), (68, 68))),
                                        text = "",
                                        object_id="#dialogue_choice_button", manager=MANAGER)
            self.choice_buttons[c] = button


            #the text for dialogue choices
            option = pygame_gui.elements.UITextBox(str(text),
                                                            scale(pygame.Rect((870, 860 + y_pos), (540, 60))),
                                                            object_id="#text_box_30_horizleft",
                                                            manager=MANAGER)
            self.text_choices[c] = option

            y_pos -= 80

    def handle_choice(self, cat):
        for b in self.choice_buttons:
            self.choice_buttons[b].kill()
        for b in self.text_choices:
            self.text_choices[b].kill()
        for b in self.option_bgs:
            self.option_bgs[b].kill()

        self.choice_buttons = {}
        chosen_text = self.possible_texts[self.chosen_text_key][self.current_scene]
        chosen_text2 = self.get_adjusted_txt(chosen_text, cat)
        self.texts = chosen_text2
        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in chosen_text2]
        self.text_index = 0
        self.frame_index = 0
        self.created_choice_buttons = False


    def load_texts(self, cat):
        you = game.clan.your_cat
        resource_dir = "resources/dicts/lifegen_talk/"
        possible_texts = {}

        if cat.status != 'exiled':
            with open(f"{resource_dir}{cat.status}.json", 'r') as read_file:
                possible_texts = ujson.loads(read_file.read())

        if cat.status not in ['loner', 'rogue', 'former Clancat', 'kittypet', 'exiled']:
            with open(f"{resource_dir}choice_dialogue.json", 'r') as read_file:
                possible_texts.update(ujson.loads(read_file.read()))

        if cat.status in ["rogue", "loner", "kittypet"]:
            # former clancats only get their own file so we can write general dialogue about not knowing what a clan is
            with open(f"{resource_dir}general_outsider.json", 'r') as read_file:
                possible_texts4 = ujson.loads(read_file.read())
                possible_texts.update(possible_texts4)
        else:
            with open(f"{resource_dir}choice_dialogue.json", 'r') as read_file:
                possible_texts.update(ujson.loads(read_file.read()))

            if cat.status not in ['kitten', "newborn"] and you.status not in ['kitten', 'newborn']:
                with open(f"{resource_dir}general_no_kit.json", 'r') as read_file:
                    possible_texts2 = ujson.loads(read_file.read())
                    possible_texts.update(possible_texts2)

            if cat.status not in ["newborn"] and you.status not in ['newborn']:
                with open(f"{resource_dir}general_no_newborn.json", 'r') as read_file:
                    possible_texts4 = ujson.loads(read_file.read())
                    possible_texts.update(possible_texts4)

            if cat.status not in ['kitten', "newborn"] and you.status in ['kitten', 'newborn']:
                with open(f"{resource_dir}general_you_kit.json", 'r') as read_file:
                    possible_texts3 = ujson.loads(read_file.read())
                    possible_texts.update(possible_texts3)

            if cat.status not in ['kitten', 'newborn'] and you.status not in ['kitten', 'newborn'] and randint(1,3)==1:
                with open(f"{resource_dir}crush.json", 'r') as read_file:
                    possible_texts3 = ujson.loads(read_file.read())
                    possible_texts.update(possible_texts3)

            if game.clan.focus:
                with open(f"{resource_dir}focuses/{game.clan.focus}.json", 'r') as read_file:
                    possible_texts5 = ujson.loads(read_file.read())
                    possible_texts.update(possible_texts5)
                    
        return self.filter_texts(cat, possible_texts)


    def filter_texts(self, cat, possible_texts):
        text = ""
        texts_list = {}
        you = game.clan.your_cat

        cluster1, cluster2 = get_cluster(cat.personality.trait)
        cluster3, cluster4 = get_cluster(you.personality.trait)

        their_trait_list = ['adventurous', 'aloof', 'ambitious', 'arrogant', 'bloodthirsty', 'bold', 'bouncy', 'calm', 'careful', 'confident', 'competitive', 'cold', 'charismatic', 'cunning', 'cowardly', 'childish', 'compassionate', 'daring', 'emotional', 'energetic', 'fierce', 'flexible', 'faithful', 'flamboyant', 'grumpy', 'gloomy', 'humble', 'insecure', 'justified', 'loyal', 'lonesome', 'loving', 'meek', 'mellow', 'methodical', 'nervous', 'oblivious', 'obsessive', 'playful', 'reserved', 'righteous', 'responsible', 'rebellious', 'strict', 'stoic', 'sneaky', 'strange', 'sincere', 'shameless', 'spontaneous', 'thoughful', 'troublesome', 'trusting', 'vengeful', 'witty', 'wise', 'impulsive', 'bullying', 'attention-seeker', 'charming', 'daring', 'noisy', 'daydreamer', 'sweet', 'polite', 'know-it-all', 'bossy', 'disciplined', 'patient', 'manipulative', 'secretive', 'rebellious', 'grumpy', 'passionate', 'honest', 'leader-like', 'smug']
        you_trait_list = ['you_adventurous', 'you_aloof', 'you_ambitious', 'you_arrogant', 'you_bloodthirsty', 'you_bold', 'you_bouncy', 'you_calm', 'you_careful', 'you_confident', 'you_competitive', 'you_cold', 'you_charismatic', 'you_cunning', 'you_cowardly', 'you_childish', 'you_compassionate', 'you_daring', 'you_emotional', 'you_energetic', 'you_fierce', 'you_flexible', 'you_faithful', 'you_flamboyant', 'you_grumpy', 'you_gloomy', 'you_humble', 'you_insecure', 'you_justified', 'you_loyal', 'you_lonesome', 'you_loving', 'you_meek', 'you_mellow', 'you_methodical', 'you_nervous', 'you_oblivious', 'you_obsessive', 'you_playful', 'you_reserved', 'you_righteous', 'you_responsible', 'you_rebellious', 'you_strict', 'you_stoic', 'you_sneaky', 'you_strange', 'you_sincere', 'you_shameless', 'you_spontaneous', 'you_thoughful', 'you_troublesome', 'you_trusting', 'you_vengeful', 'you_witty', 'you_wise', 'you_impulsive', 'you_bullying', 'you_attention-seeker', 'you_charming', 'you_daring', 'you_noisy', 'you_daydreamer', 'you_sweet', 'you_polite', 'you_know-it-all', 'you_bossy', 'you_disciplined', 'you_patient', 'you_manipulative', 'you_secretive', 'you_rebellious', 'you_passionate', 'you_honest', 'you_leader-like', 'you_smug']
        you_backstory_list = [
            "you_clanfounder",
            "you_clanborn",
            "you_outsiderroots",
            "you_half-clan",
            "you_formerlyaloner",
            "you_formerlyarogue",
            "you_formerlyakittypet",
            "you_formerlyaoutsider",
            "you_originallyfromanotherclan",
            "you_orphaned",
            "you_abandoned",
            "you_ancientspirit"
        ]
        they_backstory_list = ["they_clanfounder",
            "they_clanborn",
            "they_outsiderroots",
            "they_half-clan",
            "they_formerlyaloner",
            "they_formerlyarogue",
            "they_formerlyakittypet",
            "they_formerlyaoutsider",
            "they_originallyfromanotherclan",
            "they_orphaned",
            "they_abandoned",
            "they_ancientspirit"
        ]
        skill_list = ['teacher', 'hunter', 'fighter', 'runner', 'climber', 'swimmer', 'speaker', 'mediator1', 'clever', 'insightful', 'sense', 'kit', 'story', 'lore', 'camp', 'healer', 'star', 'omen', 'dream', 'clairvoyant', 'prophet', 'ghost', 'explorer', 'tracker', 'artistan', 'guardian', 'tunneler', 'navigator', 'song', 'grace', 'clean', 'innovator', 'comforter', 'matchmaker', 'thinker', 'cooperative', 'scholar', 'time', 'treasure', 'fisher', 'language', 'sleeper']
        you_skill_list = ['you_teacher', 'you_hunter', 'you_fighter', 'you_runner', 'you_climber', 'you_swimmer', 'you_speaker', 'you_mediator1', 'you_clever', 'you_insightful', 'you_sense', 'you_kit', 'you_story', 'you_lore', 'you_camp', 'you_healer', 'you_star', 'you_omen', 'you_dream', 'you_clairvoyant', 'you_prophet', 'you_ghost', 'you_explorer', 'you_tracker', 'you_artistan', 'you_guardian', 'you_tunneler', 'you_navigator', 'you_song', 'you_grace', 'you_clean', 'you_innovator', 'you_comforter', 'you_matchmaker', 'you_thinker', 'you_cooperative', 'you_scholar', 'you_time', 'you_treasure', 'you_fisher', 'you_language', 'you_sleeper']
        for talk_key, talk in possible_texts.items():
            tags = talk["tags"] if "tags" in talk else talk[0]
            for i in range(len(tags)):
                tags[i] = tags[i].lower()

            if "insult" in tags:
                continue

            if you.moons == 0 and "newborn" not in tags:
                continue

            if "sc_faith" in tags and cat.faith < 0:
                continue
            if "df_faith" in tags and cat.faith > 0:
                continue

            # Status tags
            if you.status not in tags and f"you_{you.status}" not in tags and f"you_{you.status.replace('' '', '_')}" not in tags and "any" not in tags and "young elder" not in tags and "no_kit" not in tags and "you_any" not in tags:
                continue
            elif "young elder" in tags and cat.status == 'elder' and cat.moons >= 100:
                continue
            elif "no_kit" in tags and (you.status in ['kitten', 'newborn'] or cat.status in ['kitten', 'newborn']):
                continue
            elif "newborn" in tags and "kitten" not in tags and you.moons != 0:
                continue

            if "they_adult" in tags and cat.status in ['apprentice', 'medicine cat apprentice', 'mediator apprentice', "queen's apprentice", "kitten", "newborn"]:
                continue

            if "you_adult" in tags and you.status in ['apprentice', 'medicine cat apprentice', 'mediator apprentice', "queen's apprentice", "kitten", "newborn"]:
                continue

            if "they_app" in tags and cat.status not in ['apprentice', 'medicine cat apprentice', 'mediator apprentice', "queen's apprentice"]:
                continue
            
            if not any(t in tags for t in ["they_dead", "they_sc", "they_df", "they_ur"]) and cat.dead:
                continue
            if not any(t in tags for t in ["you_dead", "you_sc", "you_df", "you_ur"]) and you.dead:
                continue

            if any(t in tags for t in ["they_dead", "they_sc", "they_df", "they_ur"]) and not cat.dead:
                continue
            if any(t in tags for t in ["you_dead", "you_sc", "you_df", "you_ur"]) and not you.dead:
                continue


            if "they_kittypet" in tags and not cat.status == "kittypet":
                continue
            if "they_rogue" in tags and not cat.status == "rogue":
                continue
            if "they_loner" in tags and not cat.status == "loner":
                continue

            # if "they_kittypet" not in tags and cat.status == "kittypet":
            #     continue
            # if "they_rogue" not in tags and cat.status == "rogue":
            #     continue
            # if "they_loner" not in tags and cat.status == "loner":
            #     continue

            # the status files already separate these, so statuses can be untagged in general

            if "they_outside" in tags and not cat.outside:
                continue
            if "they_dead" in tags and not cat.dead:
                continue
            if "you_dead" in tags and not you.dead:
                continue

            if "you_dftrainee" in tags and not you.joined_df:
                continue

            if "they_dftrainee" in tags and not cat.joined_df:
                continue

            if "you_not_dftrainee" in tags and cat.joined_df:
                continue
                
            if "they_not_dftrainee" in tags and cat.joined_df:
                continue

            if "they_df" in tags and (not cat.df or cat.outside):
                continue
            if "you_df" in tags and (not you.df or you.outside):
                continue
            if "they_sc" in tags and (cat.df or cat.outside):
                continue
            if "you_sc" in tags and (you.df or you.outside):
                continue
            if "they_ur" in tags and not cat.outside:
                continue
            if "you_ur" in tags and not you.outside:
                continue
            if "they_dead" in tags and not cat.dead:
                continue

            murdered_them = False
            if you.history:
                if you.history.murder:
                    if "is_murderer" in you.history.murder:
                        for murder_event in you.history.murder["is_murderer"]:
                            if cat.ID == murder_event.get("victim"):
                                murdered_them = True
                                break

            # if murdered_them and "murderedthem" not in tags:
            #     continue

            if "murderedthem" in tags and not murdered_them:
                continue

            murdered_you = False
            if cat.history:
                if cat.history.murder:
                    if "is_murderer" in cat.history.murder:
                        for murder_event in cat.history.murder["is_murderer"]:
                            if you.ID == murder_event.get("victim"):
                                murdered_you = True
                                break

            # if murdered_you and "murderedyou" not in tags:
            #     continue

            if "murderedyou" in tags and not murdered_you:
                continue

            if "grief stricken" in cat.illnesses:
                dead_cat = Cat.all_cats.get(cat.illnesses['grief stricken'].get("grief_cat"))
                if dead_cat:
                    if "grievingyou" in tags:
                        if dead_cat.name != game.clan.your_cat.name:
                            continue
                    else:
                        if dead_cat.name == game.clan.your_cat.name:
                            continue

            if "grief stricken" in you.illnesses:
                dead_cat = Cat.all_cats.get(you.illnesses['grief stricken'].get("grief_cat"))
                if dead_cat:
                    if "grievingthem" in tags:
                        if dead_cat.name != cat.name:
                            continue
                    else:
                        if dead_cat.name == cat.name:
                            continue
            
            # FORGIVEN TAGS

            youreforgiven = False
            theyreforgiven = False

            if you.forgiven < 11 and you.forgiven > 0: 
                youreforgiven = True
                                
            if cat.forgiven < 11 and cat.forgiven > 0:
                theyreforgiven = True
            
            if "you_forgiven" in tags and (you.shunned > 0 or not youreforgiven):
                continue

            if "they_forgiven" in tags and (cat.shunned > 0 or not theyreforgiven):
                continue


            roles = ["they_kitten", "they_apprentice", "they_medicine_cat_apprentice", "they_mediator_apprentice", "they_queen's_apprentice", "they_warrior", "they_mediator", "they_medicine_cat", "they_queen", "they_deputy", "they_leader", "they_elder", "they_newborn"]
            if any(r in roles for r in tags):
                has_role = False
                if "they_kitten" in tags and cat.status == "kitten":
                    has_role = True
                elif "they_apprentice" in tags and cat.status == "apprentice":
                    has_role = True
                elif "they_medicine_cat_apprentice" in tags and cat.status == "medicine cat apprentice":
                    has_role = True
                elif "they_mediator_apprentice" in tags and cat.status == "mediator apprentice":
                    has_role = True
                elif "they_queen's_apprentice" in tags and cat.status == "queen's apprentice":
                    has_role = True
                elif "they_warrior" in tags and cat.status == "warrior":
                    has_role = True
                elif "they_mediator" in tags and cat.status == "mediator":
                    has_role = True
                elif "they_medicine_cat" in tags and cat.status == "medicine cat":
                    has_role = True
                elif "they_queen" in tags and cat.status == "queen":
                    has_role = True
                elif "they_deputy" in tags and cat.status == "deputy":
                    has_role = True
                elif "they_leader" in tags and cat.status == "leader":
                    has_role = True
                elif "they_elder" in tags and cat.status == "elder":
                    has_role = True
                elif "they_newborn" in tags and cat.status == "newborn":
                    has_role = True
                if not has_role:
                    continue

            if "they_grieving" not in tags and "grief stricken" in cat.illnesses and not cat.dead:
                continue
            if "they_grieving" in tags and "grief stricken" not in cat.illnesses and not cat.dead:
                continue

            if "they_recovering_from_birth" in tags and "recovering from birth" not in cat.injuries:
                continue

            if "you_recovering_from_birth" in tags and "recovering from birth" not in you.injuries:
                continue

            if "you_not_kit" in tags and game.clan.your_cat.moons < 6:
                continue

            # Cluster tags
            if any(i in self.get_cluster_list() for i in tags):
                if cluster1 not in tags and cluster2 not in tags and ("they_"+cluster1 not in tags) and ("they_"+cluster2 not in tags):
                    continue
            if any(i in self.get_cluster_list_you() for i in tags):
                if ("you_"+cluster3) not in tags and ("you_"+cluster4) not in tags:
                    continue

            # Trait tags
            if any(i in you_trait_list for i in tags):
                ts = you_trait_list
                for j in range(len(ts)):
                    ts[j] = ts[j][3:]
                if you.personality.trait not in ts:
                    continue
            if any(i in their_trait_list for i in tags):
                if cat.personality.trait not in tags:
                    continue

            # Backstory tags
            if any(i in you_backstory_list for i in tags):
                bs_text = self.backstory_text(game.clan.your_cat).replace(" ", "").lower()
                if f"you_{bs_text}" not in tags:
                    continue

            if any(i in they_backstory_list for i in tags):
                bs_text = self.backstory_text(cat).replace(" ", "").lower()
                if f"they_{bs_text}" not in tags:
                    continue

            # Skill tags
            if any(i in you_skill_list for i in tags):
                ts = you_skill_list
                for j in range(len(ts)):
                    ts[j] = ts[j][3:]
                    ts[j] = ''.join([q for q in ts[j] if not q.isdigit()])
                if (you.skills.primary.path not in ts) or (you.skills.secondary.path not in ts):
                    continue
            if any(i in skill_list for i in tags):
                ts = skill_list
                for j in range(len(ts)):
                    ts[j] = ''.join([q for q in ts[j] if not q.isdigit()])
                if (cat.skills.primary.path not in ts) or (cat.skills.secondary.path not in ts):
                    continue

            # Season tags
            if ('leafbare' in tags and game.clan.current_season != 'Leaf-bare') or ('newleaf' in tags and game.clan.current_season != 'Newleaf') or ('leaffall' in tags and game.clan.current_season != 'Leaf-fall') or ('greenleaf' in tags and game.clan.current_season != 'Greenleaf'):
                continue

            # Biome tags
            if any(i in ['beach', 'forest', 'plains', 'mountainous', 'wetlands', 'desert'] for i in tags):
                if game.clan.biome.lower() not in tags:
                    continue

            # Injuries, grieving and illnesses tags

            if "you_pregnant" in tags and "pregnant" not in you.injuries:
                continue
            if "they_pregnant" in tags and "pregnant" not in cat.injuries:
                continue

            if "grief stricken" not in you.illnesses and "you_grieving" in tags and not you.dead:
                continue

            if "starving" not in you.illnesses and "you_starving" in tags:
                continue
            if "starving" not in cat.illnesses and "they_starving" in tags:
                continue


            if any(i in ["you_ill", "you_injured"] for i in tags):
                ill_injured = False

                if you.is_ill() and "you_ill" in tags and "grief stricken" not in you.illnesses:
                    for illness in you.illnesses:
                        if you.illnesses[illness]['severity'] != 'minor':
                            ill_injured = True
                if you.is_injured() and "you_injured" in tags and "pregnant" not in you.injuries and "recovering from birth" not in you.injuries and "sprain" not in you.injuries:
                    for injury in you.injuries:
                        if you.injuries[injury]['severity'] != 'minor':
                            ill_injured = True

                if not ill_injured:
                    continue

            if any(i in ["they_ill", "they_injured"] for i in tags):
                ill_injured = False

                if cat.is_ill() and "they_ill" in tags and "grief stricken" not in cat.illnesses and "guilty" not in cat.illnesses:
                    for illness in cat.illnesses:
                        if cat.illnesses[illness]['severity'] != 'minor':
                            ill_injured = True
                if cat.is_injured() and "they_injured" in tags and "pregnant" not in cat.injuries and "recovering from birth" not in cat.injuries and "sprain" not in cat.injuries:
                    for injury in cat.injuries:
                        if cat.injuries[injury]['severity'] != 'minor':
                            ill_injured = True

                if not ill_injured:
                    continue
            
            # Connected dialogue keys:
            if "~" in talk_key:
                talk_key_split = talk_key.split("~")
                if talk_key_split[0] in cat.connected_dialogue.keys():
                    if int(cat.connected_dialogue[talk_key_split[0]] + 1) != int(talk_key_split[1]):
                        continue
                elif int(talk_key_split[1]) != 1:
                    continue

            # Relationships
            # Family tags:
            if any(i in ["from_your_parent", "from_adopted_parent", "adopted_parent", "half sibling", "littermate", "siblings_mate", "cousin", "adopted_sibling", "parents_siblings", "from_mentor", "from_df_mentor", "from_your_kit", "from_your_apprentice", "from_df_apprentice", "from_mate", "from_parent", "adopted_parent", "from_kit", "sibling", "from_adopted_kit"] for i in tags):

                fam = False
                if "from_mentor" in tags:
                    if you.mentor == cat.ID:
                        fam = True
                if "from_df_mentor" in tags:
                    if you.df_mentor == cat.ID:
                        fam = True
                if "from_your_apprentice" in tags:
                    if cat.mentor == you.ID:
                        fam = True
                if "from_df_apprentice" in tags:
                    if cat.df_mentor == you.ID:
                        fam = True
                if "from_mate" in tags:
                    if cat.ID in you.mate:
                        fam = True
                if "from_parent" in tags or "from_your_parent" in tags:
                    if you.parent1:
                        if you.parent1 == cat.ID:
                            fam = True
                    if you.parent2:
                        if you.parent2 == cat.ID:
                            fam = True
                if "adopted_parent" in tags or "from adopted_parent" in tags or "from_adopted_parent" in tags:
                    if cat.ID in you.inheritance.get_no_blood_parents():
                        fam = True
                if "from_kit" in tags or "from_your_kit" in tags:
                    if cat.ID in you.inheritance.get_blood_kits():
                        fam = True
                if "from_adopted_kit" in tags:
                    if cat.ID in you.inheritance.get_not_blood_kits():
                        fam = True
                if "littermate" in tags:
                    if cat.ID in you.inheritance.get_siblings() and cat.moons == you.moons:
                        fam = True
                if "sibling" in tags:
                    if cat.ID in you.inheritance.get_siblings():
                        fam = True
                if "half sibling" in tags:
                    c_p1 = cat.parent1
                    if not c_p1:
                        c_p1 = "no_parent1_cat"
                    c_p2 = cat.parent2
                    if not c_p2:
                        c_p2 = "no_parent2_cat"
                    y_p1 = you.parent1
                    if not y_p1:
                        y_p1 = "no_parent1_you"
                    y_p2 = you.parent2
                    if not y_p2:
                        y_p2 = "no_parent2_you"
                    if ((c_p1 == y_p1 or c_p1 == y_p2) or (c_p2 == y_p1 or c_p2 == y_p2)) and not (c_p1 == y_p1 and c_p2 == y_p2) and not (c_p2 == y_p1 and c_p1 == y_p2) and not (c_p1 == y_p2 and c_p2 == y_p1):
                        fam = True
                if "adopted_sibling" in tags:
                    if cat.ID in you.inheritance.get_no_blood_siblings():
                        fam = True
                if "parents_siblings" in tags:
                    if cat.ID in you.inheritance.get_parents_siblings():
                        fam = True
                if "cousin" in tags:
                    if cat.ID in you.inheritance.get_cousins():
                        fam = True
                if "siblings_mate" in tags:
                    if cat.ID in you.inheritance.get_siblings_mates():
                        fam = True
                if "grandparent" in tags:
                    if cat.is_grandparent(game.clan.your_cat):
                        fam = True
                if not fam:
                    continue


            if "non-related" in tags:
                if you.inheritance.get_exact_rel_type(cat.ID) in BLOOD_RELATIVE_TYPES:
                    continue

            # If you have murdered someone and have been revealed

            # if "murder" in tags and you.shunned == 1: # "murder" tag is gone, shunned is dealt with elsewhere
            #     if game.clan.your_cat.revealed:
            #         if game.clan.your_cat.history:
            #             if "is_murderer" in game.clan.your_cat.history.murder:
            #                 if len(game.clan.your_cat.history.murder["is_murderer"]) == 0:
            #                     continue
            #                 if 'accomplices' in game.switches:
            #                     if cat.ID in game.switches['accomplices']:
            #                         continue
            #             else:
            #                 continue
            #         else:
            #             continue
            #     else:
            #         continue

            if "war" in tags:
                if game.clan.war.get("at_war", False):
                    continue

            if "non-mates" in tags:
                if you.ID in cat.mate:
                    continue

            if "clan_has_kits" in tags:
                clan_has_kits = False
                for c in Cat.all_cats_list:
                    if c.status == "kitten" and not c.dead and not c.outside:
                        clan_has_kits = True
                if not clan_has_kits:
                    continue

            if "they_older" in tags:
                if you.age == cat.age or cat.moons < you.moons:
                    continue

            if "they_sameage" in tags:
                if you.age != cat.age:
                    continue

            if "they_younger" in tags:
                if you.age == cat.age or cat.moons > you.moons:
                    continue

            if "they_shunned" in tags:
                if cat.shunned == 0:
                    continue

            if "you_shunned" in tags:
                if you.shunned == 0:
                    continue
            
            if "both_shunned" in tags or ("they_shunned" in tags and "you_shunned" in tags):
                if cat.shunned == 0 or you.shunned == 0:
                    continue

            if cat.shunned > 0 and you.shunned == 0 and "they_shunned" not in tags:
                continue

            if you.shunned > 0 and cat.shunned == 0 and "you_shunned" not in tags:
                continue

            if you.shunned > 0 and cat.shunned > 0 and "both_shunned" not in tags:
                continue

            if "guilty" in tags and "guilt" not in cat.illnesses:
                continue



            # PERMANENT CONDITIONS
            # the exclusive deaf/blind ones

            if "only_they_born_deaf" in tags:
                if "deaf" not in cat.illnesses:
                    continue
                if "deaf" in cat.illnesses and cat.permanent_condition["deaf"]["born_with"] is False:
                    continue
            if "only_they_went_deaf" in tags:
                if "deaf" not in cat.illnesses:
                    continue
                if "deaf" in cat.illnesses and cat.permanent_condition["deaf"]["born_with"] is True:
                    continue
            if "only_they_deaf" in tags and "deaf" not in cat.illnesses:
                continue

            if "only_they_born_blind" in tags:
                if "blind" not in cat.illnesses:
                    continue
                if "blind" in cat.illnesses and cat.permanent_condition["blind"]["born_with"] is False:
                    continue

            if "only_they_went_blind" in tags:
                if "blind" not in cat.illnesses:
                    continue
                if "blind" in cat.illnesses and cat.permanent_condition["blind"]["born_with"] is True:
                    continue

            if "only_they_blind" in tags and "blind" not in cat.illnesses:
                continue

            if "only_you_born_deaf" in tags:
                if "deaf" not in you.permanent_condition:
                    continue
                if "deaf" in you.permanent_condition and you.permanent_condition["deaf"]["born_with"] is False:
                    continue
            if "only_you_went_deaf" in tags:
                if "deaf" not in you.permanent_condition:
                    continue
                if "deaf" in you.permanent_condition and you.permanent_condition["deaf"]["born_with"] is True:
                    continue
            if "only_you_deaf" in tags and "deaf" not in you.permanent_condition:
                continue

            if "only_you_born_blind" in tags:
                if "blind" not in you.permanent_condition:
                    continue
                if "blind" in you.permanent_condition and you.permanent_condition["blind"]["born_with"] is False:
                    continue
            if "only_you_went_blind" in tags:
                if "blind" not in you.permanent_condition:
                    continue
                if "blind" in you.permanent_condition and you.permanent_condition["blind"]["born_with"] is True:
                    continue
            if "only_you_blind" in tags and "blind" not in you.permanent_condition:
                continue

            # non-exclusive deaf/blind
            if "deaf" in cat.permanent_condition:
                if cat.permanent_condition["deaf"]["born_with"] is True:
                    if "they_born_deaf" not in tags:
                        if "they_deaf" not in tags:
                            continue
                else:
                    if "they_born_deaf" in tags:
                        continue
                    if "they_hearing" in tags:
                        continue
                    # cats who went deaf later in life can get pretty much all normal dialogue, as they're able to talk regularly.
                    # they_hearing is for dialogue that explicitly mentions that t_c can hear, so it can be filtered out for cats who went deaf.
                    # "did you hear that?" "i just heard..." "r_k is so loud!" yanno

            if "deaf" in you.permanent_condition:
                if you.permanent_condition["deaf"]["born_with"] is True:
                    if "you_born_deaf" not in tags:
                        if "you_deaf" not in tags:
                            continue
                else:
                    if "you_born_deaf" in tags:
                        continue
                    if "you_went_deaf" not in tags:
                        if "you_deaf" not in tags:
                            continue
            
            # blind
            if "blind" in cat.permanent_condition:
                if cat.permanent_condition["blind"]["born_with"] is True:
                    if "they_born_blind" not in tags:
                        if "they_blind" not in tags:
                            continue
                else:
                    if "they_born_blind" in tags:
                        continue
<<<<<<< Updated upstream
                    if "they_went_blind" not in tags:
=======
                    if "they_went_blind" not in tags and "only_they_went_blind" not in tags:
>>>>>>> Stashed changes
                        if "they_blind" not in tags:
                            continue

            if "blind" in you.permanent_condition:
                if you.permanent_condition["blind"]["born_with"] is True:
                    if "you_born_blind" not in tags:
                        if "you_blind" not in tags:
                            continue
                else:
                    if "you_born_blind" in tags:
                        continue
                    if "you_went_blind" not in tags:
                        if "you_blind" not in tags:
                            continue

            if "you_allergies" in tags and "allergies" not in you.illnesses:
                continue
            if "they_allergies" in tags and "allergies" not in cat.illnesses:
                continue

            if "you_jointpain" in tags and "constant joint pain" not in you.illnesses:
                continue
            if "they_jointpain" in tags and "constant join pain" not in cat.illnesses:
                continue

            if "you_dizzy" in tags and "constantly dizzy" not in you.illnesses:
                continue
            if "they_dizzy" in tags and "constantly dizzy" not in cat.illnesses:
                continue

            if "you_nightmares" in tags and "constant nightmares" not in you.illnesses:
                continue
            if "they_nightmares" in tags and "constant nightmares" not in cat.illnesses:
                continue

            if "you_crookedjaw" in tags and "crooked jaw" not in you.illnesses:
                continue
            if "they_crookedjaw" in tags and "crooked jaw" not in cat.illnesses:
                continue

            if "you_failingeyesight" in tags and "failing eyesight" not in you.illnesses:
                continue
            if "they_failingeyesight" in tags and "failing eyesight" not in cat.illnesses:
                continue

            if "you_lastinggrief" in tags and "lasting grief" not in you.illnesses:
                continue
            if "they_lastinggrief" in tags and "lasting grief" not in cat.illnesses:
                continue

            # if "you_missingleg" in tags and "lost a leg" not in you.illnesses and "born without a leg" not in you.illnesses:
            #     continue
            # if "they_missingleg" in tags and "lost a leg" not in cat.illnesses and "born without a leg" not in cat.illnesses:
            #     continue

            # if "you_missingtail" in tags and "lost their tail" not in you.illnesses and "born without a tail" not in you.illnesses:
            #     continue
            # if "they_missingtail" in tags and "lost their tail" not in cat.illnesses and "born without a tail" not in cat.illnesses:
            #     continue

            if "you_paralyzed" in tags and "paralyzed" not in you.illnesses:
                continue
            if "they_paralyzed" in tags and "paralyzed" not in cat.illnesses:
                continue

            if "you_hearingloss" in tags and "partial hearing loss" not in you.illnesses:
                continue
            if "they_hearingloss" in tags and "partial hearing loss" not in cat.illnesses:
                continue

            if "you_headaches" in tags and "persistent headaches" not in you.illnesses:
                continue
            if "they_headaches" in tags and "persistent headaches" not in cat.illnesses:
                continue

            if "you_raspylungs" in tags and "raspy lungs" not in you.illnesses:
                continue
            if "they_raspylungs" in tags and "raspy lungs" not in cat.illnesses:
                continue

            if "you_recurringshock" in tags and "recurring shock" not in you.illnesses:
                continue
            if "they_recurringshock" in tags and "recurring shock" not in cat.illnesses:
                continue

            if "you_seizureprone" in tags and "seizure prone" not in you.illnesses:
                continue
            if "they_seizureprone" in tags and "seizure prone" not in cat.illnesses:
                continue

            if "you_wastingdisease" in tags and "wasting disease" not in you.illnesses:
                continue
            if "they_wastingdisease" in tags and "wasting disease" not in cat.illnesses:
                continue

            # Relationship conditions
            if you.ID in cat.relationships:
                # intial relationship stuff
                if cat.relationships[you.ID].dislike < 30 and 'hate' in tags:
                    continue
                if cat.relationships[you.ID].romantic_love < 15 and 'romantic_like' in tags:
                    continue
                if cat.relationships[you.ID].platonic_like < 25 and 'platonic_like' in tags:
                    continue
                if cat.relationships[you.ID].platonic_like < 40 and 'platonic_love' in tags:
                    continue
                if cat.relationships[you.ID].jealousy < 5 and 'jealousy' in tags:
                    continue
                if cat.relationships[you.ID].dislike < 20 and 'dislike' in tags:
                    continue
                if cat.relationships[you.ID].comfortable < 40 and 'comfort' in tags:
                    continue
                if cat.relationships[you.ID].admiration < 40 and 'respect' in tags:
                    continue
                if cat.relationships[you.ID].trust < 40 and 'trust' in tags:
                    continue
                if (cat.relationships[you.ID].platonic_like > 20 or cat.relationships[you.ID].dislike > 20) and "neutral" in tags:
                    continue

                # new relationship stuff!
                skip_rel = False
                for tag in tags:
                    if tag.startswith("min_platonic_"):
                        min_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].platonic_like < min_value:
                            skip_rel = True
                            break
                    elif tag.startswith("max_platonic_"):
                        max_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].platonic_like > max_value:
                            skip_rel = True
                            break

                    if tag.startswith("min_romantic_"):
                        min_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].romantic_love < min_value:
                            skip_rel = True
                            break
                    elif tag.startswith("max_romantic_"):
                        max_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].romantic_love > max_value:
                            skip_rel = True
                            break

                    if tag.startswith("min_dislike_"):
                        min_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].dislike < min_value:
                            skip_rel = True
                            break
                    elif tag.startswith("max_dislike_"):
                        max_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].dislike > max_value:
                            skip_rel = True
                            break

                    if tag.startswith("min_jealousy_"):
                        min_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].jealousy < min_value:
                            skip_rel = True
                            break
                    elif tag.startswith("max_jealousy_"):
                        max_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].jealousy > max_value:
                            skip_rel = True
                            break

                    if tag.startswith("min_trust_"):
                        min_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].trust < min_value:
                            skip_rel = True
                            break
                    elif tag.startswith("max_trust_"):
                        max_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].trust > max_value:
                            skip_rel = True
                            break

                    if tag.startswith("min_comfort_"):
                        min_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].comfortable < min_value:
                            skip_rel = True
                            break
                    elif tag.startswith("max_comfort_"):
                        max_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].comfortable > max_value:
                            skip_rel = True
                            break

                    if tag.startswith("min_respect_"):
                        min_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].admiration < min_value:
                            skip_rel = True
                            break
                    elif tag.startswith("max_respect_"):
                        max_value = int(tag.split("_")[-1])
                        if cat.relationships[you.ID].admiration > max_value:
                            skip_rel = True
                            break
                if skip_rel:
                    continue
            else:
                if any(i in ["hate","romantic_like","platonic_like","jealousy","dislike","comfort","respect","trust"] for i in tags):
                    continue
                values = ["platonic", "romantic", "dislike", "jealousy", "comfort", "trust", "respect"]
                for v in values:
                    for tag in tags:
                        if tag.startswith(f"max_{v}_"):
                            continue
                        if tag.startswith(f"min_{v}_"):
                            continue
            
            if game.clan.focus and game.clan.focus == "leader" and "focus" in tags:
                leader_id = game.clan.leader.ID
                if leader_id not in cat.relationships or cat.ID == leader_id:
                    continue
                if talk_key.startswith("good_opinion") and cat.relationships[leader_id].platonic_like < 30:
                    continue
                elif talk_key.startswith("bad_opinion") and cat.relationships[leader_id].dislike < 30:
                    continue

            # dead moons tags!
            if you.dead or cat.dead:
                fadedage = game.config["fading"]["age_to_fade"]
                
                skip_processing = False

                if you.dead:
                    for tag in tags:
                        if tag.startswith("min_you_deadfor_"):
                            min_value = int(tag.split("_")[-1])
                            if you.dead_for < min_value:
                                skip_processing = True
                                break
                        elif tag.startswith("max_you_deadfor_"):
                            max_value = int(tag.split("_")[-1])
                            if you.dead_for > max_value:
                                skip_processing = True
                                break

                if cat.dead and not skip_processing:
                    for tag in tags:
                        if tag.startswith("min_they_deadfor_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.dead_for < min_value:
                                skip_processing = True
                                break
                        elif tag.startswith("max_they_deadfor_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.dead_for > max_value:
                                skip_processing = True
                                break

                if skip_processing:
                    continue
            texts_list[talk_key] = talk

        return self.choose_text(cat, texts_list)


    def load_and_replace_placeholders(self, file_path, cat, you):
        with open(file_path, 'r') as read_file:
            possible_texts = ujson.loads(read_file.read())
            cluster1, cluster2 = get_cluster(cat.personality.trait)
            cluster3, cluster4 = get_cluster(you.personality.trait)
            clusters_1 = f"{cluster3} and {cluster4}" if cluster4 else f"{cluster3}"
            clusters_2 = f"{cluster1} and {cluster2}" if cluster2 else f"{cluster1}"
            
            add_on_map = {
                (True, True): " df",
                (True, False, False): " sc",
                (True, False, True): " ur"
            }
            add_on = add_on_map.get((you.dead, you.df, you.outside), "")
            if "grief stricken" in you.illnesses:
                add_on += " g"
            if you.shunned > 0:
                add_on += " sh"
            
            add_on2 = add_on_map.get((cat.dead, cat.df, cat.outside), "")
            if "grief stricken" in cat.illnesses:
                add_on2 += " g"
            if cat.shunned > 0:
                add_on2 += " sh"
            add_on2 += f" {VERSION_NAME}"
            
            possible_texts['general'][1][0] = possible_texts['general'][1][0].replace("c_1", clusters_1)
            possible_texts['general'][1][0] = possible_texts['general'][1][0].replace("c_2", clusters_2)
            possible_texts['general'][1][0] = possible_texts['general'][1][0].replace("r_1", you.status + add_on)
            possible_texts['general'][1][0] = possible_texts['general'][1][0].replace("r_2", cat.status + add_on2)
            
        return possible_texts['general']

    def choose_text(self, cat, texts_list):
        MAX_RETRIES = 30
        you = game.clan.your_cat
        resource_dir = "resources/dicts/lifegen_talk/"

        if not texts_list:
            texts_list['general'] = self.load_and_replace_placeholders(f"{resource_dir}general.json", cat, you)

        if len(game.clan.talks) > 100:
            game.clan.talks.clear()

        # Assign weights based on tags
        weighted_tags = ["you_pregnant", "they_pregnant", "from_mentor", "from_your_parent", "from_adopted_parent", "adopted_parent", "half sibling", "littermate", "siblings_mate", "cousin", "adopted_sibling", "parents_siblings", "from_df_mentor", "from_your_kit", "from_your_apprentice", "from_df_apprentice", "from_mate", "from_parent", "adopted_parent", "from_kit", "sibling", "from_adopted_kit", "they_injured", "they_ill", "you_injured", "you_ill", "you_grieving", "you_forgiven", "they_forgiven", "murderedyou", "murderedthem"] # List of tags that increase the weight
        weights = []
        for item in texts_list.values():
            tags = item["tags"] if "tags" in item else item[0]
            weight = 1
            if any(tag in weighted_tags for tag in tags):
                weight += 3
            if "focus" in tags or "connected" in tags:
                weight += 10
            weights.append(weight)

        # Check for debug mode
        if game.config.get("debug_ensure_dialogue") in texts_list:
            text_chosen_key = game.config["debug_ensure_dialogue"]
            text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
            new_text = self.get_adjusted_txt(text, cat)
            if new_text:
                if "intro" in texts_list[text_chosen_key]:
                    self.text_type = "choices"
                    self.display_intro(cat, texts_list, text_chosen_key)
                if "~" in text_chosen_key:
                    text_chosen_key_split = text_chosen_key.split("~")
                    cat.connected_dialogue[text_chosen_key_split[0]] = int(text_chosen_key_split[1])
                return new_text
            print("Could not find debug ensure dialogue within possible dialogues")

        # Try to find a valid, unused text
        for _ in range(MAX_RETRIES):
            text_chosen_key = choices(list(texts_list.keys()), weights=weights)[0]
            text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
            new_text = self.get_adjusted_txt(text, cat)
            
            if "intro" in texts_list[text_chosen_key]:
                for choice_key, choice_text in texts_list[text_chosen_key].items():
                    if isinstance(choice_text, list) and choice_key != "tags":
                        choice_text = self.get_adjusted_txt(choice_text, cat)
                        if not choice_text:
                            new_text = ""
                            break
            
            if text_chosen_key not in game.clan.talks and new_text:
                game.clan.talks.append(text_chosen_key)
                if "intro" in texts_list[text_chosen_key]:
                    self.text_type = "choices"
                    self.display_intro(cat, texts_list, text_chosen_key)
                if "~" in text_chosen_key:
                    text_chosen_key_split = text_chosen_key.split("~")
                    cat.connected_dialogue[text_chosen_key_split[0]] = int(text_chosen_key_split[1])
                return new_text

        # If no valid text found, choose one based on tag weights
        weights = []
        for item in texts_list.values():
            tags = item["tags"] if "tags" in item else item[0]
            weights.append(len(tags))
        text_chosen_key = choices(list(texts_list.keys()), weights=weights)[0]
        text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
        if text is None:
            text = self.load_and_replace_placeholders(f"{resource_dir}general.json", cat, you)[1]

        new_text = self.get_adjusted_txt(text, cat)
        for _ in range(MAX_RETRIES):
            if new_text:
                break
            text_chosen_key = choices(list(texts_list.keys()), weights=weights)[0]
            text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
            new_text = self.get_adjusted_txt(text, cat)
        else:
            text = self.load_and_replace_placeholders(f"{resource_dir}general.json", cat, you)[1]
            new_text = self.get_adjusted_txt(text, cat)

        if "~" in text_chosen_key:
            text_chosen_key_split = text_chosen_key.split("~")
            cat.connected_dialogue[text_chosen_key_split[0]] = int(text_chosen_key_split[1])
        game.clan.talks.append(text_chosen_key)
        return new_text

    def get_adjusted_txt(self, text, cat):
        you = game.clan.your_cat
        for i in range(len(text)):
            text[i] = self.adjust_txt(text[i], cat)
            if text[i] == "":
                return ""

        process_text_dict = self.cat_dict.copy()
    
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))
        
        process_text_dict["y_c"] = (game.clan.your_cat, choice(game.clan.your_cat.pronouns))
        process_text_dict["t_c"] = (cat, choice(cat.pronouns))
        
        for i in range(len(text)):
            text[i] = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text[i])
        
        text = [t1.replace("c_n", game.clan.name) for t1 in text]
        text = [t1.replace("y_c", str(you.name)) for t1 in text]
        text = [t1.replace("t_c", str(cat.name)) for t1 in text]

        return text

    def get_living_cats(self):
        living_cats = []
        for the_cat in Cat.all_cats_list:
            if not the_cat.dead and not the_cat.outside:
                living_cats.append(the_cat)
        return living_cats

    def adjust_txt(self, text, cat):
        """ Adjusts dialogue text by replacing abbreviations with cat names"""

        COUNTER_LIM = 30
        you = game.clan.your_cat

        if "your_crush" in text:
            cluster = False
            rel = False
            match = re.search(r'your_crush(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)your_crush', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"your_crush_{x}" in self.cat_dict or "your_crush" in self.cat_dict or f"{r}_your_crush" in self.cat_dict or f"{r}_your_crush_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_your_crush_{x}(?!\/)', str(self.cat_dict[f"{r}_your_crush_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)your_crush_{x}(?!\/)', str(self.cat_dict[f"your_crush_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_your_crush_(?!\/)', str(self.cat_dict[f"{r}_your_crush"].name), text)
                else:
                    text = re.sub(r'(?<!\/)your_crush(?!\/)', str(self.cat_dict["your_crush"].name), text)
            else:
                if len(you.mate) > 0 or you.no_mates:
                    return ""
                crush = None
                for c in self.get_living_cats():
                    if c.ID == you.ID or c.ID == cat.ID or c.ID in cat.mate or c.ID in you.mate or c.age != you.age or\
                    (cluster and x not in get_cluster(c.personality.trait)) or (rel and (c.ID not in cat.relationships) or\
                    (r == "plike" and cat.relationships[c.ID].platonic_like < 20) or\
                    (r == "plove" and cat.relationships[c.ID].platonic_like < 50) or\
                    (r == "rlike" and cat.relationships[c.ID].romantic_love < 10) or\
                    (r == "rlove" and cat.relationships[c.ID].romantic_love < 50) or\
                    (r == "dislike" and cat.relationships[c.ID].dislike < 15) or\
                    (r == "hate" and cat.relationships[c.ID].dislike < 50) or\
                    (r == "jealous" and cat.relationships[c.ID].jeaousy < 20) or\
                    (r == "trust" and cat.relationships[c.ID].trust < 20) or\
                    (r == "comfort" and cat.relationships[c.ID].comfortable < 20) or \
                    (r == "respect" and cat.relationships[c.ID].admiration < 20) or\
                    (r == "neutral" and ((cat.relationships[c.ID].platonic_like > 20) or (cat.relationships[c.ID].romantic_love > 20) or (cat.relationships[c.ID].dislike > 20) or (cat.relationships[c.ID].jealousy > 20) or (cat.relationships[c.ID].trust > 20) or (cat.relationships[c.ID].comfortable > 20) or (cat.relationships[c.ID].admiration > 20)))):
                        continue
                    relations = you.relationships.get(c.ID)
                    if not relations:
                        continue
                    if relations.romantic_love > 10:
                        crush = c
                        break
                if crush:
                    if cluster and rel:
                        self.cat_dict[f"{r}_your_crush_{x}"] = crush
                        text = re.sub(fr'(?<!\/){r}_your_crush_{x}(?!\/)', str(crush.name), text)
                    elif cluster and not rel:
                        self.cat_dict[f"your_crush_{x}"] = crush
                        text = re.sub(fr'(?<!\/)your_crush_{x}(?!\/)', str(crush.name), text)
                    elif rel and not cluster:
                        self.cat_dict[f"{r}_your_crush"] = crush
                        text = re.sub(fr'(?<!\/){r}_your_crush(?!\/)', str(crush.name), text)
                    else:
                        self.cat_dict["your_crush"] = crush
                        text = re.sub(r'(?<!\/)your_crush(?!\/)', str(crush.name), text)
                else:
                    return ""

        if "their_crush" in text:
            cluster = False
            rel = False
            match = re.search(r'their_crush(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)their_crush', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"their_crush_{x}" in self.cat_dict or "their_crush" in self.cat_dict or f"{r}_their_crush" in self.cat_dict or f"{r}_their_crush_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_their_crush_{x}(?!\/)', str(self.cat_dict[f"{r}_their_crush_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)their_crush_{x}(?!\/)', str(self.cat_dict[f"their_crush_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_their_crush_(?!\/)', str(self.cat_dict[f"{r}_their_crush"].name), text)
                else:
                    text = re.sub(r'(?<!\/)their_crush(?!\/)', str(self.cat_dict["their_crush"].name), text)
            else:
                if len(cat.mate) > 0 or cat.no_mates:
                    return ""
                crush = None
                for c in self.get_living_cats():
                    if c.ID == you.ID or c.ID == cat.ID or c.ID in cat.mate or c.ID in you.mate or c.age != cat.age or\
                    (cluster and x not in get_cluster(c.personality.trait)) or (rel and (c.ID not in cat.relationships) or\
                    (r == "plike" and cat.relationships[c.ID].platonic_like < 20) or\
                    (r == "plove" and cat.relationships[c.ID].platonic_like < 50) or\
                    (r == "rlike" and cat.relationships[c.ID].romantic_love < 10) or\
                    (r == "rlove" and cat.relationships[c.ID].romantic_love < 50) or\
                    (r == "dislike" and cat.relationships[c.ID].dislike < 15) or\
                    (r == "hate" and cat.relationships[c.ID].dislike < 50) or\
                    (r == "jealous" and cat.relationships[c.ID].jeaousy < 20) or\
                    (r == "trust" and cat.relationships[c.ID].trust < 20) or\
                    (r == "comfort" and cat.relationships[c.ID].comfortable < 20) or \
                    (r == "respect" and cat.relationships[c.ID].admiration < 20) or\
                    (r == "neutral" and ((cat.relationships[c.ID].platonic_like > 20) or (cat.relationships[c.ID].romantic_love > 20) or (cat.relationships[c.ID].dislike > 20) or (cat.relationships[c.ID].jealousy > 20) or (cat.relationships[c.ID].trust > 20) or (cat.relationships[c.ID].comfortable > 20) or (cat.relationships[c.ID].admiration > 20)))):
                        continue
                    relations = cat.relationships.get(c.ID)
                    if not relations:
                        continue
                    if relations.romantic_love > 10:
                        crush = c
                        break
                if crush:
                    if cluster and rel:
                        self.cat_dict[f"{r}_their_crush_{x}"] = crush
                        text = re.sub(fr'(?<!\/){r}_their_crush_{x}(?!\/)', str(crush.name), text)
                    elif cluster and not rel:
                        self.cat_dict[f"their_crush_{x}"] = crush
                        text = re.sub(fr'(?<!\/)their_crush_{x}(?!\/)', str(crush.name), text)
                    elif rel and not cluster:
                        self.cat_dict[f"{r}_their_crush"] = crush
                        text = re.sub(fr'(?<!\/){r}_their_crush(?!\/)', str(crush.name), text)
                    else:
                        self.cat_dict["their_crush"] = crush
                        text = re.sub(r'(?<!\/)their_crush(?!\/)', str(crush.name), text)
                else:
                    return ""

        # Multiple random cats
        for i in range(0,4):
            # Random cats
            r_c_str = f"r_c{i}"
            if r_c_str in text:
                cluster = False
                rel = False
                match = re.search(fr'r_c{i}(\w+)', text)
                if match:
                    x = match.group(1).strip("_")
                    cluster = True
                else:
                    x = ""

                match2 = re.search(fr'(\w+)r_c{i}', text)
                if match2:
                    r = match2.group(1).strip("_")
                    rel = True
                else:
                    r = ""

                if f"r_c{i}_{x}" in self.cat_dict or f"r_c{i}" in self.cat_dict or f"{r}_r_c{i}" in self.cat_dict or f"{r}_r_c{i}_{x}" in self.cat_dict:
                    if cluster and rel:
                        text = re.sub(fr'(?<!\/){r}_r_c{i}_{x}(?!\/)', str(self.cat_dict[f"{r}_r_c{i}_{x}"].name), text)
                    elif cluster and not rel:
                        text = re.sub(fr'(?<!\/)r_c{i}_{x}(?!\/)', str(self.cat_dict[f"r_c{i}_{x}"].name), text)
                    elif rel and not cluster:
                        text = re.sub(fr'(?<!\/){r}_r_c{i}_(?!\/)', str(self.cat_dict[f"{r}_r_c{i}"].name), text)
                    else:
                        text = re.sub(fr'(?<!\/)r_c{i}(?!\/)', str(self.cat_dict[f"r_c{i}"].name), text)
                    continue
                else:
                    alive_cats = self.get_living_cats()
                    if len(alive_cats) < 3:
                        return ""
                    alive_cat = choice(alive_cats)
                    counter = 0
                    while (alive_cat.ID == you.ID or alive_cat.ID == cat.ID or (cluster and x not in get_cluster(alive_cat.personality.trait)) or (rel and (alive_cat.ID not in cat.relationships) or\
                    (r == "plike" and cat.relationships[alive_cat.ID].platonic_like < 20) or\
                    (r == "plove" and cat.relationships[alive_cat.ID].platonic_like < 50) or\
                    (r == "rlike" and cat.relationships[alive_cat.ID].romantic_love < 10) or\
                    (r == "rlove" and cat.relationships[alive_cat.ID].romantic_love < 50) or\
                    (r == "dislike" and cat.relationships[alive_cat.ID].dislike < 15) or\
                    (r == "hate" and cat.relationships[alive_cat.ID].dislike < 50) or\
                    (r == "jealous" and cat.relationships[alive_cat.ID].jeaousy < 20) or\
                    (r == "trust" and cat.relationships[alive_cat.ID].trust < 20) or\
                    (r == "comfort" and cat.relationships[alive_cat.ID].comfortable < 20) or \
                    (r == "respect" and cat.relationships[alive_cat.ID].admiration < 20) or\
                    (r == "neutral" and (cat.relationships[alive_cat.ID].platonic_like > 20) or (cat.relationships[alive_cat.ID].romantic_love > 20) or (cat.relationships[alive_cat.ID].dislike > 20) or (cat.relationships[alive_cat.ID].jealousy > 20) or (cat.relationships[alive_cat.ID].trust > 20) or (cat.relationships[alive_cat.ID].comfortable > 20) or (cat.relationships[alive_cat.ID].admiration > 20))) or alive_cat in list(self.cat_dict.values())):
                        alive_cat = choice(alive_cats)
                        counter += 1
                        if counter >= 30:
                            return ""
                    if cluster and rel:
                        self.cat_dict[f"{r}_r_c{i}_{x}"] = alive_cat
                        text = re.sub(fr'(?<!\/){r}_r_c{i}_{x}(?!\/)', str(alive_cat.name), text)
                    elif cluster and not rel:
                        self.cat_dict[f"r_c{i}_{x}"] = alive_cat
                        text = re.sub(fr'(?<!\/)r_c{i}_{x}(?!\/)', str(alive_cat.name), text)
                    elif rel and not cluster:
                        self.cat_dict[f"{r}_r_c{i}"] = alive_cat
                        text = re.sub(fr'(?<!\/){r}_r_c{i}(?!\/)', str(alive_cat.name), text)
                    else:
                        self.cat_dict[f"r_c{i}"] = alive_cat
                        text = re.sub(fr'(?<!\/)r_c{i}(?!\/)', str(alive_cat.name), text)
            # Random warriors
            r_w_str = f"r_w{i}"
            if r_w_str in text:
                cluster = False
                rel = False
                match = re.search(fr'r_w{i}(\w+)', text)
                if match:
                    x = match.group(1).strip("_")
                    cluster = True
                else:
                    x = ""

                match2 = re.search(fr'(\w+)r_w{i}', text)
                if match2:
                    r = match2.group(1).strip("_")
                    rel = True
                else:
                    r = ""

                if f"r_w{i}_{x}" in self.cat_dict or f"r_w{i}" in self.cat_dict or f"{r}_r_w{i}" in self.cat_dict or f"{r}_r_w{i}_{x}" in self.cat_dict:
                    if cluster and rel:
                        text = re.sub(fr'(?<!\/){r}_r_w{i}_{x}(?!\/)', str(self.cat_dict[f"{r}_r_w{i}_{x}"].name), text)
                    elif cluster and not rel:
                        text = re.sub(fr'(?<!\/)r_w{i}_{x}(?!\/)', str(self.cat_dict[f"r_w{i}_{x}"].name), text)
                    elif rel and not cluster:
                        text = re.sub(fr'(?<!\/){r}_r_w{i}_(?!\/)', str(self.cat_dict[f"{r}_r_w{i}"].name), text)
                    else:
                        text = re.sub(fr'(?<!\/)r_w{i}(?!\/)', str(self.cat_dict[f"r_w{i}"].name), text)
                    continue
                alive_cats = get_alive_warriors(Cat)
                if len(alive_cats) < 3:
                    return ""
                alive_cat = choice(alive_cats)
                counter = 0
                while (alive_cat.ID == you.ID or alive_cat.ID == cat.ID or (cluster and x not in get_cluster(alive_cat.personality.trait)) or (rel and (alive_cat.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_cat.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_cat.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_cat.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_cat.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_cat.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_cat.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_cat.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_cat.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_cat.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_cat.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_cat.ID].platonic_like > 20) or (cat.relationships[alive_cat.ID].romantic_love > 20) or (cat.relationships[alive_cat.ID].dislike > 20) or (cat.relationships[alive_cat.ID].jealousy > 20) or (cat.relationships[alive_cat.ID].trust > 20) or (cat.relationships[alive_cat.ID].comfortable > 20) or (cat.relationships[alive_cat.ID].admiration > 20)))) or alive_cat in list(self.cat_dict.values())):
                    alive_cat = choice(alive_cats)
                    counter += 1
                    if counter > COUNTER_LIM:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_r_w{i}_{x}"] = alive_cat
                    text = re.sub(fr'(?<!\/){r}_r_w{i}_{x}(?!\/)', str(alive_cat.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_w{i}_{x}"] = alive_cat
                    text = re.sub(fr'(?<!\/)r_w{i}_{x}(?!\/)', str(alive_cat.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_w{i}"] = alive_cat
                    text = re.sub(fr'(?<!\/){r}_r_w{i}(?!\/)', str(alive_cat.name), text)
                else:
                    self.cat_dict[f"r_w{i}"] = alive_cat
                    text = re.sub(fr'(?<!\/)r_w{i}(?!\/)', str(alive_cat.name), text)
        
        # Random cats who are potential mates 
        if "n_r1" in text:
            if "n_r2" not in text:
                return ""
            cluster1 = False
            rel1 = False
            cluster2 = False
            rel2 = False
            match = re.search(fr'n_r1{i}(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster1 = True
            else:
                x = ""
            match2 = re.search(fr'(\w+)n_r1{i}', text)
            if match2:
                r = match2.group(1).strip("_")
                rel1 = True
            else:
                r = ""
            match3 = re.search(fr'n_r2{i}(\w+)', text)
            if match:
                x = match3.group(1).strip("_")
                cluster2 = True
            else:
                x = ""
            match4 = re.search(fr'(\w+)n_r2{i}', text)
            if match2:
                r = match4.group(1).strip("_")
                rel2 = True
            else:
                r = ""

            random_cat1 = choice(self.get_living_cats())
            random_cat2 = choice(self.get_living_cats())
            counter = 0
            # this is so ugly help
            while (random_cat1.ID == you.ID or random_cat1.ID == cat.ID or (cluster1 and x not in get_cluster(random_cat1.personality.trait)) or (rel1 and (random_cat1.ID not in cat.relationships) or\
            (r == "plike" and cat.relationships[random_cat1.ID].platonic_like < 20) or\
            (r == "plove" and cat.relationships[random_cat1.ID].platonic_like < 50) or\
            (r == "rlike" and cat.relationships[random_cat1.ID].romantic_love < 10) or\
            (r == "rlove" and cat.relationships[random_cat1.ID].romantic_love < 50) or\
            (r == "dislike" and cat.relationships[random_cat1.ID].dislike < 15) or\
            (r == "hate" and cat.relationships[random_cat1.ID].dislike < 50) or\
            (r == "jealous" and cat.relationships[random_cat1.ID].jeaousy < 20) or\
            (r == "trust" and cat.relationships[random_cat1.ID].trust < 20) or\
            (r == "comfort" and cat.relationships[random_cat1.ID].comfortable < 20) or \
            (r == "respect" and cat.relationships[random_cat1.ID].admiration < 20) or\
            (r == "neutral" and ((cat.relationships[random_cat1.ID].platonic_like > 20) or (cat.relationships[random_cat1.ID].romantic_love > 20) or (cat.relationships[random_cat1.ID].dislike > 20) or (cat.relationships[random_cat1.ID].jealousy > 20) or (cat.relationships[random_cat1.ID].trust > 20) or (cat.relationships[random_cat1.ID].comfortable > 20) or (cat.relationships[random_cat1.ID].admiration > 20)))) or not random_cat1.is_potential_mate(random_cat2) or random_cat2.age != random_cat1.age) or \
            (random_cat2.ID == you.ID or random_cat2.ID == cat.ID or (cluster2 and x not in get_cluster(random_cat2.personality.trait)) or (rel2 and (random_cat2.ID not in cat.relationships) or\
            (r == "plike" and cat.relationships[random_cat2.ID].platonic_like < 20) or\
            (r == "plove" and cat.relationships[random_cat2.ID].platonic_like < 50) or\
            (r == "rlike" and cat.relationships[random_cat2.ID].romantic_love < 10) or\
            (r == "rlove" and cat.relationships[random_cat2.ID].romantic_love < 50) or\
            (r == "dislike" and cat.relationships[random_cat2.ID].dislike < 15) or\
            (r == "hate" and cat.relationships[random_cat2.ID].dislike < 50) or\
            (r == "jealous" and cat.relationships[random_cat2.ID].jeaousy < 20) or\
            (r == "trust" and cat.relationships[random_cat2.ID].trust < 20) or\
            (r == "comfort" and cat.relationships[random_cat2.ID].comfortable < 20) or \
            (r == "respect" and cat.relationships[random_cat2.ID].admiration < 20) or\
            (r == "neutral" and ((cat.relationships[random_cat2.ID].platonic_like > 20) or (cat.relationships[random_cat2.ID].romantic_love > 20) or (cat.relationships[random_cat2.ID].dislike > 20) or (cat.relationships[random_cat2.ID].jealousy > 20) or (cat.relationships[random_cat2.ID].trust > 20) or (cat.relationships[random_cat2.ID].comfortable > 20) or (cat.relationships[random_cat1.ID].admiration > 20)))) or not random_cat2.is_potential_mate(random_cat1)):
                random_cat1 = choice(self.get_living_cats())
                random_cat2 = choice(self.get_living_cats())
                counter +=1
                if counter > 40:
                    return ""
            if random_cat1.ID == you.ID or random_cat1.ID == cat.ID or random_cat2.ID == you.ID or random_cat2.ID == cat.ID:
                return ""
            if cluster1 and rel1:
                self.cat_dict[f"{r}_n_r1_{x}"] = random_cat1
                text = re.sub(fr'(?<!\/){r}_n_r1_{x}(?!\/)', str(random_cat1.name), text)
            elif cluster1 and not rel1:
                self.cat_dict[f"n_r1{i}_{x}"] = random_cat1
                text = re.sub(fr'(?<!\/)n_r1_{x}(?!\/)', str(random_cat1.name), text)
            elif rel1 and not cluster1:
                self.cat_dict[f"{r}_n_r1"] = random_cat1
                text = re.sub(fr'(?<!\/){r}_n_r1(?!\/)', str(random_cat1.name), text)
            else:
                self.cat_dict["n_r1"] = random_cat1
                text = re.sub(r'(?<!\/)n_r1(?!\/)', str(random_cat1.name), text)

            if cluster2 and rel2:
                self.cat_dict[f"{r}_n_r2_{x}"] = random_cat2
                text = re.sub(fr'(?<!\/){r}_n_r2_{x}(?!\/)', str(random_cat2.name), text)
            elif cluster2 and not rel2:
                self.cat_dict[f"n_r2{i}_{x}"] = random_cat2
                text = re.sub(fr'(?<!\/)n_r2_{x}(?!\/)', str(random_cat2.name), text)
            elif rel2 and not cluster2:
                self.cat_dict[f"{r}_n_r2"] = random_cat2
                text = re.sub(fr'(?<!\/){r}_n_r2(?!\/)', str(random_cat2.name), text)
            else:
                self.cat_dict["n_r2"] = random_cat2
                text = re.sub(r'(?<!\/)n_r2(?!\/)', str(random_cat2.name), text)
        # Random kit
        if "r_k" in text:
            cluster = False
            rel = False
            match = re.search(r'r_k(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""

            match2 = re.search(r'(\w+)r_k', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            if f"r_k_{x}" in self.cat_dict or "r_k" in self.cat_dict or f"{r}_r_k" in self.cat_dict or f"{r}_r_k_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_k_{x}(?!\/)', str(self.cat_dict[f"{r}_r_k_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_k_{x}(?!\/)', str(self.cat_dict[f"r_k_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_k_(?!\/)', str(self.cat_dict[f"{r}_r_k"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_k(?!\/)', str(self.cat_dict["r_k"].name), text)
            else:
                alive_kits = get_alive_kits(Cat)
                if len(alive_kits) <= 1:
                    return ""

                alive_kit = choice(alive_kits)

                counter = 0
                # lord forgive me there must be a less disgusting way to do this sorry
                while (alive_kit.ID == you.ID or alive_kit.ID == cat.ID or (cluster and x not in get_cluster(alive_kit.personality.trait)) or (rel and (alive_kit.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_kit.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_kit.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_kit.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_kit.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_kit.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_kit.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_kit.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_kit.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_kit.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_kit.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_kit.ID].platonic_like > 20) or (cat.relationships[alive_kit.ID].romantic_love > 20) or (cat.relationships[alive_kit.ID].dislike > 20) or (cat.relationships[alive_kit.ID].jealousy > 20) or (cat.relationships[alive_kit.ID].trust > 20) or (cat.relationships[alive_kit.ID].comfortable > 20) or (cat.relationships[alive_kit.ID].admiration > 20))))):
                    counter += 1
                    if counter >= 30:
                        return ""
                    alive_kit = choice(alive_kits)
                if cluster and rel:
                    self.cat_dict[f"{r}_r_k_{x}"] = alive_kit
                    text = re.sub(fr'(?<!\/){r}_r_k_{x}(?!\/)', str(alive_kit.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_k_{x}"] = alive_kit
                    text = re.sub(fr'(?<!\/)r_k_{x}(?!\/)', str(alive_kit.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_k"] = alive_kit
                    text = re.sub(fr'(?<!\/){r}_r_k(?!\/)', str(alive_kit.name), text)
                else:
                    self.cat_dict["r_k"] = alive_kit
                    text = re.sub(r'(?<!\/)r_k(?!\/)', str(alive_kit.name), text)
        
        # Random warrior apprentice
        if "r_a" in text:
            cluster = False
            rel = False
            match = re.search(r'r_a(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""

            match2 = re.search(r'(\w+)r_a', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            if f"r_a_{x}" in self.cat_dict or "r_a" in self.cat_dict or f"{r}_r_a" in self.cat_dict or f"{r}_r_a_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_a_{x}(?!\/)', str(self.cat_dict[f"{r}_r_a_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_a_{x}(?!\/)', str(self.cat_dict[f"r_a_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_a_(?!\/)', str(self.cat_dict[f"{r}_r_a"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_a(?!\/)', str(self.cat_dict["r_a"].name), text)
            else:
                alive_apps = get_alive_apps(Cat)
                if len(alive_apps) <= 1:
                    return ""

                alive_app = choice(alive_apps)

                counter = 0
                # lord forgive me there must be a less disgusting way to do this sorry
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20))))):
                    counter += 1
                    if counter >= 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_r_a_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_a_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_a_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_a_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_a"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_a(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_a"] = alive_app
                    text = re.sub(r'(?<!\/)r_a(?!\/)', str(alive_app.name), text)
        
        # Random warrior
        if "r_w" in text and "r_w1" not in text and "r_w2" not in text and "r_w3" not in text:
            cluster = False
            rel = False
            match = re.search(r'r_w(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""

            match2 = re.search(r'(\w+)r_w', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            if f"r_w_{x}" in self.cat_dict or "r_w" in self.cat_dict or f"{r}_r_w" in self.cat_dict or f"{r}_r_w_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_w_{x}(?!\/)', str(self.cat_dict[f"{r}_r_w_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_w_{x}(?!\/)', str(self.cat_dict[f"r_w_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_w_(?!\/)', str(self.cat_dict[f"{r}_r_w"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_w(?!\/)', str(self.cat_dict["r_w"].name), text)
            else:
                alive_apps = get_alive_warriors(Cat)
                if len(alive_apps) <= 1:
                    return ""

                alive_app = choice(alive_apps)

                counter = 0
                # lord forgive me there must be a less disgusting way to do this sorry
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20))))):
                    counter += 1
                    if counter >= 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_r_w_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_w_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_w_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_w_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_w"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_w(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_w"] = alive_app
                    text = re.sub(r'(?<!\/)r_w(?!\/)', str(alive_app.name), text)

        # Random medicine cat or medicine cat apprentice
        if "r_m" in text:
            cluster = False
            rel = False
            match = re.search(r'r_m(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_m', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            if f"r_m_{x}" in self.cat_dict or "r_m" in self.cat_dict or f"{r}_r_m" in self.cat_dict or f"{r}_r_m_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_m_{x}(?!\/)', str(self.cat_dict[f"{r}_r_m_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_m_{x}(?!\/)', str(self.cat_dict[f"r_m_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_m_(?!\/)', str(self.cat_dict[f"{r}_r_m"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_m(?!\/)', str(self.cat_dict["r_m"].name), text)
            else:
                alive_apps = get_alive_meds(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20))))):
                    counter += 1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_r_m_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_m_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_m_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_m_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_m"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_m(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_m"] = alive_app
                    text = re.sub(r'(?<!\/)r_m(?!\/)', str(alive_app.name), text)
        # Random mediator or mediator apprentice
        if "r_d" in text:
            cluster = False
            rel = False
            match = re.search(r'r_d(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_d', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"r_d_{x}" in self.cat_dict or "r_d" in self.cat_dict or f"{r}_r_d" in self.cat_dict or f"{r}_r_d_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_d_{x}(?!\/)', str(self.cat_dict[f"{r}_r_d_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_d_{x}(?!\/)', str(self.cat_dict[f"r_d_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_d_(?!\/)', str(self.cat_dict[f"{r}_r_d"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_d(?!\/)', str(self.cat_dict["r_d"].name), text)
            else:
                alive_apps = get_alive_mediators(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20))))):
                    counter += 1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_r_d_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_d_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_d_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_d_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_d"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_d(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_d"] = alive_app
                    text = re.sub(r'(?<!\/)r_d(?!\/)', str(alive_app.name), text)
        # Random queen or queen's apprentice
        if "r_q" in text:
            cluster = False
            rel = False
            match = re.search(r'r_q(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_q', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            if f"r_q_{x}" in self.cat_dict or "r_q" in self.cat_dict or f"{r}_r_q" in self.cat_dict or f"{r}_r_q_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_q_{x}(?!\/)', str(self.cat_dict[f"{r}_r_q_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_q_{x}(?!\/)', str(self.cat_dict[f"r_q_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_q_(?!\/)', str(self.cat_dict[f"{r}_r_q"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_q(?!\/)', str(self.cat_dict["r_q"].name), text)
            else:
                alive_apps = get_alive_queens(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20))))):
                    counter += 1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_r_q_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_q_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_q_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_q_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_q"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_q(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_q"] = alive_app
                    text = re.sub(r'(?<!\/)r_q(?!\/)', str(alive_app.name), text)

        # Random elder
        if "r_e" in text:
            cluster = False
            rel = False
            match = re.search(r'r_e(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_e', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"r_e_{x}" in self.cat_dict or "r_e" in self.cat_dict or f"{r}_r_e" in self.cat_dict or f"{r}_r_e_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_e_{x}(?!\/)', str(self.cat_dict[f"{r}_r_e_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_e_{x}(?!\/)', str(self.cat_dict[f"r_e_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_e_(?!\/)', str(self.cat_dict[f"{r}_r_e"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_e(?!\/)', str(self.cat_dict["r_e"].name), text)
            else:
                alive_apps = get_alive_elders(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20))))):
                    alive_app = choice(alive_apps)
                    counter += 1
                    if counter == 30:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_r_e_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_e_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_e_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_e_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_e"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_e(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_e"] = alive_app
                    text = re.sub(r'(?<!\/)r_e(?!\/)', str(alive_app.name), text)
        
        # Random sick cat
        if "r_s" in text:
            cluster = False
            rel = False
            match = re.search(r'r_s(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_s', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"r_s_{x}" in self.cat_dict or "r_s" in self.cat_dict or f"{r}_r_s" in self.cat_dict or f"{r}_r_s_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_s_{x}(?!\/)', str(self.cat_dict[f"{r}_r_s_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_s_{x}(?!\/)', str(self.cat_dict[f"r_s_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_s_(?!\/)', str(self.cat_dict[f"{r}_r_s"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_s(?!\/)', str(self.cat_dict["r_s"].name), text)
            else:
                alive_apps = get_alive_cats(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or not alive_app.is_ill()):
                    alive_app = choice(alive_apps)
                    counter += 1
                    if counter == 30:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_r_s_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_s_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_s_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_s_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_s"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_s(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_s"] = alive_app
                    text = re.sub(r'(?<!\/)r_s(?!\/)', str(alive_app.name), text)

        # Random injured cat
        if "r_i" in text:
            cluster = False
            rel = False
            match = re.search(r'r_i(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_i', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"r_i_{x}" in self.cat_dict or "r_i" in self.cat_dict or f"{r}_r_i" in self.cat_dict or f"{r}_r_i_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_i_{x}(?!\/)', str(self.cat_dict[f"{r}_r_i_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_i_{x}(?!\/)', str(self.cat_dict[f"r_i_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_i_(?!\/)', str(self.cat_dict[f"{r}_r_i"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_i(?!\/)', str(self.cat_dict["r_i"].name), text)
            else:
                alive_apps = get_alive_cats(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or not alive_app.is_injured()):
                    alive_app = choice(alive_apps)
                    counter += 1
                    if counter == 30:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_r_i_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_i_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_i_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_i_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_i"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_i(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_i"] = alive_app
                    text = re.sub(r'(?<!\/)r_i(?!\/)', str(alive_app.name), text)
        # random grieving cat
        if "r_g" in text:
            cluster = False
            rel = False
            match = re.search(r'r_g(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_g', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"r_g_{x}" in self.cat_dict or "r_g" in self.cat_dict or f"{r}_r_g" in self.cat_dict or f"{r}_r_g_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_g_{x}(?!\/)', str(self.cat_dict[f"{r}_r_g_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_g_{x}(?!\/)', str(self.cat_dict[f"r_g_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_g_(?!\/)', str(self.cat_dict[f"{r}_r_g"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_g(?!\/)', str(self.cat_dict["r_g"].name), text)
            else:
                alive_apps = get_alive_cats(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or "grief stricken" not in alive_app.illnesses):
                    alive_app = choice(alive_apps)
                    counter += 1
                    if counter == 40:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_r_g_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_g_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_g_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)r_g_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_g"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_r_g(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["r_g"] = alive_app
                    text = re.sub(r'(?<!\/)r_g(?!\/)', str(alive_app.name), text)

        # Your sibling-- any age
        if "y_s" in text:
            cluster = False
            rel = False
            match = re.search(r'y_s(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)y_s', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"y_s_{x}" in self.cat_dict or "y_s" in self.cat_dict or f"{r}_y_s" in self.cat_dict or f"{r}_y_s_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_y_s_{x}(?!\/)', str(self.cat_dict[f"{r}_y_s_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)y_s_{x}(?!\/)', str(self.cat_dict[f"y_s_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_y_s_(?!\/)', str(self.cat_dict[f"{r}_y_s"].name), text)
                else:
                    text = re.sub(r'(?<!\/)y_s(?!\/)', str(self.cat_dict["t_s"].name), text)
            else:
                if len(you.inheritance.get_siblings()) == 0:
                    return ""
                counter = 0
                sibling = Cat.fetch_cat(choice(you.inheritance.get_siblings()))
                while sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID or sibling.ID == cat.ID or\
                (cluster and x not in get_cluster(sibling.personality.trait)) or (rel and (sibling.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[sibling.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[sibling.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[sibling.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[sibling.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[sibling.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[sibling.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[sibling.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[sibling.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[sibling.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[sibling.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[sibling.ID].platonic_like > 20) or (cat.relationships[sibling.ID].romantic_love > 20) or (cat.relationships[sibling.ID].dislike > 20) or (cat.relationships[sibling.ID].jealousy > 20) or (cat.relationships[sibling.ID].trust > 20) or (cat.relationships[sibling.ID].comfortable > 20) or (cat.relationships[sibling.ID].admiration > 20)))):
                    counter += 1
                    if counter > COUNTER_LIM:
                        return ""
                    sibling = Cat.fetch_cat(choice(you.inheritance.get_siblings()))
                
                if cluster and rel:
                    self.cat_dict[f"{r}_y_s_{x}"] = sibling
                    text = re.sub(fr'(?<!\/){r}_y_s_{x}(?!\/)', str(sibling.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"y_s_{x}"] = sibling
                    text = re.sub(fr'(?<!\/)y_s_{x}(?!\/)', str(sibling.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_y_s"] = sibling
                    text = re.sub(fr'(?<!\/){r}_y_s(?!\/)', str(sibling.name), text)
                else:
                    self.cat_dict["y_s"] = sibling
                    text = re.sub(r'(?<!\/)y_s(?!\/)', str(sibling.name), text)

        # your littermate
        if "y_l" in text:
            cluster = False
            rel = False
            match = re.search(r'y_l(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)y_l', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"y_l_{x}" in self.cat_dict or "y_l" in self.cat_dict or f"{r}_y_l" in self.cat_dict or f"{r}_y_l_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_y_l_{x}(?!\/)', str(self.cat_dict[f"{r}_y_l_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)y_l_{x}(?!\/)', str(self.cat_dict[f"y_l_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_y_l_(?!\/)', str(self.cat_dict[f"{r}_y_l"].name), text)
                else:
                    text = re.sub(r'(?<!\/)y_l(?!\/)', str(self.cat_dict["y_l"].name), text)
            else:
                if len(cat.inheritance.get_siblings()) == 0:
                    return ""
                counter = 0
                sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                while sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID or sibling.ID == cat.ID or sibling.moons != cat.moons or\
                (cluster and x not in get_cluster(sibling.personality.trait)) or (rel and (sibling.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[sibling.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[sibling.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[sibling.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[sibling.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[sibling.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[sibling.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[sibling.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[sibling.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[sibling.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[sibling.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[sibling.ID].platonic_like > 20) or (cat.relationships[sibling.ID].romantic_love > 20) or (cat.relationships[sibling.ID].dislike > 20) or (cat.relationships[sibling.ID].jealousy > 20) or (cat.relationships[sibling.ID].trust > 20) or (cat.relationships[sibling.ID].comfortable > 20) or (cat.relationships[sibling.ID].admiration > 20)))):
                    counter += 1
                    if counter > COUNTER_LIM:
                        return ""
                    sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                
                if cluster and rel:
                    self.cat_dict[f"{r}_y_l_{x}"] = sibling
                    text = re.sub(fr'(?<!\/){r}_y_l_{x}(?!\/)', str(sibling.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"y_l_{x}"] = sibling
                    text = re.sub(fr'(?<!\/)y_l_{x}(?!\/)', str(sibling.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_y_l"] = sibling
                    text = re.sub(fr'(?<!\/){r}_y_l(?!\/)', str(sibling.name), text)
                else:
                    self.cat_dict["y_l"] = sibling
                    text = re.sub(r'(?<!\/)y_l(?!\/)', str(sibling.name), text)

        # Their sibling-- any age
        if "t_s" in text:
            cluster = False
            rel = False
            match = re.search(r't_s(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)t_s', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"t_s_{x}" in self.cat_dict or "t_s" in self.cat_dict or f"{r}_t_s" in self.cat_dict or f"{r}_t_s_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_t_s_{x}(?!\/)', str(self.cat_dict[f"{r}_t_s_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)t_s_{x}(?!\/)', str(self.cat_dict[f"t_s_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_t_s_(?!\/)', str(self.cat_dict[f"{r}_t_s"].name), text)
                else:
                    text = re.sub(r'(?<!\/)t_s(?!\/)', str(self.cat_dict["t_s"].name), text)
            else:
                if len(cat.inheritance.get_siblings()) == 0:
                    return ""
                counter = 0
                sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                while sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID or sibling.ID == cat.ID or\
                (cluster and x not in get_cluster(sibling.personality.trait)) or (rel and (sibling.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[sibling.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[sibling.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[sibling.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[sibling.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[sibling.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[sibling.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[sibling.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[sibling.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[sibling.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[sibling.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[sibling.ID].platonic_like > 20) or (cat.relationships[sibling.ID].romantic_love > 20) or (cat.relationships[sibling.ID].dislike > 20) or (cat.relationships[sibling.ID].jealousy > 20) or (cat.relationships[sibling.ID].trust > 20) or (cat.relationships[sibling.ID].comfortable > 20) or (cat.relationships[sibling.ID].admiration > 20)))):
                    counter += 1
                    if counter > COUNTER_LIM:
                        return ""
                    sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                
                if cluster and rel:
                    self.cat_dict[f"{r}_t_s_{x}"] = sibling
                    text = re.sub(fr'(?<!\/){r}_t_s_{x}(?!\/)', str(sibling.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"t_s_{x}"] = sibling
                    text = re.sub(fr'(?<!\/)t_s_{x}(?!\/)', str(sibling.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_t_s"] = sibling
                    text = re.sub(fr'(?<!\/){r}_t_s(?!\/)', str(sibling.name), text)
                else:
                    self.cat_dict["t_s"] = sibling
                    text = re.sub(r'(?<!\/)t_s(?!\/)', str(sibling.name), text)

        # their littermate
        if "t_l" in text:
            cluster = False
            rel = False
            match = re.search(r't_l(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)t_l', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"t_l_{x}" in self.cat_dict or "t_l" in self.cat_dict or f"{r}_t_l" in self.cat_dict or f"{r}_t_l_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_t_l_{x}(?!\/)', str(self.cat_dict[f"{r}_t_l_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)t_l_{x}(?!\/)', str(self.cat_dict[f"t_l_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_t_l_(?!\/)', str(self.cat_dict[f"{r}_t_l"].name), text)
                else:
                    text = re.sub(r'(?<!\/)t_l(?!\/)', str(self.cat_dict["t_l"].name), text)
            else:
                if len(cat.inheritance.get_siblings()) == 0:
                    return ""
                counter = 0
                sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                while sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID or sibling.ID == cat.ID or sibling.moons != cat.moons or\
                (cluster and x not in get_cluster(sibling.personality.trait)) or (rel and (sibling.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[sibling.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[sibling.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[sibling.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[sibling.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[sibling.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[sibling.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[sibling.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[sibling.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[sibling.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[sibling.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[sibling.ID].platonic_like > 20) or (cat.relationships[sibling.ID].romantic_love > 20) or (cat.relationships[sibling.ID].dislike > 20) or (cat.relationships[sibling.ID].jealousy > 20) or (cat.relationships[sibling.ID].trust > 20) or (cat.relationships[sibling.ID].comfortable > 20) or (cat.relationships[sibling.ID].admiration > 20)))):
                    counter += 1
                    if counter > COUNTER_LIM:
                        return ""
                    sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                
                if cluster and rel:
                    self.cat_dict[f"{r}_t_l_{x}"] = sibling
                    text = re.sub(fr'(?<!\/){r}_t_l_{x}(?!\/)', str(sibling.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"t_l_{x}"] = sibling
                    text = re.sub(fr'(?<!\/)t_l_{x}(?!\/)', str(sibling.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_t_l"] = sibling
                    text = re.sub(fr'(?<!\/){r}_t_l(?!\/)', str(sibling.name), text)
                else:
                    self.cat_dict["t_l"] = sibling
                    text = re.sub(r'(?<!\/)t_l(?!\/)', str(sibling.name), text)

        # Your apprentice
        if "y_a" in text:
            if "y_a" in self.cat_dict:
                text = re.sub(r'(?<!\/)y_a(?!\/)', str(self.cat_dict["y_a"].name), text)
            else:
                if len(you.apprentice) == 0:
                    return ""
                your_app = Cat.fetch_cat(choice(you.apprentice))
                if your_app.ID == cat.ID:
                    return ""
                self.cat_dict["y_a"] = your_app
                text = re.sub(r'(?<!\/)y_a(?!\/)', str(your_app.name), text)

        # Their apprentice
        if "t_a" in text:
            if "t_a" in self.cat_dict:
                text = re.sub(r'(?<!\/)t_a(?!\/)', str(self.cat_dict["t_a"].name), text)
            else:
                if len(cat.apprentice) == 0:
                    return ""
                their_app = Cat.fetch_cat(choice(cat.apprentice))
                if their_app.ID == you.ID:
                    return ""
                self.cat_dict["t_a"] = their_app
                text = re.sub(r'(?<!\/)t_a(?!\/)', str(their_app.name), text)

        # Your parent
        if "y_p" in text:
            cluster = False
            rel = False
            match = re.search(r'y_p(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)y_p', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"y_p_{x}" in self.cat_dict or "y_p" in self.cat_dict or f"{r}_y_p" in self.cat_dict or f"{r}_y_p_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_y_p_{x}(?!\/)', str(self.cat_dict[f"{r}_y_p_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)y_p_{x}(?!\/)', str(self.cat_dict[f"y_p_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_y_p_(?!\/)', str(self.cat_dict[f"{r}_y_p"].name), text)
                else:
                    text = re.sub(r'(?<!\/)y_p(?!\/)', str(self.cat_dict["y_p"].name), text)
            else:
                try:
                    parent = Cat.fetch_cat(choice(you.inheritance.get_parents()))
                except:
                    return ""
                if len(you.inheritance.get_parents()) == 0 or parent.outside or parent.dead or parent.ID == cat.ID or\
                (cluster and x not in get_cluster(parent.personality.trait)) or (rel and (parent.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[parent.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[parent.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[parent.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[parent.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[parent.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[parent.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[parent.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[parent.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[parent.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[parent.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[parent.ID].platonic_like > 20) or (cat.relationships[parent.ID].romantic_love > 20) or (cat.relationships[parent.ID].dislike > 20) or (cat.relationships[parent.ID].jealousy > 20) or (cat.relationships[parent.ID].trust > 20) or (cat.relationships[parent.ID].comfortable > 20) or (cat.relationships[parent.ID].admiration > 20)))):
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_y_p_{x}"] = parent
                    text = re.sub(fr'(?<!\/){r}_y_p_{x}(?!\/)', str(parent.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"y_p_{x}"] = parent
                    text = re.sub(fr'(?<!\/)y_p_{x}(?!\/)', str(parent.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_y_p"] = parent
                    text = re.sub(fr'(?<!\/){r}_y_p(?!\/)', str(parent.name), text)
                else:
                    self.cat_dict["y_p"] = parent
                    text = re.sub(r'(?<!\/)y_p(?!\/)', str(parent.name), text)

        # Their parent
        if "t_p_positive" in text or "t_p_negative" in text or "t_p" in text:
            if "t_p_positive" in self.cat_dict:
                text = re.sub(r'(?<!\/)t_p_positive(?!\/)', str(self.cat_dict["t_p_positive"].name), text)
            if "t_p_negative" in self.cat_dict:
                text = re.sub(r'(?<!\/)t_p_negative(?!\/)', str(self.cat_dict["t_p_negative"].name), text)
            if "t_p" in self.cat_dict:
                text = re.sub(r'(?<!\/)t_p(?!\/)', str(self.cat_dict["t_p"].name), text)
            if "t_p_positive" not in self.cat_dict or "t_p_negative" not in self.cat_dict or "t_p" not in self.cat_dict:
                if len(cat.inheritance.get_parents()) == 0:
                    return ""
                parent = Cat.fetch_cat(choice(cat.inheritance.get_parents()))
                counter = 0
                while parent.outside or parent.dead or parent.ID == you.ID:
                    counter += 1
                    if counter > COUNTER_LIM:
                        return ""
                    parent = Cat.fetch_cat(choice(cat.inheritance.get_parents()))
                if parent.relationships and cat.ID in parent.relationships and parent.relationships[cat.ID].dislike > 10 and "t_p_negative" in text:
                    self.cat_dict["t_p_negative"] = parent
                    text = re.sub(r'(?<!\/)t_p_negative(?!\/)', str(parent.name), text)
                else:
                    return ""
                if parent.relationships and cat.ID in parent.relationships and parent.relationships[cat.ID].platonic_like > 10 and "t_p_positive" in text:
                    self.cat_dict["t_p_positive"] = parent
                    text = re.sub(r'(?<!\/)t_p_positive(?!\/)', str(parent.name), text)
                else:
                    return ""
                self.cat_dict["t_p"] = parent
                text = re.sub(r'(?<!\/)t_p(?!\/)', str(parent.name), text)
        
        # Your mate
        if "y_m" in text:
            cluster = False
            rel = False
            match = re.search(r'y_m(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)y_m', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"y_m_{x}" in self.cat_dict or "y_m" in self.cat_dict or f"{r}_y_m" in self.cat_dict or f"{r}_y_m_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_y_m_{x}(?!\/)', str(self.cat_dict[f"{r}_y_m_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)y_m_{x}(?!\/)', str(self.cat_dict[f"y_m_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_y_m_(?!\/)', str(self.cat_dict[f"{r}_y_m"].name), text)
                else:
                    text = re.sub(r'(?<!\/)y_m(?!\/)', str(self.cat_dict["y_m"].name), text)
            else:
                if you.mate:
                    mate0 = Cat.fetch_cat(choice(you.mate))
                else:
                    return ""
                if you.mate is None or len(you.mate) == 0 or you.ID in cat.mate or\
                (cluster and x not in get_cluster(mate0.personality.trait)) or (rel and (mate0.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[mate0.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[mate0.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[mate0.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[mate0.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[mate0.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[mate0.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[mate0.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[mate0.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[mate0.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[mate0.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[mate0.ID].platonic_like > 20) or (cat.relationships[mate0.ID].romantic_love > 20) or (cat.relationships[mate0.ID].dislike > 20) or (cat.relationships[mate0.ID].jealousy > 20) or (cat.relationships[mate0.ID].trust > 20) or (cat.relationships[mate0.ID].comfortable > 20) or (cat.relationships[mate0.ID].admiration > 20)))):
                    return ""
                if mate0.outside or mate0.dead:
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_y_m_{x}"] = mate0
                    text = re.sub(fr'(?<!\/){r}_y_m_{x}(?!\/)', str(mate0.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"y_m_{x}"] = mate0
                    text = re.sub(fr'(?<!\/)y_m_{x}(?!\/)', str(mate0.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_y_m"] = mate0
                    text = re.sub(fr'(?<!\/){r}_y_m(?!\/)', str(mate0.name), text)
                else:
                    self.cat_dict["y_m"] = mate0
                    text = re.sub(r'(?<!\/)y_m(?!\/)', str(mate0.name), text)

        # Their mate
        if "t_m" in text:
            cluster = False
            rel = False
            match = re.search(r't_m(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)t_m', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"t_m_{x}" in self.cat_dict or "t_m" in self.cat_dict or f"{r}_t_m" in self.cat_dict or f"{r}_t_m_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_t_m_{x}(?!\/)', str(self.cat_dict[f"{r}_t_m_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)t_m_{x}(?!\/)', str(self.cat_dict[f"t_m_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_t_m_(?!\/)', str(self.cat_dict[f"{r}_t_m"].name), text)
                else:
                    text = re.sub(r'(?<!\/)t_m(?!\/)', str(self.cat_dict["t_m"].name), text)
            else:
                if cat.mate:
                    mate1 = Cat.fetch_cat(choice(cat.mate))
                else:
                    return ""
                if cat.mate is None or len(cat.mate) == 0 or cat.ID in you.mate or\
                (cluster and x not in get_cluster(mate1.personality.trait)) or (rel and (mate1.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[mate1.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[mate1.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[mate1.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[mate1.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[mate1.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[mate1.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[mate1.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[mate1.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[mate1.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[mate1.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[mate1.ID].platonic_like > 20) or (cat.relationships[mate1.ID].romantic_love > 20) or (cat.relationships[mate1.ID].dislike > 20) or (cat.relationships[mate1.ID].jealousy > 20) or (cat.relationships[mate1.ID].trust > 20) or (cat.relationships[mate1.ID].comfortable > 20) or (cat.relationships[mate1.ID].admiration > 20)))):
                    return ""
                if mate1.outside or mate1.dead:
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_t_m_{x}"] = mate1
                    text = re.sub(fr'(?<!\/){r}_t_m_{x}(?!\/)', str(mate1.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"t_m_{x}"] = mate1
                    text = re.sub(fr'(?<!\/)t_m_{x}(?!\/)', str(mate1.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_t_m"] = mate1
                    text = re.sub(fr'(?<!\/){r}_t_m(?!\/)', str(mate1.name), text)
                else:
                    self.cat_dict["t_m"] = mate1
                    text = re.sub(r'(?<!\/)t_m(?!\/)', str(mate1.name), text)

        # Their adult kit
        if "t_ka" in text:
            cluster = False
            rel = False
            match = re.search(r't_ka(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)t_ka', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"t_ka_{x}" in self.cat_dict or "t_ka" in self.cat_dict or f"{r}_t_ka" in self.cat_dict or f"{r}_t_ka_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_t_ka_{x}(?!\/)', str(self.cat_dict[f"{r}_t_ka_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)t_ka_{x}(?!\/)', str(self.cat_dict[f"t_ka_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_t_ka_(?!\/)', str(self.cat_dict[f"{r}_t_ka"].name), text)
                else:
                    text = re.sub(r'(?<!\/)t_ka(?!\/)', str(self.cat_dict["t_ka"].name), text)
            else:
                if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
                if kit.moons < 12 or kit.outside or kit.dead or kit.ID == cat.ID or\
                (cluster and x not in get_cluster(kit.personality.trait)) or (rel and (kit.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[kit.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[kit.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[kit.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[kit.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[kit.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[kit.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[kit.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[kit.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[kit.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[kit.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[kit.ID].platonic_like > 20) or (cat.relationships[kit.ID].romantic_love > 20) or (cat.relationships[kit.ID].dislike > 20) or (cat.relationships[kit.ID].jealousy > 20) or (cat.relationships[kit.ID].trust > 20) or (cat.relationships[kit.ID].comfortable > 20) or (cat.relationships[kit.ID].admiration > 20)))):
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_t_ka_{x}"] = kit
                    text = re.sub(fr'(?<!\/){r}_t_ka_{x}(?!\/)', str(kit.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"t_ka_{x}"] = kit
                    text = re.sub(fr'(?<!\/)t_ka_{x}(?!\/)', str(kit.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_t_ka"] = kit
                    text = re.sub(fr'(?<!\/){r}_t_ka(?!\/)', str(kit.name), text)
                else:
                    self.cat_dict["t_ka"] = kit
                    text = re.sub(r'(?<!\/)t_ka(?!\/)', str(kit.name), text)

        # Their kitten kit
        if "t_kk" in text:
            cluster = False
            rel = False
            match = re.search(r't_kk(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)t_kk', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"t_kk_{x}" in self.cat_dict or "t_kk" in self.cat_dict or f"{r}_t_kk" in self.cat_dict or f"{r}_t_kk_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_t_kk_{x}(?!\/)', str(self.cat_dict[f"{r}_t_kk_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)t_kk_{x}(?!\/)', str(self.cat_dict[f"t_kk_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_t_kk_(?!\/)', str(self.cat_dict[f"{r}_t_kk"].name), text)
                else:
                    text = re.sub(r'(?<!\/)t_kk(?!\/)', str(self.cat_dict["t_kk"].name), text)
            else:
                if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
                if kit.moons >= 6 or kit.outside or kit.dead or kit.ID == cat.ID or\
                (cluster and x not in get_cluster(kit.personality.trait)) or (rel and (kit.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[kit.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[kit.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[kit.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[kit.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[kit.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[kit.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[kit.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[kit.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[kit.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[kit.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[kit.ID].platonic_like > 20) or (cat.relationships[kit.ID].romantic_love > 20) or (cat.relationships[kit.ID].dislike > 20) or (cat.relationships[kit.ID].jealousy > 20) or (cat.relationships[kit.ID].trust > 20) or (cat.relationships[kit.ID].comfortable > 20) or (cat.relationships[kit.ID].admiration > 20)))):
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_t_kk_{x}"] = kit
                    text = re.sub(fr'(?<!\/){r}_t_kk_{x}(?!\/)', str(kit.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"t_kk_{x}"] = kit
                    text = re.sub(fr'(?<!\/)t_kk_{x}(?!\/)', str(kit.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_t_kk"] = kit
                    text = re.sub(fr'(?<!\/){r}_t_kk(?!\/)', str(kit.name), text)
                else:
                    self.cat_dict["t_kk"] = kit
                    text = re.sub(r'(?<!\/)t_kk(?!\/)', str(kit.name), text)

        # Their kit
        if "t_k" in text and "t_kk" not in text and "t_ka" not in text:
            cluster = False
            rel = False
            match = re.search(r't_k(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)t_k', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"t_k_{x}" in self.cat_dict or "t_k" in self.cat_dict or f"{r}_t_k" in self.cat_dict or f"{r}_t_k_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_t_k_{x}(?!\/)', str(self.cat_dict[f"{r}_t_k_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)t_k_{x}(?!\/)', str(self.cat_dict[f"t_k_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_t_k_(?!\/)', str(self.cat_dict[f"{r}_t_k"].name), text)
                else:
                    text = re.sub(r'(?<!\/)t_k(?!\/)', str(self.cat_dict["t_k"].name), text)
            else:
                if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
                if kit.outside or kit.dead or kit.ID == cat.ID or\
                (cluster and x not in get_cluster(kit.personality.trait)) or (rel and (kit.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[kit.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[kit.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[kit.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[kit.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[kit.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[kit.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[kit.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[kit.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[kit.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[kit.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[kit.ID].platonic_like > 20) or (cat.relationships[kit.ID].romantic_love > 20) or (cat.relationships[kit.ID].dislike > 20) or (cat.relationships[kit.ID].jealousy > 20) or (cat.relationships[kit.ID].trust > 20) or (cat.relationships[kit.ID].comfortable > 20) or (cat.relationships[kit.ID].admiration > 20)))):
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_t_k_{x}"] = kit
                    text = re.sub(fr'(?<!\/){r}_t_k_{x}(?!\/)', str(kit.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"t_k_{x}"] = kit
                    text = re.sub(fr'(?<!\/)t_k_{x}(?!\/)', str(kit.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_t_k"] = kit
                    text = re.sub(fr'(?<!\/){r}_t_k(?!\/)', str(kit.name), text)
                else:
                    self.cat_dict["t_k"] = kit
                    text = re.sub(r'(?<!\/)t_k(?!\/)', str(kit.name), text)

        # Your kit
        if "y_k" in text and "y_kk" not in text:
            cluster = False
            rel = False
            match = re.search(r'y_k(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)y_k', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"y_k_{x}" in self.cat_dict or "y_k" in self.cat_dict or f"{r}_y_k" in self.cat_dict or f"{r}_y_k_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_y_k_{x}(?!\/)', str(self.cat_dict[f"{r}_y_k_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)y_k_{x}(?!\/)', str(self.cat_dict[f"y_k_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_y_k_(?!\/)', str(self.cat_dict[f"{r}_y_k"].name), text)
                else:
                    text = re.sub(r'(?<!\/)y_k(?!\/)', str(self.cat_dict["y_k"].name), text)
            else:
                if you.inheritance.get_children() is None or len(you.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(you.inheritance.get_children()))
                if kit.outside or kit.dead or kit.ID == cat.ID or\
                (cluster and x not in get_cluster(kit.personality.trait)) or (rel and (kit.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[kit.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[kit.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[kit.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[kit.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[kit.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[kit.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[kit.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[kit.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[kit.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[kit.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[kit.ID].platonic_like > 20) or (cat.relationships[kit.ID].romantic_love > 20) or (cat.relationships[kit.ID].dislike > 20) or (cat.relationships[kit.ID].jealousy > 20) or (cat.relationships[kit.ID].trust > 20) or (cat.relationships[kit.ID].comfortable > 20) or (cat.relationships[kit.ID].admiration > 20)))):
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_y_k_{x}"] = kit
                    text = re.sub(fr'(?<!\/){r}_y_k_{x}(?!\/)', str(kit.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"y_k_{x}"] = kit
                    text = re.sub(fr'(?<!\/)y_k_{x}(?!\/)', str(kit.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_y_k"] = kit
                    text = re.sub(fr'(?<!\/){r}_y_k(?!\/)', str(kit.name), text)
                else:
                    self.cat_dict["y_k"] = kit
                    text = re.sub(r'(?<!\/)y_k(?!\/)', str(kit.name), text)

        # Your kit-- kitten age
        if "y_kk" in text:
            cluster = False
            rel = False
            match = re.search(r'y_kk(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)y_kk', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"y_kk_{x}" in self.cat_dict or "y_kk" in self.cat_dict or f"{r}_y_kk" in self.cat_dict or f"{r}_y_kk_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_y_kk_{x}(?!\/)', str(self.cat_dict[f"{r}_y_kk_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)y_kk_{x}(?!\/)', str(self.cat_dict[f"y_kk_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_y_kk_(?!\/)', str(self.cat_dict[f"{r}_y_kk"].name), text)
                else:
                    text = re.sub(r'(?<!\/)y_kk(?!\/)', str(self.cat_dict["y_kk"].name), text)
            else:
                if you.inheritance.get_children() is None or len(you.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(you.inheritance.get_children()))
                if kit.moons >= 6 or kit.outside or kit.dead or kit.ID == cat.ID or\
                (cluster and x not in get_cluster(kit.personality.trait)) or (rel and (kit.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[kit.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[kit.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[kit.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[kit.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[kit.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[kit.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[kit.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[kit.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[kit.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[kit.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[kit.ID].platonic_like > 20) or (cat.relationships[kit.ID].romantic_love > 20) or (cat.relationships[kit.ID].dislike > 20) or (cat.relationships[kit.ID].jealousy > 20) or (cat.relationships[kit.ID].trust > 20) or (cat.relationships[kit.ID].comfortable > 20) or (cat.relationships[kit.ID].admiration > 20)))):
                    return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_y_kk_{x}"] = kit
                    text = re.sub(fr'(?<!\/){r}_y_kk_{x}(?!\/)', str(kit.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"y_kk_{x}"] = kit
                    text = re.sub(fr'(?<!\/)y_kk_{x}(?!\/)', str(kit.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_y_kk"] = kit
                    text = re.sub(fr'(?<!\/){r}_y_kk(?!\/)', str(kit.name), text)
                else:
                    self.cat_dict["y_kk"] = kit
                    text = re.sub(r'(?<!\/)y_kk(?!\/)', str(kit.name), text)
        
        # Random cat
        if "r_c" in text and "r_c1" not in text and "r_c2" not in text and "r_c3" not in text:
            cluster = False
            rel = False
            match = re.search(r'r_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
           
            if f"r_c_{x}" in self.cat_dict or "r_c" in self.cat_dict or f"{r}_r_c" in self.cat_dict or f"{r}_r_c_{x}" in self.cat_dict:
                words = text.split()
                for i, word in enumerate(words):
                    if word == "r_c" and (i == 0 or words[i-1][-1] not in ["{", "|"]):
                        words[i] = str(self.cat_dict["r_c"].name)
                text = " ".join(words)

                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_r_c_{x}(?!\/)', str(self.cat_dict[f"{r}_r_c_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)r_c_{x}(?!\/)', str(self.cat_dict[f"r_c_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_r_c_(?!\/)', str(self.cat_dict[f"{r}_r_c"].name), text)
                else:
                    text = re.sub(r'(?<!\/)r_c(?!\/)', str(self.cat_dict["r_c"].name), text)
            else:
                random_cat = choice(self.get_living_cats())
                counter = 0
                while (random_cat.ID == you.ID or random_cat.ID == cat.ID or (cluster and x not in get_cluster(random_cat.personality.trait)) or (rel and (random_cat.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[random_cat.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[random_cat.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[random_cat.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[random_cat.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[random_cat.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[random_cat.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[random_cat.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[random_cat.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[random_cat.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[random_cat.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[random_cat.ID].platonic_like > 20) or (cat.relationships[random_cat.ID].romantic_love > 20) or (cat.relationships[random_cat.ID].dislike > 20) or (cat.relationships[random_cat.ID].jealousy > 20) or (cat.relationships[random_cat.ID].trust > 20) or (cat.relationships[random_cat.ID].comfortable > 20) or (cat.relationships[random_cat.ID].admiration > 20))))):
                    if counter == 30:
                        return ""
                    random_cat = choice(self.get_living_cats())
                    counter += 1
                if cluster and rel:
                    self.cat_dict[f"{r}_r_c_{x}"] = random_cat
                    text = re.sub(fr'(?<!\/){r}_r_c_{x}(?!\/)', str(random_cat.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"r_c_{x}"] = random_cat
                    text = re.sub(fr'(?<!\/)r_c_{x}(?!\/)', str(random_cat.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_r_c"] = random_cat
                    text = re.sub(fr'(?<!\/){r}_r_c(?!\/)', str(random_cat.name), text)
                else:
                    self.cat_dict["r_c"] = random_cat
                    text = re.sub(r'(?<!\/)r_c(?!\/)', str(random_cat.name), text)
        # Other Clan
        if "o_c" in text:
            if "o_c" in self.other_dict:
                text = re.sub(r'(?<!\/)o_c(?!\/)', str(self.other_dict["o_c"].name), text)
            else:
                other_clan = choice(game.clan.all_clans)
                if not other_clan:
                    return ""
                self.other_dict["o_c"] = other_clan
                text = re.sub(r'(?<!\/)o_c(?!\/)', str(other_clan.name), text)

        # Your DF Mentor
        if "df_m_n" in text:
            if you.joined_df and not you.dead and you.df_mentor and cat.ID != you.df_mentor:
                self.cat_dict["df_m_n"] = Cat.all_cats.get(you.df_mentor)
                text = re.sub(r'(?<!\/)df_m_n(?!\/)', str(Cat.all_cats.get(you.df_mentor).name), text)
            else:
                return ""
            
        # Their mentor
        if "tm_n" in text:
            if cat.mentor is None or cat.mentor == you.ID:
                return ""
            self.cat_dict["tm_n"] = Cat.fetch_cat(cat.mentor)
            text = re.sub(r'(?<!\/)tm_n(?!\/)', str(Cat.fetch_cat(cat.mentor).name), text)
            

        # Your mentor
        if "m_n" in text:
            if you.mentor is None or you.mentor == cat.ID:
                return ""
            self.cat_dict["m_n"] = Cat.fetch_cat(you.mentor)
            text = re.sub(r'(?<!\/)m_n(?!\/)', str(Cat.fetch_cat(you.mentor).name), text)

        # Their DF metnor
        if "t_df_mn" in text:
            if cat.joined_df and not cat.dead and cat.df_mentor:
                self.cat_dict["t_df_mn"] = Cat.all_cats.get(cat.df_mentor)
                text = re.sub(r'(?<!\/)t_df_mn(?!\/)', str(Cat.all_cats.get(cat.df_mentor).name), text)
            else:
                return ""
        
        # Clan leader's name
        if "l_n" in text:
            cluster = False
            rel = False
            match = re.search(r'l_n(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)l_n', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if game.clan.leader is None:
                return ""
            if game.clan.leader.dead or game.clan.leader.outside or game.clan.leader.ID == you.ID or game.clan.leader.ID == cat.ID or\
            (rel and (game.clan.leader.ID not in cat.relationships) or\
            (r == "plike" and cat.relationships[game.clan.leader.ID].platonic_like < 20) or\
            (r == "plove" and cat.relationships[game.clan.leader.ID].platonic_like < 50) or\
            (r == "rlike" and cat.relationships[game.clan.leader.ID].romantic_love < 10) or\
            (r == "rlove" and cat.relationships[game.clan.leader.ID].romantic_love < 50) or\
            (r == "dislike" and cat.relationships[game.clan.leader.ID].dislike < 15) or\
            (r == "hate" and cat.relationships[game.clan.leader.ID].dislike < 50) or\
            (r == "jealous" and cat.relationships[game.clan.leader.ID].jeaousy < 20) or\
            (r == "trust" and cat.relationships[game.clan.leader.ID].trust < 20) or\
            (r == "comfort" and cat.relationships[game.clan.leader.ID].comfortable < 20) or \
            (r == "respect" and cat.relationships[game.clan.leader.ID].admiration < 20) or\
            (r == "neutral" and ((cat.relationships[game.clan.leader.ID].platonic_like > 20) or (cat.relationships[game.clan.leader.ID].romantic_love > 20) or (cat.relationships[game.clan.leader.ID].dislike > 20) or (cat.relationships[game.clan.leader.ID].jealousy > 20) or (cat.relationships[game.clan.leader.ID].trust > 20) or (cat.relationships[game.clan.leader.ID].comfortable > 20) or (cat.relationships[game.clan.leader.ID].admiration > 20)))):
                return ""
            if cluster and rel:
                self.cat_dict[f"{r}_l_n_{x}"] = game.clan.leader
                text = re.sub(fr'(?<!\/){r}_l_n_{x}(?!\/)', str(game.clan.leader.name), text)
            elif cluster and not rel:
                self.cat_dict[f"l_n_{x}"] = game.clan.leader
                text = re.sub(fr'(?<!\/)l_n_{x}(?!\/)', str(game.clan.leader.name), text)
            elif rel and not cluster:
                self.cat_dict[f"{r}_l_n"] = game.clan.leader
                text = re.sub(fr'(?<!\/){r}_l_n(?!\/)', str(game.clan.leader.name), text)
            else:
                self.cat_dict["l_n"] = game.clan.leader
                text = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.leader.name), text)

        # Deputy's name
        if "d_n" in text:
            cluster = False
            rel = False
            match = re.search(r'd_n(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)d_n', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if game.clan.leader is None:
                return ""
            if game.clan.deputy is None:
                return ""
            if game.clan.deputy.dead or game.clan.deputy.outside or game.clan.deputy.ID == you.ID or game.clan.deputy.ID == cat.ID or\
            (rel and (game.clan.leader.ID not in cat.relationships) or\
            (r == "plike" and cat.relationships[game.clan.leader.ID].platonic_like < 20) or\
            (r == "plove" and cat.relationships[game.clan.leader.ID].platonic_like < 50) or\
            (r == "rlike" and cat.relationships[game.clan.leader.ID].romantic_love < 10) or\
            (r == "rlove" and cat.relationships[game.clan.leader.ID].romantic_love < 50) or\
            (r == "dislike" and cat.relationships[game.clan.leader.ID].dislike < 15) or\
            (r == "hate" and cat.relationships[game.clan.leader.ID].dislike < 50) or\
            (r == "jealous" and cat.relationships[game.clan.leader.ID].jeaousy < 20) or\
            (r == "trust" and cat.relationships[game.clan.leader.ID].trust < 20) or\
            (r == "comfort" and cat.relationships[game.clan.leader.ID].comfortable < 20) or \
            (r == "respect" and cat.relationships[game.clan.leader.ID].admiration < 20) or\
            (r == "neutral" and ((cat.relationships[game.clan.leader.ID].platonic_like > 20) or (cat.relationships[game.clan.leader.ID].romantic_love > 20) or (cat.relationships[game.clan.leader.ID].dislike > 20) or (cat.relationships[game.clan.leader.ID].jealousy > 20) or (cat.relationships[game.clan.leader.ID].trust > 20) or (cat.relationships[game.clan.leader.ID].comfortable > 20) or (cat.relationships[game.clan.leader.ID].admiration > 20)))):
                return ""
            if cluster and rel:
                self.cat_dict[f"{r}_d_n_{x}"] = game.clan.deputy
                text = re.sub(fr'(?<!\/){r}_d_n_{x}(?!\/)', str(game.clan.deputy.name), text)
            elif cluster and not rel:
                self.cat_dict[f"d_n_{x}"] = game.clan.deputy
                text = re.sub(fr'(?<!\/)d_n_{x}(?!\/)', str(game.clan.deputy.name), text)
            elif rel and not cluster:
                self.cat_dict[f"{r}_d_n"] = game.clan.deputy
                text = re.sub(fr'(?<!\/){r}_d_n(?!\/)', str(game.clan.deputy.name), text)
            else:
                self.cat_dict["d_n"] = game.clan.deputy
                text = re.sub(r'(?<!\/)d_n(?!\/)', str(game.clan.deputy.name), text)


        # d_c is the cat you/they are grieving
        if "grief stricken" in cat.illnesses:
            try:
                dead_cat = Cat.all_cats.get(cat.illnesses['grief stricken'].get("grief_cat"))
                words = text.split()
                for i, word in enumerate(words):
                    if word == "d_c" and (i == 0 or words[i-1][-1] != "{"):
                        words[i] = str(dead_cat.name)
                text = " ".join(words)
                text = re.sub(r'(?<!\/)d_c(?!\/)', str(dead_cat.name), text)
                self.cat_dict["d_c"] = dead_cat
            except:
                return ""
        elif "grief stricken" in you.illnesses:
            try:
                dead_cat = Cat.all_cats.get(you.illnesses['grief stricken'].get("grief_cat"))
                words = text.split()
                for i, word in enumerate(words):
                    if word == "d_c" and (i == 0 or words[i-1][-1] != "{"):
                        words[i] = str(dead_cat.name)
                text = " ".join(words)
                text = re.sub(r'(?<!\/)d_c(?!\/)', str(dead_cat.name), text)
                self.cat_dict["d_c"] = dead_cat
            except:
                return ""

        if "d_c" in text:
            cluster = False
            rel = False
            match = re.search(r'd_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)d_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"d_c_{x}" in self.cat_dict or "d_c" in self.cat_dict or f"{r}_d_c" in self.cat_dict or f"{r}_d_c_{x}" in self.cat_dict:
                words = text.split()
                for i, word in enumerate(words):
                    if word == "d_c" and (i == 0 or words[i-1][-1] != "{"):
                        words[i] = str(self.cat_dict["d_c"].name)
                text = " ".join(words)

                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_d_c_{x}(?!\/)', str(self.cat_dict[f"{r}_d_c_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)d_c_{x}(?!\/)', str(self.cat_dict[f"d_c_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_d_c_(?!\/)', str(self.cat_dict[f"{r}_d_c"].name), text)
                else:
                    text = re.sub(r'(?<!\/)d_c(?!\/)', str(self.cat_dict["d_c"].name), text)
            else:
                dead_cat = Cat.all_cats.get(choice(game.clan.starclan_cats))
                counter = 0
                while (dead_cat.ID == you.ID or dead_cat.ID == cat.ID or dead_cat.ID in [game.clan.instructor.ID, game.clan.demon.ID] or (cluster and x not in get_cluster(dead_cat.personality.trait)) or (rel and (dead_cat.ID not in cat.relationships) or (dead_cat.ID in cat.relationships and (
                (r == "plike" and cat.relationships[dead_cat.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[dead_cat.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[dead_cat.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[dead_cat.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[dead_cat.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[dead_cat.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[dead_cat.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[dead_cat.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[dead_cat.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[dead_cat.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[dead_cat.ID].platonic_like > 20) or (cat.relationships[dead_cat.ID].romantic_love > 20) or (cat.relationships[dead_cat.ID].dislike > 20) or (cat.relationships[dead_cat.ID].jealousy > 20) or (cat.relationships[dead_cat.ID].trust > 20) or (cat.relationships[dead_cat.ID].comfortable > 20) or (cat.relationships[dead_cat.ID].admiration > 20))))))):
                    if counter == 30:
                        return ""
                    dead_cat = Cat.all_cats.get(choice(game.clan.starclan_cats))
                    counter += 1
                self.cat_dict["d_c"] = dead_cat
                words = text.split()
                for i, word in enumerate(words):
                    if word == "d_c" and (i == 0 or words[i-1][-1] != "{"):
                        words[i] = str(dead_cat.name)
                text = " ".join(words)
                if cluster and rel:
                    self.cat_dict[f"{r}_d_c_{x}"] = dead_cat
                    text = re.sub(fr'(?<!\/){r}_d_c_{x}(?!\/)', str(dead_cat.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"d_c_{x}"] = dead_cat
                    text = re.sub(fr'(?<!\/)d_c_{x}(?!\/)', str(dead_cat.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_d_c"] = dead_cat
                    text = re.sub(fr'(?<!\/){r}_d_c(?!\/)', str(dead_cat.name), text)
                else:
                    self.cat_dict["d_c"] = dead_cat
                    text = re.sub(r'(?<!\/)d_c(?!\/)', str(dead_cat.name), text)

        if "rdf_c" in text:
            cluster = False
            rel = False
            match = re.search(r'rdf_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rdf_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"rdf_c_{x}" in self.cat_dict or "rdf_c" in self.cat_dict or f"{r}_rdf_c" in self.cat_dict or f"{r}_rdf_c_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rdf_c_{x}(?!\/)', str(self.cat_dict[f"{r}_rdf_c_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rdf_c_{x}(?!\/)', str(self.cat_dict[f"rdf_c_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rdf_c_(?!\/)', str(self.cat_dict[f"{r}_rdf_c"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rdf_c(?!\/)', str(self.cat_dict["rdf_c"].name), text)
            else:
                random_cat = Cat.all_cats.get(choice(game.clan.darkforest_cats))
                counter = 0
                while (random_cat.ID == you.ID or random_cat.ID == cat.ID or (cluster and x not in get_cluster(random_cat.personality.trait)) or (rel and (random_cat.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[random_cat.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[random_cat.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[random_cat.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[random_cat.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[random_cat.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[random_cat.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[random_cat.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[random_cat.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[random_cat.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[random_cat.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[random_cat.ID].platonic_like > 20) or (cat.relationships[random_cat.ID].romantic_love > 20) or (cat.relationships[random_cat.ID].dislike > 20) or (cat.relationships[random_cat.ID].jealousy > 20) or (cat.relationships[random_cat.ID].trust > 20) or (cat.relationships[random_cat.ID].comfortable > 20) or (cat.relationships[random_cat.ID].admiration > 20))))):
                    if counter == 30:
                        print("counter moment")
                        return ""
                    random_cat = Cat.all_cats.get(choice(game.clan.darkforest_cats))
                    counter +=1
                if cluster and rel:
                    self.cat_dict[f"{r}_rdf_c_{x}"] = random_cat
                    text = re.sub(fr'(?<!\/){r}_rdf_c_{x}(?!\/)', str(random_cat.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rdf_c_{x}"] = random_cat
                    text = re.sub(fr'(?<!\/)rdf_c_{x}(?!\/)', str(random_cat.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rdf_c"] = random_cat
                    text = re.sub(fr'(?<!\/){r}_rdf_c(?!\/)', str(random_cat.name), text)
                else:
                    self.cat_dict["rdf_c"] = random_cat
                    text = re.sub(r'(?<!\/)rdf_c(?!\/)', str(random_cat.name), text)
        
        if "rsh_c" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"rsh_c_{x}" in self.cat_dict or "rsh_c" in self.cat_dict or f"{r}_rsh_c" in self.cat_dict or f"{r}_rsh_c_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_c_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_c_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_c_{x}(?!\/)', str(self.cat_dict[f"rsh_c_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_c_(?!\/)', str(self.cat_dict[f"{r}_rsh_c"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_c(?!\/)', str(self.cat_dict["rsh_c"].name), text)
            else:
                random_cat = choice(self.get_living_cats())
                counter = 0
                while (random_cat.ID == you.ID or random_cat.ID == cat.ID or (cluster and x not in get_cluster(random_cat.personality.trait)) or (rel and (random_cat.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[random_cat.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[random_cat.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[random_cat.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[random_cat.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[random_cat.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[random_cat.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[random_cat.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[random_cat.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[random_cat.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[random_cat.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[random_cat.ID].platonic_like > 20) or (cat.relationships[random_cat.ID].romantic_love > 20) or (cat.relationships[random_cat.ID].dislike > 20) or (cat.relationships[random_cat.ID].jealousy > 20) or (cat.relationships[random_cat.ID].trust > 20) or (cat.relationships[random_cat.ID].comfortable > 20) or (cat.relationships[random_cat.ID].admiration > 20)))) or random_cat.shunned == 0):
                    if counter == 30:
                        return ""
                    random_cat = choice(self.get_living_cats())
                    counter +=1
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_c_{x}"] = random_cat
                    text = re.sub(fr'(?<!\/){r}_rsh_c_{x}(?!\/)', str(random_cat.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_c_{x}"] = random_cat
                    text = re.sub(fr'(?<!\/)rsh_c_{x}(?!\/)', str(random_cat.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_c"] = random_cat
                    text = re.sub(fr'(?<!\/){r}_rsh_c(?!\/)', str(random_cat.name), text)
                else:
                    self.cat_dict["rsh_c"] = random_cat
                    text = re.sub(r'(?<!\/)rsh_c(?!\/)', str(random_cat.name), text)

        if "rsh_k" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_k(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_k', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            alive_kits = get_alive_kits(Cat)
            if len(alive_kits) < 1:
                return ""
            if f"rsh_k_{x}" in self.cat_dict or "rsh_k" in self.cat_dict or f"{r}_rsh_k" in self.cat_dict or f"{r}_rsh_k_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_k_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_k_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_k_{x}(?!\/)', str(self.cat_dict[f"rsh_k_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_k_(?!\/)', str(self.cat_dict[f"{r}_rsh_k"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_k(?!\/)', str(self.cat_dict["rsh_k"].name), text)
            else:
                alive_kit = choice(alive_kits)
                counter = 0
                while (alive_kit.ID == you.ID or alive_kit.ID == cat.ID or (cluster and x not in get_cluster(alive_kit.personality.trait)) or (rel and (alive_kit.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_kit.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_kit.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_kit.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_kit.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_kit.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_kit.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_kit.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_kit.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_kit.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_kit.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_kit.ID].platonic_like > 20) or (cat.relationships[alive_kit.ID].romantic_love > 20) or (cat.relationships[alive_kit.ID].dislike > 20) or (cat.relationships[alive_kit.ID].jealousy > 20) or (cat.relationships[alive_kit.ID].trust > 20) or (cat.relationships[alive_kit.ID].comfortable > 20) or (cat.relationships[alive_kit.ID].admiration > 20)))) or alive_kit.shunned == 0):
                    alive_kit = choice(alive_kits)
                    counter+=1
                    if counter == 30:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_k_{x}"] = alive_kit
                    text = re.sub(fr'(?<!\/){r}_rsh_k_{x}(?!\/)', str(alive_kit.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_k_{x}"] = alive_kit
                    text = re.sub(fr'(?<!\/)rsh_k_{x}(?!\/)', str(alive_kit.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_k"] = alive_kit
                    text = re.sub(fr'(?<!\/){r}_rsh_k(?!\/)', str(alive_kit.name), text)
                else:
                    self.cat_dict["rsh_k"] = alive_kit
                    text = re.sub(r'(?<!\/)rsh_k(?!\/)', str(alive_kit.name), text)
        if "rsh_a" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_a(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_a', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            alive_apps = get_alive_apps(Cat)
            if len(alive_apps) < 1:
                return ""
            if f"rsh_a_{x}" in self.cat_dict or "rsh_a" in self.cat_dict or f"{r}_rsh_a" in self.cat_dict or f"{r}_rsh_a_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_a_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_a_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_a_{x}(?!\/)', str(self.cat_dict[f"rsh_a_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_a_(?!\/)', str(self.cat_dict[f"{r}_rsh_a"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_a(?!\/)', str(self.cat_dict["rsh_a"].name), text)
            else:
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or alive_app.shunned == 0):
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_k_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_k_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_k_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)rsh_k_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_k"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_k(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["rsh_k"] = alive_app
                    text = re.sub(r'(?<!\/)rsh_k(?!\/)', str(alive_app.name), text)
        if "rsh_w" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_w(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_w', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            alive_apps = get_alive_warriors(Cat)
            if len(alive_apps) < 1:
                return ""
            if f"rsh_w_{x}" in self.cat_dict or "rsh_w" in self.cat_dict or f"{r}_rsh_w" in self.cat_dict or f"{r}_rsh_w_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_w_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_a_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_w_{x}(?!\/)', str(self.cat_dict[f"rsh_w_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_w_(?!\/)', str(self.cat_dict[f"{r}_rsh_w"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_w(?!\/)', str(self.cat_dict["rsh_w"].name), text)
            else:
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or alive_app.shunned == 0):
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_w_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_w_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_w_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)rsh_w_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_w"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_w(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["rsh_w"] = alive_app
                    text = re.sub(r'(?<!\/)rsh_w(?!\/)', str(alive_app.name), text)
        if "rsh_m" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_m(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_m', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            alive_apps = get_alive_meds(Cat)
            if len(alive_apps) < 1:
                return ""
            if f"rsh_a_{x}" in self.cat_dict or "rsh_m" in self.cat_dict or f"{r}_rsh_m" in self.cat_dict or f"{r}_rsh_m_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_m_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_m_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_m_{x}(?!\/)', str(self.cat_dict[f"rsh_m_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_m_(?!\/)', str(self.cat_dict[f"{r}_rsh_m"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_m(?!\/)', str(self.cat_dict["rsh_m"].name), text)
            else:
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or alive_app.shunned == 0):
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_m_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_m_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_m_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)rsh_m_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_m"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_m(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["rsh_m"] = alive_app
                    text = re.sub(r'(?<!\/)rsh_m(?!\/)', str(alive_app.name), text)
        if "rsh_d" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_d(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_d', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            alive_apps = get_alive_mediators(Cat)
            if len(alive_apps) < 1:
                return ""
            if f"rsh_d_{x}" in self.cat_dict or "rsh_d" in self.cat_dict or f"{r}_rsh_d" in self.cat_dict or f"{r}_rsh_d_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_d_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_d_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_d_{x}(?!\/)', str(self.cat_dict[f"rsh_d_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_d_(?!\/)', str(self.cat_dict[f"{r}_rsh_d"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_d(?!\/)', str(self.cat_dict["rsh_d"].name), text)
            else:
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or alive_app.shunned == 0):
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_d_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_d_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_d_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)rsh_d_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_d"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_d(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["rsh_d"] = alive_app
                    text = re.sub(r'(?<!\/)rsh_d(?!\/)', str(alive_app.name), text)
        if "rsh_q" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_q(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_q', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            alive_apps = get_alive_queens(Cat)
            if len(alive_apps) < 1:
                return ""
            if f"rsh_q_{x}" in self.cat_dict or "rsh_q" in self.cat_dict or f"{r}_rsh_q" in self.cat_dict or f"{r}_rsh_q_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_q_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_q_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_q_{x}(?!\/)', str(self.cat_dict[f"rsh_q_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_q_(?!\/)', str(self.cat_dict[f"{r}_rsh_q"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_q(?!\/)', str(self.cat_dict["rsh_q"].name), text)
            else:
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or alive_app.shunned == 0):
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_q_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_q_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_q_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)rsh_q_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_q"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_q(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["rsh_q"] = alive_app
                    text = re.sub(r'(?<!\/)rsh_q(?!\/)', str(alive_app.name), text)
        if "rsh_e" in text:
            cluster = False
            rel = False
            match = re.search(r'rsh_e(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)rsh_e', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            alive_apps = get_alive_elders(Cat)
            if len(alive_apps) < 1:
                return ""
            if f"rsh_e_{x}" in self.cat_dict or "rsh_e" in self.cat_dict or f"{r}_rsh_e" in self.cat_dict or f"{r}_rsh_e_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_rsh_e_{x}(?!\/)', str(self.cat_dict[f"{r}_rsh_e_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)rsh_e_{x}(?!\/)', str(self.cat_dict[f"rsh_e_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_rsh_e_(?!\/)', str(self.cat_dict[f"{r}_rsh_e"].name), text)
                else:
                    text = re.sub(r'(?<!\/)rsh_e(?!\/)', str(self.cat_dict["rsh_e"].name), text)
            else:
                alive_app = choice(alive_apps)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20)))) or alive_app.shunned == 0):
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                if cluster and rel:
                    self.cat_dict[f"{r}_rsh_e_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_e_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"rsh_e_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)rsh_e_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_rsh_e"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_rsh_e(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["rsh_e"] = alive_app
                    text = re.sub(r'(?<!\/)rsh_e(?!\/)', str(alive_app.name), text)
        if "sh_d" in text:
            cluster = False
            rel = False
            match = re.search(r'sh_d(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)sh_d', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            random_cat = choice(self.get_living_cats())
            counter = 0
            while (random_cat.ID == you.ID or random_cat.ID == cat.ID or (cluster and x not in get_cluster(random_cat.personality.trait)) or (rel and (random_cat.ID not in cat.relationships) or\
            (r == "plike" and cat.relationships[random_cat.ID].platonic_like < 20) or\
            (r == "plove" and cat.relationships[random_cat.ID].platonic_like < 50) or\
            (r == "rlike" and cat.relationships[random_cat.ID].romantic_love < 10) or\
            (r == "rlove" and cat.relationships[random_cat.ID].romantic_love < 50) or\
            (r == "dislike" and cat.relationships[random_cat.ID].dislike < 15) or\
            (r == "hate" and cat.relationships[random_cat.ID].dislike < 50) or\
            (r == "jealous" and cat.relationships[random_cat.ID].jeaousy < 20) or\
            (r == "trust" and cat.relationships[random_cat.ID].trust < 20) or\
            (r == "comfort" and cat.relationships[random_cat.ID].comfortable < 20) or \
            (r == "respect" and cat.relationships[random_cat.ID].admiration < 20) or\
            (r == "neutral" and ((cat.relationships[random_cat.ID].platonic_like > 20) or (cat.relationships[random_cat.ID].romantic_love > 20) or (cat.relationships[random_cat.ID].dislike > 20) or (cat.relationships[random_cat.ID].jealousy > 20) or (cat.relationships[random_cat.ID].trust > 20) or (cat.relationships[random_cat.ID].comfortable > 20) or (cat.relationships[random_cat.ID].admiration > 20)))) or random_cat.shunned == 0 or random_cat.status != "deputy"):
                if counter == 30:
                    return ""
                random_cat = choice(self.get_living_cats())
                counter +=1
            if cluster and rel:
                self.cat_dict[f"{r}_sh_d_{x}"] = random_cat
                text = re.sub(fr'(?<!\/){r}_sh_d_{x}(?!\/)', str(random_cat.name), text)
            elif cluster and not rel:
                self.cat_dict[f"sh_d_{x}"] = random_cat
                text = re.sub(fr'(?<!\/)sh_d_{x}(?!\/)', str(random_cat.name), text)
            elif rel and not cluster:
                self.cat_dict[f"{r}_sh_d"] = random_cat
                text = re.sub(fr'(?<!\/){r}_sh_d(?!\/)', str(random_cat.name), text)
            else:
                self.cat_dict["sh_d"] = random_cat
                text = re.sub(r'(?<!\/)sh_d(?!\/)', str(random_cat.name), text)
        if "sh_l" in text:
            cluster = False
            rel = False
            match = re.search(r'sh_l(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)sh_l', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            random_cat = choice(self.get_living_cats())
            counter = 0
            while (random_cat.ID == you.ID or random_cat.ID == cat.ID or (cluster and x not in get_cluster(random_cat.personality.trait)) or (rel and (random_cat.ID not in cat.relationships) or\
            (r == "plike" and cat.relationships[random_cat.ID].platonic_like < 20) or\
            (r == "plove" and cat.relationships[random_cat.ID].platonic_like < 50) or\
            (r == "rlike" and cat.relationships[random_cat.ID].romantic_love < 10) or\
            (r == "rlove" and cat.relationships[random_cat.ID].romantic_love < 50) or\
            (r == "dislike" and cat.relationships[random_cat.ID].dislike < 15) or\
            (r == "hate" and cat.relationships[random_cat.ID].dislike < 50) or\
            (r == "jealous" and cat.relationships[random_cat.ID].jeaousy < 20) or\
            (r == "trust" and cat.relationships[random_cat.ID].trust < 20) or\
            (r == "comfort" and cat.relationships[random_cat.ID].comfortable < 20) or \
            (r == "respect" and cat.relationships[random_cat.ID].admiration < 20) or\
            (r == "neutral" and ((cat.relationships[random_cat.ID].platonic_like > 20) or (cat.relationships[random_cat.ID].romantic_love > 20) or (cat.relationships[random_cat.ID].dislike > 20) or (cat.relationships[random_cat.ID].jealousy > 20) or (cat.relationships[random_cat.ID].trust > 20) or (cat.relationships[random_cat.ID].comfortable > 20) or (cat.relationships[random_cat.ID].admiration > 20)))) or random_cat.shunned == 0 or random_cat.status != "leader"):
                if counter == 30:
                    return ""
                random_cat = choice(self.get_living_cats())
                counter +=1
            if cluster and rel:
                self.cat_dict[f"{r}_sh_l_{x}"] = random_cat
                text = re.sub(fr'(?<!\/){r}_sh_l_{x}(?!\/)', str(random_cat.name), text)
            elif cluster and not rel:
                self.cat_dict[f"sh_l_{x}"] = random_cat
                text = re.sub(fr'(?<!\/)sh_l_{x}(?!\/)', str(random_cat.name), text)
            elif rel and not cluster:
                self.cat_dict[f"{r}_sh_l"] = random_cat
                text = re.sub(fr'(?<!\/){r}_sh_l(?!\/)', str(random_cat.name), text)
            else:
                self.cat_dict["sh_l"] = random_cat
                text = re.sub(r'(?<!\/)sh_l(?!\/)', str(random_cat.name), text)

        if "w_cClan" in text:
            if game.clan.war.get("at_war", False):
                return ""
            text = text.replace("w_c", str(game.clan.war["enemy"]))

        # random lost cat
        if "l_c" in text:
            cluster = False
            rel = False
            match = re.search(r'l_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)l_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"l_c_{x}" in self.cat_dict or "l_c" in self.cat_dict or f"{r}_l_c" in self.cat_dict or f"{r}_l_c_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_l_c_{x}(?!\/)', str(self.cat_dict[f"{r}_l_c_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)l_c_{x}(?!\/)', str(self.cat_dict[f"l_c_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_l_c_(?!\/)', str(self.cat_dict[f"{r}_l_c"].name), text)
                else:
                    text = re.sub(r'(?<!\/)l_c(?!\/)', str(self.cat_dict["l_c"].name), text)
            else:
                alive_outside_cats = [i for i in Cat.all_cats.values() if not i.dead and i.outside and not i.exiled]
                if len(alive_outside_cats) <= 0:
                    return ""
                alive_app = choice(alive_outside_cats)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or cat.status in ["rogue", "loner", "former Clancat", "kittypet"] or (cluster and x not in get_cluster(alive_app.personality.trait))\
                or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or (cat.relationships[alive_app.ID].romantic_love > 20) or (cat.relationships[alive_app.ID].dislike > 20) or (cat.relationships[alive_app.ID].jealousy > 20) or (cat.relationships[alive_app.ID].trust > 20) or (cat.relationships[alive_app.ID].comfortable > 20) or (cat.relationships[alive_app.ID].admiration > 20))))):
                    alive_app = choice(alive_outside_cats)
                    counter += 1
                    if counter == 30:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_l_c_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_l_c_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"l_c_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)l_c_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_l_c"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_l_c(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["l_c"] = alive_app
                    text = re.sub(r'(?<!\/)l_c(?!\/)', str(alive_app.name), text)

        # random exiled cat
        if "e_c" in text:
            cluster = False
            rel = False
            match = re.search(r'e_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)e_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            if f"e_c_{x}" in self.cat_dict or "e_c" in self.cat_dict or f"{r}_e_c" in self.cat_dict or f"{r}_e_c_{x}" in self.cat_dict:
                if cluster and rel:
                    text = re.sub(fr'(?<!\/){r}_e_c_{x}(?!\/)', str(self.cat_dict[f"{r}_e_c_{x}"].name), text)
                elif cluster and not rel:
                    text = re.sub(fr'(?<!\/)e_c_{x}(?!\/)', str(self.cat_dict[f"e_c_{x}"].name), text)
                elif rel and not cluster:
                    text = re.sub(fr'(?<!\/){r}_e_c_(?!\/)', str(self.cat_dict[f"{r}_e_c"].name), text)
                else:
                    text = re.sub(r'(?<!\/)e_c(?!\/)', str(self.cat_dict["e_c"].name), text)
            else:
                alive_outside_cats = [i for i in Cat.all_cats.values() if not i.dead and i.outside and i.exiled]
                if len(alive_outside_cats) <= 0:
                    return ""
                alive_app = choice(alive_outside_cats)
                counter = 0
                while (alive_app.ID == you.ID or alive_app.ID == cat.ID or (cluster and x not in get_cluster(alive_app.personality.trait)) or (rel and (alive_app.ID not in cat.relationships) or\
                (r == "plike" and cat.relationships[alive_app.ID].platonic_like < 20) or\
                (r == "plove" and cat.relationships[alive_app.ID].platonic_like < 50) or\
                (r == "rlike" and cat.relationships[alive_app.ID].romantic_love < 10) or\
                (r == "rlove" and cat.relationships[alive_app.ID].romantic_love < 50) or\
                (r == "dislike" and cat.relationships[alive_app.ID].dislike < 15) or\
                (r == "hate" and cat.relationships[alive_app.ID].dislike < 50) or\
                (r == "jealous" and cat.relationships[alive_app.ID].jeaousy < 20) or\
                (r == "trust" and cat.relationships[alive_app.ID].trust < 20) or\
                (r == "comfort" and cat.relationships[alive_app.ID].comfortable < 20) or \
                (r == "respect" and cat.relationships[alive_app.ID].admiration < 20) or\
                (r == "neutral" and ((cat.relationships[alive_app.ID].platonic_like > 20) or\
                (cat.relationships[alive_app.ID].romantic_love > 20) or \
                (cat.relationships[alive_app.ID].dislike > 20) or\
                (cat.relationships[alive_app.ID].jealousy > 20) or\
                (cat.relationships[alive_app.ID].trust > 20) or \
                (cat.relationships[alive_app.ID].comfortable > 20) or\
                (cat.relationships[alive_app.ID].admiration > 20))))):
                    alive_app = choice(alive_outside_cats)
                    counter += 1
                    if counter == 30:
                        return ""
                if cluster and rel:
                    self.cat_dict[f"{r}_e_c_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_e_c_{x}(?!\/)', str(alive_app.name), text)
                elif cluster and not rel:
                    self.cat_dict[f"e_c_{x}"] = alive_app
                    text = re.sub(fr'(?<!\/)e_c_{x}(?!\/)', str(alive_app.name), text)
                elif rel and not cluster:
                    self.cat_dict[f"{r}_e_c"] = alive_app
                    text = re.sub(fr'(?<!\/){r}_e_c(?!\/)', str(alive_app.name), text)
                else:
                    self.cat_dict["e_c"] = alive_app
                    text = re.sub(r'(?<!\/)e_c(?!\/)', str(alive_app.name), text)

        return text

    def backstory_text(self, cat):
        with open(f"resources/dicts/backstories.json", 'r') as read_file:
            BACKSTORIES = ujson.loads(read_file.read())

        backstory = cat.backstory
        if backstory is None:
            return ''
        bs_category = None

        for category in BACKSTORIES["backstory_categories"]:
            if backstory in BACKSTORIES["backstory_categories"][category]:
                bs_category = category
                break
        if bs_category is not None:
            bs_display = BACKSTORIES["backstory_display"][bs_category]
        else:
            bs_display = None
            print("ERROR: Backstory category was not found.")
        if not bs_display:
            return "clanfounder"
        return bs_display