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
import csv
import logging
import time
import traceback
from collections import OrderedDict
from w3lib.html import remove_tags


class My_Spider(Spider):
    name = "staples_cat_generator"
    download_timeout = 120

    custom_settings = {
        #"PROXY_PR_ON": True,
        "PROXY_ON": True,
        "PASSWORD": "1yocxe3k3sr3",
        "HTTPCACHE_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "FEED_EXPORT_ENCODING": "utf-8",
        "CONCURRENT_REQUESTS": 3,
        "COOKIES_ENABLED": False,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": .1,
        "AUTOTHROTTLE_MAX_DELAY": .3,
        "RETRY_TIMES": 3,
        "DOWNLOAD_DELAY": 0,
    }

    def start_requests(self):

        #txt check
        # with open("staples_cat.txt", "r") as file:
        #     reader = csv.reader(file)
        #     for row in reader:
        #         if row[0].strip():
        #             print(row[0].strip())
        

        start_urls = [
            {
                "url": "https://www.staples.com/",
            },
        ]
        for url in start_urls:
            yield Request(
                url.get("url"),
                callback=self.jump,
            )

    def jump(self, response):
        next_data = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
        a = next_data.split('cat_CL')
        for i in range(1, len(a)):
            cntrl = next_data.split('cat_CL')[i].split(",")[0].replace("\"", "")
            # print("cat_CL" + cntrl)
            added = "CL" + cntrl
            added = added.split("/")[0].split("}")[0].split("?")[0].split("'")[0]
            print(added)

            file1 = open("staples_cat.txt","w")
            file1.write(added +"\n")
