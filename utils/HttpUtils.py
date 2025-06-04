import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO
import gzip
import ssl
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpUtils:
    @staticmethod
    def do_get(url, headers=None):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        try:
            response = session.get(url, headers=headers, verify=False)
            return response
        except Exception as e:
            print(f"do_get error ==> {url} {e}")
            return None

    @staticmethod
    def do_post(url, headers=None, data=None, json_data=None):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        try:
            if json_data:
                response = session.post(url, headers=headers, json=json_data, verify=False)
            else:
                response = session.post(url, headers=headers, data=data, verify=False)
            return response
        except Exception as e:
            print(f"do_post error ==> {url} {e}")
            return None

    @staticmethod
    def get_content(response):
        if response is None:
            return ""

        try:
            if 'gzip' in response.headers.get('Content-Encoding', '').lower():
                return gzip.decompress(response.content).decode('utf-8')
            return response.text
        except Exception as e:
            print(f"get_content error ==> {e}")
            return ""

