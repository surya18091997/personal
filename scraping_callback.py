from itertools import repeat

from html_extractor import extract
from scraping_pipeline import ScrapingPipeline


def callback(callback_func,*cargs,**ckwargs):
    def dec1(func):
        def modded_deco():
            if not callable(callback_func):
                return func()
            initial_func_return_val =  func()
            if initial_func_return_val:
                return callback_func(initial_func_return_val,*cargs,**ckwargs)
            return callback_func(*cargs,**ckwargs)
        return modded_deco
    return dec1


class StaticScraping(ScrapingPipeline):
    def __init__(self,config) -> None:
        for key,value in config.items():
            self.__setattr__(key,value)
        super().__init__(self.login)
        self.output = []
        self.file_counter = 0

    def write_callback(self):
        print(self.output)
        print(self.file_counter)
        #write_to_s3
        pass

    def scrape_known_urls(self):
        n = 10000
        no_of_workers = len(self.urls)/50 if len(self.urls)>100 else 2

        @callback(getattr(self,"crawl_callback",self.write_callback))
        def get_page_data():
            response_list = self.run_multithreaded_requests(no_of_workers,urls,repeat(self.request_kwargs))
            for response in response_list:
                data = extract(self.extractor_config, response.text)
                self.output.append(data)
        
        urls_list = [self.urls[i:i+n] for i in range(0, len(self.urls), n)]
        for urls in urls_list:
            get_page_data()
        self.file_counter+=1

    def paginate_and_scrape(self):
        pass

        









extractor_config = {
    #"isin": "//tr[contains(./td[1],'ISIN')]/td[2]/text()",
    "issuer_name": "//tr[contains(./td[1],'Issuer Name')]/td[2]",
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
}

config = {
    "login":False,
    #"need_urls":False,
    #"scraping_page_url":"",
    "extractor_config":extractor_config,
    "urls":["https://www.indiabondinfo.nsdl.com/bds-web/homePortal.do?action=searchDtls&isinno=INE0D4F08011",
                "https://www.indiabondinfo.nsdl.com/bds-web/homePortal.do?action=searchDtls&isinno=INE501X07356",
                "https://www.indiabondinfo.nsdl.com/bds-web/homePortal.do?action=searchDtls&isinno=INE540P07350"],
    "request_kwargs":{"headers":headers},
    #"callback":None
}
a=StaticScraping(config)
a.scrape_known_urls()
