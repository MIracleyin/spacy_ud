#!/usr/bin/env python
# -*- coding: utf-8 -*-
# !@Time    : 2021/4/30 下午4:49
# !@Author  : miracleyin @email: miracleyin@live.com
# !@File    : main.py

import spacy
import urllib
import urllib.request
import zipfile
import os
from lxml import etree  # 读取XML文件
from utils import *

debug_mode = True


def model_build(model_name="fr_core_news_sm"):
    """
    :param model_name: 使用的模型名词
    :return: 模型对象
    """
    try:
        nlp = spacy.load(model_name, disable=['ner'])
    except:
        from spacy.cli import download
        download(model_name)
        nlp = spacy.load(model_name, disable=['ner'])
    return nlp


def data_download():
    """
    :return: 下载数据，只需要运行一次
    """
    # 第一次使用时运行
    zipurl = "https://repository.ortolang.fr/api/content/export?&path=/democrat/5/&filename=democrat&scope=YW5vbnltb3Vz3"
    tmp = urllib.request.urlretrieve(zipurl)
    filename = tmp[0]
    print("filename : ", filename, "\n")
    # 提取数据集 dataset
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(".", )

    base_name, ext = os.path.splitext(os.path.basename(zipurl))
    list(os.listdir("."))


def data_loading(debug_mode):
    """
    将数据导入，处理成sentences 和 tokens
    :param debug_mode: debug下倒入example
    :return: sentences，tokens
    """
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
    def without_namespace(s):
        return s.split('}')[-1]

    text_tree = etree.parse(text_path)
    # 检查关于XML文件中books的信息
    text_node = text_tree.getroot()[1]
    sentences = []  # sentence的列表(每个元素都是一个字典);
    token_id = 1  # 注意 : 在XML文件中, 每个tokens的下标都是从1开始的
    for child in text_node: # 对于一句话
        tag = without_namespace(child.tag)
        if (tag != 's'):
            continue
        s = child
        sentence_id = len(sentences)
        tokens = []
        for child in s: # 对于
            tag = without_namespace(child.tag)
            if (tag != 'w'):
                continue
            w = child
            assert (token_id == int(w.get('n')))
            token = {
                'id': token_id,  # 整型
                'sentence_id': sentence_id,  # 整型
            }
            for child in w:
                tag = without_namespace(child.tag)
                if (tag == "form"):
                    token['form'] = child.text  # 字符串String
            tokens.append(token)
            token_id += 1
        sentence = {
            'id': sentence_id,  # 整型
            'tokens': tokens,  # tokens 列表(字典)
            'mentions': []  # mentions 列表 (之后会把列表填满)
        }

        sentences.append(sentence)
    tokens = [{'id': 0, 'sentence_id': None, 'form': 'DUMMY_TOKEN'}]
    for sentence in sentences:
        tokens.extend(sentence['tokens'])
    return sentences, tokens

def anno_loading(debug_mode, sentences, tokens):
    """
    导入sentences 和 token，导入 anno 并据此处理成chain
    :param debug_mode: debug下 导入例子的 anno数据
    :param sentences: 被导入的sentences
    :param tokens: 被导入的tokens
    :return: 返回附上由anno数据构成的mention 的sentences  对tokens无处理 故不返回
    """
    if (debug_mode):
        root_path = os.path.join(os.curdir)
        part_name = "exemple"
        annotations_path = os.path.join(root_path, f"{part_name}-urs.xml")
    else:
        root_path = os.path.join("democrat", "5", "data")
        part_name = "bouvardetpecuchet"
        annotations_path = os.path.join(root_path, "xml-urs", f"{part_name}-urs.xml")
    # 加载注释annotations（mentions 和 共指的chains）

    annotations_tree = etree.parse(annotations_path) # 这个是处理好的标注
    mentions = {}  # 从 ids (整型) 到 mentions (字典).
    standOff_node = annotations_tree.getroot()[2]
    annotation_node = standOff_node[1]
    annotationGrp_node = annotation_node[0]
    for child in annotationGrp_node: # 首先构建ids对sentences 和 mentions
        if (child.tag != "span"):
            continue
        from_id = int(child.get('from').split('_')[-1])  # span该跨度中的第一个token的下索引
        to_id = int(child.get('to').split('_')[-1])  # 该跨度中最后一个标记的索引
        mention_id = int(child.get('id').split('-')[-1])  # 索引
        sentence_id = tokens[from_id]['sentence_id'] # 获取这个mention所属句子的id
        text = ' '.join([token['form'] for token in tokens[from_id:(to_id + 1)]]) # 把from 到 to所有的词遍历，加入到text里
        mention = {
            'id': mention_id,  # 整型
            'from_id': from_id,  # 整型
            'to_id': to_id,  # 整型
            'sentence_id': sentence_id,  # 整型
            'text': text,  # 字符串
        }
        sentences[sentence_id]['mentions'].append(mention)
        mentions[mention_id] = mention
    chains = {}  # 从 ids (整型类型) 到 chains (字典类型).
    annotationGrp_node = annotation_node[1]
    for child in annotationGrp_node: # 接着将idx映射为 key-value
        if (child.tag != "link"): continue

        chain_id = int(child.get('id').split('-')[-1])  # chain的索引
        mention_ids = [int(mention.split('-')[-1]) for mention in child.get('target').split()]  # span的索引

        # 创建chain，并把chain的引用加到对应的mentions中
        chain = {
            'id': chain_id,  # Integer
            'mentions': [mentions[mention_id] for mention_id in mention_ids],  # mentions列表
        }
        chain['mentions'].sort(key=(lambda mention: mention['to_id']))  # 确保列表是按照线性顺序排序的。
        for mention in chain['mentions']: mention['gold_chain'] = chain  # Chain
        chains[chain_id] = chain
    return chains, sentences

