# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, urljoin  # 引入 urljoin, urlparse
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        # 保持原始代码不变
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
        pass

    def getName(self):
        pass

    # ... (其他方法保持不变)

    pheader={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
        'dnt': '1',
        'sec-ch-ua-mobile': '?1',
        # 'origin': 'https://jx.8852.top', # 移除硬编码，在 playerContent 中动态添加
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'zh-CN,zh;q=0.9',
        'priority': 'u=1, i',
        # 'referer': '' # 移除硬编码，在 playerContent 中动态添加
    }
    
    # 辅助函数：根据URL生成播放请求头，避免重复代码
    def get_pheader_for_url(self, url):
        pheader = self.pheader.copy()
        try:
            parsed = urlparse(url)
            referer_url = f"{parsed.scheme}://{parsed.netloc}/"
            pheader['referer'] = referer_url
            pheader['origin'] = referer_url.strip('/')
        except:
            pass
        return pheader
    
    # ... (homeContent, categoryContent, detailContent, searchContent 保持不变)

    def playerContent(self, flag, id, vipFlags):
        # 修复点 1：获取动态的播放请求头
        p,url=0,''
        header = {} # 初始化 header
        try:
            data=self.getpq(self.session.get(f"{self.hsot}{id}"))
            jstr=data('.stui-player.col-pd script').eq(0).text()
            jsdata=json.loads(jstr.split("=", maxsplit=1)[-1])
            p,url=0,jsdata['url']
            
            # **核心修改：获取播放 URL 对应的动态 Referer/Origin 头**
            header = self.get_pheader_for_url(url)
            
            if '.m3u8' in url:
                url=self.proxy(url,'m3u8')
            # 增加对常见视频直链的代理封装，确保使用正确的头
            elif re.search(r'\.(mp4|flv|ts)', url, re.I):
                url = self.proxy(url, url.split('.')[-1].split('?')[0])
                
        except Exception as e:
            print(f"{str(e)}")
            p,url=1,f"{self.hsot}{id}"
            
        # 修复点 2：返回动态生成的 header
        return  {'parse': p, 'url': url, 'header': header}

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url,param['type'])

    # ... (gethost, getlist, getpq, host_late 保持不变)

    def m3Proxy(self, url):
        # 修复点 3：M3U8 请求使用动态 header
        pheader = self.get_pheader_for_url(url)
        
        ydata = requests.get(url, headers=pheader, proxies=self.proxies, allow_redirects=False)
        data = ydata.content.decode('utf-8')
        
        if ydata.headers.get('Location'):
            url = ydata.headers['Location']
            data = requests.get(url, headers=pheader, proxies=self.proxies).content.decode('utf-8') # 重定向也使用 pheader
            
        lines = data.strip().split('\n')
        last_r = url[:url.rfind('/')]
        parsed_url = urlparse(url)
        durl = parsed_url.scheme + "://" + parsed_url.netloc
        
        # 修复点 4：M3U8 切片链接拼接使用 urljoin 提高准确性
        for index, string in enumerate(lines):
            string = string.strip() # 清理空白
            if '#EXT' not in string and string:
                if 'http' not in string:
                    # 使用 urljoin 替代原始的条件判断和字符串拼接
                    string = urljoin(last_r + '/', string) 
                    
                # 重新封装切片链接
                lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
                
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegurl", data] # 更改 Content-Type

    def tsProxy(self, url,type):
        # 修复点 5：TS/MP4/图片 请求使用动态 header
        h=self.get_pheader_for_url(url)
        if type=='img':
            h=self.headers.copy()
            h.update({'referer': urlparse(url).scheme + '://' + urlparse(url).netloc + '/'}) # 尝试给图片一个 Referer
            
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
        
        # 增加非 200 状态码处理
        if data.status_code != 200:
            print(f"TS代理失败: {url}, 状态码: {data.status_code}")
            return [data.status_code, "text/plain", f"Proxy failed for {url}"]
            
        return [200, data.headers['Content-Type'], data.content]

    # ... (proxy, e64, d64 保持不变)
