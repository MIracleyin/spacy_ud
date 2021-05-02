#!/usr/bin/env python
# -*- coding: utf-8 -*-
# !@Time    : 2021/4/30 下午8:29
# !@Author  : miracleyin @email: miracleyin@live.com
# !@File    : utils.py

# 阴阳性可能的值  'FEM', 'MASC', 'UNK'.
# 辅助功能均是在该进mention，这里会大量使用到tokens的内容，使用from_id构建起来
relative_pronouns = ["qui", "que", "qu'", "quoi", "où", "dont", "lequel", "laquelle", "lesquels", "lesquelles"]
reflexive_pronouns = ["me", "m'", "moi", "te", "t'", "toi", "se", "s'", "lui", "elle", "soi", "nous", "vous", "eux",
                      "elles"]  # Remarque : les pronoms réflexifs ne sont pas annotés comme entités dans le corpus (à vérifier). Autre remarque : la forme ne suffit pas toujours à déterminer qu'un token est un pronom réflexif.
personnal_pronouns = {
    'FIRST': ["je", "-je", "j'", "me", "m'", "moi", "-moi", "on", "-on", "nous", "nous"],
    'SEC': ["tu", "-tu", "te", "t'", "toi", "-toi", "vous", "-vous"],
    # 'THIRD': [],
}


def determine_gender(mention, tokens):
    # On commence par le cas spécial d'un pronom possessif. On s'intéresse alors au genre de l'entité possédante. Celui-ci n'est pas marqué en français.
    # 我们从自反代词(如下)的特殊情况开始。然后，我们对相应的实体的性别进行标注。这在法语中没有标注。

    # UNK : 不确定的内容
    # 如果mention的from to相同 且from出现在 xxx 中 那么是 unk的
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
                                                           "notre", "nos", "votre", "vos", "leur",
                                                           "leurs"])): return "UNK";

    # 阴性
    # 如果mention的from 在 xxx 那么是 FEM 的
    if (tokens[mention['from_id']]['form'].lower() in ["ma", "ta", "sa", "la", "une", "sa", "cette", "celle", "elle",
                                                       "-elle", "elles", "-elles", "chacune", "laquelle",
                                                       "lesquelles"]): return 'FEM'
    # 阳性
    # 如果mention的from 在 xxx 那么是 MASC
    if (tokens[mention['from_id']]['form'].lower() in ["mon", "ton", "son", "le", "un", "son", "du", "ce", "celui",
                                                       "il", "-il", "lui", "lequel"]): return 'MASC'
    # 此外 则视为 unk
    return 'UNK'


#
# 判断两个提到的词是否有匹配的阴阳性
def gender_match(mention, other_mention):
    if ((mention['gender'] == 'UNK') or (other_mention['gender'] == 'UNK')): return True
    return (mention['gender'] == other_mention['gender'])


# 单复数可能的值'SING', 'PLUR', 'UNK'.
def determine_number(mention, tokens):
    # On commence par le cas spécial d'un pronom possessif. On s'intéresse alors au nombre de l'entité possédante.
    # 我们从自反代词(如下)的特殊情况开始。然后，我们对其实体的数量进行标记

    # 单数
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["mon", "ma", "mes", "ton", "ta", "tes", "son", "sa",
                                                           "ses"])): return 'SING'

    # 复数
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["notre", "nos", "votre", "vos", "leur",
                                                           "leurs"])): return 'PLUR'

    # 单数
    if (tokens[mention['from_id']]['form'].lower() in ["mon", "ma", "ton", "ta", "son", "sa", "notre", "votre", "leur",
                                                       "le", "la", "l'", "un", "une", "ce", "cette", "celle", "celui",
                                                       "c'", "je", "j'", "-je", "moi", "-moi", "m'", "tu", "-tu", "toi",
                                                       "t'", "il", "-il", "elle", "-elle", "lui", "soi", "au", "chacun",
                                                       "chacune", "chaque", "cela", "ça", "du", "laquelle", "lequel",
                                                       "quelque", "tout"]): return 'SING'
    # 复数
    if (tokens[mention['from_id']]['form'].lower() in ["mes", "tes", "ses", "nos", "vos", "leurs", "les", "des", "ces",
                                                       "nous", "-nous", "vous", "-vous", "ils", "-ils", "elles",
                                                       "-elles", "eux", "on", "aux", "des", "lesquels", "lesquelles",
                                                       "quelques", "certains", "tous", "toutes",
                                                       "plusieurs"]): return 'PLUR'

    if ((tokens[mention['from_id']]['pos'] == "NUM") and (
            tokens[mention['from_id']]['form'].lower() not in ["zero", "un"])): return 'PLUR'
    if ((mention['to_id'] >= (mention['from_id'] + 1)) and (
            tokens[mention['from_id']]['form'].lower() == 'de')): return 'SING' if (
            tokens[mention['from_id'] + 1]['form'] == 'la') else 'PLUR'
    if ('et' in [tokens[i]['form'] for i in range((mention['from_id'] + 1), mention['to_id'])]): return 'PLUR'
    if ((mention['from_id'] == mention['to_id']) and (tokens[mention['from_id']]['pos'] == "PROPN")): return 'SING'

    # for i in range(mention['from_id'], (mention['to_id'] + 1)): print(tokens[i])
    # input(mention['text'])
    return 'UNK'


