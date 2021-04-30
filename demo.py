#!/usr/bin/env python
# -*- coding: utf-8 -*-
# !@Time    : 2021/4/30 10:22
# !@Author  : miracleyin @email: miracleyin@live.com
# !@file: demo.py
# !/usr/bin/env python
# -*- coding: utf-8 -*-
# !@Time    : 2021/4/30 10:19
# !@Author  : miracleyin @email: miracleyin@live.com
# !@file: demo.py

# !/usr/bin/env python
# coding: utf-8

# # 导入模块, 例子 + 测试spaCy
#
# 用法语解析模块加载SpaCy NLP库。
# 该模型 "fr_core_news_sm "使用了通用依存句法分析Universal Dependencies （UD）项目中的形态-句法和依赖性标签。
#
#

# In[ ]:


import spacy

model_name = "fr_core_news_sm"
try:
    nlp = spacy.load(model_name, disable=['ner'])
except:
    from spacy.cli import download

    download(model_name)
    nlp = spacy.load(model_name, disable=['ner'])

print("NLP pipeline:")
for i, (name, proc) in enumerate(nlp.pipeline):
    print(f'\n\ti : [{i}] : ', "\nname : ", name, "\nproc : ", proc)
pipeline = {name: proc for name, proc in nlp.pipeline}

tagger = pipeline['morphologizer'] if ('morphologizer' in pipeline) else nlp.tagger
parser = pipeline['parser'] if ('parser' in pipeline) else nlp.parser

# In[30]:


doc = nlp(
    "-- Elle a écrit un bon article, Sabine? -- Il est très bon. Je l'ai lu hier.")  # Crée un objet Doc et lui applique la chaîne de traitement.
print(f"Texte analysé: {doc.text}\n")
print("i", "text", "pos_", "dep_", "head", "head.i", "subtree\n")
for token in doc:
    print(token.i, "\t", token.text, "\t", token.pos_, "\t"
          , token.dep_, "\t", token.head, "\t", token.head.i
          , "\n : ", [t.text for t in token.subtree])

# In[ ]:


# # 下载 语料库Democrat

# In[25]:


import urllib
import urllib.request
import zipfile
import os

# In[26]:


# zipurl = "https://repository.ortolang.fr/api/content/export?&path=/democrat/5/&filename=democrat&scope=YW5vbnltb3Vz3"
# tmp = urllib.request.urlretrieve(zipurl)
# filename = tmp[0]
# print("filename : ", filename, "\n")
## 提取数据集 dataset
# with zipfile.ZipFile(filename, 'r') as zip_ref:
#    zip_ref.extractall(".", )
#
# base_name, ext = os.path.splitext(os.path.basename(zipurl))
# list(os.listdir("."))

# In[27]:


print(list(os.listdir("democrat")))
print(list(os.listdir("democrat/5")))
print(list(os.listdir("democrat/5/data")))

# 文本文件
print(list(os.listdir("democrat/5/data/xml")))
# 这个文件夹中包含注释的文件
print(list(os.listdir("democrat/5/data/xml-urs")))

# # 载入语料库 Chargement du corpus.

#
# 在用example.xml和example-urs.xml文件测试时，将debug_mode变量设为True。
#
# (实现了指代消解算法) 把这个变量设置为False，就可以在Democrat语料库上运行它。

# In[31]:


debug_mode = True

"""
os.getcwd()会返回绝对路径
os.curdir是返回当前路径，print出来会是个点
"""
# 加载数据
if (debug_mode):
    root_path = os.path.join(os.curdir)
    part_name = "exemple"

    text_path = os.path.join(root_path, f"{part_name}.xml")
    annotations_path = os.path.join(root_path, f"{part_name}-urs.xml")
else:
    root_path = os.path.join("democrat", "5", "data")
    part_name = "bouvardetpecuchet"

    text_path = os.path.join(root_path, "xml", f"{part_name}.xml")
    annotations_path = os.path.join(root_path, "xml-urs", f"{part_name}-urs.xml")

from lxml import etree  # 读取XML文件


