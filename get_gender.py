import pandas as pd
import numpy as np
import warnings
import re


def custom_contains(vec, pattern, flags=0):
    if isinstance(pattern, list):
        #vec.str.findall(pattern)
        return pd.Series(np.array(
            [vec.str.contains(sub_pattern, flags) for sub_pattern in pattern]
        ).sum(axis=0) > 0, index=vec.index)
    else:
        try:
            return vec.str.contains(pattern, regex=True, flags=flags)
        except re.error:
            return pd.Series([False if j is None else True for j in [regex.search(pattern, i, flags) for i in vec]],
                             index=vec.index)


class GenderGetter:

    def __init__(self, data, column, tokenizer):
        warnings.simplefilter("ignore")

        self.data = data
        #self.data = prepare_texts(self.data, 'texts')
        self.column = column
        self.tokenizer = tokenizer
        #self.patterns_elems = patterns_elems

        self.patterns_list = ['female_offender', 'male_offender']
        self.meta_dict = {}
        #self.patterns_list = patterns_list
        self.patterns = {}
        self.patterns_constructor()

        self.res_data = pd.DataFrame({"id": self.data["id"].copy(),
                                      "criminal_court": self.data["criminal_court"].copy(), "defendant_gender": np.nan})

        self.apply_patterns()

    def patterns_constructor(self):
        if self.patterns_list is None or "male_offender" in self.patterns_list:
            self.patterns["male_offender"] = r"\b([Пп]одсудим(ый|ого)|[Оо]бвиняем(ый|ого))"

        if self.patterns_list is None or "female_offender" in self.patterns_list:
            self.patterns["female_offender"] = r"\b([Пп]одсудим(ая|ой)|[Оо]бвиняем(ая|ой))"

    def apply_patterns(self):
        for j in pd.Series(zip(self.data["id"], self.data["criminal_court"])).unique():
            #print(j)
            #if j in ["e9553d42d859582b52a1cf64aacbe2e2"]:
            #    breakpoint()
            try:
                temp_tokens = pd.Series(self.tokenizer.tokenize(self.data.loc[(self.data["id"] == j[0]) &
                                                                              (self.data['criminal_court'] == j[1]),
                                                                              self.column].iloc[0]))
                self.meta_dict = {"tokens": temp_tokens, "res_dataframe": pd.DataFrame(),
                                              "judicial": pd.DataFrame()}
            except TypeError:
                self.meta_dict = {"tokens": pd.Series(dtype="object"), "res_dataframe": pd.DataFrame(),
                                              "judicial": pd.DataFrame()}
            # if j in ["711636338e1bf89202803dd9ac6b1f2a", "e61c9b607cdcb6c72d49020cfb40ed68"]:
            #    breakpoint()
            for pattern in self.patterns:
                # res = self.meta_dict[j]["tokens"].str.contains(self.patterns[pattern])
                res = custom_contains(self.meta_dict["tokens"], self.patterns[pattern])
                # match_loc = [1 if len(k) != 0 else 0 for k in res]
                self.meta_dict[pattern] = res
                self.meta_dict["res_dataframe"][pattern] = res
            self.apply_logic(j)

    def apply_logic(self, j):
        temp_data = self.meta_dict["res_dataframe"]
        if sum(temp_data["male_offender"]) > sum(temp_data["female_offender"]):
            self.res_data.loc[(self.data["id"] == j[0]) & (self.data['criminal_court'] == j[1]),
                              "defendant_gender"] = "M"
        elif sum(temp_data["male_offender"]) < sum(temp_data["female_offender"]):
            self.res_data.loc[(self.data["id"] == j[0]) & (self.data['criminal_court'] == j[1]),
                              "defendant_gender"] = "F"
        #if sum(temp_data["male_offender"]) > 0 and sum(temp_data["female_offender"]) == 0:
        #    self.res_data.loc[self.res_data['id'] == j, "gender"] = "M"
        #elif sum(temp_data["male_offender"]) == 0 and sum(temp_data["female_offender"]) > 0:
        #    self.res_data.loc[self.res_data['id'] == j, "gender"] = "F"
        #elif sum(temp_data["male_offender"]) > 0 and sum(temp_data["female_offender"]) > 0:
            #if sum(temp_data["male_offender"]) / (sum(temp_data["male_offender"]) +
            #                                      sum(temp_data["female_offender"])) < 0.2:
            #    self.res_data.loc[self.res_data['id'] == j, "gender"] = "F"
            #elif sum(temp_data["female_offender"]) / (sum(temp_data["male_offender"]) +
            #                                          sum(temp_data["female_offender"])) < 0.2:
            #    self.res_data.loc[self.res_data['id'] == j, "gender"] = "M"

        # sum(self.data.loc[self.data["id"] == j, ["solo_defendant", "sole_charge"]].sum(axis=1)) == 2
