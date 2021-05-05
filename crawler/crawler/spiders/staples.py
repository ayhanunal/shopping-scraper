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
    name = "staples"
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
        
    
    _all_categories = []
    def start_requests(self):

        with open("staples_cat.txt", "r") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0].strip():
                    cat_id = row[0].strip().replace("cat_", "")
                    api_link = "https://www.staples.com/searchux/api/v1/classProxy?SEARCHUX2=true&pn={}&ajaxRequest=true&deviceType=desktop&autoFilter=false&categoryId=" + cat_id
                    self._all_categories.append(api_link)

        
        # random.shuffle(self._all_categories)
        self._all_categories = list(set(self._all_categories))
        print(f"Total INDEX ::: {len(self._all_categories)}")
        
        url="https://www.staples.com/"
        yield Request(
            url,
            callback=self.all_category_request,
            dont_filter=True,
        )
    
    def all_category_request(self, response):
        current_index = response.meta.get("current_index", 0)
        yield Request(
            self._all_categories[current_index].format(1), #format(1) to request the first page
            callback=self.all_products_request,
            dont_filter=True,
            meta={
                "current_index" : current_index,
                "base_url" : self._all_categories[current_index],
            }
        )
    
    def all_products_request(self, response):
        current_index = response.meta.get("current_index")
        is403 = True if response.status == 403 else False
        page = response.meta.get("page", 2)
        
        print(f"CATEGORY ID :::: {response.url.split('categoryId=')[1]} - index: {current_index} - page: {page}")
        
        if is403:
            yield Request(
                url=self._all_categories[current_index+1].format(1),
                callback=self.all_products_request,
                dont_filter=True,
                meta={
                    "current_index" : current_index + 1,
                    "purge_cookies": True,
                    "base_url" : self._all_categories[current_index+1],
                }
            )
            return
    
        seen = False
        try:
            data = json.loads(response.body) #the result returned by the api - json
        except:
            data = None
        
        if data and "totalCount" in data and data["totalCount"] > 0:
            for p in data["products"]:
                seen = True
                office_dict = {}
                
                #url
                product_url = f"https://www.staples.com{p['url']}"
                office_dict["ProductPageURL"] = product_url

                #image
                if "image" in p and p["image"]:
                    office_dict["ImageURL"] = p["image"]

                #description #2
                if "description" in p and p["description"]:
                    if "paragraph" in p["description"] and "bullets" in p["description"]:
                        desc2 = " ".join(x for x in p["description"]["paragraph"]) + " " + " ".join(x for x in p["description"]["bullets"])
                        if desc2:
                            office_dict["Description #2"] = remove_tags(desc2).replace('®', '').replace('™', '')
                    elif "paragraph" in p["description"]:
                        desc2 = " ".join(x for x in p["description"]["paragraph"])
                        if desc2:
                            office_dict["Description #2"] = remove_tags(desc2).replace('®', '').replace('™', '')
                    elif "bullets" in p["description"]:
                        desc2 = " ".join(x for x in p["description"]["bullets"])
                        if desc2:
                            office_dict["Description #2"] = remove_tags(desc2).replace('®', '').replace('™', '')
                
                #description #1
                if "title" in p and p["title"]:
                    office_dict["Description #1"] = p["title"].replace('®', '').replace('™', '')

                #MFRPart #
                if "model" in p and p["model"]:
                    office_dict["MFRPart #"] = p["model"]

                #manufacturer
                if "manufacturerName" in p and p["manufacturerName"]:
                    office_dict["Manufacturer"] = p["manufacturerName"]
                
                #sku
                if "compareItemID" in p and p["compareItemID"]:
                    office_dict["SKU"] = p["compareItemID"]

                #availability
                if "inStoreOnly" in p and p["inStoreOnly"]:
                    office_dict["Availability"] = "Store Only"
                elif "isOutOfStock" in p and p["isOutOfStock"]:
                    office_dict["Availability"] = "Out of Stock"
                elif "isOutOfStock" in p and not p["isOutOfStock"]:
                    office_dict["Availability"] = "In Stock"
                
                #price
                if "priceValue" in p and p["priceValue"] and p["priceValue"] != 0:
                    office_dict["Price"] = str(p["priceValue"])
                elif "price" in p and p["price"]:
                    office_dict["Price"] = p["price"].replace("€", "").replace("$", "")
                    
                
                # cat_dict = data["breadCrumb"]
                # cat_array = []
                # if "thirdLevelName" in cat_dict:
                #     cat_array.append(cat_dict["thirdLevelName"])
                # if "secondLevelName" in cat_dict:
                #     cat_array.append(cat_dict["secondLevelName"])
                # if "firstLevelName" in cat_dict:
                #     cat_array.append(cat_dict["firstLevelName"])
                # if "name" in cat_dict:
                #     cat_array.append(cat_dict["name"])
                
                # used = set()
                # category_list = [
                #     x for x in cat_array if x not in used and (used.add(x) or True)
                # ]
                # if category_list:
                #     try:
                #         category_list.remove("Home")
                #         for i in range(len(category_list)):
                #             if i < 4:
                #                 office_dict[f"Category #{i+1}"] = category_list[i]
                #     except:
                #         pass
                
                
                #Go to product details ->parse
                # yield Request(
                #     product_url,
                #     callback=self.parse,
                #     meta={
                #         "office_dict" : office_dict,
                #         "purge_cookies": True  
                #     },

                # )
                
                yield office_dict

        if page == 2 or seen: #current categories pagination
            base_url = response.meta.get("base_url")
            headers = {
                "accept": "application/json",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
            }
            yield Request(
                base_url.format(page),
                callback=self.all_products_request,
                headers=headers,
                dont_filter=True,
                meta={
                    "page" : page+1,
                    "current_index" : current_index,
                    "base_url" : base_url,
                    "purge_cookies": True   
                }
            )
        elif current_index + 1 < len(self._all_categories): #next categories.
            yield Request(
                url=self._all_categories[current_index+1].format(1),
                callback=self.all_products_request,
                dont_filter=True,
                meta={
                    "current_index" : current_index + 1,
                    "purge_cookies": True,
                    "base_url" : self._all_categories[current_index+1],
                }
            )
        


        
    def parse(self, response):
        office_dict = response.meta.get("office_dict", {})
        
        # is403 = True if response.status == 403 else False
        
        # if is403:
        #     yield Request(
        #         response.url,
        #         callback=self.parse,
        #         dont_filter=True,
        #         meta={
        #             "office_dict" : office_dict,
        #             "purge_cookies": True  
        #         },
        #     )
        

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
            product_info = data["skuState"]["skuData"]["items"][0]["product"]

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




