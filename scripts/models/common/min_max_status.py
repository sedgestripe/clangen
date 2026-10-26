from enum import Enum


class MinMaxStatusDictKey(Enum):
    medicine_cat = "medicine cat"
    warrior = "warrior"
    leader = "leader"
    deputy = "deputy"
    apprentice = "apprentice"
    medicine_cat_apprentice = "medicine cat apprentice"
    healer_cats = "healer cats"
    normal_adult = "normal adult"
    all_apprentices = "all apprentices"

    # LG
    kitten = "kitten"
    mediator = "mediator"
    queen = "queen"
    mediator_apprentice = "mediator apprentice"
    queens_apprentice = "queen's apprentice"
    elder = "elder"
    df = "df"
    patrol_cats = "patrol_cats"
