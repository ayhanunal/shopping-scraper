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
    name = "wbmason2"
    download_timeout = 120

    custom_settings = {
        "PROXY_ON": True,
        # "PROXY_PR_ON": True,
        "PASSWORD": "1yocxe3k3sr3",
        "HTTPCACHE_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def start_requests(self):
        url = "https://www.wbmason.com/"
        yield Request(url, callback=self.jump)

    def jump(self, response):
        for l1 in response.xpath("//li[@class='dep-tab']/ul/li/div/a"):
            cat1 = l1.xpath('./span/text()').extract_first().strip()
            clist1 = list()
            clist1.append(cat1)
            for l2 in l1.xpath("./../../ul//li//a[contains(@href,'SearchResult')]"):
                url2 = response.urljoin(l2.xpath('./@href').extract_first())
                cat2 = l2.xpath('./text()').extract_first()
                if cat2:
                    cat2 = cat2.strip()
                else:
                    cat2 = ""

                clist2 = list(clist1)
                clist2.append(cat2)

                yield Request(url2, callback=self.parse_listing, meta={'catlist': clist2})

    def parse_listing(self, response):
        catlist = response.meta.get('catlist')

        if response.xpath("//div[@class='products-grid']/div/div/a/@href"):

            for item in response.xpath(
                "//div[@class='products-grid']/div/div/a/@href"
            ).extract():
                yield Request(
                    url=response.urljoin(item),
                    callback=self.parse,
                    meta={
                        "cat1": catlist[0],
                        "cat2": catlist[1],
                    },
                )

            next_page = response.xpath("//a[@class='forward-one']/@href").get()
            if next_page:
                yield Request(
                    url=response.urljoin(next_page),
                    callback=self.parse_listing,
                    meta={
                        'catlist': catlist
                    },
                )

        elif response.xpath("//div[@class='item-container-cat']/a/@href"):
            print("PARSE LISTING - ELIF")
            # for item in response.xpath(
            #     "//div[@class='item-container-cat']/a/@href"
            # ).extract():
            #     yield Request(
            #         url=response.urljoin(item),
            #         callback=self.parse_sub_categories,
            #         meta={
            #             "cat1": response.meta.get("cat1"),
            #             "cat2": response.meta.get("cat2"),
            #         },
            #     )
        else:
            print("PARSE LISTING - ELSE")

    # def parse_sub_categories(self, response):

    #     if response.xpath("//div[@class='products-grid']/div/div/a/@href").extract():
    #         yield Request(
    #             url=response.url,
    #             callback=self.parse_product,
    #             meta={
    #                 "cat1": response.meta.get("cat1"),
    #                 "cat2": response.meta.get("cat2"),
    #             },
    #         )
    #     elif response.xpath("//div[@class='pp-button-contain']/a/@href").extract():
    #         for item in response.xpath(
    #             "//div[@class='pp-button-contain']/a/@href"
    #         ).extract():
    #             yield Request(
    #                 url=response.urljoin(item),
    #                 callback=self.parse_product,
    #                 meta={
    #                     "cat1": response.meta.get("cat1"),
    #                     "cat2": response.meta.get("cat2"),
    #                 },
    #             )

    def parse(self, response):
        # item_loader = ScrapyLoader(response=response)

        office_dict = {}

        if response.xpath("//input[@value='Add To Cart']"):
            # item_loader.add_value("Availability", "In Stock")
            office_dict["Availability"] = "In Stock"
        else:
            # item_loader.add_value("Availability", "Out Of Stock")
            office_dict["Availability"] = "Out Of Stock"

        category1 = response.meta.get("cat1")
        category2 = response.meta.get("cat2")
        if category1:
            # item_loader.add_value("Category1", category1)
            office_dict["Category #1"] = category1
            if category2:
                # item_loader.add_value("Category2", category2)
                office_dict["Category #2"] = category2
        elif category1 == None and category2:
            # item_loader.add_value("Category1", category2)
            office_dict["Category #1"] = category2

        script_data = response.xpath("//script[contains(.,'@context')]/text()").get()
        if script_data and script_data != "":
            data = json.loads(script_data)

            if "name" in data:
                desc1 = data["name"]
                # item_loader.add_value("Description1", desc1)
                office_dict["Description #1"] = desc1

            if "image" in data:
                image = data["image"][0]
                # item_loader.add_value("ImageURL", image)
                office_dict["ImageURL"] = image

            if "description" in data:
                desc2 = data["description"]
                # item_loader.add_value("Description2", desc2)
                office_dict["Description #2"] = desc2

            if "sku" in data:
                sku = data["sku"]
                # item_loader.add_value("SKU", sku)
                office_dict["SKU"] = sku
            else:
                office_dict["SKU"] = None

            if "brand" in data and "name" in data["brand"]:
                manufacturer = data["brand"]["name"]
                # item_loader.add_value("Manufacturer", manufacturer)
                office_dict["Manufacturer"] = manufacturer

            if "offers" in data:
                if "url" in data["offers"]:
                    ext_url = data["offers"]["url"]
                    # item_loader.add_value("ProductPageURL", ext_url)
                    office_dict["ProductPageURL"] = ext_url
                if "price" in data["offers"]:
                    price = data["offers"]["price"]
                    # item_loader.add_value("Price", price.strip())
                    office_dict["Price"] = price.strip()
                else:
                    price = response.xpath(
                        "//div[@class='item-price']/div/span/text()"
                    ).get()
                    if price:
                        # item_loader.add_value("Price", price.replace("$","").strip())
                        office_dict["Price"] = price.replace("$", "").strip()
                    else:
                        price = response.xpath(
                            "//div[contains(@class,'pos-relative')]//text()[contains(.,'$')]"
                        ).get()
                        if price:
                            # item_loader.add_value("Price", price.replace("$","").strip())
                            office_dict["Price"] = price.replace("$", "").strip()

        # Supplier
        # UNSPSC
        # UPC

        # yield item_loader.load_item()
        yield office_dict
