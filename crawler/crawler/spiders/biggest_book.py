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
    name = "biggest_book"
    download_timeout = 120

    custom_settings = {
        # "PROXY_ON": True,
        # "PROXY_PR_ON": True,
        "HTTPCACHE_ENABLED": True,
        "LOG_LEVEL": "INFO",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "x-api-key": "31BC6E02FD51DF7F7CE37186A31EE9B9DEF9C642526BC29F8201D81B669B9",
        "cache-control": "no-cache",
    }

    def start_requests(self):

        yield Request(
            "https://api.essendant.com/digital/digitalservices/search/v2/navigation?&vc=n",
            callback=self.parse,
            headers=self.headers,
        )

    def parse(self, response):
        data = json.loads(response.body)
        for cat in data["navigation"]["categories"]:
            for sub_cat in cat["subCategories"]:
                cat_name = cat["description"] + "/" + sub_cat["description"]
                cat_id = sub_cat["id"]
                f_url = f"https://api.essendant.com/digital/digitalservices/search/v2/search?fc={cat_id}&cr=1&rs=48&vc=n"
                yield Request(
                    f_url,
                    callback=self.parse_listing,
                    headers=self.headers,
                    meta={"cat_name": cat_name, "cat_id": cat_id,},
                )

    def parse_listing(self, response):

        page = response.meta.get("page", 49)

        data = json.loads(response.body)
        total_result = data["searchResult"]["pageContext"]["availableResults"]
        for item in data["searchResult"]["products"]:
            win_code = item["win"]
            office_data = {
                "price": str(item["actualPrice"]),
                "manufacturer": item["brand"]["description"],
                "desc_1": item["description"],
                "image": "http:" + item["image"]["url"],
                "cat_name": response.meta.get("cat_name"),
                "win_code": win_code,
            }
            f_url = f"https://api.essendant.com/digital/digitalservices/search/v2/items?&vc=n&sgs=Simple&win={win_code}&"
            yield Request(
                f_url,
                callback=self.parse_office,
                headers=self.headers,
                meta=office_data,
            )

        if page <= total_result:
            cat_id = response.meta.get("cat_id")
            f_url = f"https://api.essendant.com/digital/digitalservices/search/v2/search?fc={cat_id}&cr={page}&rs=48&vc=n"
            yield Request(
                f_url,
                callback=self.parse_listing,
                headers=self.headers,
                meta={
                    "cat_name": response.meta.get("cat_name"),
                    "cat_id": cat_id,
                    "page": page + 48,
                },
            )

    def parse_office(self, response):
        # item_loader = ScrapyLoader(response=response)

        office_dict = {}

        price = response.meta.get("price")
        manufacturer = response.meta.get("manufacturer")
        desc_1 = response.meta.get("desc_1")
        image = response.meta.get("image")

        win_code = response.meta.get("win_code")
        ext_url = f"https://www.biggestbook.com/ui#/itemDetail?itemId={win_code}&uom=BX&sgs=Simple&cm_sp=Home-{win_code}_SpotNaN"

        try:
            data = json.loads(response.body)
            content = data["items"][0]

            used = set()
            categories = response.meta.get("cat_name").split("/")
            category_list = [
                x.strip() for x in categories if x not in used and (used.add(x) or True)
            ]
            category_list.append(content["categories"][0]["description"])
            if category_list:
                try:
                    for i in range(len(category_list)):
                        if i < 4:
                            # item_loader.add_value(f"Category{i+1}", category_list[i])
                            office_dict[f"Category #{i+1}"] = category_list[i]
                except:
                    pass

            if win_code:
                # item_loader.add_value("SKU", win_code)
                office_dict["SKU"] = win_code

            if desc_1:
                # item_loader.add_value("Description1", desc_1)
                office_dict["Description #1"] = desc_1

            desc_2 = content["sellingCopy"]
            if desc_2:
                # item_loader.add_value("Description2", desc_2)
                office_dict["Description #2"] = desc_2

            if price:
                # item_loader.add_value("Price", price)
                office_dict["Price"] = price

            # if category:
            #     item_loader.add_value("Category", category)

            # item_loader.add_value("ProductPageURL", ext_url)
            office_dict["ProductPageURL"] = ext_url

            MFR_part = content["mpn"]
            if MFR_part:
                # item_loader.add_value("MFRPart", MFR_part)
                office_dict["MFRPart #"] = MFR_part

            if image:
                # item_loader.add_value("ImageURL", image)
                office_dict["ImageURL"] = image

            if manufacturer:
                # item_loader.add_value("Manufacturer", manufacturer)
                office_dict["Manufacturer"] = manufacturer

            upc = content["upc"]
            if upc and upc != "000000000000":
                # item_loader.add_value("UPC", upc)
                office_dict["UPC"] = upc

            unspsc = content["unspsc"]
            if unspsc and unspsc != "000000000000":
                # item_loader.add_value("UNSPSC", unspsc)
                office_dict["UNSPSC"] = unspsc
        except:
            pass

        # yield item_loader.load_item()
        yield office_dict
