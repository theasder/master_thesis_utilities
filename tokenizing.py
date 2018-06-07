# -*- coding: utf-8 -*-

import pymorphy2
from nltk import word_tokenize, sent_tokenize, bigrams, trigrams
from nltk.tokenize import MWETokenizer
from urlextract import URLExtract

import re
from functools import lru_cache

def create_tokenizer():
    with open('mwe-prep-ru-final.txt', 'r') as f:
        lines = f.read().split('\n')
    mwe_list = [tuple(line.split(' ')) for line in lines if 'lemma' not in line and line != '']
    
    with open('mwes-prep-en.html', 'r') as f:
        lines = f.read().split('\n')   
    mwe_list_en = []

    for line in lines:
        if '</b>:' in line:
            mwe_list_en.append(tuple(line.split('</b>: ')[1].split(' <td align=right>')[0].split(' ')))
    
    mwe_list.extend(mwe_list_en)
    return MWETokenizer(mwe_list)
    
def is_english(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        if s in ['(', ')', '.', ';', '--', '"', ',', '~', '-']:
            return False
        return True

morph = pymorphy2.MorphAnalyzer()
extractor = URLExtract()
tokenizer = create_tokenizer()

@lru_cache(maxsize=100000)
def lemmatize(word, add_flag=True):
    if word[0] == '@':
        return 'пользователь'
    elif word[0] == '#':
        return 'тег'
    
#     normalize_dict = {
#         'утрехт': 'Утрехт'
#     }
    
#     for term in normalize_dict:
#         if word[:len(term)].lower() == term:
#             return normalize_dict[term]
    
    p = morph.parse(word)[0]
    tags = ['Surn', 'Name', 'Patr', 'Orgn', 'Trad', 'Geox', 'Orgn']

    if add_flag:
        for tag in tags:
            if tag in p.tag:
                return word + '_' + tag
            
    if word in ['.', ',', '(', ')', '/', '&', ':', ';', '!', '?']:
        return word
    
    if word in ['---', '--', '—', '–', '−', '-']:
        return '-'

    if word in ['...', '..', '…']:
        return '.'
    
    if word in ['>', '_']:
        return ';'

    if set(word) & {'\\', '=', '|', 'є', '…', '^', 'ψ', '⊹', 'σ', 'τ', 'έ', 'χ', 
                    'ν', 'η', 'á', '®', 'џ', '№' }:
        return

    # удаляем русские окончания у англоязычных слов
    if word != '':
        parsed_word = morph.parse(word)[0]
        if parsed_word.normal_form[-1] in ['\'']:
            word = parsed_word.normal_form[:-1]
            p = morph.parse(word)[0]
            if len(word) == 1 and (p.tag.POS == 'NOUN' or p.tag.POS is None):
                return

            return word

        modified_word = re.sub(r'-([а-яА-Я]{1,2})$', r'\'\1', word)

        parsed_word = morph.parse(modified_word)[0]
        if parsed_word.normal_form[-1] == '\'':
            word = parsed_word.normal_form[:-1]

            p = morph.parse(word)[0]
            if len(word) == 1 and (p.tag.POS == 'NOUN' or p.tag.POS is None):
                return

            return word
        if '-' in word[-3:]:
            return word[:word.rfind("-")]
        if '\'' in word[-3:]:
            return word[:word.rfind("'")]
    return word


def lemmatize_words(text, add_flag=False):
    text = re.sub(r'\n', r'. ', text)
    urls = extractor.find_urls(text)
    for url in urls:
        text = text.replace(url, 'url')
    text = re.sub(r':[\w_]+:', r'', text)
    text = re.sub(r'(\)|\(){2,}', r'.', text)
    text = re.sub(r'([\wа-яА-Яё]+)\.ру', r'\1_ру', text)
    text = re.sub(r'(\w+)\.(\W)', r'\1. \2', text)
    text = re.sub(r'([а-яА-ЯёЁ]+)\.([А-Я])', r'\1. \2', text)
    text = re.sub(r'(www\.)?\w+\.\w{2,3}', r'url', text)
    text = re.sub(r'Абу Даби', r'Абу-Даби', text)
    text = re.sub(r'Новогород', r'Новгород', text)
    text = re.sub(r'Калиниград', r'Калининград', text)
    
    words = word_tokenize(text)
    lemmas = tokenizer.tokenize([lemmatize(word, add_flag) for word in words 
                                 if lemmatize(word, add_flag) is not None])
    
    english_lemma = ''
    all_lemmas = []
    for i in range(len(lemmas)):
        if is_english(lemmas[i]) and english_lemma == '':
            english_lemma = lemmas[i]
        elif is_english(lemmas[i]) and english_lemma != '':
            english_lemma += '_' + lemmas[i]
        elif english_lemma != '':
            all_lemmas.append(english_lemma)
            all_lemmas.append(lemmas[i])
            english_lemma = ''
        else:
            all_lemmas.append(lemmas[i])
    
    # удаляем повторяющиеся друг за другом токены
    all_lemmas = [v for i, v in enumerate(all_lemmas) if i == 0 or v != all_lemmas[i - 1]]
    
    s = ' '.join(all_lemmas)
    s = re.sub(r'\s+', ' ', s)
    return [elem for elem in s.split(' ') if elem != '']