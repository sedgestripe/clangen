"""
LIFEGEN: patrol consequences that don't exist in ClanGen's text pool events.
These were part of PatrolOutcome before ClanGen's patrol rework and are run after
handle_consequences.execute_outcome for the chosen patrol outcome.
"""

from html import escape
from random import choice
from typing import Union

from scripts.cat.cats import Cat
from scripts.cat.pelts import Pelt
from scripts.clan import OtherClan
from scripts.clan_package.settings import get_clan_setting
from scripts.game_structure.game.settings import game_setting_get


def execute_lifegen_outcome(
    lifegen_info: dict,
    involved_cats: dict[str, Union[Cat, list[Cat]]],
    other_clan: OtherClan = None,
) -> list[str]:
    """
    Applies the LifeGen-only consequences of a patrol outcome.
    :param lifegen_info: the LifeGen outcome info, as stored in PatrolEvent.lifegen_outcomes
    :param involved_cats: the involved cats of the chosen outcome
    :param other_clan: the other clan involved in the patrol
    :return: list of result strings (may contain empty strings)
    """
    if not lifegen_info:
        return []

    results = [_handle_murder(lifegen_info.get("murder"), involved_cats, other_clan)]
    if not get_clan_setting("all accessories"):
        results.append(
            _handle_accessories(lifegen_info.get("accessory"), involved_cats)
        )
    results.append(_handle_df_convert(lifegen_info.get("convert"), involved_cats))
    _handle_faith_changes(lifegen_info.get("faith_effects"), involved_cats)

    return results


def _gather_cats(abbr_list: list, involved_cats: dict) -> list[Cat]:
    """Finds the cat objects for the given abbreviations"""
    cats = []
    for abbr in abbr_list:
        cat = involved_cats.get(abbr)
        if isinstance(cat, list):
            cats.extend(c for c in cat if c not in cats)
        elif cat and cat not in cats:
            cats.append(cat)
    return cats


def _profile_link(cat: Cat) -> str:
    """Create a hyperlink to a cat profile from patrol results."""
    return f'<a href="cat://{cat.ID}"><b>{escape(str(cat.name))}</b></a>'


def _handle_murder(blocks: list, involved_cats: dict, other_clan: OtherClan) -> str:
    """cat killin each other on patrol. just dark forest right now"""
    if not blocks:
        return ""

    results = []
    for block in blocks:
        murderers = _gather_cats(block.get("murderer", []), involved_cats)
        victims = _gather_cats(block.get("victim", []), involved_cats)

        # skip if we don't have both a murderer and a victim to work with
        if not murderers or not victims:
            continue

        murderer = murderers[-1]
        victim = victims[-1]
        if victim.dead:
            continue

        results.append(
            f"{_profile_link(murderer)} has murdered {_profile_link(victim)}."
        )

        death_text = block.get("history") or "m_c was murdered on patrol."
        if other_clan:
            death_text = death_text.replace("o_c_n", other_clan.name)

        victim.history.add_death(death_text=death_text, other_cat=murderer)
        murderer.history.add_murder(murderer_id=murderer.ID, victim=victim)
        murderer.history.reveal_murder(
            victim=victim, murderer_id=murderer.ID, clan_reveal=False
        )
        victim.die()

    return " ".join(results)


def _handle_df_convert(abbr_list: list, involved_cats: dict) -> str:
    """Handle converting cats to the DF in DF patrols"""
    if not abbr_list:
        return ""

    cats_to_convert = _gather_cats(abbr_list, involved_cats)
    if not cats_to_convert:
        print(
            f"Something was indicated in convert, but no cats were indicated: {abbr_list}"
        )
        return ""

    results = []
    for _cat in cats_to_convert:
        results.append(f"{_cat.name} has joined the Dark Forest.")
        _cat.join_df()

    return " ".join(results)


def _handle_faith_changes(blocks: list, involved_cats: dict):
    """Handle changing a cats faith in patrols"""
    if not blocks:
        return

    for block in blocks:
        amount = block.get("amount", 0)
        for _cat in _gather_cats(block.get("faith_cat", []), involved_cats):
            # faith is capped at -9 and 9
            _cat.faith = max(-9, min(9, _cat.faith + amount))


def _handle_accessories(blocks: list, involved_cats: dict) -> str:
    """cats getting accessories"""
    if not blocks:
        return ""

    results = []
    for block in blocks:
        cats = _gather_cats(block.get("cats", []), involved_cats)
        accessory = block.get("accessory", [])

        if not (cats and accessory):
            print(f"something is wrong with accessory - {block}")
            continue

        for _cat in cats:
            if _give_accessory(_cat, accessory) and not block.get("no_results"):
                results.append(f"{_cat.name} got an accessory!")

    return " ".join(results)


def _give_accessory(cat: Cat, acc_list: list) -> str | None:
    """Gives the cat a random accessory from the list, adding it to their inventory"""
    if game_setting_get("lifegen_sprite_changes"):
        acc_categories = Pelt.lifegen_acc_categories
    else:
        acc_categories = Pelt.clangen_acc_categories

    resolved = []
    for item in acc_list:
        if item not in acc_categories and item not in Pelt.all_lifegen_accessories:
            print("WARNING: Invalid accessory present in patrol outcome:", item)
            continue
        if item in acc_categories:
            resolved.extend(acc_categories[item])
        else:
            resolved.append(item)

    resolved = [acc for acc in resolved if acc not in cat.pelt.inventory]

    if not resolved:
        return None

    chosen_acc = choice(resolved)
    cat.pelt.inventory.append(chosen_acc)
    cat.pelt.accessory = cat.pelt.accessory + (chosen_acc,)

    return chosen_acc
