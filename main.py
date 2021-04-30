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

debug_mode = False


def model_build(model_name="fr_core_news_sm"):
    try:
        nlp = spacy.load(model_name, disable=['ner'])
    except:
        from spacy.cli import download
        download(model_name)
        nlp = spacy.load(model_name, disable=['ner'])
    return nlp


def data_download():
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


def data_loading(debug_mode, pipeline):
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
    titleStmt_node = text_tree.getroot()[0][0][0]
    assert (without_namespace(titleStmt_node.tag) == "titleStmt")
    for child in titleStmt_node:
        tag = without_namespace(child.tag)
        if (tag in ["author", "title"]):
            # print("etree.tostring(child) : ",etree.tostring(child))
            print(f"\ntag+child.text : {tag}: {child.text}")
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
    tokens = [{'id': 0, 'sentence_id': None, 'form': 'DUMMY_TOKEN'}]
    for sentence in sentences:
        tokens.extend(sentence['tokens'])
    # 检查XML中的token ids是否是我们认为的那样
    for i, token in enumerate(tokens):
        assert (token['id'] == i)

    print(f"\n{len(sentences)} sentences")
    print("sentence : ", sentence)
    # 不计入虚假标记(dummy token)
    print(f"\n{len(tokens) - 1} tokens")
    print("tokens : ", tokens)
    # 加载注释annotations（mentions 和 共指的chains）
    for sentence in sentences:
        assert (sentence['mentions'] == []), "这个代码块已被执行了。为了避免冲突，请重新加载文本（以前的代码块）"
    annotations_tree = etree.parse(annotations_path)
    mentions = {}  # 从 ids (整型) 到 mentions (字典).
    standOff_node = annotations_tree.getroot()[2]
    annotation_node = standOff_node[1]
    annotationGrp_node = annotation_node[0]
    assert (annotationGrp_node.get('subtype') == "MENTION")
    for child in annotationGrp_node:
        if (child.tag != "span"):
            continue
        from_id = int(child.get('from').split('_')[-1])  # span该跨度中的第一个token的下索引
        to_id = int(child.get('to').split('_')[-1])  # 该跨度中最后一个标记的索引。
        mention_id = int(child.get('id').split('-')[-1])  # 索引
        assert (child.get('id') == f"u-MENTION-{mention_id}")
        sentence_id = tokens[from_id]['sentence_id']
        text = ' '.join([token['form'] for token in tokens[from_id:(to_id + 1)]])
        mention = {
            'id': mention_id,  # 整型
            'from_id': from_id,  # 整型
            'to_id': to_id,  # 整型
            'sentence_id': sentence_id,  # 整型
            'text': text,  # 字符串
        }
        sentences[sentence_id]['mentions'].append(mention)
        mentions[mention_id] = mention
    print(
        f"{len(mentions)} mentions")  # ---------------------------------------------------------------------------------
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
    # ------------------------------------------------chains---------------------------------------
    print(f"{len(chains)} chains")

    if (debug_mode):
        print()
        for i, sentence in enumerate(sentences):
            # ---------------------------------------------------sentences{i}--------------------------------------
            print(f"sentences[{i}]:")
            for k, v in sentence.items(): print(f'\t{k}: {v}')
        print()
        for i, mention in enumerate(sentences[0]['mentions']):
            print(f"sentences[0]['mentions'][{i}]:")
            for k, v in mention.items(): print(f'\t{k}: {v}')

        print()
        for i, chain in chains.items():
            print(f"chains[{i}]:")
            # ---------------------------------------------chains{i}-------------------------------------------
            for k, v in chain.items(): print(f'\t{k}: {v}')
    else:
        print("sentences[0]:")
        # ------------------------------------sentences[0]------------------------------------------------
        for k, v in sentences[0].items(): print(f'\t{k}: {v}')

        print()
        print("sentences[0]['mentions'][0]:")
        # ----------------------sentences[0]['mentions'][0]---------------------------------------------
        for k, v in sentences[0]['mentions'][0].items(): print(f'\t{k}: {v}')

        print()
        print("chains[1]:")
        # --------------------------------chains[1]-----------------------------------------------------
        for k, v in chains[1].items(): print(f'\t{k}: {v}')

    def aux(form):
        return "–" if (form == "—") else form  # # 与表象相反，这不是字符

    spacy_doc = spacy.tokens.Doc(nlp.vocab, words=[aux(token['form']) for token in tokens], spaces=None)
    print(len(spacy_doc.text))
    tagger = pipeline['morphologizer'] if ('morphologizer' in pipeline) else nlp.tagger
    parser = pipeline['parser'] if ('parser' in pipeline) else nlp.parser
    if ('tok2vec' in pipeline):
        spacy_doc = pipeline['tok2vec'](spacy_doc)
    for spacy_token in spacy_doc:
        if (spacy_token.i == 0):
            continue  # 忽视特殊标签(dummy token )
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

    return tokens, sentences


