# coding:utf-8
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy_redis.spiders import RedisCrawlSpider
from lxml import etree
from scrapy.http import Request, FormRequest
import redis
from scrapy.conf import settings
from scrapy.log import logger
import md5
import json
import HTMLParser
import copy
import re
import lxml
import random
import time
import sys
import requests
import os
from urlparse import urljoin


# import boto3
reload(sys)
sys.setdefaultencoding('utf8')

INSIDE_KEY_WORDS = settings['INSIDE_KEY_WORDS']


class WeixinSpider(RedisCrawlSpider):
    name = 'weixin'
    allowed_domains = ['weixin.com']
    redis_key = 'weixin:start_urls'
    start_urls = ['https://i.weread.qq.com/book/articles?bookId=MP_WXS_2390582660&count=10']  # 肖磊看市]
    custom_settings = {'DOWNLOADER_MIDDLEWARES': {'btc_news.middlewares.ProxyMiddleware': None, 'btc_news.middlewares.UserAgentmiddleware': 100}}
    headers = {}
    handle_httpstatus_list = [401]

    def __init__(self):
        self.r = redis.Redis('localhost', port=6379)
        self.data = {}
        for url in self.start_urls:
            self.r.lpush(self.redis_key, url)
        self.get_headers()

# 获取微信阅读的请求headers
    def get_headers(self):
        url = 'https://i.weread.qq.com/login'
        data = '{"deviceId":"3339194867987931887675104222","inBackground":0,"kickType":1,"refCgi":"https://i.weread.qq.com/mp/cover?bookId=MP_WXS_3548542976","refreshToken":"onb3MjkNtSPdfSJlDdp5cCVIJYWw@kbFVENIIQris7ZvDvT9XlQAA","trackId":"861873034694818","wxToken":0}'
        html = requests.post(url=url, data=data, timeout=5).json()
        self.headers['accessToken'] = html['accessToken']
        self.headers['vid'] = html['vid']

    def parse(self, response):
        print u"start 微信", response.status
        try:
            if response.status == 401:
                self.get_headers
            else:
                res = json.loads(response.body)['reviews']
                for article in res[:1]:
                    article = article['review']
                    title = article['mpInfo']['title']
                    content_url = article['mpInfo']['doc_url']
                    cover_url = article['mpInfo']['pic_url']
                    author = article['mpInfo']['mp_name']
                    dis = article['mpInfo']['content']
                    article_data = copy.deepcopy(self.data)
                    article_data['cover_url'] = cover_url
                    article_data['title'] = title
                    article_data['description'] = dis
                    article_data['author'] = author
                    yield article_data
        except Exception as e:
            print self.name, e
        finally:
            self.r.lpush(self.redis_key, response.url)
