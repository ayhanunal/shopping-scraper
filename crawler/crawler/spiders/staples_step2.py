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
    name = "staples_step2"
    handle_httpstatus_list = [403]
    download_timeout = 120
    custom_settings = {
        "PROXY_PR_ON": True,
        # "PROXY_ON": True,
        # "PASSWORD": "1yocxe3k3sr3",
        "HTTPCACHE_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "FEED_EXPORT_ENCODING": "utf-8",
        "CONCURRENT_REQUESTS": 3,
        "COOKIES_ENABLED": False,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": .1,
        "AUTOTHROTTLE_MAX_DELAY": .3,
        "RETRY_TIMES": 3,
        "DOWNLOAD_DELAY": 3,
    }

    def start_requests(self):
        with open("staples_20210203.csv", "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                office_dict = {}
                office_dict["ProductPageURL"] = row["ProductPageURL"]
                office_dict["ImageURL"] = row["ImageURL"]
                office_dict["Description #2"] = row["Description #2"]
                office_dict["Description #1"] = row["Description #1"]
                office_dict["MFRPart #"] = row["MFRPart #"]
                office_dict["Manufacturer"] = row["Manufacturer"]
                office_dict["SKU"] = row["SKU"]
                office_dict["Availability"] = row["Availability"]
                office_dict["Price"] = row["Price"]

                yield Request(
                    url=row["ProductPageURL"],
                    callback=self.parse,
                    meta={
                        "office_dict":office_dict,
                        "purge_cookies": True,
                    }
                )


    def parse(self, response):
        office_dict = response.meta.get("office_dict", {})
        
        is403 = True if response.status == 403 else False
        
        if is403:
            yield Request(
                response.url,
                callback=self.parse,
                dont_filter=True,
                meta={
                    "office_dict" : office_dict,
                    "purge_cookies": True  
                },
            )
            return
        

        #categories
        used = set()
        categories = [
            x.replace("\n", "")
            .replace("\t", "")
            .replace("\r", "")
            .replace("\xa0", "")
            .strip()
            for x in response.xpath(
                "//div[@id='breadcrumbs_container']/ol/li//text()[.!='>']"
            ).extract()
        ]
        category_list = [
            x for x in categories if x not in used and (used.add(x) or True)
        ]
        if category_list:
            try:
                category_list.remove("Home")
                for i in range(len(category_list)):
                    if i < 4:
                        office_dict[f"Category #{i+1}"] = category_list[i]
            except:
                pass
        
        try:
            script_data_var1 = response.xpath("//script[contains(.,'PRELOADED_STATE')]/text()").get()
            if script_data_var1 and script_data_var1 != "":
                data = json.loads(script_data_var1.split("PRELOADED_STATE__ = ")[1].strip(";").strip())
            else:
                script_data_var2 = response.xpath("//script[@id='__NEXT_DATA__']//text()").get()
                if script_data_var2 and script_data_var2 != "":
                    data = json.loads(script_data_var2.strip())["props"]["initialStateOrStore"]
                else:
                    data = None
        except:
            data = None

        if data:
            try:
                product_info = data["skuState"]["skuData"]["items"][0]["product"]
            except:
                product_info = None
            
            if product_info:
                if not "Description #1" in office_dict or not office_dict["Description #1"]:
                    desc_1 = product_info["name"] if "name" in product_info and product_info["name"] else ""
                    if desc_1:
                        office_dict["Description #1"] = desc_1.replace('®', '').replace('™', '')
                    else:
                        desc_1 = response.xpath(
                            "normalize-space(//h1[@id='product_title']/text())"
                        ).get()
                        if desc_1:
                            desc_1 = (
                                desc_1.replace("\n", "")
                                .replace("\t", "")
                                .replace("\r", "")
                                .replace("\xa0", "")
                                .replace("\u00ae", "")
                                .replace("\u2122", "")
                                .replace('"', "").replace('®', '').replace('™', '')
                                .strip()
                            )
                            office_dict["Description #1"] = desc_1
    
                if not "MFRPart #" in office_dict or not office_dict["MFRPart #"]:
                    mfr_part = product_info["manufacturerPartNumber"] if "manufacturerPartNumber" in product_info and product_info["manufacturerPartNumber"] else ""
                    if mfr_part:
                        office_dict["MFRPart #"] = mfr_part
                    else:
                        mfr_part = "".join(
                            response.xpath(
                                "//span[@id='manufacturer_number']/text()"
                            ).extract()
                        )
                        if mfr_part:
                            mfr_part = mfr_part.split("#:")[1].strip()
                            office_dict["MFRPart #"] = mfr_part
    
                if not "Manufacturer" in office_dict or not office_dict["Manufacturer"]:
                    manufacturer = product_info["brandName"] if "brandName" in product_info and product_info["brandName"] else ""
                    if manufacturer:
                        office_dict["Manufacturer"] = manufacturer
    
                if not "UPC" in office_dict or not office_dict["UPC"]:
                    upc = product_info["upcCode"] if "upcCode" in product_info and product_info["upcCode"] else ""
                    if upc:
                        if int(upc) != 0:
                            office_dict["UPC"] = upc
    
                if not "SKU" in office_dict or not office_dict["SKU"]:
                    sku = product_info["partNumber"] if "partNumber" in product_info and product_info["partNumber"] else ""
                    if sku and sku != "":
                        office_dict["SKU"] = sku
    
                
                if not "Price" in office_dict or not office_dict["Price"]:
                    try:
                        price = str(
                            data["skuState"]["skuData"]["items"][0]["price"]["item"][0][
                                "data"
                            ]["priceInfo"][0]["finalPrice"]
                        )
                        office_dict["Price"] = price
                    except:
                        price = response.xpath(
                            "//div[@class='price-info__final_price']//text()"
                        ).get()
                        if price:
                            office_dict["Price"] = price.replace("$", "").strip()
                        else:
                            price = response.xpath(
                                "//div[@id='priceInfoContainer']//text()[contains(.,'$')]/parent::div/text()"
                            ).get()
                            if price:
                                office_dict["Price"] = price.replace("$", "").strip()

        if "SKU" not in office_dict and data:
            sku = "".join(response.xpath("//span[@id='item_number']/text()").extract())
            if sku:
                sku = sku.split("#:")[1].strip()
                office_dict["SKU"] = sku
            else:
                sku = response.url.split("/")[-1].split("_")[1]
                if sku:
                    office_dict["SKU"] = sku.strip()
                else:
                    office_dict["SKU"] = None

        yield office_dict




