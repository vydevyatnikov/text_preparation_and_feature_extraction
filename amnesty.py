import pandas as pd
import numpy as np
import re
import nltk
import warnings
from prepare_texts import prepare_texts
from get_gender import custom_contains

warnings.filterwarnings("ignore",
                        'This pattern is interpreted as a regular expression, and has match groups.')


class AmnestyGetter:

    def __init__(self, data, column, tokenizer, prepare_text=False):
        # self.data = prepare_texts(data, 'texts')
        self.data = data
        self.column = column
        if prepare_text:
            self.data = prepare_texts(self.data, self.column)

        self.patterns_list = ['amnesty', 'appeal_or_cassation_ruling', 'return_to_prosecutor']
        self.aux_patterns_list = ['result_part', 'header_part']
        self.tokenizer = tokenizer

        self.patterns = self.patterns_constructor(self.patterns_list)
        self.aux_patterns = self.patterns_constructor(self.aux_patterns_list)


        self.meta_dict = {}
        self.res_data = pd.DataFrame({"id": self.data["id"].copy(),
                                      "criminal_court": self.data["criminal_court"].copy(),
                                      "amnesty": False})
        self.apply_patterns()

    @staticmethod
    def patterns_constructor(patterns):
        output = {}

        if patterns is None or 'result_part' in patterns:
            output['result_part'] = r'(П\s*О\s*С\s*Т\s*А\s*Н\s*О\s*В\s*И\s*Л(?:\s*А)?\b)|(П\s*Р\s*И\s*Г\s*О\s*В\s*О\s*Р\s*И\s*Л(?:\s*А)?\b)'

        if patterns is None or 'header_part' in patterns:
            output['header_part'] = r'У\s*С\s*Т\s*А\s*Н\s*О\s*В\s*И\s*Л'

        if patterns is None or 'return_to_prosecutor' in patterns:
            output['return_to_prosecutor'] = r'(?:[Вв]ернут\w+|[Вв]озвра\w+)(?:\W{1,3}\w+){,5}?\W{0,3}прокурор\w*'

        if patterns is None or 'amnesty' in patterns:
            output['amnesty'] = r'\b[Аа]мнисти\w+'

        if patterns is None or 'appeal_or_cassation_ruling' in patterns:
            output['appeal_or_cassation_ruling'] = r'\b[Аа]пелляц\w+|\b[Кк]ассац\w+'

        return output

    def apply_patterns(self):
        for j in pd.Series(zip(self.data["id"], self.data["criminal_court"])).unique():
            #print(j)
            if j[0] in [#'288f193df3541f148fd1de4951ad6de3', 'ccbc8e4e9deca9366f760a5ffe21e20b',
            #            #'b699e988ba058fa208b0c6c06dcc9ed7', 'c34e30e7c32309c7dda70405e27469c9',
            #            #'31e002ec2b4a30b3d7926747c4fa06c2',
            #            '53740a4ecfe9f4583e5fb42731637f32', '8e3b32719bf4848d3ea128b7a8a99c8b',
                        '31f73d084a44c6a33ec66f8cff0e054c'
                        ]:
                pass
            try:
                text = self.data.loc[(self.data["id"] == j[0]) & (self.data['criminal_court'] == j[1]),
                                     self.column].iloc[0]
                temp_tokens = pd.Series(self.tokenizer.tokenize(text))
                result_part = temp_tokens.str.contains(self.aux_patterns['result_part'], regex=True,
                                                       flags=re.IGNORECASE)
                if sum(result_part) != 0:
                    temp_tokens = temp_tokens.loc[result_part.loc[result_part].index.values[-1]:]
                else:
                    continue
                self.meta_dict = {"tokens": temp_tokens, "res_dataframe": pd.DataFrame()}

            except TypeError:
                continue
            for pattern in self.patterns:
                # res = self.meta_dict[j]["tokens"].str.contains(self.patterns[pattern])
                res = custom_contains(self.meta_dict["tokens"], self.patterns[pattern])
                # match_loc = [1 if len(k) != 0 else 0 for k in res]
                self.meta_dict[pattern] = res
                self.meta_dict["res_dataframe"][pattern] = res
            self.apply_logic(j)

    def apply_logic(self, j):
        data_in_question = self.meta_dict['res_dataframe']
        if data_in_question.appeal_or_cassation_ruling.sum() > 0:
            first_appeal_or_cassation_ruling = np.where(data_in_question.appeal_or_cassation_ruling == True)[0][0]
            data_in_question = data_in_question.iloc[:first_appeal_or_cassation_ruling]
        #if 'result' in self.data.columns and not regex.search(r'возвращен\w+|подсуд\w+',
        #                    str(self.data.loc[(self.data["id"] == j[0]) &
        #                                      (self.data['criminal_court'] == j[1]), 'result'].iloc[0]),
        #                    flags=regex.IGNORECASE):
        if (data_in_question.loc[data_in_question.amnesty].shape[0] > 0 and
                data_in_question.return_to_prosecutor.sum() == 0):
            self.res_data.loc[(self.res_data["id"] == j[0]) &
                              (self.res_data['criminal_court'] == j[1]), 'amnesty'] = True
