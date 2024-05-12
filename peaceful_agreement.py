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
        self.patterns = PatternsConstructor().get_patterns()

        self.res_data = pd.DataFrame({"id": self.data["id"].copy(),
                                      "criminal_court": self.data["criminal_court"].copy(),
                                      "peaceful_agreement": np.NaN})

        self.apply_patterns()

    def apply_patterns(self):
        for j in pd.Series(zip(self.data["id"], self.data["criminal_court"])).unique():
            print(j)
            try:
                temp_tokens = pd.Series(self.tokenizer.tokenize(self.data.loc[(self.data["id"] == j[0]) &
                                                                              (self.data["criminal_court"] == j[1]),
                                                                              self.column].iloc[0]))
                temp_match_loc = pd.Series([1 if len(k) != 0 else 0 for k in temp_tokens.str.findall(
                    r'(П\s*О\s*С\s*Т\s*А\s*Н\s*О\s*В\s*И\s*Л)|(П\s*Р\s*И\s*Г\s*О\s*В\s*О\s*Р\s*И\s*Л)',
                    re.IGNORECASE)]).astype(bool)
                if sum(temp_match_loc) == 0:
                    #    breakpoint()
                    self.meta_dict[j[1]][j[0]] = {"tokens": temp_tokens,
                                                  "res_dataframe": pd.DataFrame(), "judicial": pd.DataFrame()}
                    #breakpoint()
                else:
                    self.meta_dict[j[1]][j[0]] = {
                        "tokens": temp_tokens.loc[temp_tokens.index.values[temp_match_loc][-1]:],
                        "res_dataframe": pd.DataFrame(), "judicial": pd.DataFrame()}
            except TypeError:
                self.meta_dict[j[1]][j[0]] = {"tokens": pd.Series(dtype="object"), "res_dataframe": pd.DataFrame(),
                                              "judicial": pd.DataFrame()}
            self.temp_blocked = []
            for pattern in self.patterns:
                res = self.custom_contains(self.meta_dict[j[1]][j[0]]["tokens"], self.patterns[pattern])
                self.meta_dict[j[1]][j[0]][pattern] = res
                self.meta_dict[j[1]][j[0]]["res_dataframe"][pattern] = res
            self.apply_logic(j)

    def apply_logic(self, case_id):
        data_in_question = self.meta_dict[case_id[1]][case_id[0]]["res_dataframe"]

        temp_data = data_in_question.loc[data_in_question.peaceful_agreement &
                                         (data_in_question.deny + data_in_question.appeal == 0)]

        if temp_data.shape[0] > 0:
            self.res_data.loc[(self.res_data['id'] == case_id[0]) & (self.res_data["criminal_court"] == case_id[1]),
                              "peaceful_agreement"] = True
        else:
            self.res_data.loc[(self.res_data['id'] == case_id[0]) & (self.res_data["criminal_court"] == case_id[1]),
                              "peaceful_agreement"] = False

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

        if mode is None or "peaceful_agreement" in mode:
            patterns_dict["peaceful_agreement"] = r"\b[Пп]римирени\w+"

        if mode is None or 'deny' in mode:
            patterns_dict['deny'] = r"\b[Оо][Тт][Кк][Аа][Зз][Аа][Тт]\w+"

        if mode is None or "appeal" in mode:
            patterns_dict['appeal'] = r"\b[Аа]пелляци\w+"

        return patterns_dict


if __name__ == "__main__":
    pd.set_option("display.max_columns", 100)
    pd.set_option("display.max_rows", 100)

    tokenizer = nltk.data.load("tokenizers/punkt/russian.pickle")
    temp = pd.read_csv(f"path/to/data",
                       index_col=0)

    lesgo = Filters(temp.copy(), tokenizer, patterns_list=["peaceful_agreement", "deny", "appeal"])
    final_data = pd.merge(temp, lesgo.res_data,
                          how="left", on=["id", "criminal_court"])
    print("it's done")
    final_data.to_csv("path/to/data")
