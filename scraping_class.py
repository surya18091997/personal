import asyncio
import concurrent.futures
import io
import json
import time
from datetime import datetime
from itertools import repeat

import aiohttp
import grequests
import pandas as pd
import requests
from bs4 import BeautifulSoup
from lxml import etree

PROXIES = {
    "http": "http://6586a20482ca48bfb1f5c845fe3ab37a:@proxy.crawlera.com:8010/",
    "https": "http://6586a20482ca48bfb1f5c845fe3ab37a:@proxy.crawlera.com:8010/",
}
async_proxy = "http://6586a20482ca48bfb1f5c845fe3ab37a:@proxy.crawlera.com:8010"

# headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
# res=requests.get('http://watchoutinvestors.com/wilful_defaulters.asp',proxies=PROXIES)
# res=requests.get('https://nsdl.co.in/downloadables/excel/Issuer_Details_September_2022.xlsx',headers=headers)
# res.raise_for_status()


def get_table_data_frm_response(table_page_response, condition, need_anchor=[]):
    dom = BeautifulSoup(table_page_response.content, "lxml")
    if "xpath" in condition.keys():
        dom = etree.HTML(str(dom))
        dom = dom.xpath(condition["xpath"])[0]
        dom = BeautifulSoup(etree.tostring(dom), "lxml")
    else:
        dom = dom.find("table", **condition)
    table_headers = [header.text.strip() for header in dom.find_all("th")]
    table_data_dict = []
    for row in (dom.find_all("tr"))[1:]:
        row_data_element = row.find_all("td")
        row_data_text = [td.text for td in row.find_all("td")]
        row_data_dict = dict(zip(table_headers, row_data_text))
        if need_anchor:
            for anchor_col in need_anchor:
                href_tag_name = anchor_col + "_href"
                anchor_tags = row_data_element[
                    table_headers.index(anchor_col)
                ].find_all("a")
                row_data_dict[href_tag_name] = [
                    anchor.get("href") for anchor in anchor_tags
                ]
        table_data_dict.append(row_data_dict)
    return table_data_dict


def get_df_from_response(response, **kwargs):
    if "Content-Disposition" in response.headers.keys():
        file_type_str = response.headers["Content-Disposition"]
    else:
        file_type_str = response.url.split("/")[-1]
    with io.BytesIO(response.content) as file_bytes:
        if ".xlsx" in file_type_str:
            df = pd.read_excel(file_bytes, engine="openpyxl", **kwargs)
        elif ".xls" in file_type_str:
            df = pd.read_excel(file_bytes, engine="xlrd", **kwargs)
        elif ".csv" in file_type_str:
            df = pd.read_csv(file_bytes, **kwargs)
        else:
            df = None
        return df, file_type_str


def get_df_data(df, to_dump=False):
    if df.shape[0]:
        df_data = df.to_json(orient="records")
        if not to_dump:
            df_data = json.loads(df_data)
        return df_data


def multithreaded_method(url, *args):
    kwargs = args[0]
    response = requests.get(url, **kwargs)
    return response


def run_multithreading(method, max_workers, *args, **kwargs):
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        result = executor.map(method, *args)
        if result:
            return [res for res in result]


def run_async_requests(url_list, **kwargs):
    req_gen = (grequests.get(u, **kwargs) for u in url_list)
    resp_list = grequests.map(req_gen)
    return resp_list


# get_table_data_frm_response(res,condition={"class_":""},need_anchor=["Defaulter Name"])
# result=run_multithreading(multithreaded_method,5,[i for i in range(1,100)])


class CrawlingBase:
    def __init__(self) -> None:
        self.session = requests.session()

    def get(self, url, **kwargs):
        """
        Get Method call
        kwargs - This params should be related to python-requests library
        """

        response = self.session.get(url, **kwargs)
        return response

    @staticmethod
    def run_multithreading(method, max_workers, *args):
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            result = executor.map(method, *args)
            return [res for res in result]


class B(CrawlingBase):
    def __init__(self, login=False) -> None:
        super().__init__()
        self.requests_dict = {"verify": False}
        if not login:
            self.requests_dict.update({"proxies": PROXIES})
        self.run_datetime = datetime.now()

    def get(self, url, **kwargs):
        response = CrawlingBase.get(self, url, **kwargs, **self.requests_dict)
        response.raise_for_status()
        return response

    def multithreaded_get(self, url, kwargs={}):
        response = self.get(url, **kwargs)
        return response

    def run_multithreaded_requests(self, max_workers, urls_list, request_kwargs=None):
        if request_kwargs:
            result = self.run_multithreading(
                self.multithreaded_get, max_workers, urls_list, request_kwargs
            )
        else:
            result = self.run_multithreading(
                self.multithreaded_get, max_workers, urls_list
            )
        return result

    def run_async_requests(self, url_list, **kwargs):
        async def async_get(url, session):
            async with session.get(
                url=url, ssl=False, proxy=async_proxy, **kwargs
            ) as response:
                if response.status != 200:
                    raise ValueError("Request Failed")
                response = await response.text()
                return response

        async def main():
            async with aiohttp.ClientSession() as session:
                result = await asyncio.gather(
                    *[async_get(url, session) for url in url_list]
                )
            return result

        result = asyncio.run(main())
        return result


urls = [
    "https://pokeapi.co/api/v2/pokemon/1",
    "https://pokeapi.co/api/v2/pokemon/2",
    "https://pokeapi.co/api/v2/pokemon/3",
    "https://pokeapi.co/api/v2/pokemon/4",
    "https://pokeapi.co/api/v2/pokemon/5",
    "https://pokeapi.co/api/v2/pokemon/6",
    "https://pokeapi.co/api/v2/pokemon/7",
    "https://pokeapi.co/api/v2/pokemon/8",
    "https://pokeapi.co/api/v2/pokemon/9",
    "https://pokeapi.co/api/v2/pokemon/10",
]
q = B()
start_time = time.time()
# result=q.run_multithreaded_requests(2,urls)
result = q.run_async_requests(urls)
print("time_taken  ", time.time() - start_time)