# 判断两个mentions的数字是否匹配。
def number_match(mention, other_mention):
    if ((mention['number'] == 'UNK') or (other_mention['number'] == 'UNK')): return True
    return (mention['number'] == other_mention['number'])


# 不同人称的值 'FIRST', 'SEC', 'THIRD'.
def determine_person(mention, tokens):
    # 我们从自反代词(如下)的特殊情况开始。然后，我们对其实体的数量进行标注
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["mon", "ma", "mes", "notre", "nos"])): return "FIRST"
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["ton", "ta", "tes", "votre", "vos"])): return "SEC"
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["son", "sa", "ses", "leur", "leurs"])): return "THIRD"

    # 人称代词的情况
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["je", "j'", "-je", "me", "moi", "-moi", "m'", "nous",
                                                           "-nous", "on"])): return "FIRST"
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["tu", "-tu", "te", "toi", "-toi", "t'", "vous",
                                                           "-vous"])): return "SEC"
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["il", "-il", "elle", "-elle", "lui", "ils",
                                                           "elles"])): return "THIRD"

    return 'THIRD'


# 判断两个提及的人是否匹配
def person_match(mention, other_mention):
    # 在mentions来自不同句子的情况下，不加任何约束，因为它们可以用不同人所发出。
    if (mention['sentence_id'] != other_mention['sentence_id']): return True
    return (mention['person'] == other_mention['person'])


# 表示一个实体是否应该被系统完全忽略
def ignore(mention, tokens):
    if (mention['from_id'] != mention['to_id']): return False
    # if(determine_person(mention) != "THIRD"): return True ## 忽略所有以第一和第二人称表达的词/实体

    token = tokens[mention['from_id']]

    if (token['pos'] == "VERB"): return True  ## 忽视被注释为实体的动词
    if ((token['pos'] == "PRON") and (
            token['form'].lower() in ["rien"] + relative_pronouns + ["y", "en", "ce", "c'", "cela"])): return True

    return False


# 指出是否应该以回指的方式解决提及到的词/实体。
# 那些没有被解决的将会产生一个新的指代chains
def should_be_resolved(mention, tokens):
    if (mention['from_id'] != mention['to_id']): return False  ## 只有单一tokens会消除

    token = tokens[mention['from_id']]

    if (determine_person(mention, tokens) != "THIRD"): return False  # # 只有以第三人称提到的实体才会被消除
    if ((token['pos'] == "PRON") and (
            token['form'].lower() not in ["chacun", "chacune"])): return True  ## 所有的代名词都将被消除，除了这里列出的那些
    if ((token['pos'] == 'DET') and (token['dep_label'] == "poss")): return True

    return False  # Nothing else will be resolved.


