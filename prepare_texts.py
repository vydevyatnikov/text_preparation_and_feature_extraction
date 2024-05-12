import re


def deal_w_caps(text):
    matches = re.findall(r'\b[А-ЯЁ]{2,}', text)
    for match in matches:
        text = re.subn(match, match.capitalize(), text)[0]
    return text


def prepare_texts(data):
    data["texts"] = data.texts.str.replace("(\\r|\\t)", " ", regex=True)

    data["texts"] = data.texts.str.replace("(\\xa0)+", " ", regex=True).str.replace(
        "(\\x07|\\x0b)", " ", regex=True)

    # self.data["texts"] = self.data.texts.str.replace("\.\\n", ". ", regex=True).str.replace(
    #    "(?<![\.,:;]) *\\n", ". ", regex=True).str.replace("(?<=[\.,:;]) *\\n", " ", regex=True)

    # self.data["texts"] = self.data.texts.str.replace("\.\\n", ". ", regex=True).str.replace(
    #    "(?<![\.,:;]) \\n", ". ", regex=True).str.replace(
    #    "(?<![\.,:;] )\\n", ". ", regex=True).str.replace("(?<=[\.,:;]) *\\n", " ", regex=True)

    data["texts"] = data.texts.str.replace("(?<=[\.,:;]) *\\n", " ", regex=True).str.replace(
        "\.\\n", ". ", regex=True).str.replace("(?<![\.,:;]) *\\n", ". ", regex=True)

    data['texts'] = data.texts.str.replace(
        "Evaluation Only. Created with Aspose.Words. Copyright 2003-2024 Aspose Pty Ltd.", "").str.replace(
        'Created with an evaluation copy of Aspose.Words. To discover the full versions of our APIs please visit: https://products.aspose.com/words/',
        "")

    data["texts"] = data.texts.str.replace(" {2,}", " ", regex=True)
    data['texts'] = data['texts'].apply(deal_w_caps)
    # while True:
    # data['texts'] = data.texts.str.replace("([а-яё])(?=[А-ЯЁ])", " ", regex=True)
    return data
