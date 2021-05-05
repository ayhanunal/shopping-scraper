from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose

def strip_newlines(x):
    return x.replace("\n"," ").strip().strip("\n").strip()
    
class ScrapyLoader(ItemLoader):
    default_input_processor = MapCompose(strip_newlines)
    default_output_processor = TakeFirst()
    