def nlp_analysis(sentences, tokens, pipeline):
    """
    这个部分处理sentence和tokens，使用模型，并将分析结果附到tokens中
    :param sentences: 附上mention的sentences
    :param tokens:
    :param pipeline: 处理模型的流程
    :return: 处理过到sentences 和 tokens mention依附于sentence 故不单独返回
    """
    def aux(form):
        return "–" if (form == "—") else form  # # 与表象相反，这不是字符

    spacy_doc = spacy.tokens.Doc(nlp.vocab, words=[aux(token['form']) for token in tokens], spaces=None)
    # print(len(spacy_doc.text))
    tagger = pipeline['morphologizer'] if ('morphologizer' in pipeline) else nlp.tagger
    parser = pipeline['parser'] if ('parser' in pipeline) else nlp.parser
    if ('tok2vec' in pipeline):
        spacy_doc = pipeline['tok2vec'](spacy_doc)
    for spacy_token in spacy_doc:
        if (spacy_token.i == 0):
            continue  # 忽视特殊标签(dummy token )
        token = tokens[spacy_token.i]
        sentence = sentences[token['sentence_id']] # 将分析结果附到sentence上
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
        token = tokens[spacy_token.i] # 保留tokens最后所需要到标签
        assert ((token['id'] == spacy_token.i))
        token['pos'] = spacy_token.pos_  # Part-of-speech tag. # 获取每个token的词性
        token['dep_label'] = spacy_token.dep_  # # token和它的头(head)之间的依赖关系的Label
        token['head_id'] = spacy_token.head.i  # # 该token的头部(head)的索引。Index of the head of the token.
        token['subtree'] = [tokens[t.i] for t in spacy_token.subtree]  ## 依赖关系树中该tokens的所有依存的列表


    return sentences, tokens

def cal_anaphore(sentences, tokens):
    # 我们将在 "global_scores "进行计数
    # 严格意义上讲，每条指代的chains对应于之前句子中提到的内容，都有一个分数。
    global_scores = {}  # 从chians ID（整数）到突出值（浮点数）
    # 计算每种类型的回指代词的总出现次数以及正确消解的出现次数。
    stats = {}  # # 从表格（字符串）到对（正确（整数），总计（整数））


def main():
    pass


if __name__ == '__main__':
    nlp = model_build()
    pipeline = {name: proc for name, proc in nlp.pipeline}
    sentences, tokens = data_loading(debug_mode) # 这个部分和原来等价
    chains, sentences = anno_loading(debug_mode, sentences, tokens) # 这个部分和原来等价
    sentences, tokens = nlp_analysis(sentences, tokens, pipeline) # 这个部分和原来等价
    #cal_anaphore(sentences, tokens)
    sentence = sentences[0]
    for mention in sentence['mentions']:
        if (ignore(mention, tokens)): continue
        mention['gender'] = determine_gender(mention, tokens)
        mention['number'] = determine_number(mention, tokens)
        mention['person'] = determine_person(mention, tokens)
        mention['salience_factors'] = compute_salience_factors(mention, tokens, sentence)