# ## Chargement du texte (en tant que liste de tokens).

# In[32]:


# 用于删除XML标签中的名称空间的函数
def without_namespace(s):
    return s.split('}')[-1]


text_tree = etree.parse(text_path)

# 检查关于XML文件中books的信息
titleStmt_node = text_tree.getroot()[0][0][0]
assert (without_namespace(titleStmt_node.tag) == "titleStmt")
for child in titleStmt_node:
    tag = without_namespace(child.tag)
    if (tag in ["author", "title"]):
        # print("etree.tostring(child) : ",etree.tostring(child))
        print(f"\ntag+child.text : {tag}: {child.text}")

"""
etree.HTML():构造了一个XPath解析对象并对HTML文本进行自动修正。
etree.tostring()：输出修正后的结果，类型是bytes
"""

# 夹在文本 Loads the text.
sentences = []  # sentence的列表(每个元素都是一个字典);
text_node = text_tree.getroot()[1]
assert (without_namespace(text_node.tag) == "text")
token_id = 1  # 注意 : 在XML文件中, 每个tokens的下标都是从1开始的

for child in text_node:
    tag = without_namespace(child.tag)
    if (tag != 's'): continue
    s = child
    sentence_id = len(sentences)

    tokens = []
    for child in s:
        tag = without_namespace(child.tag)
        if (tag != 'w'): continue
        w = child

        assert (token_id == int(w.get('n')))

        token = {
            'id': token_id,  # 整型
            'sentence_id': sentence_id,  # 整型
        }

        for child in w:
            tag = without_namespace(child.tag)
            if (tag == "form"): token['form'] = child.text  # 字符串String

        tokens.append(token)
        token_id += 1

    sentence = {
        'id': sentence_id,  # 整型
        'tokens': tokens,  # tokens 列表(字典)
        'mentions': []  # mentions 列表 (之后会把列表填满)
    }

    sentences.append(sentence)

# 添加一个虚假标记(dummy token)，以便标记的id与标记的位置相对应。
tokens = [{'id': 0, 'sentence_id': None, 'form': 'DUMMY_TOKEN'}]
for sentence in sentences: tokens.extend(sentence['tokens'])

# 检查XML中的token ids是否是我们认为的那样
for i, token in enumerate(tokens): assert (token['id'] == i)

print(f"\n{len(sentences)} sentences")
print("sentence : ", sentence)
# 不计入虚假标记(dummy token)
print(f"\n{len(tokens) - 1} tokens")
print("tokens : ", tokens)

#
# ## 加载注释annotations（mentions 和 共指的chains）。

# In[33]:


for sentence in sentences: assert (sentence['mentions'] == []), "这个代码块已被执行了。为了避免冲突，请重新加载文本（以前的代码块）"

annotations_tree = etree.parse(annotations_path)

mentions = {}  # 从 ids (整型) 到 mentions (字典).
standOff_node = annotations_tree.getroot()[2]
annotation_node = standOff_node[1]
annotationGrp_node = annotation_node[0]
assert (annotationGrp_node.get('subtype') == "MENTION")
for child in annotationGrp_node:
    if (child.tag != "span"): continue

    from_id = int(child.get('from').split('_')[-1])  # span该跨度中的第一个token的下索引
    to_id = int(child.get('to').split('_')[-1])  # 该跨度中最后一个标记的索引。
    mention_id = int(child.get('id').split('-')[-1])  # 索引
    assert (child.get('id') == f"u-MENTION-{mention_id}")

    sentence_id = tokens[from_id]['sentence_id']
    text = ' '.join([token['form'] for token in tokens[from_id:(to_id + 1)]])

    # input(text)

    # 创建mention
    mention = {
        'id': mention_id,  # 整型
        'from_id': from_id,  # 整型
        'to_id': to_id,  # 整型
        'sentence_id': sentence_id,  # 整型
        'text': text,  # 字符串
    }
    sentences[sentence_id]['mentions'].append(mention)
    mentions[mention_id] = mention