def cal_anaphore(tokens, sentences):
    def add_new_chain(mention):
        new_chain_id = len(global_scores) + len(local_scores)
        # 新chains的显著性值被初始化为提到的显著性值的副本。
        local_scores[new_chain_id] = ([mention], dict(mention['salience_factors']))
        mention['predicted_chain_id'] = new_chain_id

        if (debug_mode):
            print(f"Une nouvelle chaîne de coréférence (id={new_chain_id}) a été créée pour '{mention['text']}'.")
            print(f"Local score: {mention['salience_factors']}")

    # 我们将在 "global_scores "进行计数
    # 严格意义上讲，每条指代的chains对应于之前句子中提到的内容，都有一个分数。
    global_scores = {}  # # 从链ID（整数）到突出值（浮点数）
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
        anaphora = []  ## 要消除的mention列表
        for mention in sentence['mentions']:
            if (ignore(mention, tokens)):
                continue
            mention['gender'] = determine_gender(mention, tokens)
            mention['number'] = determine_number(mention, tokens)
            mention['person'] = determine_person(mention, tokens)
            mention['salience_factors'] = compute_salience_factors(mention, tokens)
            if (should_be_resolved(mention, tokens)):
                anaphora.append(mention)
            else:
                new_entities.append(mention)
            for mention in new_entities:
                add_new_chain(mention)
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
                    add_new_chain(mention)
                    continue
                # 3.4. 把代词添加到选择的指代的chain中
                mention['predicted_chain_id'] = best_candidate['predicted_chain_id']
                if (debug_mode): print(
                    f"'{mention['text']}' a été assigné·e à la chaîne id={mention['predicted_chain_id']} via l'antécédent '{best_candidate['text']}'.")
                if (debug_mode):  # 这里可以用来调试bug Peut être utilisé pour débugger.
                    print(f"id: {mention['id']}, text: {mention['text']}, sentence: {mention['sentence_id']}")
                    print('resolved to')
                    print(
                        f"id: {best_candidate['id']}, text: {best_candidate['text']}, sentence: {best_candidate['sentence_id']}")
                    print(f"score: {best_score}")
                    print(f"correct: {mention['gold_chain']['id'] == best_candidate['gold_chain']['id']}")
                    input()
                # 更新数据
                correct, total = stats.get(mention['text'].lower(), (0, 0))
                if (mention['gold_chain']['id'] == best_candidate['gold_chain']['id']):
                    correct += 1
                total += 1
                stats[mention['text'].lower()] = (correct, total)
                # 更新与mentions连接的chains的local_score的分数
                pass  # TODO
                if (debug_mode):
                    print(f"local score: {local_scores[mention['predicted_chain_id']][1]}")
            pass  # TODO
            if (debug_mode): print(f"global scores: {global_scores}\n")
def main():
    pass


if __name__ == '__main__':
    nlp = model_build()
    pipeline = {name: proc for name, proc in nlp.pipeline}
    tokens, sentences = data_loading(debug_mode, pipeline)
    #head = []
    #dep
    new_entities = []  # # 将被附加到新的指代chains列表
    anaphora = []  ## 要消除的mention列表。
    for sentence in sentences:
        for mention in sentence["mentions"]:
        #   token = tokens[mention['from_id']]
        #    dep.append(token['dep_label'])
        #   head.append(token['head_id'])
        #print((set(head)))
            if (ignore(mention, tokens)): continue
#
            mention['gender'] = determine_gender(mention, tokens)
            mention['number'] = determine_number(mention, tokens)
            mention['person'] = determine_person(mention, tokens)
            mention['salience_factors'] = compute_salience_factors(mention, tokens)
            if (should_be_resolved(mention, tokens)):
                anaphora.append(mention)
            else:
                new_entities.append(mention)
            print(mention['salience_factors'])
