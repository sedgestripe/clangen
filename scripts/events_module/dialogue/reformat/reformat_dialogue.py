import json
import re
import copy

# SCRIPT FOR REFORMATTING LIFEGEN DIALOGUE
# swaps lifegen abbrevs out for r_c:{index} abbrevs
# this will NOT work on dialogue that has already been reformatted. it will goof it up.
# Simply run this file in the top right to reformat dialogue

DEBUG_KEY = "about_parent4"


def load_json(path):
    with open(path, "r") as read_file:
        return json.loads(read_file.read())


def get_matches(abbrev, text):
    match = re.search(rf"(?:([A-Za-z]+)-)?{re.escape(abbrev)}(?:-([A-Za-z]+))?", text)
    full_abbrev = match.group(0)
    rel_addon = match.group(1)
    cluster_addon = match.group(2)

    return full_abbrev, rel_addon, cluster_addon


def debug_print(key, text):
    if DEBUG_KEY == key:
        print(text)


# LOAD RESOURCES
abbrev_convert = load_json(
    "scripts/events_module/dialogue/reformat_resources/abbrev_convert.json"
)
resources = load_json(
    "scripts/events_module/dialogue/reformat_resources/all_resources.json"
)

# assign variables from resources
cluster_addons = resources["cluster_addons"]
skill_addons = resources["skill_addons"]
rel_addons = resources["rel_addons"]
rel_addon_convert = resources["rel_addon_convert"]

rel_tag_convert = resources["rel_tags"]
murder_tag_convert = resources["murder_tag_convert"]

file_names = resources["file_names"]
abbrev_list = resources["abbrev_list"]

taken_keys = {}
# iterate through every file

# open the old file
dialogue_json = load_json("scripts/events_module/dialogue/reformat/old_dialogue.json")

# create the new dialogue dict. edited dialogue items will be added here
new_dialogue_dict = {}

