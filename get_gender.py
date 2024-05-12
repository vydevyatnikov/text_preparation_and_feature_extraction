import pandas as pd
import numpy as np
import re
import nltk
import regex
import warnings


def series_in(series, values_set):
    return pd.Series([True if i in values_set else False for i in series.values], index=series.index)


class Filters:

    def __init__(self, data, tokenizer, func: str = "findall",  column: str = "texts", patterns_list: list = None):
        warnings.simplefilter("ignore")

        self.data = data
        self.column = column
        self.func = func
        self.tokenizer = tokenizer
        self.just_for_fun = None
        self.temp_blocked = None
        #self.prepare_texts()

        self.patterns_list = patterns_list
        self.meta_dict = {0: {}, 1: {}}
        self.patterns_list = patterns_list
        self.patterns = PatternsConstructor().get_patterns(self.patterns_list)

        self.res_data = pd.DataFrame({"id": self.data["id"].copy(),
                                      "criminal_court": self.data["criminal_court"].copy(), "defendant_gender": np.NaN})

        self.apply_patterns()

    def apply_patterns(self):
        for j in pd.Series(zip(self.data["id"], self.data["criminal_court"])).unique():
            print(j)
            try:
                temp_tokens = pd.Series(self.tokenizer.tokenize(self.data.loc[(self.data["id"] == j[0]) &
                                                                              (self.data['criminal_court'] == j[1]),
                                                                              self.column].iloc[0]))
                self.meta_dict[j[1]][j[0]] = {"tokens": temp_tokens, "res_dataframe": pd.DataFrame(),
                                              "judicial": pd.DataFrame()}
            except TypeError:
                self.meta_dict[j[1]][j[0]] = {"tokens": pd.Series(dtype="object"), "res_dataframe": pd.DataFrame(),
                                              "judicial": pd.DataFrame()}
            for pattern in self.patterns:
                res = self.custom_contains(self.meta_dict[j[1]][j[0]]["tokens"], self.patterns[pattern])
                # match_loc = [1 if len(k) != 0 else 0 for k in res]
                self.meta_dict[j[1]][j[0]][pattern] = res
                self.meta_dict[j[1]][j[0]]["res_dataframe"][pattern] = res
            self.apply_logic(j)

    def apply_logic(self, j):
        temp_data = self.meta_dict[j[1]][j[0]]["res_dataframe"]
        if sum(temp_data["male_offender"]) > sum(temp_data["female_offender"]):
            self.res_data.loc[(self.data["id"] == j[0]) & (self.data['criminal_court'] == j[1]),
                              "defendant_gender"] = "M"
        elif sum(temp_data["male_offender"]) < sum(temp_data["female_offender"]):
            self.res_data.loc[(self.data["id"] == j[0]) & (self.data['criminal_court'] == j[1]),
                              "defendant_gender"] = "F"

    @staticmethod
    def custom_contains(vec, pattern):
        if isinstance(pattern, list):
            return pd.Series(np.array(
                [vec.str.contains(sub_pattern) for sub_pattern in pattern]
                                      ).sum(axis=0) > 0, index=vec.index)
        else:
            try:
                return vec.str.contains(pattern)
            except re.error:
                return pd.Series([False if j is None else True for j in [regex.search(pattern, i) for i in vec]],
                                 index=vec.index)


class PatternsConstructor:

    def __init__(self):

        self.elems = {}


    def get_patterns(self, mode: list = None):

        patterns_dict = {}

        if mode is None or "male_offender" in mode:
            patterns_dict["male_offender"] = r"\b([Пп]одсудим(ый|ого)|[Оо]бвиняем(ый|ого))"

        if mode is None or "female_offender" in mode:
            patterns_dict["female_offender"] = r"\b([Пп]одсудим(ая|ой)|[Оо]бвиняем(ая|ой))"

        return patterns_dict


if __name__ == "__main__":
    pd.set_option("display.max_columns", 100)
    pd.set_option("display.max_rows", 100)

    tokenizer = nltk.data.load("tokenizers/punkt/russian.pickle")

    temp = pd.read_csv("path/to/data", index_col=0)
    lesgo = Filters(temp.copy(), tokenizer, patterns_list=["female_offender", "male_offender"])

    final_data = pd.merge(temp, lesgo.res_data, how="left", on=["id", "criminal_court"])

    final_data.to_csv("path/to/data")
