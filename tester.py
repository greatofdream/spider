import os
import json
import time
import math
import hashlib
import argparse
from urllib.request import Request, urlopen
import requests
import re
from pyquery import PyQuery as pq

# 命令行参数解析器
# 例: python tester.py --search_engine baidu --keyword muslim
parser = argparse.ArgumentParser()
parser.add_argument('--search_engine', default='baidu',
                    choices=['google', 'baidu'],
                    help='search engine: google or baidu')
parser.add_argument('--keyword', default='穆斯林人',
                    help='search keywords (recommended baidu--穆斯林人 google--穆斯林')
parser.add_argument('--image_number', type=int, default=-1,
                    help='target number of images to be retrieved. -1 means infinity')
parser.add_argument('--get_src', type=bool, default=False,
                    help='whether or not get source link of image')
# 命令行参数
args = parser.parse_args()

# 手动指定参数
# args.search_engine = 'google'
# args.keyword = '穆斯林'
# args.image_number = -1
# args.get_src = False

# 图片搜索结果url，翻页参数未指定
image_search_url = {
    'baidu': 'http://image.baidu.com/search/flip?'
             'tn=baiduimage'
             '&word={keyword}'
             '&pn=%s'.format(keyword=args.keyword),
    'google': 'https://www.google.com.hk/search?'
              'q={keyword}'
              '&tbm=isch'
              '&start=%s'.format(keyword=args.keyword),
}

# 页面解析方式
PARSE_PATTERN = {
    'baidu':  ['re', ['"thumbURL":"(.*?)",']],
    'google': ['css', ['table.images_table td', 'img', 'src', 'a']],
}

# 单页面图片结果数
IMG_NUM_PER_PAGE = {
    'baidu': 60,
    'google': 20,
}

# request头
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/74.0.3729.169 Safari/537.36'
}

# 保存路径: ./images/<args.search_engine>/
BASE_OUTPUT_DIR = 'images'
if not os.path.exists(BASE_OUTPUT_DIR):
    os.mkdir(BASE_OUTPUT_DIR)
OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, args.search_engine)
if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)

# 进程记录文件
RECORD_PATH = os.path.join(OUTPUT_DIR, 'record.json')
if os.path.exists(os.path.join(RECORD_PATH)):
    with open(os.path.join(RECORD_PATH), 'r') as f:
        d = json.loads(f.read())
        scrawled = set(d['scrawled_url'])  # 已爬取图片链接
        retrieved_index = int(d['retrieved_index'])  # 已爬取图片数目
        ori_time = time.time() - float(d['time'])  # 爬取消耗时间
else:
    scrawled = set()
    retrieved_index = 0
    ori_time = time.time()
ti = ori_time


# 图片元素表
def get_image_list(url, parse_method, pattern):
    if parse_method not in ['re', 'css', 'xpath']:
        raise KeyError

    response = requests.get(url)
    if parse_method == 'css':
        doc = pq(response.text)
        return doc(pattern)
    elif parse_method == 're':
        return re.findall(pattern, response.text, re.S)


# 解析图片url
def get_imgurl(image_list, parse_method, pattern=None, with_src=False):
    if parse_method not in ['re', 'css', 'xpath']:
        raise KeyError

    if parse_method == 'css':
        assert isinstance(pattern, list)
        for e in image_list:
            img_url = e(pattern[0]).attr(pattern[1])
            href = e(pattern[0]).attr('href') if with_src else None
            yield img_url, href

    elif parse_method == 're':
        for i in image_list:
            yield i, None


# 获取并保存图片
def retrieve_and_save_image(fp, img_url, href=None, with_src=False,
                            img_format='jpg', hashfunc=hashlib.md5()):
    if with_src and not href:
        raise Exception
    if img_url in scrawled:
        return False

    # 对访问过的图片url进行数字签名后保存
    hashfunc.update(img_url.encode('utf8'))
    scrawled.add(hashfunc.hexdigest())

    save_name = os.path.join(fp, str(retrieved_index))
    if with_src:
        with open(save_name + '.txt', 'w') as f:
            f.write('\n'.join([href, img_url]))
    with open(save_name + '.' + img_format, 'wb') as f:
        request = Request(img_url, None, headers=headers)
        response = urlopen(request)
        f.write(response.read())
    return True


if __name__ == '__main__':
    # 数字签名算法
    md5 = hashlib.md5()

    # 根据指定待爬取图片数目计算需要访问的页数和最后一页图片数
    img_num_per_page = IMG_NUM_PER_PAGE[args.search_engine]
    if args.image_number == -1:
        target_page_number = -1
        img_num_in_last_page = IMG_NUM_PER_PAGE
    else:
        target_page_number = math.ceil(args.image_number / img_num_per_page)
        img_num_in_last_page = (args.image_number + 1) % img_num_per_page - 1

    # 页数
    page_index = 0
    try:
        while True:
            try:
                elems = get_image_list(
                    image_search_url[args.search_engine]
                    % str(page_index * img_num_per_page),
                    PARSE_PATTERN[args.search_engine][0],
                    PARSE_PATTERN[args.search_engine][1][0])
                for j, (img_url, href) in enumerate(get_imgurl(
                        elems, PARSE_PATTERN[args.search_engine][0],
                        PARSE_PATTERN[args.search_engine][1][1:],
                        with_src=args.get_src)):
                    if page_index == target_page_number or \
                            (page_index == target_page_number - 1
                             and j == img_num_in_last_page):
                        exit(0)
                    if retrieve_and_save_image(OUTPUT_DIR, img_url, href,
                                               with_src=args.get_src,
                                               hashfunc=md5):
                        retrieved_index += 1
                        ti = time.time()
                        print('\r%d images scrawled ... '
                              'total time cost: %.2fs time cost per image: %.2fs'
                              % (retrieved_index, ti - ori_time,
                                 (ti - ori_time) / retrieved_index), end='')
                page_index += 1
            except Exception:
                continue
    finally:
        if retrieved_index:
            with open(RECORD_PATH, 'w') as f:
                f.write(json.dumps(
                    {'retrieved_index': retrieved_index,
                     'time': ti - ori_time,
                     'scrawled_url': list(scrawled)}))
