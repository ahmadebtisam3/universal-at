import scrapy
import json
import logging

from scrapy.exporters import JsonItemExporter

from universal_proj.items import UniversalProjItem


class UniVeSpider(scrapy.Spider):
    name = 'uni_ve'
    allowed_domains = ['www.universal.at']
    start_urls = ['http://www.universal.at/']
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "referrer": "https://www.universal.at/sport-freizeit/"
    }
    link_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "max-age=0",
        "referrer": "https://www.universal.at/sport-freizeit/",
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self.u_logger = self.get_logger()
        self.exporter = self._exporter_for_item()

    @staticmethod
    def get_logger(name=__name__):
        # defining custom logger
        logger = logging.getLogger(name=name)
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("universal_spider.log")
        handler.setFormatter(
            logging.Formatter("%(name)s - %(levelname)s - %(message)s")
            )
        logger.addHandler(handler)
        return logger

    @staticmethod
    def _exporter_for_item():
        file = open("products.json", 'ab')
        exporter = JsonItemExporter(file)
        exporter.start_exporting()
        return exporter

    @staticmethod
    def get_search_body(ref):
        return "{\"previousRequest\":{\"query\":\"\",\"clientId\":\"UniversalAt\",\"count\":72,\"filters\":{},\"locale\":\"de_DE\",\"minAvailCode\":2,\"order\":\"relevance\",\"pageNoDisplay\":1,\"specialArticles\":[],\"start\":0,\"version\":15,\"noLegacyEsi\":false},\"userAgent\":\"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0\",\"source\":\"extern\",\"personalization\":\"$$-2$$web$$s-2\",\"channel\":\"web\",\"clientId\":\"UniversalAt\",\"count\":72,\"filters\":{},\"locale\":\"de_AT\",\"minAvailCode\":2,\"order\":\"relevance\",\"pageNoDisplay\":1,\"specialArticles\":[],\"start\":0,\"version\":15,\"noLegacyEsi\":false,\"uri\":\""+ref+"\",\"allowTest\":true,\"seoFiltered\":false,\"doRedirectToCategoryUrl\":false,\"hostname\":\"https://www.universal.at\",\"isBot\":false}"

    def parse(self, response):
        for uri in self.get_nav_links(response):
            sub_url = uri.xpath("@href").get()
            url = self.start_urls[0][:-1]+sub_url
            name = uri.xpath("text()")
            if name:
                name = sub_url[1:-1]
                print("url : ", url, "name :", name)
                yield response.follow(url, self.get_link_from_api,
                                      cb_kwargs={'name': name})

    def get_link_from_api(self, response, name):
        resp = scrapy.Request(
            url=f"https://www.universal.at/api/search/seo?clientId=UniversalAt&query=&uri=%2F{name}%2F&locale=de_AT",
            callback=self.link_collector,
            headers=self.link_headers,
            method='GET'
        )
        yield resp

    def link_collector(self, response):
        dic = json.loads(response.body)
        try:
            links = dic.get("toplinks")
            if links:
                for url in links['links']:
                    product_page_link = self.start_urls[0][:-1]+url['url']
                    self.u_logger.info(product_page_link)
                    # print(product_page_link)
                    yield self.get_data_from_search_api(url['url'])
        except KeyError as k:
            self.u_logger.error(k, exc_info=True)

    def get_data_from_search_api(self, ref):
        header = self.headers.copy()
        header["referrer"] = ref
        resp = scrapy.Request(
                           url="https://www.universal.at/api/search/search",
                           callback=self.collect_data,
                           headers=header,
                           body=self.get_search_body(ref),
                           method='POST',
                           errback=self.error_occured,
                                )
        return resp

    @staticmethod
    def get_nav_links(response):
        return response.xpath("//a[contains(@class, 'sh')]")

    def collect_data(self, response):
        print("response status : ", response)
        bas_url = self.start_urls[0][:-1]
        dic = json.loads(response.body)
        try:
            for product in dic["searchresult"]["result"]["products"]:
                item = UniversalProjItem()
                item['brand_name'] = product["brand"]["name"]
                item['name'] = product["name"]
                images = []
                price = []
                currency = []
                product_url = []
                sku = []
                for product_type in product["variations"]:
                    images.append(product_type["imageUrl"])
                    price.append(product_type["price"]["value"])
                    currency.append(product_type["price"]["currency"])
                    product_url.append(bas_url+product_type['productUrl'])
                    sku.append(product_type['sku'])
                item['image_url'] = images
                item['price'] = price
                item['currency'] = currency
                item['product_url'] = product_url
                item['sku'] = sku
                self.exporter.export_item(item)
            self.exporter.finish_exporting()
        except KeyError as e:
            self.u_logger.error(e, exc_info=True)

    def error_occured(self, response):
        self.u_logger.error("products not fetched "+str(response))
