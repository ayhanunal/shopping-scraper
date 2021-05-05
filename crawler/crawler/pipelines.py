# -*- coding: utf-8 -*-

from scrapy.exceptions import DropItem
from datetime import datetime
import string
import re


class CrawlerPipeline(object):

    def __init__(self):
        self.ids_seen = set()
        
    def process_item(self, item, spider):

        if "sku_passed" not in item:
            if "SKU" not in item or not item["SKU"]:
                raise DropItem("SKU missing: %s" % item)
            
        if "Price Date" not in item or not item["Price Date"]:
            item["Price Date"] = datetime.now().strftime("%Y-%m-%d")
                
        if "Price" in item and item["Price"]:
            item["Price"] = item["Price"].replace("$", "").strip()
             
        if 'Description #1' in item and item['Description #1']:
            item['Description #1'] = item['Description #1'].replace('<br/>', '').replace('®', '').replace('™', '')
        
        if 'Description #2' in item and item['Description #2']:
            item['Description #2'] = item['Description #2'].replace('®', '').replace('™', '')
        
        if 'Manufacturer' in item and item['Manufacturer']:
            item['Manufacturer'] = item['Manufacturer'].replace('®', '').replace('™', '')
        
        if 'Category #1' in item and item['Category #1']:
            item['Category #1'] = item['Category #1'].replace('®', '').replace('™', '')
        
        if 'Category #2' in item and item['Category #2']:
            item['Category #2'] = item['Category #2'].replace('®', '').replace('™', '')
        
        if 'Category #3' in item and item['Category #3']:
            item['Category #3'] = item['Category #3'].replace('®', '').replace('™', '')
        
        if 'Category #4' in item and item['Category #4']:
            item['Category #4'] = item['Category #4'].replace('®', '').replace('™', '')
        
        if "SKU" in item and item["SKU"]:
            item["SKU"] = item["SKU"].strip()
            if "MFRPart #" not in item or not item["MFRPart #"] or len(item["MFRPart #"]) == 0:
                item["MFRPart #"] = item["SKU"]
        else:
            item["SKU"] = ""
            if "MFRPart #" not in item or not item["MFRPart #"] or len(item["MFRPart #"]) == 0:
                item["MFRPart #"] = ""
            
        for field in item.keys():
            if item[field]:
                if item[field] == "null" or item[field] == "None" or item[field] == "none":
                    item[field] = ""
                
                try:
                    item[field] = item[field].strip()
                except:
                    try:
                        item[field] = item[field]
                        item[field] = item[field].decode('utf-8').strip().encode('ascii', 'ignore')
                    except:
                        pass
                    
            else:
                item[field] = ""
        
    
        if "sku_passed" in item and item["sku_passed"]:
            del item["sku_passed"]
            return item
        else:
            if item["SKU"] in self.ids_seen:
                raise DropItem("Duplicate item: %s" % item )
            else:
                self.ids_seen.add(item["SKU"])
                return item