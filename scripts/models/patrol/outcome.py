from __future__ import annotations

from typing import Annotated, Dict, List, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic_core import MISSING
from scripts.models.common.gather_cat import GatherCat
from scripts.models.common.herb import Herb
from scripts.models.common.min_max_status import MinMaxStatusDictKey
from scripts.models.common.new_cat import NewCat
from scripts.models.common.future_event import FutureEvent
from scripts.models.common.relationship_status import RelationshipStatus
from scripts.models.common.skill import Skill
from scripts.models.common.trait import Trait
from scripts.models.common.kit_trait import KitTrait
from scripts.models.patrol.can_have_status import CanHaveStat
from scripts.models.patrol.history_text import HistoryText
from scripts.models.patrol.injury_item import InjuryItem
from scripts.models.patrol.leader_lives_lost import LeaderLivesLost
from scripts.models.patrol.patrol_herb import PatrolHerb
from scripts.models.patrol.prey import Prey
from scripts.models.common.relationship import Relationship


class Outcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(..., description="Displayed outcome text.")
    frequency: Annotated[
        int,
        Field(
            description="Controls how common an outcome is.",
            json_schema_extra={
                "default": 4
            },  # Necessary so that JSON Schema still shows a default without making the field optional
        ),
    ]
    exp: int = Field(..., description="Base exp gain.")
    stat_skill: Union[List[Skill], MISSING] = Field(
        MISSING,
        description="Makes this a stat outcome which can occur if a stat cat can be found.",
    )
    # stat_trait: Union[List[Trait], MISSING] = Field(
    #     MISSING,
    #     description="Makes this a stat outcome which can occur if a stat cat can be found.",
    # )

    # LG Change: Need kit traits for LG patrols
    stat_trait: Union[List[Union[Trait, KitTrait]], MISSING] = Field(
        MISSING,
        description="Makes this a stat outcome which can occur if a stat cat can be found.",
    )
    # can_have_stat: Union[List[CanHaveStat], MISSING] = Field(
    #     MISSING,
    #     description="Overrides default behavior or adds additional requirements for stat_cat picking.",
    # )
    # LG Change: Need r_c:X abbrevs
    can_have_stat: Union[List[Union[CanHaveStat, GatherCat]], MISSING] = Field(
        MISSING,
        description="Overrides default behavior or adds additional requirements for stat_cat picking.",
    )
    # --
    # LG
    stat_residence: Union[List[str], MISSING] = Field(
        MISSING, description="Dead residence the stat cat must be a part of."
    )
    stat_cluster: Union[List[str], MISSING] = Field(
        MISSING, description="Cluster the stat cat must be a part of."
    )
    stat_faith: Union[List[int], MISSING] = Field(
        MISSING, description="Faith range the stat cat must be a part of."
    )
    # ---
    prey: Union[List[Prey], MISSING] = Field(
        MISSING, description="Indicates how much prey each cat brings back."
    )
    herbs: Union[List[Union[Herb, PatrolHerb]], MISSING] = Field(
        MISSING, description="Indicates which herbs will be given."
    )
    lost_cats: Union[List[GatherCat], MISSING] = Field(
        MISSING, description="Indicates which cats will become lost."
    )
    dead_cats: Union[List[Union[GatherCat, LeaderLivesLost]], MISSING] = Field(
        MISSING, description="Indicates which cats will die."
    )
    injury: Union[List[InjuryItem], MISSING] = Field(
        MISSING, description="Indicates which cats get injured and how."
    )

    # LG
    murder: Union[List[dict], MISSING] = Field(
        MISSING, description="Indicates which cats will be murdered and by who."
    )
    accessory: Union[List[dict], MISSING] = Field(
        MISSING, description="Indicates accessories gained from the outcome."
    )
    faith_effects: Union[List[dict], MISSING] = Field(
        MISSING, description="Indicates faith effects given."
    )
    convert: Union[List[str], MISSING] = Field(
        MISSING, description="Indicates which cats were converted to the Dark Forest."
    )
    faith_effect: Union[List[dict], MISSING] = Field(
        MISSING, description="Indicates faith effects caused by the outcome."
    )

    # ---

    min_max_status: Union[Dict[MinMaxStatusDictKey, Tuple[int, int]], MISSING] = Field(
        MISSING,
        description="Allows specification of the minimum and maximum number of specific types of cats that are allowed on the patrol.",
    )
    history_text: Union[HistoryText, MISSING] = Field(
        MISSING, description="Controls the history-text for scars and death."
    )
    relationships: Union[List[Relationship], MISSING] = Field(
        MISSING, description="Indicates effect on cat relationships."
    )
    relationship_constraint: Union[List[RelationshipStatus], MISSING] = Field(
        MISSING,
        description="Dictates what relationships m_c must have towards r_c. Do not use this section if there is no r_c in the event.",
    )
    new_cat: Union[List[NewCat], MISSING] = Field(
        MISSING,
        description="Adds new cat(s), either joining the clan or as outside cats. The {index} value corresponds to their index value on this list (e.g. n_c:0 refers to the first cat in this list).",
    )
    art: Union[str, MISSING] = Field(
        MISSING,
        description="Name of outcome-specific art, without file extension (no .png). If no art is specified, the intro art will be used.",
    )
    art_clean: Union[str, MISSING] = Field(
        MISSING,
        description="Name of non-gore outcome-specific art, without file extension (no .png). Adding a clean version of the art marks the normal version as containing gore.",
    )
    outsider_rep: Union[int, MISSING] = Field(
        MISSING,
        description="How much outsider reputation will change. Can be positive or negative.",
    )
    other_clan_rep: Union[int, MISSING] = Field(
        MISSING,
        description="How much reputation with other Clan will change. Can be positive or negative.",
    )
    future_event: Union[FutureEvent, MISSING] = MISSING