def compute_salience_factors(mention, tokens, sentence, anaphora_id=0):
    """
    处理一句话
    :
    :param mention:
    :param tokens:
    :return:
    """
    values = {'sentence_recency': 0,
              'suject_emphasis': 0,
              'existential_emphasis': 0,
              'accusative_emphasis': 0,
              'indirect_object_emphasis': 0,
              'non_adverbial_emphasis': 0,
              'head_noun_emphasis': 0,
              'parallel': 0,
              'cataphora': 0
              }
    indef = ['un', 'une', 'des']
    partitive = ['du', 'de la', 'de l', 'des']
    # if mention['from_id'] == mention['to_id']:
    # Sentence recency = 100 pts
    values['sentence_recency'] += 100
    #####################################
    # 判断mention的各种熟悉即可
    # 主语 Subject emphasis = 80 pts
    if tokens[mention['from_id'] - 1]['dep_label'] == 'nsubj':
        values['suject_emphasis'] += 80

    # 存在词 Existential emphasis 70 pts
    if tokens[mention['from_id'] - 1]['form'] in indef or tokens[mention['from_id'] - 1]['form'] in partitive:
        values['existential_emphasis'] += 70

    # 直接宾语Accusative (direct object) emphasis = 50 pts
    if tokens[mention['from_id'] - 1]['dep_label'] == 'obj':
        values['accusative_emphasis'] += 50

    # 间接宾语 Indirect object and oblique complement emphasis = 40 pts
    if tokens[mention['from_id'] - 1]['dep_label'] == 'iobj' or tokens[mention['from_id'] - 1]['dep_label'] == 'obl:arg':
        values['indirect_object_emphasis'] += 40

    # 头部名词 Head noun emphasis = 80 pts
    if tokens[mention['from_id'] - 1]['dep_label'] != 'nmod':
        values['head_noun_emphasis'] += 80
    ####################################
    # 需要结合根据句子的属性来判断
    # Parallelism
    # values['parallel'] += 35
    for token in sentence['tokens']:
        if token['form'] in [".", "?"]:
            sym_pos = token['id']
    pre_sentence_mention = []
    post_sentence_mention = []
    for mention in sentence['mentions']:
        # 如果mention的尾端小于逗号，那么在前半部分，反之在后半部分
        if mention['to_id'] < sym_pos:
            pre_sentence_mention.append(mention)
        if mention['from_id'] > sym_pos:
            post_sentence_mention.append(mention)
    for mention in pre_sentence_mention:
        # 发现是副词就break 否则计算
        # 如何mention长度不为1 那么是否要遍历 from_id to_id
        if tokens[mention['from_id'] - 1]['dep_label'] in ["advcl", "advmod"]: # 具体调整一下就好
            break
        elif tokens[mention['from_id'] - 1]['dep_label']  in ["nsubj", "nsubjpass"]:
            values['parallel'] += 35
    for mention in post_sentence_mention:
        if tokens[mention['from_id'] - 1]['dep_label'] in ["advcl", "advmod"]: # 具体调整一下就好
            break
        elif tokens[mention['from_id'] - 1]['dep_label']  in ["nsubj", "nsubjpass"]:
            values['parallel'] += 35
    # 非副词 Non-adverbial emphasis = 50 pts
    # values['non_adverbial_emphasis'] += 50
    # 就是一个句子里, 把 被逗号隔开的副词短语部分的词排除 剩下的词每个➕50分,
    # 例如 in the car of Sabine, I found my money .
    # 这个句子里in the car of Sabine被逗号隔开 且它是副词短语 了,
    # 然后这段里的名词/代词在 判断非副词时 要被舍弃;
    # 而其他的所有名词/代词(如这句子里的[I], [money] )每个+50分
    for token in sentence['tokens']:
        if token['form'] == ",":
            dot_pos = token['id']
    pre_mention = []
    post_mention = []
    for mention in sentence['mentions']:
        # 如果mention的尾端小于逗号，那么在前半部分，反之在后半部分
        if mention['to_id'] < dot_pos:
            pre_mention.append(mention)
        if mention['from_id'] > dot_pos:
            post_mention.append(mention)
    for mention in pre_mention:
        # 发现是副词就break 否则计算
        # 如何mention长度不为1 那么是否要遍历 from_id to_id
        if tokens[mention['from_id'] - 1]['dep_label'] in ["advcl", "advmod"]: # 具体调整一下就好
            break
        elif tokens[mention['from_id'] - 1]['dep_label']  in ["nsubj", "nsubjpass"]:
            values['non_adverbial_emphasis'] += 50
    for mention in post_mention:
        if tokens[mention['from_id'] - 1]['dep_label'] in ["advcl", "advmod"]: # 具体调整一下就好
            break
        elif tokens[mention['from_id'] - 1]['dep_label']  in ["nsubj", "nsubjpass"]:
            values['non_adverbial_emphasis'] += 50

    ####################################
    # Cataphora
    if mention['from_id'] > anaphora_id:
        values['cataphora'] -= 175

    # print(f"{mention['text']}, with id {mention['from_id']}  = {values}")
    return values