print(f"{len(mentions)} mentions")  # ---------------------------------------------------------------------------------
print("mentions : ", mentions)

chains = {}  # 从 ids (整型类型) 到 chains (字典类型).
annotationGrp_node = annotation_node[1]
assert (annotationGrp_node.get('subtype') == "CHAINE")
for child in annotationGrp_node:
    if (child.tag != "link"): continue

    chain_id = int(child.get('id').split('-')[-1])  # chain的索引
    assert (child.get('id') == f"s-CHAINE-{chain_id}")
    mention_ids = [int(mention.split('-')[-1]) for mention in child.get('target').split()]  # span的索引
    assert (child.get('target') == ' '.join([f'#u-MENTION-{mention_id}' for mention_id in mention_ids]))

    # 创建chain，并把chain的引用加到对应的mentions中

    chain = {
        'id': chain_id,  # Integer
        'mentions': [mentions[mention_id] for mention_id in mention_ids],  # mentions列表
    }
    chain['mentions'].sort(key=(lambda mention: mention['to_id']))  # 确保列表是按照线性顺序排序的。
    for mention in chain['mentions']: mention['gold_chain'] = chain  # Chain
    chains[chain_id] = chain

print(
    f"{len(chains)} chains")  # ------------------------------------------------chains---------------------------------------

if (debug_mode):
    print()
    for i, sentence in enumerate(sentences):
        print(
            f"sentences[{i}]:")  # ---------------------------------------------------sentences{i}--------------------------------------
        for k, v in sentence.items(): print(f'\t{k}: {v}')

    print()
    for i, mention in enumerate(sentences[0]['mentions']):
        print(f"sentences[0]['mentions'][{i}]:")
        for k, v in mention.items(): print(f'\t{k}: {v}')

    print()
    for i, chain in chains.items():
        print(
            f"chains[{i}]:")  # ---------------------------------------------chains{i}-------------------------------------------
        for k, v in chain.items(): print(f'\t{k}: {v}')
else:
    print(
        "sentences[0]:")  # ------------------------------------sentences[0]------------------------------------------------
    for k, v in sentences[0].items(): print(f'\t{k}: {v}')

    print()
    print(
        "sentences[0]['mentions'][0]:")  # ----------------------sentences[0]['mentions'][0]---------------------------------------------
    for k, v in sentences[0]['mentions'][0].items(): print(f'\t{k}: {v}')

    print()
    print(
        "chains[1]:")  # --------------------------------chains[1]-----------------------------------------------------
    for k, v in chains[1].items(): print(f'\t{k}: {v}')


# ## 把SpaCy的形态-句法分析和句法分析的结果添加到该token中。

# In[34]:


# # 转换一些SpaCy不能很好处理的字符。
def aux(form):
    # return form
    # return "--" if(form == "—") else form
    return "–" if (form == "—") else form  # # 与表象相反，这不是字符


# 创建一个SpaCy文件，这是（形态）句法分析所必需的。
spacy_doc = spacy.tokens.Doc(nlp.vocab, words=[aux(token['form']) for token in tokens], spaces=None)
print(len(spacy_doc.text))
# print("spacy_doc.text : ",spacy_doc.text)
if ('tok2vec' in pipeline): spacy_doc = pipeline['tok2vec'](spacy_doc)

# The following makes sure SpaCy sees sentence boundaries where we know they are (otherwise SpaCy would try to infer them).
# 以下内容可以确保SpaCy能看到句子的边界（否则SpaCy会自己推断预测句子）。
for spacy_token in spacy_doc:
    if (spacy_token.i == 0): continue  # 忽视特殊标签(dummy token )

    token = tokens[spacy_token.i]
    sentence = sentences[token['sentence_id']]

    if (sentence['tokens'][0]['id'] == spacy_token.i):
        spacy_token.is_sent_start = True
    else:
        spacy_token.is_sent_start = False

# POS tagging
tagger(spacy_doc)

# 依存句法分析
parser(spacy_doc)

