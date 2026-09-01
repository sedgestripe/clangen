import json
import copy
import re


file_names = [
    "apprentice",
    "deputy",
    "elder",
    "exiled",
    "former Clancat",
    "general_no_kit",
    "general",
    "kitten",
    "kittypet",
    "leader",
    "loner",
    "mediator apprentice",
    "mediator",
    "medicine cat apprentice",
    "medicine cat",
    "queen",
    "queen's apprentice",
    "rogue",
    "warrior",
    "young elder",
]
# TODO: aauugh
file_path_convert = {
    "apprentice": {"file": "adolescent", "rank": ["apprentice"]},
    "deputy": {"file": "adult", "rank": ["deputy"]},
    "elder": {"file": "adult", "rank": ["elder"]},
    "exiled": {"file": "general", "standing": ["exiled"]},
    "former Clancat": {"file": "general", "standing": ["lost"]},
    "general_no_kit": {"file": "general_no_kit", "age": ["not_kitten"]},
    "general": {"file": "general"},
    "kitten": {"file": "kitten", "rank": ["kitten"]},
    "kittypet": {"file": "general", "rank": ["kittypet"]},
    "leader": {"file": "adult", "rank": ["leader"]},
    "loner": {"file": "general", "rank": ["loner"]},
    "mediator apprentice": {"file": "adolescent", "rank": ["mediator apprentice"]},
    "mediator": {"file": "adult", "rank": ["mediator"]},
    "medicine cat apprentice": {
        "file": "adolescent",
        "rank": ["medicine cat apprentice"],
    },
    "medicine cat": {"file": "adult", "rank": ["medicine cat"]},
    "queen": {"file": "adult", "rank": ["queen"]},
    "queen's apprentice": {"file": "adolescent", "rank": ["queen's apprentice"]},
    "rogue": {"file": "general", "rank": ["rogue"]},
    "warrior": {"file": "adult", "rank": ["warrior"]},
    "young elder": {"file": "general", "rank": ["elder"], "age": ["not_senior"]},
}


folder_names = ["events", "events_dead_df", "events_dead_sc", "events_dead_ur"]

clusters = [
    "assertive",
    "stable",
    "unlawful",
    "cool",
    "brooding",
    "sweet",
    "introspective",
    "unabashed",
    "upstanding",
    "neurotic",
    "silly",
]
with open(
    "scripts/events_module/dialogue/reformat_resources/abbrev_convert.json", "r"
) as read_file:
    abbrev_convert = json.loads(read_file.read())

with open(
    "scripts/events_module/dialogue/reformat_resources/all_resources.json", "r"
) as read_file:
    resources = json.loads(read_file.read())

# assign variables from resources
cluster_addons = resources["cluster_addons"]
skill_addons = resources["skill_addons"]


def get_matches(abbrev, text):
    match = re.search(rf"(?:([A-Za-z]+)-)?{re.escape(abbrev)}(?:-([A-Za-z]+))?", text)
    full_abbrev = match.group(0)
    rel_addon = match.group(1)
    cluster_addon = match.group(2)

    return full_abbrev, rel_addon, cluster_addon


for folder in folder_names:
    for status in file_names:
        old_events = {}
        new_events = {}
        try:
            with open(
                f"resources/lang/en/events/lifegen_events/{folder}/{status}.json", "r"
            ) as read_file:
                old_events = json.loads(read_file.read())
        except FileNotFoundError:
            continue

        event_count = 0
        done_events = []
        for key, event_list in old_events.items():
            for event_string in event_list:
                if event_string in done_events:
                    continue
                TYPES = []
                cluster_found = False
                cats_block = {}
                rel_block = []
                for cluster in clusters:
                    if cluster in key:
                        cluster_found = True
                        cats_block["y_c"] = {"cluster": [cluster]}
                if key == "df":
                    TYPES.append("df")
                elif "shunned" in key:
                    TYPES.append("shunned")
                elif "rare" in key:
                    TYPES.append("rare")
                elif key == "affair":
                    TYPES.append("affair")
                else:
                    TYPES.append("general")

                if not cluster_found:
                    cats_block["y_c"] = {}
                event_count += 1

                random_cat_count = 0
                check = copy.deepcopy(abbrev_convert)
                for abbrev, abbrev_info in check.items():
                    if abbrev in event_string:
                        full_abbrev, rel, cluster = get_matches(abbrev, event_string)
                        # get new r_c abbrev
                        new_abbrev = f"r_c:{random_cat_count}"
                        random_cat_count += 1
                        event_string = event_string.replace(full_abbrev, new_abbrev)

                        rel_list = []
                        cluster_list = []
                        skill_list = []

                        if rel:
                            rel_dict = {
                                "dislike": "max_like_-15",
                                "plike": "min_like_20",
                                "plove": "min_like_50",
                                "rlike": "min_romance_20",
                                "rlove": "min_romance_50",
                                "trust": "min_trust_20",
                                "jealous": "max_respect_-10",
                                "jealousy": "max_respect_-10",
                                "comfort": "min_comfort_15",
                            }
                            if rel in rel_dict:
                                rel_list.append(rel_dict[rel])
                        if cluster:
                            if cluster in cluster_addons:
                                cluster_list.append(cluster)
                            elif cluster in skill_addons:
                                skill_list.append(cluster)

                        if "relationship" in abbrev_info.copy():
                            for item in abbrev_info["relationship"].copy():
                                if abbrev in abbrev_info["relationship"]["cats_to"]:
                                    abbrev_info["relationship"]["cats_to"].remove(
                                        abbrev
                                    )
                                    abbrev_info["relationship"]["cats_to"].append(
                                        new_abbrev
                                    )
                                if abbrev in abbrev_info["relationship"]["cats_from"]:
                                    abbrev_info["relationship"]["cats_from"].remove(
                                        abbrev
                                    )
                                    abbrev_info["relationship"]["cats_from"].append(
                                        new_abbrev
                                    )

                            rel_block.append(abbrev_info["relationship"])
                            abbrev_info.pop("relationship")
                        cats_block[new_abbrev] = abbrev_info

                        if cluster_list:
                            cats_block[new_abbrev]["cluster"] = cluster_list
                        if skill_list:
                            cats_block[new_abbrev]["skill"] = skill_list
                        if rel_list:
                            print("Rel list present for", full_abbrev)
                            found = False
                            for item in rel_block:
                                if (
                                    new_abbrev in item["cats_to"]
                                    and "y_c" in item["cats_from"]
                                ):
                                    found = True
                                    item["relationship"].extend(rel_list)
                            if not found:
                                rel_block.append(
                                    {
                                        "cats_from": ["y_c"],
                                        "cats_to": [new_abbrev],
                                        "relationship": rel_list,
                                    }
                                )

                # get key and block for final writing
                new_event_key = key.split(" ")[0] + str(event_count)
                new_event_block = {
                    "cats": cats_block,
                    "relationships": rel_block,
                    "types": TYPES,
                    "event": event_string,
                }
                new_events[new_event_key] = new_event_block
                done_events.append(event_string)

        with open(
            f"resources/lang/en/events/lifegen_events/NEW/{folder}/{status}.json", "w"
        ) as json_file:
            json.dump(new_events, json_file, indent=4, separators=(",", ": "))
