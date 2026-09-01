import os
import ujson

their_trait_list = [
    "adventurous",
    "aloof",
    "ambitious",
    "arrogant",
    "bloodthirsty",
    "bold",
    "bouncy",
    "calm",
    "careful",
    "confident",
    "competitive",
    "cold",
    "charismatic",
    "cunning",
    "cowardly",
    "childish",
    "compassionate",
    "emotional",
    "energetic",
    "fierce",
    "flexible",
    "faithful",
    "flamboyant",
    "grumpy",
    "gloomy",
    "humble",
    "insecure",
    "justified",
    "loyal",
    "lonesome",
    "loving",
    "meek",
    "mellow",
    "methodical",
    "nervous",
    "oblivious",
    "obsessive",
    "playful",
    "reserved",
    "righteous",
    "responsible",
    "rebellious",
    "strict",
    "stoic",
    "sneaky",
    "strange",
    "sincere",
    "shameless",
    "spontaneous",
    "thoughtful",
    "troublesome",
    "trusting",
    "vengeful",
    "witty",
    "wise",
    "impulsive",
    "bullying",
    "attention-seeker",
    "charming",
    "daring",
    "noisy",
    "daydreamer",
    "sweet",
    "polite",
    "know-it-all",
    "bossy",
    "disciplined",
    "patient",
    "manipulative",
    "secretive",
    "rebellious",
    "passionate",
    "honest",
    "leader-like",
    "smug",
    "unruly",
    "shy",
    "self-conscious",
    "skittish",
    "fearless",
]
you_trait_list = [
    "you_adventurous",
    "you_aloof",
    "you_ambitious",
    "you_arrogant",
    "you_bloodthirsty",
    "you_bold",
    "you_bouncy",
    "you_calm",
    "you_careful",
    "you_confident",
    "you_competitive",
    "you_cold",
    "you_charismatic",
    "you_cunning",
    "you_cowardly",
    "you_childish",
    "you_compassionate",
    "you_emotional",
    "you_energetic",
    "you_fierce",
    "you_flexible",
    "you_faithful",
    "you_flamboyant",
    "you_grumpy",
    "you_gloomy",
    "you_humble",
    "you_insecure",
    "you_justified",
    "you_loyal",
    "you_lonesome",
    "you_loving",
    "you_meek",
    "you_mellow",
    "you_methodical",
    "you_nervous",
    "you_oblivious",
    "you_obsessive",
    "you_playful",
    "you_reserved",
    "you_righteous",
    "you_responsible",
    "you_rebellious",
    "you_strict",
    "you_stoic",
    "you_sneaky",
    "you_strange",
    "you_sincere",
    "you_shameless",
    "you_spontaneous",
    "you_thoughtful",
    "you_troublesome",
    "you_trusting",
    "you_vengeful",
    "you_witty",
    "you_wise",
    "you_impulsive",
    "you_bullying",
    "you_attention-seeker",
    "you_charming",
    "you_daring",
    "you_noisy",
    "you_daydreamer",
    "you_sweet",
    "you_polite",
    "you_know-it-all",
    "you_bossy",
    "you_disciplined",
    "you_patient",
    "you_manipulative",
    "you_secretive",
    "you_rebellious",
    "you_passionate",
    "you_honest",
    "you_leader-like",
    "you_smug",
    "you_unruly",
    "you_shy",
    "you_self-conscious",
    "you_skittish",
    "you_fearless",
]
you_backstory_list = [
    "you_clanfounder",
    "you_clanborn",
    "you_outsiderroots",
    "you_half-Clan",
    "you_formerlyaloner",
    "you_formerlyarogue",
    "you_formerlyakittypet",
    "you_formerlyaoutsider",
    "you_originallyfromanotherclan",
    "you_orphaned",
    "you_abandoned",
]
they_backstory_list = [
    "they_clanfounder",
    "they_clanborn",
    "they_outsiderroots",
    "they_half-Clan",
    "they_formerlyaloner",
    "they_formerlyarogue",
    "they_formerlyakittypet",
    "they_formerlyaoutsider",
    "they_originallyfromanotherclan",
    "they_orphaned",
    "they_abandoned",
]
skill_list = [
    "teacher",
    "hunter",
    "fighter",
    "runner",
    "climber",
    "swimmer",
    "speaker",
    "mediator",
    "clever",
    "insightful",
    "sense",
    "kit",
    "story",
    "lore",
    "camp",
    "healer",
    "star",
    "omen",
    "dream",
    "clairvoyant",
    "prophet",
    "ghost",
    "explorer",
    "tracker",
    "artistan",
    "guardian",
    "tunneler",
    "navigator",
    "song",
    "grace",
    "clean",
    "innovator",
    "comforter",
    "matchmaker",
    "thinker",
    "cooperative",
    "scholar",
    "time",
    "treasure",
    "fisher",
    "language",
    "sleeper",
]
you_skill_list = [
    "you_teacher",
    "you_hunter",
    "you_fighter",
    "you_runner",
    "you_climber",
    "you_swimmer",
    "you_speaker",
    "you_mediator",
    "you_clever",
    "you_insightful",
    "you_sense",
    "you_kit",
    "you_story",
    "you_lore",
    "you_camp",
    "you_healer",
    "you_star",
    "you_omen",
    "you_dream",
    "you_clairvoyant",
    "you_prophet",
    "you_ghost",
    "you_explorer",
    "you_tracker",
    "you_artistan",
    "you_guardian",
    "you_tunneler",
    "you_navigator",
    "you_song",
    "you_grace",
    "you_clean",
    "you_innovator",
    "you_comforter",
    "you_matchmaker",
    "you_thinker",
    "you_cooperative",
    "you_scholar",
    "you_time",
    "you_treasure",
    "you_fisher",
    "you_language",
    "you_sleeper",
]
roles = [
    "Any",
    "any",
    "young elder",
    "newborn",
    "kitten",
    "apprentice",
    "medicine cat apprentice",
    "mediator apprentice",
    "no_kit",
    "queen's apprentice",
    "warrior",
    "medicine cat",
    "mediator",
    "queen",
    "deputy",
    "leader",
    "elder",
    "you_any",
    "you_kitten",
]
cluster_list = [
    "assertive",
    "brooding",
    "cool",
    "upstanding",
    "introspective",
    "neurotic",
    "silly",
    "stable",
    "sweet",
    "unabashed",
    "unlawful",
]
you_cluster_list = [
    "you_assertive",
    "you_brooding",
    "you_cool",
    "you_upstanding",
    "you_introspective",
    "you_neurotic",
    "you_silly",
    "you_stable",
    "you_sweet",
    "you_unabashed",
    "you_unlawful",
]