for dkey, dialogue_block in dialogue_json.items():
    if dkey not in taken_keys:
        taken_keys.update({dkey: 1})
        dialogue_key = dkey
    else:
        taken_keys[dkey] += 1
        dialogue_key = dkey + "_" + str(taken_keys[dkey])
    # abbrev list
    # e.g "plike-r_c", "y_k-brooding"
    RANDOM_CATS = []

    # "full_abbrev": "new_r_c_abbrev"
    # e.g "plike-r_c": "r_c:0"
    # currently not actually being used? will keep for now
    RANDOM_CATS_DICT = {}

    # dialogue dict
    # e.g "y_c": {}, "t_c": {}, "r_c:0": {}
    CAT_DICT = {}

    SEASON = []
    BIOME = []
    CAMP = []
    FREQUENCY = 2
    TAGS = []
    RELATIONSHIPS = []
    MURDER = {}

    # scenes. key:dialogue
    # e.g "intro": []
    SCENES = {}

    abbrevs_done = []

    for key, block in dialogue_block.items():
        # get the stuff that doesnt need to be delved into out of the way
        if key in ["y_c", "t_c"]:
            CAT_DICT[key] = dialogue_block[key]

        elif key == "season":
            season_convert = {
                "new-leaf": "newleaf",
                "leaffall": "leaf-fall",
                "leafbare": "leaf-bare",
                "green-leaf": "greenleaf",
            }
            for season in dialogue_block[key]:
                check = season.lower()
                if check in season_convert:
                    SEASON.append(season_convert[check])
                else:
                    SEASON.append(check)

        if key == "biome":
            BIOME = dialogue_block[key]

        if key == "camp":
            CAMP = dialogue_block[key]

        elif key == "season":
            new_season = []
            for season in dialogue_block[key]:
                season = season.lower()
                convert_dict = {
                    "new-leaf": "newleaf",
                    "green-leaf": "greenleaf",
                    "leaffall": "leaf-fall",
                    "leafbare": "leaf-bare",
                }
                if season in convert_dict:
                    new_season.append(convert_dict[season])
                else:
                    new_season.append(season)
            SEASON = new_season

        elif key == "tags":
            murder_tags = []
            new_murder_dict = {
                "victim": {"cat": "", "success": None},
                "accomplice": {"cat": "", "success": None},
                "discovered": None,
            }
            for tag in dialogue_block[key]:
                if tag in murder_tag_convert:
                    murder_tags.append(tag)
                    convert = murder_tag_convert[tag]
                    for item in convert:
                        # item == "accomplice" or "victim"
                        if isinstance(convert[item], dict):
                            for item2 in convert[item]:
                                # item2 = "cats" or "success" or "discovered"
                                new_murder_dict[item][item2] = convert[item][item2]
                        else:
                            new_murder_dict[item] = convert[item]
                else:
                    if tag == "reject":
                        TAGS.append("reject")

            for new_item in new_murder_dict.copy():
                if isinstance(new_murder_dict[new_item], dict):
                    for subitem in new_murder_dict[new_item].copy():
                        if not new_murder_dict[new_item][subitem]:
                            new_murder_dict[new_item].pop(subitem)
                else:
                    if not new_murder_dict[new_item]:
                        new_murder_dict.pop(new_item)

            for item in new_murder_dict.copy():
                if not new_murder_dict[item]:
                    new_murder_dict.pop(item)

            # if murder_tags:
            #     print(dialogue_key, "MURDER CONVERT")
            #     print(murder_tags)
            #     print("CHANGED TO")
            #     print(new_murder_dict)
            #     print()
            MURDER = new_murder_dict

        # rel tags
        elif key == "relationship":
            for tag in dialogue_block[key]:
                # min and max relationship tags are being added to t_c and y_c dict in RELATIONSHIPS
                # it creates a new one if it cant find it
                located = False
                if ("min_" in tag) or ("max" in tag):
                    if "platonic" in tag:
                        new_tag = tag.replace("platonic", "like")
                    elif "romantic" in tag:
                        new_tag = tag.replace("romantic", "romance")
                    else:
                        new_tag = tag
                elif tag in rel_tag_convert:
                    new_tag = rel_tag_convert[tag]
                else:
                    print("Unknown rel tag:", tag)
                    new_tag = tag
                for rel in RELATIONSHIPS:
                    if "y_c" in rel["cats_to"] and "t_c" in rel["cats_from"]:
                        located = True
                        rel["relationship"].append(new_tag)
                if not located:
                    RELATIONSHIPS.append(
                        {
                            "cats_from": ["t_c"],
                            "cats_to": ["y_c"],
                            "relationship": [new_tag],
                        }
                    )

        # RANDOM ABBREVS
        # if its a scene
        elif isinstance(block, list):
            SCENES[key] = []
            for line in block:
                # check every dialogue line
                for lone_abbrev in abbrev_list:
                    # check every possible abbrev
                    new_cat_info = {}
                    if lone_abbrev in line:
                        abbrevs_done.append(lone_abbrev)
                        # if the abbrev is found, check if it has any addons
                        full_abbrev, rel_addon, cluster_addon = get_matches(
                            lone_abbrev, line
                        )

                        if lone_abbrev == "r_c" and "r_c1" in abbrevs_done:
                            continue
                        if lone_abbrev == "r_w" and "r_w1" in abbrevs_done:
                            continue

                        if full_abbrev not in RANDOM_CATS:
                            RANDOM_CATS.append(full_abbrev)

                        random_cat_index = RANDOM_CATS.index(full_abbrev)
                        random_cat_abbrev = f"r_c:{random_cat_index}"
                        RANDOM_CATS_DICT[full_abbrev] = random_cat_abbrev

                        # grab the conversion from the json
                        new_cat_info = copy.deepcopy(abbrev_convert[lone_abbrev])
                        # debug_print(
                        #     dialogue_key,
                        #     f"{random_cat_abbrev} NEW INFO FOR {dialogue_key} {lone_abbrev}: {new_cat_info}"
                        #     )

                        line = line.replace(full_abbrev, random_cat_abbrev)

                        # now change the abbrevs in convert relationship to be the r_c ones
                        if "relationship" in new_cat_info:
                            if lone_abbrev in new_cat_info["relationship"]["cats_from"]:
                                new_cat_info["relationship"]["cats_from"].remove(
                                    lone_abbrev
                                )
                                new_cat_info["relationship"]["cats_from"].append(
                                    random_cat_abbrev
                                )
                            if lone_abbrev in new_cat_info["relationship"]["cats_to"]:
                                new_cat_info["relationship"]["cats_to"].remove(
                                    lone_abbrev
                                )
                                new_cat_info["relationship"]["cats_to"].append(
                                    random_cat_abbrev
                                )

                        if "murder" in new_cat_info:
                            MURDER["victim"] = random_cat_abbrev
                            new_cat_info.pop("murder")

                        # now add the addon information where it needs to go
                        # REL
                        if rel_addon:
                            if "relationship" in new_cat_info:
                                if "relationship" in new_cat_info["relationship"]:
                                    if (
                                        rel_addon_convert[rel_addon]
                                        not in new_cat_info["relationship"][
                                            "relationship"
                                        ]
                                    ):
                                        new_cat_info["relationship"][
                                            "relationship"
                                        ].append(rel_addon_convert[rel_addon])
                                else:
                                    new_cat_info["relationship"]["relationship"] = [
                                        rel_addon_convert[rel_addon]
                                    ]
                            else:
                                new_cat_info["relationship"] = {
                                    "cats_from": ["t_c"],
                                    "cats_to": [random_cat_abbrev],
                                    "relationship": [rel_addon_convert[rel_addon]],
                                }

                        # CLUSTER
                        if cluster_addon:
                            if cluster_addon in cluster_addons:
                                if "cluster" in new_cat_info:
                                    if cluster_addon not in new_cat_info["cluster"]:
                                        new_cat_info["cluster"].append(cluster_addon)
                                else:
                                    new_cat_info["cluster"] = [cluster_addon]
                            elif cluster_addon in skill_addons:
                                if "skill" in new_cat_info:
                                    if cluster_addon not in new_cat_info["skill"]:
                                        new_cat_info["skill"].append(
                                            f"{cluster_addon.upper()},1"
                                        )
                                else:
                                    new_cat_info["skill"] = [
                                        f"{cluster_addon.upper()},1"
                                    ]

                        CAT_DICT[random_cat_abbrev] = new_cat_info

                # append the edited line
                SCENES[key].append(line)

            # correct relationships
            for cat, block in CAT_DICT.items():
                if "relationship" in block:
                    RELATIONSHIPS.append(block["relationship"])
                    block.pop("relationship")

        elif isinstance(block, dict) and "_choices" in key:
            # this one is a selection of choices
            # this replaces abbrevs in text selections, but not scene names
            # bc. the player wont see that anyway
            SCENES[key] = block
            for choice_key, choice_block in block.items():
                line = choice_block["text"]
                for lone_abbrev in abbrev_list:
                    if lone_abbrev in line:
                        full_abbrev, rel_addon, cluster_addon = get_matches(
                            lone_abbrev, line
                        )

                        if full_abbrev not in RANDOM_CATS:
                            RANDOM_CATS.append(full_abbrev)
                        random_cat_index = RANDOM_CATS.index(full_abbrev)
                        random_cat_abbrev = f"r_c:{random_cat_index}"
                        # print("RC INDEX:", random_cat_index)
                        RANDOM_CATS_DICT[full_abbrev] = random_cat_abbrev

                        line = line.replace(full_abbrev, random_cat_abbrev)
                SCENES[key][choice_key]["text"] = line
        elif isinstance(block, dict) and "_scene_effects" in key:
            # TODO: rel effects convert
            SCENES[key] = block

    new_block = {}
    # now assign everything to the new block!
    if BIOME:
        new_block["biome"] = BIOME
    if CAMP:
        new_block["camp"] = CAMP
    if SEASON:
        new_block["season"] = SEASON
    if FREQUENCY:
        new_block["frequency"] = FREQUENCY

    for key, item in CAT_DICT.items():
        if "cats" not in new_block:
            new_block["cats"] = {}
        if item:
            for constraint in item.copy():
                if constraint == "shunned":
                    # not sure if i want this or if i should keep the shunned bool
                    # come back to it
                    if item["shunned"] == "any":
                        item["standing"] = ["member", "shunned"]
                    elif item["shunned"] is True:
                        item["standing"] = ["shunned"]
                    item.pop("shunned")
                if constraint == "forgiven":
                    # not sure if i want this or if i should keep the shunned bool
                    # come back to it
                    if item["forgiven"] == "any":
                        item["forgiven"] = ["member", "forgiven"]
                    elif item["forgiven"] is True:
                        item["standing"] = ["forgiven"]
                    item.pop("forgiven")

                # status -> rank
                if constraint == "status":
                    item["rank"] = item[constraint]
                    item.pop(constraint)
                # dead moons
                if constraint == "dead":
                    for tag in item["dead"]:
                        min_moons = None
                        max_moons = None
                        found = False
                        if "deadfor" in tag:
                            found = True
                            min_max = tag.split("_")[0]
                            moons = tag.split("_")[-1]
                            item["dead"].remove(tag)

                            if min_max == "min":
                                min_moons = int(moons)
                            elif min_max == "max":
                                max_moons = int(moons)
                        if found:
                            if not min_moons:
                                min_moons = 0
                            if not max_moons:
                                max_moons = -1
                            item["min_max_dead_moons"] = [min_moons, max_moons]
                    # dead -> residence
                    item["residence"] = item[constraint]
                    item.pop(constraint)

        new_block["cats"][key] = item
    if RELATIONSHIPS:
        new_block["relationships"] = RELATIONSHIPS

    if MURDER:
        new_block["recent_murder"] = MURDER

    if TAGS:
        new_block["tags"] = TAGS
    for key, item in SCENES.items():
        new_block[key] = item

    new_dialogue_dict.update({dialogue_key: new_block})

    file_path = "scripts/events_module/dialogue/reformat/new_dialogue.json"

    text = json.dumps(new_dialogue_dict, indent=4)

    # uncomment for no more multiline lists
    # text = re.sub(
    #     r'\[\s+([^\[\]]+?)\s+\]',
    #     lambda m: "[" + " ".join(m.group(1).split()) + "]",
    #     text
    # )

    with open(file_path, "w") as f:
        # print("WRITING", FILE)
        f.write(text)