# 把需要的信息加到tokens中
for spacy_token in spacy_doc:
    if (spacy_token.i == 0): continue  # 忽视特殊标签(dummy token )

    token = tokens[spacy_token.i]
    assert ((token['id'] == spacy_token.i))

    token['pos'] = spacy_token.pos_  # Part-of-speech tag.
    token['dep_label'] = spacy_token.dep_  # # token和它的头(head)之间的依赖关系的Label
    token['head_id'] = spacy_token.head.i  # # 该token的头部(head)的索引。Index of the head of the token.
    token['subtree'] = [tokens[t.i] for t in spacy_token.subtree]  ## 依赖关系树中该tokens的所有依存的列表

if (debug_mode):
    for i, sentence in enumerate(list(spacy_doc.sents)):
        print(f"sentence n.{i}:")
        for token in sentence:
            print("\t", token.i, "\t", token.text, "\t", token.pos_, "\t", token.dep_, "\t", token.head)
        for token in sentence:
            print('\t', token.text, "\t", token.dep_)


# ## 辅助功能

# 以下是确定语料库中实体中的阴阳性(FEM : 阴性=女; MASC: 阳性=男)、
#                             单复数(SING : 单数; PLUR: 复数)
#                             人称(FIRST : 第一人称, SEC : 第二人称, THIRD : 第三人称)的函数。
# 注: 法语中分单复数, 阴阳性
#
# UNK=UNKNOWN 值，指在默认情况下与所有其他值兼容，但当相应的信息不可分别或者是不可用时，返回UNK值。

# In[35]:


# 阴阳性可能的值  'FEM', 'MASC', 'UNK'.
def determine_gender(mention):
    # On commence par le cas spécial d'un pronom possessif. On s'intéresse alors au genre de l'entité possédante. Celui-ci n'est pas marqué en français.
    # 我们从自反代词(如下)的特殊情况开始。然后，我们对相应的实体的性别进行标注。这在法语中没有标注。

    # UNK : 不确定的内容
    if ((mention['from_id'] == mention['to_id']) and (
            tokens[mention['from_id']]['form'].lower() in ["mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
                                                           "notre", "nos", "votre", "vos", "leur",
                                                           "leurs"])): return "UNK";

    # 阴性
    if (tokens[mention['from_id']]['form'].lower() in ["ma", "ta", "sa", "la", "une", "sa", "cette", "celle", "elle",
                                                       "-elle", "elles", "-elles", "chacune", "laquelle",
                                                       "lesquelles"]): return 'FEM'
    # 阳性
    if (tokens[mention['from_id']]['form'].lower() in ["mon", "ton", "son", "le", "un", "son", "du", "ce", "celui",
                                                       "il", "-il", "lui", "lequel"]): return 'MASC'
    return 'UNK'


#
# 判断两个提到的词是否有匹配的阴阳性
def gender_match(mention, other_mention):
    if ((mention['gender'] == 'UNK') or (other_mention['gender'] == 'UNK')): return True
    return (mention['gender'] == other_mention['gender'])


# 单复数可能的值'SING', 'PLUR', 'UNK'.
def determine_number(mention):
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
def determine_person(mention):
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


#
# 'ignore'函数表示系统是否应该完全忽略一个语句（即它不会被包括在任何指代的chains中）。
#
# `should_be_resolved`函数表示一个声明是否应该由系统来解决。否则，在默认情况下，它将被包含在一个新创建的指代的chains中。

# In[36]:


relative_pronouns = ["qui", "que", "qu'", "quoi", "où", "dont", "lequel", "laquelle", "lesquels", "lesquelles"]
reflexive_pronouns = ["me", "m'", "moi", "te", "t'", "toi", "se", "s'", "lui", "elle", "soi", "nous", "vous", "eux",
                      "elles"]  # Remarque : les pronoms réflexifs ne sont pas annotés comme entités dans le corpus (à vérifier). Autre remarque : la forme ne suffit pas toujours à déterminer qu'un token est un pronom réflexif.
