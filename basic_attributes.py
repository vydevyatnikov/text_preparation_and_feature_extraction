import pandas as pd
import numpy as np
import sys

pd.set_option("display.max_columns", 100)
pd.set_option("display.max_rows", 100)
np.set_printoptions(threshold=sys.maxsize)


def basic_attributes(data, article):
    if "solo_defendant" in data.columns:
        data.drop(columns="solo_defendant", inplace=True)

    if "sole_charge" in data.columns:
        data.drop(columns="sole_charge", inplace=True)

    if "charge_part" in data.columns:
        data.drop(columns="charge_part", inplace=True)

    data["Статья УК РФ"] = data["Статья УК РФ"].str.replace(";$", "", regex=True).str.replace(
        "[Сс]т\.", "Статья", regex=True).str.replace("[Чч]\.", "часть", regex=True).str.replace(
        "(?<=\d),", "", regex=True)
    data["solo_defendant"] = [False if pd.isnull(i) or "," in i else True for i in data["ФИО"]]
    data["sole_charge"] = [False if "," in i or ";" in i else True for i in
                           data["Статья УК РФ"]]  # Проверить случаи, где есть запятая, но нет точки с запятой

    data["charge_part"] = np.NaN
    pat = f"статья {article} часть "
    for i in data["Статья УК РФ"].unique():
        if ";" not in i and article in i and "часть" in i.lower():
            try:
                data.loc[data["Статья УК РФ"] == i, "charge_part"] = int(i[i.lower().index(pat) + len(pat)])
            except ValueError:
                print(i)
    return data


data = pd.read_csv(f"path/to/data", index_col=0)
data = basic_attributes(data, "264")
data.to_csv(f"path/to/data")
