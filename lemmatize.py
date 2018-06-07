from functools import lru_cache
import pymorphy2
from nltk import word_tokenize, sent_tokenize, bigrams, trigrams
import re

morph = pymorphy2.MorphAnalyzer()


def special_match(strg, search=re.compile(r'[^а-яА-Яёa-zA-Z0-9\.]').search):
    return strg


def sanitize_some_text(text):
#     clean = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', r'', text)
    clean = text
#     clean = re.sub(r"[`#\"\]\[%«»\+@·*~$&”]+", " ", clean)
#     clean = re.sub(r'\n', r' ', clean)
#     clean = re.sub(r'\s+', r' ', clean)
    return clean


def my_sent_tokenize(text):
    text = re.sub(r'…', r'.', text)
    text = re.sub(r'\.{2,3}', r'.', text)
    sents = sent_tokenize(text)
    return sents


def my_word_tokenize(sent):
    words = word_tokenize(sent)
    out = []

    for word in words:
        if '/' in word:
            tokens = word.split('/')
            if len(tokens[0]) == 1:
                pass
            for token in tokens:
                out.append(token)
        else:
            if len(word) >= 2 and word[-2:] == '..':
                out.append(word[:-2])
                out.append('..')
            elif len(word) >= 1 and word[-1] == '…':
                out.append(word[:-1])
                out.append('...')
            elif len(word) >= 1 and word[0] == '…':
                out.append('...')
                out.append(word[1:])
            else:
                out.append(word)

        if len(word) >= 1 and word[0] == '-':
            word = word[1:]
        if len(word) >= 1 and word[-1] == '-':
            word = word[:-1]
        if set(word) == {'-'}:
            return
    return out


@lru_cache(maxsize=100000)
def process_bigrams(bigram):
    f_gram, s_gram = bigram
    f = morph.parse(f_gram)[0]
    s = morph.parse(s_gram)[0]

    if f.tag.POS in ['PREP', 'NPRO'] and s.tag.POS in ['PREP', 'NPRO']:
        return

    if f.tag.POS == 'PREP' and s.tag.POS in ['VERB', 'INFN']:
        return

    if f_gram == 'smiling' or s_gram == 'smiling':
        return
    single_word = f_gram + ' ' + s_gram
    bgrm = morph.parse(single_word)[0]

    if bgrm.tag.POS not in ['NOUN', 'VERB', 'INFN',
                            'PREP', 'NPRO', 'GRND',
                            'ADVB', 'ADJS'] and bgrm.tag.POS is not None:
        return

    if f.tag.POS == 'NOUN' and s.tag.POS == 'NOUN':
        return f.normal_form + ' ' + s_gram

    if f_gram[-1] == '.' and s.tag.POS == 'NOUN':
        return f_gram + ' ' + s.normal_form

    return f_gram + ' ' + s_gram


@lru_cache(maxsize=100000)
def process_trigrams(trigram):
    if 'smiling' in trigram:
        return

    return ' '.join(trigram)


def delete_sublist(l, subl, delim=';'):
    while True:
        i = 0
        flag = False
        for i in range(0, len(l) - len(subl)):
            if l[i:i+len(subl)] == subl:
                flag = True
                break
        if flag:
            if delim == ';':
                l = l[:i] + [';'] + l[i + len(subl):]
            elif delim == '':
                l = l[:i] + l[i + len(subl):]
            elif delim == '_':
                pr = '_'.join(subl)
                l = l[:i] + [pr] + l[i + len(subl):]
        else:
            break

    return l


