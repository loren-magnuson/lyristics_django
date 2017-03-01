# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals


class LyristicsScrapySpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


import base64
import re
import urllib

from scrapy.responsetypes import responsetypes
from scrapy.utils.decorators import defers


_token = r'[{}]+'.format(re.escape(''.join(set(map(chr, range(32, 127))) -
                                           set('()<>@,;:\\"/[]?= '))))

_char = set(map(chr, range(127)))
_quoted = r'"(?:[{}]|(?:\\[{}]))*"'.format(re.escape(''.join(_char -
                                                             set('"\\\r'))),
                                           re.escape(''.join(_char)))

_urlchar = r"[\w;/\\?:@&=+$,-_.!~*'()]"


class DataURLDownloadHandler(object):
    def __init__(self, settings):
        super(DataURLDownloadHandler, self).__init__()

    _data_url_pattern = re.compile((r'data:'
                                    r'({token}/{token})?'
                                    r'(?:;{token}=(?:{token}|{quoted}))*'
                                    r'(;base64)?'
                                    r',({urlchar}*)'
                                    ).format(token=_token, quoted=_quoted,
                                             urlchar=_urlchar))

    @defers
    def download_request(self, request, spider):
        # XXX: I think this needs urllib.unquote().
        m = self._data_url_pattern.match(request.url)
        if not m:
            raise ValueError("invalid data URL")
        mimetype, is_base64, data = m.groups()
        data = urllib.unquote(data)
        if is_base64:
            data = base64.urlsafe_b64decode(data)
        respcls = responsetypes.from_mimetype(mimetype)

        return respcls(url=request.url, body=data)