def process_json_data(data):
    list_of_tags = [
        "both_shunned",
        "you_df",
        "they_blind",
        "non-mates",
        "they_kitten",
        "they_starving",
        "they_grieving",
        "they_sc",
        "littermate",
        "mate",
        "from_your_kit",
        "they_half-clan",
        "you_half-clan",
        "platonic_love",
        "has_mate",
        "reject",
        "accept",
        "heartbroken",
        "from_parent",
        "siblings_mate",
        "non-related",
        "murder",
        "war",
        "dead_close",
        "talk_dead",
        "hate",
        "romantic_like",
        "platonic_like",
        "jealousy",
        "dislike",
        "comfort",
        "respect",
        "trust",
        "neutral",
        "insult",
        "flirt",
        "leafbare",
        "newleaf",
        "greenleaf",
        "leaffall",
        "beach",
        "forest",
        "plains",
        "mountainous",
        "wetlands",
        "desert",
        "you_ill",
        "you_injured",
        "they_ill",
        "you_grieving",
        "they_injured",
        "they_grieving",
        "adopted_parent",
        "from_mentor",
        "from_your_apprentice",
        "from_kit",
        "from_mate",
        "from_adopted_kit",
        "from_kit",
        "sibling",
        "half_sibling",
        "adopted_sibling",
        "parents_siblings",
        "cousin",
        "you_pregnant",
        "they_pregnant",
        "you_dftrainee",
        "grievingthem",
        "they_adult",
        "they_younger",
        "you_warrior",
        "they_outside",
        "they_elder",
        "only_you_deaf",
        "they_df",
        "they_ur",
        "they_sc",
        "you_df",
        "you_ur",
        "you_sc",
        "they_medicine_cat",
        "from_adopted_parent",
        "only_they_blind",
        "clan_has_kits",
        "murderedthem",
        "from_df_apprentice",
        "from_df_mentor",
        "they_dftrainee",
        "you_blind",
        "they_loner",
        "they_rogue",
        "you_apprentice",
        "they_medicine_cat_apprentice",
        "they_warrior",
        "only_you_blind",
        "you_apprentice",
        "grievingyou",
        "they_apprentice",
    ]
    list_of_tags.extend(
        cluster_list
        + you_cluster_list
        + roles
        + their_trait_list
        + you_trait_list
        + you_backstory_list
        + they_backstory_list
        + skill_list
        + you_skill_list
    )
    no_tags = set()
    for key, value in data.items():
        l = value[0]
        for i in range(len(l)):
            l[i] = l[i].lower()
        for i in l:
            if i not in list_of_tags:
                no_tags.add(i)

    return no_tags


