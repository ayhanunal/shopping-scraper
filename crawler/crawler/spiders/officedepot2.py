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
import random
import csv
import logging
import time
import traceback
from collections import OrderedDict
from w3lib.html import remove_tags


class My_Spider(Spider):
    name = "officedepot2"
    download_timeout = 120

    custom_settings = {
        # "PROXY_ON": True,
        # "PROXY_PR_ON": True,
        "HTTPCACHE_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "FEED_EXPORT_ENCODING": "utf-8",
        "DOWNLOAD_DELAY": 3,
        "RETRY_HTTP_CODES": [500, 503, 504, 400, 401, 403, 405, 407, 408, 416, 456, 502, 429, 307],
        "CONCURRENT_REQUESTS": 3,
    }
    headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
        "upgrade-insecure-requests": "1",
    },

    _all_categories = []
    _current_index = 0
    def start_requests(self):
        with open("officedepot_cat.txt", "r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0].strip():
                    cat_url = row[0].strip().strip("/") + "&recordsPerPageNumber=72&No=0/"
                    self._all_categories.append(cat_url)

        
        # random.shuffle(self._all_categories)
        self._all_categories = list(set(self._all_categories))
        print(f"Total INDEX ::: {len(self._all_categories)}")
        
        yield Request(
            self._all_categories[self._current_index],
            callback=self.parse_categorie,
            headers=self.headers,
        )

    product_count = 0
    def parse_categorie(self, response):
        for item in response.xpath("//div[@id='productView']/div//div[@class='photo_no_QV flcl']/a[1]/@href").extract():
            self.product_count += 1
            yield Request(
                url=response.urljoin(item), callback=self.parse, headers=self.headers,
            )

        next_page = response.xpath("//a[.='Next']/@href").get()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse_categorie,
                headers=self.headers,
            )
        elif self._current_index + 1 < len(self._all_categories):
            self._current_index += 1
            yield Request(
                self._all_categories[self._current_index],
                callback=self.parse_categorie,
                headers=self.headers,
            )
        else:
            print(f"Spider END !! Total Product: {self.product_count}")
                
    def parse(self, response):
        # item_loader = ScrapyLoader(response=response)

        office_dict = {}

        try:
            sku = response.xpath(
                "//td[contains(.,'Item')]/following-sibling::*/text()"
            ).get()
            if sku:
                # item_loader.add_value("SKU", sku.strip())
                office_dict["SKU"] = sku.strip()
            else:
                return

            desc2 = "".join(
                response.xpath(
                    "//section[@id='descriptionContent']/div//text()"
                ).extract()
            )
            if desc2:
                desc2 = (
                    desc2.replace("\n", "")
                    .replace("\t", "")
                    .replace("\r", "")
                    .replace("\xa0", "")
                    .replace("\u00ae", "")
                    .replace("\u2122", "")
                    .replace('"', "")
                    .strip()
                )
                # item_loader.add_value("Description2", desc2)
                office_dict["Description #2"] = desc2

            MFR_part = response.xpath(
                "//td[contains(.,'Manufacturer')]/following-sibling::*/text()"
            ).get()
            if MFR_part:
                # item_loader.add_value("MFRPart", MFR_part.strip())
                office_dict["MFRPart #"] = MFR_part.strip()

            manufacturer = response.xpath(
                "//td[contains(.,'manufacturer')]/following-sibling::*/text()"
            ).get()
            if manufacturer:
                manufacturer = manufacturer.strip()
            else:
                manufacturer = response.xpath(
                    "normalize-space(//td[contains(.,'brand name')]/following-sibling::*/text())"
                ).get()
                if manufacturer:
                    manufacturer = manufacturer.strip()

            if "No Brand" not in manufacturer:
                # item_loader.add_value("Manufacturer", manufacturer)
                office_dict["Manufacturer"] = manufacturer

            price = response.xpath("//span[@class='price_column right ']/text()").get()
            if price:
                # item_loader.add_value("Price", price.strip())
                office_dict["Price"] = price.strip()

            availability = "".join(
                response.xpath("//div[@class='deliveryMessage']//text()").extract()
            )
            if availability:
                # item_loader.add_value("Availability", availability.strip())
                office_dict["Availability"] = availability.strip()
            else:
                availability = response.xpath(
                    "normalize-space(//p[@class='bopisLabel']//text())"
                ).get()
                if availability:
                    # item_loader.add_value("Availability", availability.strip())
                    office_dict["Availability"] = availability.strip()

            used = set()
            categories = [
                x.replace("\n", "")
                .replace("\t", "")
                .replace("\r", "")
                .replace("\xa0", "")
                .strip()
                for x in response.xpath(
                    "//div[@id='siteBreadcrumb']/ol/li//span/text()"
                ).extract()
            ]
            category_list = [
                x for x in categories if x not in used and (used.add(x) or True)
            ]
            if category_list:
                try:
                    category_list.remove("Home")
                    category_list.remove("Product Details")
                    for i in range(len(category_list)):
                        if i < 4:
                            # item_loader.add_value(f"Category{i+1}", category_list[i])
                            office_dict[f"Category #{i+1}"] = category_list[i]
                except:
                    pass

            # category = "/".join(response.xpath("//div[@id='siteBreadcrumb']/ol/li//span/text()").extract())
            # if category:
            #     category = category.replace("\n","").replace("\t","").replace("\r","").replace("\xa0","").strip()
            #     item_loader.add_value("Category", category.strip())

            # item_loader.add_value("ProductPageURL", response.url)
            office_dict["ProductPageURL"] = response.url

            images = [
                x
                for x in response.xpath(
                    "//meta[@property='og:image']/@content"
                ).extract()
            ]
            if images and len(images) > 0:
                # item_loader.add_value("ImageURL", images)
                office_dict["ImageURL"] = images

            desc1 = "".join(response.xpath("//h1[@itemprop='name']/text()").get())
            if desc1:
                desc1 = (
                    desc1.replace("\n", "")
                    .replace("\t", "")
                    .replace("\r", "")
                    .replace("\xa0", "")
                    .replace("\u00ae", "")
                    .replace("\u2122", "")
                    .replace('"', "")
                    .strip()
                )
                # item_loader.add_value("Description1", desc1)
                office_dict["Description #1"] = desc1

            upc = response.xpath("//div[@class='wc-fragment'][1]/@data-gtin").get()
            if upc:
                # item_loader.add_value("UPC", upc)
                office_dict["UPC"] = upc

        except:
            pass

        # Status
        # Supplier
        # UNSPSC

        # yield item_loader.load_item()
        yield office_dict
