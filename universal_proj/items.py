# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UniversalProjItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
    brand_name = scrapy.Field()
    data_sheet_url = scrapy.Field()
    image_url = scrapy.Field()
    old_price = scrapy.Field()
    price = scrapy.Field()
    currency = scrapy.Field()
    product_url = scrapy.Field()
    sku = scrapy.Field()
    