def find_no_roles(data):
    for key, value in data.items():
        l = None
        try:
            l = value[0]
            for i in range(len(l)):
                l[i] = l[i].lower()
            if not any(a in l for a in roles) and not any(
                "you_" + a in l for a in roles
            ):
                print(key)
            if len(value[0]) == 1:
                print(key)
        except:
            print(f"error with {key}")


def read_json_files_in_folder(folder_path):
    nono_tags = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(".json") and filename != "choice_dialogue.json":
            with open(os.path.join(folder_path, filename), "r") as json_file:
                try:
                    data = ujson.load(json_file)
                    find_no_roles(data)
                    nono_tags.update(process_json_data(data))
                except ValueError:
                    print(f"Error reading JSON data from {filename}")
    print(nono_tags)


if __name__ == "__main__":
    folder_path = "resources\dicts\lifegen_talk"
    read_json_files_in_folder(folder_path)

# cluster_list = ["assertive", "brooding", "cool", "upstanding", "introspective", "neurotic", "silly", "stable", "sweet", "unabashed", "unlawful"]

# cluster_dict = {}
# for i in cluster_list:
#     cluster_dict[i] = 0

# def count_dialogue(f, data):
#     newborn_count = 0
#     for key, value in data.items():
#         l = value["tags"] if "tags" in value else value[0]
#         if "newborn" in l:
#             newborn_count += 1
#             for d in cluster_list:
#                 if d in l:
#                     cluster_dict[d]+=1
#     print(f"{f} contains {newborn_count} newborn dialogues")
#     return newborn_count

# def read_json_files_in_folder(folder_path):

#     print("They are role newborn: dialogue data")
#     total_newborn_count = 0
#     for filename in os.listdir(folder_path):
#         if filename.endswith('.json'):
#             with open(os.path.join(folder_path, filename), 'r') as json_file:
#                 try:
#                         data = ujson.load(json_file)
#                         total_newborn_count += count_dialogue(filename, data)
#                 except ValueError:
#                     print(f"Error reading JSON data from {filename}")
#     print(f"Total dialogues: {total_newborn_count}")
#     print(cluster_dict)

# if __name__ == "__main__":
#     folder_path = "resources\dicts\lifegen_talk"
#     read_json_files_in_folder(folder_path)

# import os
# import ujson
# import json

# def handle_duplicate_keys(pairs):
#     """
#     Rename duplicate keys by appending a number.
#     """
#     seen = {}
#     result = {}

#     for key, value in pairs:
#         while key in seen:
#             seen[key] += 1
#             key = f"{key}_{seen[key]}"
#         else:
#             seen[key] = 1

#         result[key] = value

#     return result

# def process_json_file(filepath):
#     with open(filepath, 'r') as json_file:
#         data_str = json_file.read()

#     # Load JSON with duplicate key handling
#     data = json.loads(data_str, object_pairs_hook=handle_duplicate_keys)

#     with open(filepath, 'w') as json_file:
#         ujson.dump(data, json_file, indent=4)

# def read_json_files_in_folder(folder_path):
#     for filename in os.listdir(folder_path):
#         if filename.endswith('.json'):
#             process_json_file(os.path.join(folder_path, filename))

# if __name__ == "__main__":
#     folder_path = "resources\dicts\lifegen_talk"
#     read_json_files_in_folder(folder_path)