personnal_pronouns = {
    'FIRST': ["je", "-je", "j'", "me", "m'", "moi", "-moi", "on", "-on", "nous", "nous"],
    'SEC': ["tu", "-tu", "te", "t'", "toi", "-toi", "vous", "-vous"],
    # 'THIRD': [],
}


# 表示一个实体是否应该被系统完全忽略
def ignore(mention):
    if (mention['from_id'] != mention['to_id']): return False
    # if(determine_person(mention) != "THIRD"): return True ## 忽略所有以第一和第二人称表达的词/实体

    token = tokens[mention['from_id']]

    if (token['pos'] == "VERB"): return True  ## 忽视被注释为实体的动词
    if ((token['pos'] == "PRON") and (
            token['form'].lower() in ["rien"] + relative_pronouns + ["y", "en", "ce", "c'", "cela"])): return True

    return False


# 指出是否应该以回指的方式解决提及到的词/实体。
# 那些没有被解决的将会产生一个新的指代chains
def should_be_resolved(mention):
    if (mention['from_id'] != mention['to_id']): return False  ## 只有单一tokens会消除

    token = tokens[mention['from_id']]

    if (determine_person(mention) != "THIRD"): return False  # # 只有以第三人称提到的实体才会被消除
    if ((token['pos'] == "PRON") and (
            token['form'].lower() not in ["chacun", "chacune"])): return True  ## 所有的代名词都将被消除，除了这里列出的那些
    if ((token['pos'] == 'DET') and (token['dep_label'] == "poss")): return True

    return False  # Nothing else will be resolved.


# # `compute_salience_factors`函数(麻烦多注解, 还有写一下思路)
#     该返回一个字典，表明每个特征对于给定输入的值
#
#     1, 主语Subject emphasis：该短语是主语，得80分。
#     2, 存在性Existential emphasis：表示不确定的名词短语如, un : 一个(阳性), une : 一个 (阴性)，des : 多个(复数)，得70分。
#     3, 直接宾语direct object：该短语是直接宾语，得50分。
#     4, 间接宾语和补语Indirect object and oblique complement：该短语是间接宾语或补语（介词名词短语），得40分。
#     5, 非副词Non-adverbial：不是用逗号将句子的其余部分与其他情况用逗号隔开；。得50分。例如下面的[the car of Sabine]和[Sabine]
#             - in [the car of [Sabine]], he finded his wallet
#     6, 头部名词：如果提到的内容没有严格包含在一个更大的名词短语中，则得80分。
#             - in the car of [Sabine], he findes his wallet(强调的是car不是sabine)
#     7, 句子重复Sentence recency：100分，无条件。
#
# 为了实现它，你需要使用附加在tokens上的、由SpaCy制作的各种信息。
#
#

# In[38]:


def compute_salience_factors(mention):
    values = {}

    # Sentence recency
    values['sentence_recency'] = 100

    # Subject emphasis 强调/重点

    pass  # TODO

    # Existential emphasis
    pass  # TODO

    # Accusative宾格的 (direct object) emphasis
    pass  # TODO

    # Indirect object and oblique complement emphasis
    pass  # TODO

    # Non-adverbial emphasis 非副词
    pass  # TODO

    # Head noun emphasis
    pass  # TODO

    return values


#
#
# ## 指代消解 (麻烦多写点注解)
#

# In[39]:


# 我们将在 "global_scores "进行计数
# 严格意义上讲，每条指代的chains对应于之前句子中提到的内容，都有一个分数。
global_scores = {}  # # 从链ID（整数）到突出值（浮点数）

#
# 计算每种类型的回指代词的总出现次数以及正确消解的出现次数。
stats = {}  # # 从表格（字符串）到对（正确（整数），总计（整数））

