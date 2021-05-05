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
    name = "quill"
    download_timeout = 120

    custom_settings = {
        # "PROXY_ON": True,
        # "PROXY_PR_ON": True,
        # "PASSWORD": "1yocxe3k3sr3",
        "HTTPCACHE_ENABLED": True,
        "LOG_LEVEL": "INFO",
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    def start_requests(self):
        start_urls = [
            "https://www.quill.com/bulk-printer-paper-and-office-paper/cbu/28.html",
            "https://www.quill.com/face-masks/SITE/search?keywords=face+masks&ajx=1",
            "https://www.quill.com/office-supplies/cbu/2.html",
            "https://www.quill.com/writing-supplies-instruments/cbd/1541.html",
            "https://www.quill.com/janitorial-office-cleaning-supplies/cbu/6.html",
            "https://www.quill.com/office-printers-and-scanners/cbu/31.html",
            "https://www.quill.com/business-laptops-and-desktop-computers/cbu/3.html",
            "https://www.quill.com/office-technology/cbx/305.html",
            "https://www.quill.com/coffee-water-snacks/cbu/34.html",
            "https://www.quill.com/discount-modern-office-furniture-chairs-desks-tables/cbu/1.html",
            "https://www.quill.com/teaching-and-school-supplies/cbu/36.html",
            "https://www.quill.com/shipping-supplies-and-mailing-envelopes/cbu/29.html",
            "https://www.quill.com/safety-supplies/cbu/35.html",
            "https://www.quill.com/workwear-and-uniforms/cbu/118.html",
            "https://www.quill.com/tools-maintenance-mro-supplies/cbu/39.html",
            "https://www.quill.com/bulk-medical-supplies/cbu/38.html",
            "https://www.quill.com/retail-store-supplies/cbx/46.html",
        ]
        for url in start_urls:
            yield Request(url, callback=self.jump, meta={"url":url})

    def jump(self, response):

        if response.xpath(
            "//div[@class='categoryDiv']//h3/a[@href!='']/@href"
        ).extract():
            for item in response.xpath(
                "//div[@class='categoryDiv']//h3/a[@href!='']/@href"
            ).extract():
                f_url = response.urljoin(item)
                yield Request(
                    url=f_url, callback=self.parse_menu,
                )

        elif response.xpath(
            "//li[@class='ul__li--featured']/a[@href!='']/@href"
        ).extract():
            for item in response.xpath(
                "//li[@class='ul__li--featured']/a[@href!='']/@href"
            ).extract():
                f_url = response.urljoin(item)
                yield Request(
                    url=f_url, callback=self.parse_menu,
                )

        # 1. ile ayni
        elif response.xpath(
            "//div[@class='trdShowFeat']/h3/a[@href!='']/@href"
        ).extract():
            for item in response.xpath(
                "//div[@class='trdShowFeat']/h3/a[@href!='']/@href"
            ).extract():
                f_url = response.urljoin(item)
                yield Request(
                    url=f_url, callback=self.parse_menu,
                )

        elif response.xpath("//img[contains(@alt,'Shop All')]/../../@href").extract():
            for item in response.xpath(
                "//img[contains(@alt,'Shop All')]/../../@href"
            ).extract():
                f_url = response.urljoin(item)
                yield Request(
                    url=f_url, callback=self.parse_menu,
                )
        else:
            yield Request(
                url=response.meta["url"], 
                dont_filter=True,
                callback=self.parse_menu,
            )

    def parse_menu(self, response):

        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath("//h3[@id='skuName']/a[@href!='']/@href").extract():
            f_url = response.urljoin(item)
            yield Request(
                url=f_url, callback=self.parse,
            )
            seen = True

        if page == 2 or seen:
            if "?" in response.url:
                if "?page" in response.url:
                    p_url = response.url.split("?page")[0] + f"?page={page}"
                else:
                    p_url = response.url.split("&page")[0] + f"&page={page}"
            else:
                p_url = response.url.split("?page")[0] + f"?page={page}"
            yield Request(url=p_url, callback=self.parse_menu, meta={"page": page + 1})

    def parse(self, response):
        # item_loader = ScrapyLoader(response=response)

        office_dict = {}

        sku = response.xpath(
            "//div[contains(@class,'skuImageZoom')]/img[@id='SkuPageMainImg']/@data-sku"
        ).get()
        if sku:
            # item_loader.add_value("SKU", sku)
            office_dict["SKU"] = sku
        else:
            sku = response.xpath("//div[@id='pnlTxtBox']/div/input/@data-sku").get()
            if sku:
                # item_loader.add_value("SKU", sku)
                office_dict["SKU"] = sku
            else:
                office_dict["SKU"] = None

        desc_1 = response.xpath("normalize-space(//h1[@class='skuName']/text())").get()
        if desc_1:
            desc_1 = (
                desc_1.replace("\n", "")
                .replace("\t", "")
                .replace("\r", "")
                .replace("\xa0", "")
                .replace("\u00ae", "")
                .replace("\u2122", "")
                .replace('"', "")
                .strip()
            )
            # item_loader.add_value("Description1", desc_1)
            office_dict["Description #1"] = desc_1

        desc_2 = "".join(response.xpath("//div[@class='qOverflow']//text()").extract())
        if desc_2:
            desc_2 = (
                desc_2.replace("\n", "")
                .replace("\t", "")
                .replace("\r", "")
                .replace("\xa0", "")
                .replace("\u00ae", "")
                .replace("\u2122", "")
                .replace('"', "")
                .strip()
            )
            # item_loader.add_value("Description2", desc_2)
            office_dict["Description #2"] = desc_2

        price = response.xpath(
            "//div[@id='PriceLabel']//span[@class='priceupdate']/text()"
        ).get()
        if price:
            # item_loader.add_value("Price", price.strip())
            office_dict["Price"] = price.strip()
        else:
            price = response.xpath(
                "normalize-space(//div[@id='PriceLabel']//span[@id='skuPriceLabel' and contains(@class,'red')]/text())"
            ).get()
            if price:
                # item_loader.add_value("Price", price.strip())
                office_dict["Price"] = price.strip()
            else:
                price = response.xpath(
                    "//div[@id='pnlTxtBox']/div/input/@data-price"
                ).get()
                if price:
                    # item_loader.add_value("Price", price.strip())
                    office_dict["Price"] = price.strip()

        availability = response.xpath(
            "//div[@class='skuDetailCol']/div[contains(@class,'out-of-stock-button')]/text()"
        ).get()
        if availability:
            # item_loader.add_value("Availability", "Out of Stock")
            office_dict["Availability"] = "Out of Stock"
        else:
            # item_loader.add_value("Availability", "In Stock")
            office_dict["Availability"] = "In Stock"

        used = set()
        categories = [
            x.replace("\n", "")
            .replace("\t", "")
            .replace("\r", "")
            .replace("\xa0", "")
            .strip()
            for x in response.xpath(
                "//ol[contains(@class,'breadCrumbSchema')]/li/a/span/text()"
            ).extract()
        ]
        category_list = [
            x for x in categories if x not in used and (used.add(x) or True)
        ]
        if category_list:
            try:
                for i in range(len(category_list)):
                    if i < 4:
                        # item_loader.add_value(f"Category{i+1}", category_list[i])
                        office_dict[f"Category #{i+1}"] = category_list[i]
            except:
                pass

        # category = " > ".join(response.xpath("//ol[contains(@class,'breadCrumbSchema')]/li/a/span/text()").extract())
        # if category:
        #     category = category.replace("\n","").replace("\t","").replace("\r","").replace("\xa0","").strip()
        #     item_loader.add_value("Category", category.strip())

        # item_loader.add_value("ProductPageURL", response.url)
        office_dict["ProductPageURL"] = response.url

        images = response.xpath(
            "//div[contains(@class,'skuImageZoom')]/img[@id='SkuPageMainImg']/@src"
        ).get()
        if images:
            images = "https:" + images
            # item_loader.add_value("ImageURL", images)
            office_dict["ImageURL"] = images

        manufacturer = response.xpath(
            "//span[.='Brand: ']/following-sibling::text()"
        ).get()
        if manufacturer:
            # item_loader.add_value("Manufacturer", manufacturer.strip())
            office_dict["Manufacturer"] = manufacturer.strip()
        else:
            manufacturer = response.xpath(
                "//td/span[.='Brand']/following-sibling::text()"
            ).get()
            if manufacturer:
                manufacturer = manufacturer.replace(":", "").strip()
                # item_loader.add_value("Manufacturer", manufacturer.strip())
                office_dict["Manufacturer"] = manufacturer.strip()

        MFR_part = response.xpath("//span[.='Item #:']/following-sibling::text()").get()
        if MFR_part:
            # item_loader.add_value("MFRPart", MFR_part.strip())
            office_dict["MFRPart #"] = MFR_part.strip()
        else:
            mfr_item = response.xpath("//div[@id='pnlTxtBox']/div/input")
            if mfr_item:
                effort_code = mfr_item.xpath("./@data-effortcode").get()
                find_number = mfr_item.xpath("./@data-findnumber").get()
                if effort_code and find_number:
                    MFR_part = effort_code + "-" + find_number
                    # item_loader.add_value("MFRPart", MFR_part)
                    office_dict["MFRPart #"] = MFR_part.strip()

        # yield item_loader.load_item()
        yield office_dict
