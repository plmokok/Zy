# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, unquote
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        # ... (init 方法与方案一相同)
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?1',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=2',
        }
        try:self.proxies = json.loads(extend)
        except:self.proxies = {}
        self.hsot=self.gethost()
        # self.hsot='https://hd.hdys2.com'
        self.headers.update({'referer': f"{self.hsot}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        self.dynamic_referer = None 
        pass

    # ... (其他方法保持与方案一相同，直到 playerContent) ...
    
    def playerContent(self, flag, id, vipFlags):
        # 此方法中没有 requests.get 调用，保持与方案一相同
        # ...
        pass
        
    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url,param['type'])

    def gethost(self):
        params = {
            'v': '1',
        }
        self.headers.update({'referer': 'https://a.hdys.top/'})
        # 【修改：禁用 SSL 校验】
        response = self.session.get('https://a.hdys.top/assets/js/config.js',proxies=self.proxies, params=params, headers=self.headers, verify=False)
        return self.host_late(response.text.split(';')[:-4])

    # ... (getlist, getpq 方法保持与方案一相同) ...
    
    def host_late(self, url_list):
        if isinstance(url_list, str):
            urls = [u.strip() for u in url_list.split(',')]
        else:
            urls = url_list

        if len(urls) <= 1:
            return urls[0] if urls else ''

        results = {}
        threads = []

        def test_host(url):
            try:
                url=re.findall(r'"([^"]*)"', url)[0]
                start_time = time.time()
                self.headers.update({'referer': f'{url}/'})
                # 【修改：禁用 SSL 校验】
                response = requests.head(url,proxies=self.proxies,headers=self.headers,timeout=1.0, allow_redirects=False, verify=False)
                delay = (time.time() - start_time) * 1000
                results[url] = delay
            except Exception as e:
                results[url] = float('inf')

        for url in urls:
            t = threading.Thread(target=test_host, args=(url,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return min(results.items(), key=lambda x: x[1])[0]

    def m3Proxy(self, url):
        # 应用动态 Referer/Origin
        m3u8_header = self.pheader.copy()
        if self.dynamic_referer:
            m3u8_header['Referer'] = self.dynamic_referer
            m3u8_header['Origin'] = self.dynamic_referer.rstrip('/')

        # 【修改：禁用 SSL 校验】
        ydata = requests.get(url, headers=m3u8_header, proxies=self.proxies, allow_redirects=False, verify=False)
        data = ydata.content.decode('utf-8')
        
        # 处理重定向
        if ydata.headers.get('Location'):
            url = ydata.headers['Location']
            # 重定向后的请求使用相同的 Header
            # 【修改：禁用 SSL 校验】
            ydata = requests.get(url, headers=m3u8_header, proxies=self.proxies, verify=False)
            data = ydata.content.decode('utf-8')
            
        lines = data.strip().split('\n')
        last_r = url[:url.rfind('/')]
        parsed_url = urlparse(url)
        durl = parsed_url.scheme + "://" + parsed_url.netloc
        for index, string in enumerate(lines):
            if '#EXT' not in string:
                if 'http' not in string:
                    domain=last_r if string.count('/') < 2 else durl
                    string = domain + ('' if string.startswith('/') else '/') + string
                lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegur", data]

    def tsProxy(self, url,type):
        # 应用动态 Referer/Origin
        h = self.pheader.copy()
        if type=='img':
            h = self.headers.copy()
        
        if self.dynamic_referer:
            h['Referer'] = self.dynamic_referer
            h['Origin'] = self.dynamic_referer.rstrip('/')
            
        if 'User-Agent' not in h:
             h['User-Agent'] = self.headers.get('User-Agent', self.pheader.get('User-Agent'))

        # 【修改：禁用 SSL 校验】
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True, verify=False)
        return [200, data.headers['Content-Type'], data.content]

    # ... (proxy, getProxyUrl, e64, d64 方法保持与方案一相同) ...