for sentence in sentences:
    # 1. 每个global_score的总分除以2。
    pass  # TODO

    # 对于当前句子，对于每个指代的chains核心推理字符串，我们将在`local_scores`中存储该字自身的分数。
    # 与其将其存储为一个单一的分数，不如将其分解为突出性特征。
    local_scores = {}  ## 从链ID（整数）到对（提及的列表，特征（字符串）到值（浮点数）的字典）

    # 对于每一个mention，我们预测其性别、数量并计算其特征值。
    new_entities = []  # # 将被附加到新的指代chains列表
    anaphora = []  ## 要消除的mention列表。
    for mention in sentence['mentions']:
        if (ignore(mention)): continue

        mention['gender'] = determine_gender(mention)
        mention['number'] = determine_number(mention)
        mention['person'] = determine_person(mention)
        mention['salience_factors'] = compute_salience_factors(mention)

        if (should_be_resolved(mention)):
            anaphora.append(mention)
        else:
            new_entities.append(mention)

        # 为 "mention "创建一个新的链。


    def add_new_chain(mention):
        new_chain_id = len(global_scores) + len(local_scores)
        # 新chains的显著性值被初始化为提到的显著性值的副本。
        local_scores[new_chain_id] = ([mention], dict(mention['salience_factors']))
        mention['predicted_chain_id'] = new_chain_id

        if (debug_mode):
            print(f"Une nouvelle chaîne de coréférence (id={new_chain_id}) a été créée pour '{mention['text']}'.")
            print(f"Local score: {mention['salience_factors']}")

        # 2. 创建新的指代chains


    for mention in new_entities:
        add_new_chain(mention)

        # 3. 解决人称代词的回指问题。
    for mention in anaphora:
        if (debug_mode): print(f"\n{mention}")

        # 3.1. 收集mentions中的”候选词“提及的收集（过滤前）
        candidates = []  # Liste de mentions.
        pass  # TODO

        # 3.2. 过滤不满足的”候选词“。
        pass  # TODO

        # 3.3. 计算每个候选词的显著性分数
        # 考虑到具体的突出性权重。
        best_score = -float('inf')
        best_candidate = None
        for candidate in candidates:
            salience_score = 0.0

            pass  # TODO

            if (debug_mode):
                print(f"candidate: {candidate}")
                print(f"score: {salience_score}")

            # 更行找到的最优的“候选词”
            if ((salience_score > best_score) or ((salience_score == best_score) and (
                    abs(candidate['id'] - mention['id']) < abs(best_candidate['id'] - mention['id'])))):
                best_score = salience_score
                best_candidate = candidate

        if (debug_mode):
            print(f"best candidate: {best_candidate}")

            # 如果没有任何 ”候选词“, 我们自己给mention创建一个新的chain
            add_new_chain(mention)
            continue

        # 3.4. 把代词添加到选择的指代的chain中
        mention['predicted_chain_id'] = best_candidate['predicted_chain_id']
        if (debug_mode): print(
            f"'{mention['text']}' a été assigné·e à la chaîne id={mention['predicted_chain_id']} via l'antécédent '{best_candidate['text']}'.")

        if (False):  # 这里可以用来调试bug Peut être utilisé pour débugger.
            print(f"id: {mention['id']}, text: {mention['text']}, sentence: {mention['sentence_id']}")
            print('resolved to')
            print(
                f"id: {best_candidate['id']}, text: {best_candidate['text']}, sentence: {best_candidate['sentence_id']}")
            print(f"score: {best_score}")
            print(f"correct: {mention['gold_chain']['id'] == best_candidate['gold_chain']['id']}")
            input()

        # 更新数据
        correct, total = stats.get(mention['text'].lower(), (0, 0))
        if (mention['gold_chain']['id'] == best_candidate['gold_chain']['id']): correct += 1
        total += 1
        stats[mention['text'].lower()] = (correct, total)

        # 更新与mentions连接的chains的local_score的分数
        pass  # TODO

        if (debug_mode): print(f"local score: {local_scores[mention['predicted_chain_id']][1]}")

    # 4. 把每个global_scores分数加上到local_scores上
    pass  # TODO

    if (debug_mode): print(f"global scores: {global_scores}\n")

# 显示数据。

# In[ ]:


correct, total = 0, 0
for form, (c, t) in stats.items():
    print(f"performance for '{form}': {c}/{t} = {c / t}")
    correct += c
    total += t
print(f"global performance: {correct}/{total} = {correct / total}")
