#!usr/bin/env
# -*-coding:utf-8 -*-
import logging
from scrapy.conf import settings
from spiders.spider_tools import mytools
from scrapy.downloadermiddlewares.downloadtimeout import DownloadTimeoutMiddleware
from scrapy.contrib.spidermiddleware.httperror import HttpErrorMiddleware
from twisted.internet.error import TimeoutError
from twisted.internet import defer

logger = logging.getLogger(__name__)


class ProxyMiddleware(object):
    # overwrite process request
    def process_request(self, request, spider):
        if settings['RUN_ENV'] == 'TEST':
            pass
        else:
            if "https" in request.url:
                request.meta['proxy'] = "https://127.0.0.1:8888"
            else:
                request.meta['proxy'] = "http://127.0.0.1:8888"


class UserAgentmiddleware(object):

    def process_request(self, request, spider):
        # 需要重新设置headers的爬虫列表
        if spider.name == 'weixin':
            headers = spider.headers
            request.headers['accessToken'] = headers['accessToken']
            request.headers['vid'] = headers['vid']
        else:
            request.headers['User-Agent'] = ['Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/64.0.3282.119 Chrome/64.0.3282.119 Safari/537.36']


class TimeoutDownloadMiddleware(DownloadTimeoutMiddleware):
    ALL_EXCEPTIONS = (defer.TimeoutError, TimeoutError)

    def process_request(self, request, spider):
        timeout = 15
        request.meta.setdefault('download_timeout', timeout)

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.ALL_EXCEPTIONS):
            mytools.lpushUrlIntoRedisWith(spider.redis_key, request.url)
            response = HtmlResponse(url=request.url)
            return response


class Httpstatus(HttpErrorMiddleware):

    def process_spider_exception(self, response, exception, spider):

        if response.status != 200 and spider.name != 'weixin':
            logger.info(
                "Ignoring response %(response)r: HTTP status code is not handled or not allowed and push url into redis",
                {'response': response}, extra={'spider': spider},
            )
            mytools.lpushUrlIntoRedisWith(spider.redis_key, response.url)
