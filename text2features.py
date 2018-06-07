from copy import deepcopy
import pprint
import json

import pymorphy2
from nltk import sent_tokenize
import treetaggerwrapper
from treetaggerwrapper import Tag
from tqdm import tqdm
# from nltk.stem import SnowballStemmer
import textdistance

from tokenizing import lemmatize_words, is_english

morph = pymorphy2.MorphAnalyzer()
# stemmer = SnowballStemmer('russian')
ftrs = ['CATEGORY', 'Form', 'Gender', 'Number', 'Person', 'Tense', 'Voice', 'Degree', 'Type']

with open('data/pos_translate.json', encoding='utf-8') as f:
    pos_tag_translate = json.load(f)

    
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class NormalizeError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression):
        self.expression = expression
        self.message = 'Normalization is incorrect. Need to add special cases.'
        super().__init__(self.message, self.expression)
        
class TokenError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression):
        self.expression = expression
        self.message = 'Token is incorrect. Need to fix preprocessing.'
        super().__init__(self.message, self.expression)

class CollectFeatures:
    def word2features(self, sent, named_entities):
        tokens = self.pos_tagging(sent, named_entities)
        
        tokens_features = []
        labels = []

        for i in range(len(tokens)):
            token = tokens[i]

            try:
#                 stemmed = stemmer.stem(token.word)
                features = {
#                     'bias': 1.0,
#                     'normal_form': token.lemma,
#                     'word.lower()': token.word.lower(),
#                     'postag': token.pos,
                    'word.isupper()': token.word.isupper(),
                    'word.istitle()': token.word.istitle(),
                    'word.isdigit()': token.word.isdigit(),
#                     'ending': token.word[len(stemmed):],
                    'is_english': is_english(token.word)
                }
                if token.pos in pos_tag_translate:
                    pos_tag_translated = pos_tag_translate[token.pos]
                    for feature in pos_tag_translated:
                        features[feature] = pos_tag_translated[feature]
                else:
                    lbls = list(pos_tag_translate.keys())
                    min_lbl = lbls[0]
                    min_dist = textdistance.levenshtein.distance(token.pos, min_lbl)

                    for lbl in lbls[1:]:
                        if textdistance.levenshtein.distance(token.pos, lbl) < min_dist:
                            min_dist = textdistance.levenshtein.distance(token.pos, lbl)
                            min_lbl = lbl
                        if min_dist == 1:
                            break

                    pos_tag_translated = pos_tag_translate[min_lbl]
                    for feature in pos_tag_translated: #ftrs:
                        if pos_tag_translated[feature] not in ['', '-', '-']:
                            features[feature] = pos_tag_translated[feature]
                
            except AttributeError:
                raise TokenError((token, sent, tokens))

            if i > 0:
                token1 = tokens[i - 1]
                try:
#                     stemmed = stemmer.stem(token1.word)
                    features.update({
#                         '-1:normal_form': token1.lemma,
                        '-1:word.istitle()': token1.word.istitle(),
                        '-1:word.isupper()': token1.word.isupper(),
                        '-1:word.isdigit()': token1.word.isdigit(),
#                         '-1:ending': token1.word[len(stemmed):],
                        '-1:is_english': is_english(token1.word)
                    })
                    if token1.pos in pos_tag_translate:
                        pos_tag_translated = pos_tag_translate[token1.pos]
                        for feature in pos_tag_translated:
                            features['-1:' + feature] = pos_tag_translated[feature]
                    else:
                        lbls = list(pos_tag_translate.keys())
                        min_lbl = lbls[0]
                        min_dist = textdistance.levenshtein.distance(token1.pos, min_lbl)
                        
                        for lbl in lbls[1:]:
                            if textdistance.levenshtein.distance(token1.pos, lbl) < min_dist:
                                min_dist = textdistance.levenshtein.distance(token1.pos, lbl)
                                min_lbl = lbl
                            if min_dist == 1:
                                break
                        
                        pos_tag_translated = pos_tag_translate[min_lbl]
                        for feature in pos_tag_translated: #ftrs:
                            if pos_tag_translated[feature] not in ['', '-', '-']:
                                features['-1:' + feature] = pos_tag_translated[feature]
                        
                        
                except AttributeError:
                    raise TokenError((token, sent, tokens))
            
#             if i == 0:
#                 features['BOS'] = True

            if i > 1:
                token1 = tokens[i - 2]
                try:
