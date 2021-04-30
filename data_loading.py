#!/usr/bin/env python
# -*- coding: utf-8 -*-
# !@Time    : 2021/4/30 下午5:05
# !@Author  : miracleyin @email: miracleyin@live.com
# !@File    : data_loading.py

import urllib
import urllib.request
import zipfile
import os

if __name__ == '__main__':
    zipurl = "https://repository.ortolang.fr/api/content/export?&path=/democrat/5/&filename=democrat&scope=YW5vbnltb3Vz3"
    tmp = urllib.request.urlretrieve(zipurl)
    filename = tmp[0]
    print("filename : ", filename, "\n")
    # 提取数据集 dataset
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(".", )

    base_name, ext = os.path.splitext(os.path.basename(zipurl))
    list(os.listdir("."))
    print(list(os.listdir("democrat")))
    print(list(os.listdir("democrat/5")))
    print(list(os.listdir("democrat/5/data")))

    # 文本文件
    print(list(os.listdir("democrat/5/data/xml")))
    # 这个文件夹中包含注释的文件
    print(list(os.listdir("democrat/5/data/xml-urs")))