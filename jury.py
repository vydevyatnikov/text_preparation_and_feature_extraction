import pandas as pd
import re
import nltk
import warnings
from prepare_texts import prepare_texts
from get_gender import custom_contains

warnings.filterwarnings("ignore",
                        'This pattern is interpreted as a regular expression, and has match groups.')


class JuryGetter:

    def __init__(self, data, column, tokenizer, prepare_text=False):
        # self.data = prepare_texts(data, 'texts')
        self.data = data
        self.column = column
        if prepare_text:
            self.data = prepare_texts(self.data, self.column)

        self.patterns_list = ['jury', 'verdict', 'return_to_prosecutor']
        self.aux_patterns_list = ['result_part', 'header_part']
        self.tokenizer = tokenizer

        self.patterns = self.patterns_constructor(self.patterns_list)
        self.aux_patterns = self.patterns_constructor(self.aux_patterns_list)


        self.meta_dict = {}
        self.res_data = pd.DataFrame({"id": self.data["id"].copy(),
                                      "criminal_court": self.data["criminal_court"].copy(),
                                      "jury": False})
        self.apply_patterns()

    @staticmethod
    def patterns_constructor(patterns):
        output = {}

        if patterns is None or 'result_part' in patterns:
            output['result_part'] = r'(П\s*О\s*С\s*Т\s*А\s*Н\s*О\s*В\s*И\s*Л\b)|(П\s*Р\s*И\s*Г\s*О\s*В\s*О\s*Р\s*И\s*Л\b)'

        if patterns is None or 'header_part' in patterns:
            output['header_part'] = r'У\s*С\s*Т\s*А\s*Н\s*О\s*В\s*И\s*Л'

        if patterns is None or 'return_to_prosecutor' in patterns:
            output['return_to_prosecutor'] = r'(?:[Вв]ернут\w+|[Вв]озвра\w+)(?:\W{1,3}\w+){,5}?\W{0,3}прокурор\w*'

        if patterns is None or 'jury' in patterns:
            output['jury'] = r'(?:[Кк]оллег\w+ )?[Пп]рисяжны(?:х|е)'

        if patterns is None or 'verdict' in patterns:
            output['verdict'] = r'[Вв]ердикт\w*'

        return output

    def apply_patterns(self):
        for j in pd.Series(zip(self.data["id"], self.data["criminal_court"])).unique():
            #print(j)
            if j[0] in [#'288f193df3541f148fd1de4951ad6de3', 'ccbc8e4e9deca9366f760a5ffe21e20b',
            #            #'b699e988ba058fa208b0c6c06dcc9ed7', 'c34e30e7c32309c7dda70405e27469c9',
            #            #'31e002ec2b4a30b3d7926747c4fa06c2',
            #            '53740a4ecfe9f4583e5fb42731637f32', '8e3b32719bf4848d3ea128b7a8a99c8b',
                        'd5031b0339abd30d1e81bd168573d270'
                        ]:
                pass
            try:
                text = self.data.loc[(self.data["id"] == j[0]) & (self.data['criminal_court'] == j[1]),
                                     self.column].iloc[0]
                temp_tokens = pd.Series(self.tokenizer.tokenize(text))
                self.meta_dict = {"tokens": temp_tokens, "res_dataframe": pd.DataFrame()}

                # result part
                result_part = self.meta_dict['tokens'].str.contains(self.aux_patterns['result_part'], regex=True,
                                                                    flags=re.IGNORECASE)
                if sum(result_part) != 0:
                    result_num = result_part.loc[result_part].index.values[-1]
                else:
                    result_num = len(temp_tokens)

                # header part
                header_part = self.meta_dict['tokens'].str.contains(self.aux_patterns['header_part'], regex=True,
                                                                    flags=re.IGNORECASE)
                if sum(header_part) != 0:
                    header_num = header_part.loc[header_part].index.values[0]
                else:
                    header_num = 0

            except TypeError:
                continue
            for pattern in self.patterns:
                # res = self.meta_dict[j]["tokens"].str.contains(self.patterns[pattern])
                res = custom_contains(self.meta_dict["tokens"], self.patterns[pattern])
                # match_loc = [1 if len(k) != 0 else 0 for k in res]
                self.meta_dict[pattern] = res
                self.meta_dict["res_dataframe"][pattern] = res
            self.apply_logic(j, header_num, result_num)

    def apply_logic(self, j, header_num, result_num):
        data_in_question = self.meta_dict['res_dataframe']
        #if 'result' in self.data.columns and not regex.search(r'возвращен\w+|подсуд\w+',
        #                    str(self.data.loc[(self.data["id"] == j[0]) &
        #                                      (self.data['criminal_court'] == j[1]), 'result'].iloc[0]),
        #                    flags=regex.IGNORECASE):
        if data_in_question.loc[data_in_question.jury & (data_in_question.index <= header_num)].shape[0] > 0:
            self.res_data.loc[(self.res_data["id"] == j[0]) &
                              (self.res_data['criminal_court'] == j[1]), 'jury'] = True
        elif (data_in_question.loc[data_in_question.jury & data_in_question.verdict &
                                  (data_in_question.index < result_num)].shape[0] > 0 and
              data_in_question.return_to_prosecutor.sum() == 0):
            self.res_data.loc[(self.res_data["id"] == j[0]) &
                              (self.res_data['criminal_court'] == j[1]), 'jury'] = True
