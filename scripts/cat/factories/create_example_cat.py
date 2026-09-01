from __future__ import annotations

from random import sample, choices
from typing import TYPE_CHECKING

from scripts.cat.enums import CatRank
from scripts.cat.factories.new_cat_factory import NewCatFactory
from scripts.cat.factories.test_cat_factory import TestCatFactory
from scripts.cat.pelts import Pelt

if TYPE_CHECKING:
    from scripts.cat.cats import Cat


def create_example_cats(
    majority_rank: CatRank,
    rank_weights: dict,
    lifegen_kitten_creation=False,
    max_cats=12,
) -> list["Cat"]:
    majority_rank_cats = sample(range(max_cats), 3)

    chosen_cats = []
    if lifegen_kitten_creation:
        for cat_index in range(max_cats):
            chosen_cats.append(NewCatFactory.create_cat(rank=CatRank.KITTEN, moons=1))
    else:
        for cat_index in range(max_cats):
            if cat_index in majority_rank_cats:
                chosen_cats.append(NewCatFactory.create_cat(rank=majority_rank))
            else:
                random_rank = choices(
                    list(rank_weights.keys()), list(rank_weights.values())
                )[0]
                chosen_cats.append(NewCatFactory.create_cat(rank=random_rank))

    return chosen_cats


def create_option_preview_cat(scar: str = None, acc: str = None):
    """
    Creates a cat with the specified scar and/or accessory.
    :param scar: Desired scar (only one)
    :param acc: Desired accessory (only one)
    """
    new_cat = TestCatFactory.create_cat(
        moons=60,
        loading_cat=True,
        pelt=Pelt(
            name="SingleColour",
            colour="WHITE",
            length="medium",
            eye_color="SAGE",
            reverse=False,
            white_patches=None,
            vitiligo=None,
            points=None,
            tortie_marking=None,
            tortie_base=None,
            tortie_pattern=None,
            tortie_colour=None,
            tint="gray",
            skin="BLUE",
            scars=[scar] if scar else [],
            adult_sprite="8",
            accessory=[acc] if acc else [],
        ),
    )

    return new_cat