def remove_conj_prcl_prep(lemmas, bigram=True):
    with open('pos/conj.txt', 'r') as conj_f:
        conjs = conj_f.read().split('\n')
    with open('pos/prcl.txt', 'r') as prcl_f:
        prcls = prcl_f.read().split('\n')
    with open('pos/advb.txt', 'r') as advb_f:
        advbs = advb_f.read().split('\n')
    with open('pos/prep.txt', 'r') as prep_f:
        preps = prep_f.read().split('\n')

    for conj in conjs:
        conj_list = conj.split(' ')
        lemmas = delete_sublist(lemmas, conj_list, delim=';')

    for prcl in prcls:
        prcl_list = prcl.split(' ')
        lemmas = delete_sublist(lemmas, prcl_list, delim='')

    for advb in advbs:
        advb_list = advb.split(' ')
        lemmas = delete_sublist(lemmas, advb_list, delim='')

    if bigram:
        for prep in preps:
            prep_list = prep.split(' ')
            lemmas = delete_sublist(lemmas, prep_list, delim='_')
    else:
        for prep in preps:
            prep_list = prep.split(' ')
            lemmas = delete_sublist(lemmas, prep_list, delim='')

    for i in range(len(lemmas)):
        p = morph.parse(lemmas[i])[0]
        if p.tag.POS == 'CONJ' and bigram:
            lemmas[i] = ';'
        elif bigram and p.tag.POS in ['NOUN', 'VERB', 'INFN', 'PREP', 'NPRO'] or p.tag.POS is None:
            pass
        elif not bigram and p.tag.POS in ['NOUN', 'VERB', 'INFN'] or p.tag.POS is None:
            pass
        else:
            lemmas[i] = ''

    return lemmas


def lemmatize_bigrams(text):
    text = sanitize_some_text(text)
    words = my_word_tokenize(text)
    lemmas = [lemmatize(word) for word in words if lemmatize(word) is not None]
    lemmas = remove_conj_prcl_prep(lemmas, bigram=True)
    s = ' '.join(lemmas)
    s = re.sub(r'\s+', ' ', s)

    grms = []
    for part in s.split(';'):
        w = [elem for elem in part.split(' ') if elem != ""]
        grms.extend([process_bigrams(elem) for elem in list(bigrams(w)) if process_bigrams(elem) != None])
        grms.extend([process_trigrams(elem) for elem in list(trigrams(w)) if process_trigrams(elem) != None])
    return grms


@lru_cache(maxsize=100000)
def lemmatize(word):
    p = morph.parse(word)[0]
    tags = ['Surn', 'Name', 'Patr', 'Orgn', 'Trad', 'Geox', 'Orgn']

    for tag in tags:
        if tag in p.tag:
            return word + '_' + tag
    if word in ['.', ',']:
        return word

    if word in ['...', '..', '!', '/', '>', '_', '--'
                '?', ':', ';', '(', ')', '…']:
#             or p.tag.POS == 'CONJ':
        return ';'

#     if is_number(word):
#         return

#     if '.' in word[1:-1]:
#         words = word.split('.')
#         if len(words[0]) == 1 and len(words[1]) == 1:
#             return

#         if lemmatize(words[0]) is not None and lemmatize(words[1]) is not None:
#             return lemmatize(words[0]) + '. ' + lemmatize(words[1])
#         elif lemmatize(words[0]) is None and lemmatize(words[1]) is not None:
#             return lemmatize(words[1])
#         elif lemmatize(words[0]) is not None and lemmatize(words[1]) is None:
#             return lemmatize(words[0])
#         else:
#             return

#     if len(word) == 1 and (p.tag.POS == 'NOUN' or p.tag.POS is None):
#         return

    if set(word) & {'\\', '=', '|', 'є', '…', '^', 'ψ', '⊹', 'σ', 'τ', 'έ', 'χ', 
                    'ν', 'η', 'á', '®', 'џ', '№' }:
        return

    # удаляем русские окончания у англоязычных слов
    if word != '':
        parsed_word = morph.parse(word)[0]
        if parsed_word.normal_form[-1] == '\'':
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

    return word


def lemmatize_words(text):
    words = word_tokenize(text)
    lemmas = [lemmatize(word) for word in words if lemmatize(word) is not None]
    # lemmas = remove_conj_prcl_prep(lemmas, bigram=False)

    s = ' '.join(lemmas)
    s = re.sub(r'slightly_smiling_face', '', s)
    s = re.sub(r'\s+', ' ', s)
    return [elem for elem in s.split(' ') if elem != '']
    # out_lemmas = [morph.parse(elem)[0].normal_form for elem in s.split(' ') if elem != '']
    # return out_lemmas
