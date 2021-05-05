from __future__ import absolute_import
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy import Request, FormRequest
from lxml import html as lxhtml
from scrapy.utils.log import configure_logging
from datetime import datetime, timedelta
from scrapy.loader.processors import MapCompose
import json
import sys
import re
import logging
import time
import traceback
from collections import OrderedDict


class My_Spider(Spider):
    name = "officedepot_cat_generator"
    download_timeout = 120

    custom_settings = {
        "PROXY_ON": True,
        # "PROXY_PR_ON": True,
        "HTTPCACHE_ENABLED": False,
        "LOG_LEVEL": "DEBUG",
        "FEED_EXPORT_ENCODING": "utf-8",
        "DOWNLOAD_DELAY": 3,
        "RETRY_HTTP_CODES": [500, 503, 504, 400, 401, 403, 405, 407, 408, 416, 456, 502, 429, 307],
        "CONCURRENT_REQUESTS": 3,
    }
    headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
        "upgrade-insecure-requests": "1",
    },

    def start_requests(self):
        url = "https://www.officedepot.com"
        yield Request(url, callback=self.jump)

    def jump(self, response):

        for item in response.xpath(
            "//div[contains(@data-auid,'MainNavProducts')]/div/div[1]/div[1]//li/a/@href"
        ).extract():
            yield Request(
                url=response.urljoin(item), 
                callback=self.parse_categorie,
                headers=self.headers,
            )

    def parse_categorie(self, response):
        if response.xpath("//span[@class='cat_all_count']/a/@href").get():
            url = response.xpath("//span[@class='cat_all_count']/a/@href").get()
            if url:
                yield Request(
                    url=response.urljoin(url),
                    callback=self.parse_categorie,
                    headers=self.headers,
                )
        elif response.xpath("//a[contains(.,'iew all')]/@href").get():
            url = response.xpath("//a[contains(.,'iew all')]/@href").get()
            if url:
                yield Request(
                    url=response.urljoin(url),
                    callback=self.parse_categorie,
                    headers=self.headers,
                )
        elif response.xpath("//ul[contains(@class,'category_refinement')]/li/a/@href").getall():
            for item in response.xpath(
                "//ul[contains(@class,'category_refinement')]/li/a/@href"
            ).extract():
                yield Request(
                    url=response.urljoin(item),
                    callback=self.parse_categorie,
                    headers=self.headers,
                )
        elif response.xpath("//div[@id='productView']/div//div[@class='photo_no_QV flcl']/a[1]/@href").extract():
            cat_url = response.url
            file1 = open("officedepot_cat.txt","a")
            file1.write(cat_url.strip() + "\n")
                
    