import pandas as pd
import warnings
import re
from prepare_texts import prepare_texts


def series_in(series, values_set):
    return pd.Series([True if i in values_set else False for i in series.values], index=series.index)


class PeacefulAgreementGetter:

    def __init__(self, data, column, tokenizer, prepare_text=False):
        warnings.simplefilter("ignore")

        self.data = data
        self.column = column
        if prepare_text:
            self.data = prepare_texts(self.data, self.column)

        self.tokenizer = tokenizer
        # self.patterns_elems = patterns_elems

        self.patterns_list = ["peaceful_agreement", "deny", "appeal", 'sentence_header',
                              'guided_by', 'to_cancel', 'peaceful_articles']
        self.meta_dict = {}
        # self.patterns = PatternsConstructor().get_patterns(self.patterns_list)
        self.patterns = {}
        self.patterns_constructor()

        self.res_data = pd.DataFrame({"id": self.data["id"].copy(),
                                      "criminal_court": self.data["criminal_court"].copy(),
                                      "peaceful_agreement": False})

        self.apply_patterns()
        # self.check_for_undefined_results()

    def patterns_constructor(self):
        if self.patterns_list is None or "peaceful_agreement" in self.patterns_list:
            self.patterns["peaceful_agreement"] = r"\b[Пп]римирени\w+"

        if self.patterns_list is None or 'deny' in self.patterns_list:
            self.patterns['deny'] = r"\b[Оо][Тт][Кк][Аа][Зз][Аа][Тт]\w+"

        if self.patterns_list is None or "appeal" in self.patterns_list:
            self.patterns['appeal'] = r"\b[Аа]пелляци\w+"

        if self.patterns_list is None or 'sentence_header' in self.patterns_list:
            self.patterns['sentence_header'] = r"\b[Пп]\s*[Рр]\s*[Ии]\s*[Гг]\s*[Оо]\s*[Вв]\s*[Оо]\s*[Рр]\b"

        if self.patterns_list is None or 'peaceful_articles' in self.patterns_list:
            self.patterns['peaceful_articles'] = r'\b25(?!\.)\b|\b76(?!\.)\b'

        if self.patterns_list is None or 'to_cancel' in self.patterns_list:
            self.patterns['to_cancel'] = r'[Пп]рекратить'

        if self.patterns_list is None or 'guided_by' in self.patterns_list:
            self.patterns['guided_by'] = r'[Рр]уководствуясь'

    def apply_patterns(self):
        for j in pd.Series(zip(self.data["id"], self.data["criminal_court"])).unique():
            # if j[0] in ["a148b25bb41a284b8ca54c44ea3f9e4e"]:
            #    breakpoint()
            # print(j)
            try:
                temp_tokens = pd.Series(self.tokenizer.tokenize(self.data.loc[(self.data["id"] == j[0]) &
                                                                              (self.data["criminal_court"] == j[1]),
                self.column].iloc[0]))
                if len(temp_tokens) == 0:
                    continue
                result_part = pd.Series([1 if len(k) != 0 else 0 for k in temp_tokens.str.findall(
                    r'(П\s*О\s*С\s*Т\s*А\s*Н\s*О\s*В\s*И\s*Л(?:\s*А)?\b)|(П\s*Р\s*И\s*Г\s*О\s*В\s*О\s*Р\s*И\s*Л(?:\s*А)?\b)',
                    re.IGNORECASE)]).astype(bool)
                headers_part = pd.Series([1 if len(k) != 0 else 0
                                          for k in temp_tokens.str.findall(r'У\s*С\s*Т\s*А\s*Н\s*О\s*В\s*И\s*Л',
                                                                           re.IGNORECASE)]).astype(bool)
                if sum(result_part) != 0:
                    result_part_sentence_num = temp_tokens.index.values[result_part][-1]
                else:
                    result_part_sentence_num = temp_tokens.index.values[-1]
                if sum(headers_part) != 0:
                    headers_part_sentence_num = temp_tokens.index.values[headers_part][0]
                else:
                    headers_part_sentence_num = temp_tokens.index.values[0]

                self.meta_dict = {"tokens": temp_tokens,
                                  "res_dataframe": pd.DataFrame(), "judicial": pd.DataFrame()}
            except TypeError:
                continue
            # if j in ["711636338e1bf89202803dd9ac6b1f2a", "e61c9b607cdcb6c72d49020cfb40ed68"]:
            #    breakpoint()
            for pattern in self.patterns:
                # res = self.meta_dict[j]["tokens"].str.contains(self.patterns[pattern])
                res = self.custom_contains(self.meta_dict["tokens"], self.patterns[pattern])
                # match_loc = [1 if len(k) != 0 else 0 for k in res]
                self.meta_dict[pattern] = res
                self.meta_dict["res_dataframe"][pattern] = res
            self.apply_logic(j, result_part_sentence_num, headers_part_sentence_num)

    def apply_logic(self, case_id, result_part_sentence_num, num_of_header_tokens):
        data_in_question = self.meta_dict["res_dataframe"]
        head_data = data_in_question.iloc[:num_of_header_tokens]
        result_data = data_in_question.iloc[result_part_sentence_num:]
        if head_data.sentence_header.sum() != 0:
            return

        if data_in_question.loc[data_in_question.to_cancel &
                                (data_in_question.peaceful_agreement | data_in_question.peaceful_articles)].shape[
            0] > 0:
            self.res_data.loc[(self.res_data['id'] == case_id[0]) & (self.res_data["criminal_court"] == case_id[1]),
            "peaceful_agreement"] = True
        elif data_in_question.loc[data_in_question.guided_by & data_in_question.peaceful_articles].shape[0] > 0:
            self.res_data.loc[(self.res_data['id'] == case_id[0]) & (self.res_data["criminal_court"] == case_id[1]),
            "peaceful_agreement"] = True

        temp_data = data_in_question.loc[data_in_question.peaceful_agreement &
                                         (data_in_question.deny + data_in_question.appeal == 0)]
        # if temp_data.shape[0] > 0:
        #    self.res_data.loc[(self.res_data['id'] == case_id[0]) & (self.res_data["criminal_court"] == case_id[1]),
        #                      "peaceful_agreement"] = True
        # else:
        #    self.res_data.loc[(self.res_data['id'] == case_id[0]) & (self.res_data["criminal_court"] == case_id[1]),
        #                      "peaceful_agreement"] = False
