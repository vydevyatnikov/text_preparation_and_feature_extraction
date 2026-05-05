import re

import pandas as pd
import numpy as np
import sys
import regex

pd.set_option("display.max_columns", 100)
pd.set_option("display.max_rows", 100)
np.set_printoptions(threshold=sys.maxsize)


class BasicAttributesGetter:

    def __init__(self, data):
        self.data = data

        self.res_data = pd.DataFrame({"id": self.data["id"].copy(),
                                      "criminal_court": self.data["criminal_court"].copy(),
                                      "sole_charged_with": pd.NA,
                                      "sole_sentenced_under": pd.NA,
                                      "solo_defendant": pd.NA,
                                      'sentence_bin': pd.NA,
                                      **{f'{k[0]}_{k[1]}': pd.NA
                                         for k in ((phase, element)
                                                   for phase in ['charged_with', 'sentenced_under']
                                                   for element in ['article', 'part', 'clause'])}},
                                     index=self.data.index)
        if self.data.shape[0] != 0:
            self.basic_attributes()

    def basic_attributes(self):
        if self.data.shape[0] != len(np.unique(self.data.index.values)):
            raise AssertionError

        #if "solo_defendant" in self.data.columns:
        #    self.data.drop(columns="solo_defendant", inplace=True)
        #if "sole_charge" in self.data.columns:
        #    self.data.drop(columns="sole_charge", inplace=True)
        #if "charge_part" in self.data.columns:
        #    self.data.drop(columns="charge_part", inplace=True)

        #self.data.rename(columns={'ФИО': 'defendant', 'Номер дела (материала)': 'case_number', 'Тип документа': 'doc_type',
        #                     'Статья УК РФ': 'article', 'Дата поступления': 'receipt_date',
        #                     'Дата решения': 'decision_date', 'Наименование суда': 'court_name',
        #                     'Аннотация': "annotation", 'Результат': 'result', 'Субъект РФ': 'region'}, inplace=True)
        #self.data.loc[self.data.region == 'Город Москва', 'region'] = 'город Москва'
        #self.data.loc[self.data.region == 'Город Санкт-Петербург', 'region'] = 'город Санкт-Петербург'
        #self.data.loc[self.data.region == 'Кемеровская область - Кузбасс', 'region'] = 'Кемеровская область'

        #if 'charged_with' in self.data.columns and 'sentenced_under' in self.data.columns:
        #    for phase in ['charged_with', 'sentenced_under']:
        #        for element in ['article', 'part', 'clause']:
        #            self.data[phase + '_' + element] = pd.Series([pd.NA]*self.data.shape[0], dtype='str')
        charged_with_present = 'charged_with' in self.data.columns
        sentenced_under_present = 'sentenced_under' in self.data.columns
        for ids in self.data.index.values:
            #if ids == 54:
            #   breakpoint()
            if charged_with_present:
                charged_with_dict = self.get_elements(self.data.loc[ids, 'charged_with'])
                for key in charged_with_dict:
                    if charged_with_dict[key] != '':
                        self.res_data.loc[ids, 'charged_with' + '_' + key] = charged_with_dict[key]

            if sentenced_under_present:
                sentenced_under_dict = self.get_elements(self.data.loc[ids, 'sentenced_under'])
                for key in sentenced_under_dict:
                    if sentenced_under_dict[key] != '':
                        self.res_data.loc[ids, 'sentenced_under' + '_' + key] = sentenced_under_dict[key]

            #data['charged_with_article'] = data['charged_with'].apply(get_articles)
            #data['sentenced_under_article'] = data['sentenced_under'].apply(get_articles)

            #data['article'] = data['article'].str.replace(";$", "", regex=True).str.replace(
            #    "[Сс]т\.", "Статья", regex=True).str.replace("[Чч]\.", "часть", regex=True).str.replace(
            #    "(?<=\d),", "", regex=True)

        self.res_data["sole_charged_with"] = [False if pd.isnull(i) or ";" in i else True
                                              for i in self.res_data['charged_with_article']]
        self.res_data["sole_sentenced_under"] = [False if pd.isnull(i) or ";" in i else True
                                                 for i in self.res_data['sentenced_under_article']]
        if 'defendant' in self.data.columns:
            self.res_data["solo_defendant"] = [False if pd.isnull(i) or "," in i else True
                                               for i in self.data["defendant"]]
        if 'doc_type' in self.data.columns and sum(pd.isnull(self.data['doc_type'])) != self.data.shape[0]:
            self.res_data['sentence_bin'] = self.data['doc_type'].str.contains('приговор',
                                                                               regex=True, flags=re.IGNORECASE)

        #data["charged_with_part"] = np.NaN
        #data["sentenced_under_part"] = np.NaN
        #pat = f"статья {article} часть "
        #for i in data['article'].unique():
        #    if ";" not in i and article in i and "часть" in i.lower():
        #        try:
        #            data.loc[data['article'] == i, "charge_part"] = int(i[i.lower().index(pat) + len(pat)])
        #        except ValueError:
        #            print(i)
        #return self.data

    def get_elements(self, txt):
        elements = {'article': '', 'part': '', 'clause': ''}
        if pd.isnull(txt):
            return elements
        txt = txt.split('; ')
        for art in txt:
            last_article_match = regex.search(r'(\d{2,3})(?:\.\d)?$', art)
            if last_article_match is not None and int(last_article_match.group(1)) >= 105:
                elements['article'] = self.add_element(elements['article'], last_article_match.group(0))
                #if len(articles) == 0:
                #    articles += last_article_match.group(0)
                #else:
                #    articles += '; ' + last_article_match.group(0)

                last_part_match = regex.search(r'(?<=ч. )\d(,\d)*(?= ст. ' + last_article_match.group(0) + r')', art)
                if last_part_match is not None:
                    elements['part'] = self.add_element(elements['part'],
                                                        last_part_match.group(0).replace(',', '; '))

                    last_clause_match = regex.search(r'(?<=п. )\w(,\w)*(?= ч. ' + last_part_match.group(0) +
                                                     ' ст. ' + last_article_match.group(0) + r')', art)
                    if last_clause_match is not None:
                        elements['clause'] = self.add_element(elements['clause'],
                                                              last_clause_match.group(0).replace(',', '; '))

        return elements

    @staticmethod
    def add_element(string, element, separator='; '):
        if len(string) == 0:
            string += element
        else:
            string += separator + element
        return string
