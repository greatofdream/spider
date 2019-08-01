#!/usr/bin/python
# -*- coding: UTF-8 -*-

from selenium import webdriver
import urllib.request
from bs4 import BeautifulSoup 
import requests
import sys,os
if len(sys.argv)>1:
    keyword = sys.argv[1]
else:
    keyword = input('输入某个民族比如"回族明星":')

if os.path.exists(keyword):
    print("将重写{}文件夹".format(keyword))
else:
    print('创建{}文件夹'.format(keyword))
    os.mkdir(keyword)

keywordCoding = urllib.request.quote(keyword)
baiduUrl = 'https://www.baidu.com/s?wd='
browser = webdriver.Chrome()
print('向百度发起请求')
browser.get(baiduUrl + keywordCoding)
print('抓取完毕')
html = browser.page_source

soup =  BeautifulSoup(html, 'html.parser')
img = soup.find_all(attrs='op_exactqa_item_img')
for im in img:
    print('从{}获取{}明星图片'.format(im.img['src'],im.a['title']))
    r = requests.get(im.img['src'])
    with open(keyword+'/'+im.a['title']+'.png','wb') as opt:
        opt.write(r.content)

browser.quit()