#                     stemmed = stemmer.stem(token1.word)
                    features.update({
#                         '-2:normal_form': token1.lemma,
                        '-2:word.istitle()': token1.word.istitle(),
                        '-2:word.isupper()': token1.word.isupper(),
                        '-2:word.isdigit()': token1.word.isdigit(),
#                         '-2:ending': token1.word[len(stemmed):],
                        '-2:is_english': is_english(token1.word)
                    })
                    if token1.pos in pos_tag_translate:
                        pos_tag_translated = pos_tag_translate[token1.pos]
                        for feature in pos_tag_translated:
                            features['-2:' + feature] = pos_tag_translated[feature]
                    else:
                        lbls = list(pos_tag_translate.keys())
                        min_lbl = lbls[0]
                        min_dist = textdistance.levenshtein.distance(token1.pos, min_lbl)
                        
                        for lbl in lbls[1:]:
                            if textdistance.levenshtein.distance(token1.pos, lbl) < min_dist:
                                min_dist = textdistance.levenshtein.distance(token1.pos, lbl)
                                min_lbl = lbl
                            if min_dist == 1:
                                break
                        
                        pos_tag_translated = pos_tag_translate[min_lbl]
                        for feature in pos_tag_translated: #ftrs:
                            if pos_tag_translated[feature] not in ['', '-', '-']:
                                features['-2:' + feature] = pos_tag_translated[feature]              
                    
                except AttributeError:
                    raise TokenError((token, sent, tokens))
            if i == len(tokens) - 1:
                features['EOS'] = True

            label = ''

            if len(named_entities['Name']) > 0 and \
                    token.lemma.lower() == named_entities['Name'][0].lower():

                label = 'NAM'
                named_entities['Name'].pop(0)

            elif len(named_entities['Surname']) > 0 and \
                    token.lemma.lower() == named_entities['Surname'][0].lower():

                label = 'SUR'
                named_entities['Surname'].pop(0)

            elif len(named_entities['Location']) > 0 and \
                    token.lemma.lower() == named_entities['Location'][0].lower():
                label = 'LOC'
                named_entities['Location'].pop(0)

            else:
                label = 'O'

            tokens_features.append(features)
            labels.append(label)

        return tokens_features, labels
    
    def pos_tagging(self, text, named_entities=None):

        tags = self.tagger.tag_text(text)
        tags = treetaggerwrapper.make_tags(tags)

        normalize_dict = {
            'утрехт': 'Утрехт',
            'мовчан': 'Мовчан',
            'максимов': 'Максимов',
            'нью-йорк': 'Нью-Йорк',
            'нижнего_новгорода': 'Нижний_Новгород',
            'нижнем_новгороде': 'Нижний_Новгород',
            'дашков': 'Дашки',
            'приокского': 'Приокский',
            'арк': 'Аркадий',
            'санкт-петербург': 'Санкт-Петербург',
            'арсений': 'Арсений',
            'жеглов': 'Жеглов',
            'анахайм': 'Анахайм',
            'долгопрудн': 'Долгопрудный',
            'артем': 'Артём',
            'данил': 'Данил',
            'толик': 'Толик',
            'лазаде': 'Лазада'
        }

        fixed_tags = []

        if named_entities is None:
            named_entities = {}

        for tag in tags:
            is_term = False

            parsed_tag = morph.parse(tag.word)[0]

            for term in normalize_dict:
                if tag.word[:len(term)].lower() == term:
                    word = normalize_dict[term] + tag.word[len(term):]
                    lemma = normalize_dict[term].lower()
                    is_term = True
                    fixed_tags.append(Tag(word, tag.pos, lemma))
                    break
    
            if not is_term and tag.word.upper() in named_entities.get('Surname', []):
                fixed_tags.append(Tag(tag.word, tag.pos, tag.word.lower()))
            elif not is_term and parsed_tag.score == 1.0:
                fixed_tags.append(Tag(tag.word.lower(), tag.pos, parsed_tag.normal_form))
            elif not is_term:
                fixed_tags.append(tag)

        return fixed_tags
    
    def get_data(self):
        return self.processed_data, self.labeling
    
    def __init__(self, data):
        self.processed_data = []
        self.labeling = []
        nes = ['Name', 'Surname', 'Location']
        
        counter = 0
        self.tagger = treetaggerwrapper.TreeTagger(TAGLANG='ru')
        
        # 890 : 920 зависает
        
        for el in tqdm(data[:890] + data[920:]):
            elem = deepcopy(el)
            lemmas = lemmatize_words(elem['text'])

            elem['text'] = ' '.join(lemmas)
            sents = sent_tokenize(elem['text'])

            for sent in sents:
                tokens, labels = self.word2features(sent, elem)
                self.processed_data.append(tokens)
                self.labeling.append(labels)

            for ne in nes:
                if elem[ne] != []:
                    raise NormalizeError((elem[ne], elem['text'], self.pos_tagging(elem['text'])))
                    
            counter += 1
            
import json
import io
collecting = CollectFeatures(data)
processed_data, labeling = collecting.get_data()

with io.open('data/x_no_normal_forms.json', 'w', encoding='utf8') as f:
    f.write(json.dumps(processed_data, indent=4, ensure_ascii=False))
    
with io.open('data/y_no_normal_forms.json', 'w', encoding='utf8') as f:
    f.write(json.dumps(labeling, indent=4, ensure_ascii=False))