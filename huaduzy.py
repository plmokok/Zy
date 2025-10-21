# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, urljoin  # <-- 引入 urljoin, urlparse
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        '''
        如果一直访问不了，手动访问导航页:https://a.hdys.top，替换：
        self.host = 'https://xxx.xxx.xxx'
        '''
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

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    pheader={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
        'dnt': '1',
        'sec-ch-ua-mobile': '?1',
        'origin': 'https://jx.8852.top', # <-- 保留硬编码，但将在 playerContent 中覆盖
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'zh-CN,zh;q=0.9',
        'priority': 'u=1, i',
    }
    
    # **新增辅助函数：用于动态生成播放头**
    def get_dynamic_pheader(self, url):
        pheader = self.pheader.copy()
        try:
            parsed = urlparse(url)
            # Referer 和 Origin 设置为视频源的根域名，这是最通用的防盗链破解方法
            referer_url = f"{parsed.scheme}://{parsed.netloc}/"
            pheader['referer'] = referer_url
            pheader['origin'] = referer_url.strip('/')
        except Exception as e:
            print(f"生成动态pheader失败: {str(e)}")
            
        return pheader

    def homeContent(self, filter):
        data=self.getpq(self.session.get(self.hsot))
        cdata=data('.stui-header__menu.type-slide li')
        ldata=data('.stui-vodlist.clearfix li')
        result = {}
        classes = []
        for k in cdata.items():
            i=k('a').attr('href')
            if i and 'type' in i:
                classes.append({
                    'type_name': k.text(),
                    'type_id': re.search(r'\d+', i).group(0)
                })
        result['class'] = classes
        result['list'] = self.getlist(ldata)
        return result

    # ... (homeVideoContent, categoryContent, detailContent, searchContent 保持不变)

    def playerContent(self, flag, id, vipFlags):
        dynamic_header = self.pheader.copy() # 默认使用原始 pheader
        try:
            data=self.getpq(self.session.get(f"{self.hsot}{id}"))
            jstr=data('.stui-player.col-pd script').eq(0).text()
            jsdata=json.loads(jstr.split("=", maxsplit=1)[-1])
            p,url=0,jsdata['url']
            
            # **核心修改 1：获取动态播放头，覆盖默认的 pheader**
            dynamic_header = self.get_dynamic_pheader(url)
            
            if '.m3u8' in url:
                url=self.proxy(url,'m3u8')
            # 增加对常见视频直链的代理封装
            elif re.search(r'\.(mp4|flv|ts)', url, re.I):
                url = self.proxy(url, url.split('.')[-1].split('?')[0])
                
        except Exception as e:
            print(f"{str(e)}")
            p,url=1,f"{self.hsot}{id}"
            
        # **核心修改 2：返回动态生成的 header**
        return  {'parse': p, 'url': url, 'header': dynamic_header}

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
        # **核心修改 3：M3U8 请求使用动态 header**
        pheader = self.get_dynamic_pheader(url)
        
        ydata = requests.get(url, headers=pheader, proxies=self.proxies, allow_redirects=False)
        data = ydata.content.decode('utf-8')
        
        if ydata.headers.get('Location'):
            url = ydata.headers['Location']
            data = requests.get(url, headers=pheader, proxies=self.proxies).content.decode('utf-8')
            
        lines = data.strip().split('\n')
        last_r = url[:url.rfind('/')]
        parsed_url = urlparse(url)
        durl = parsed_url.scheme + "://" + parsed_url.netloc
        
        # **核心修改 4：M3U8 切片链接拼接使用 urljoin**
        for index, string in enumerate(lines):
            string = string.strip()
            if '#EXT' not in string and string:
                if 'http' not in string:
                    # 使用 urljoin 替代原始的条件判断和字符串拼接
                    string = urljoin(last_r + '/', string) 
                lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
                
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegurl", data] # <-- 更改 Content-Type

    def tsProxy(self, url,type):
        # **核心修改 5：TS/MP4/图片 请求使用动态 header**
        h=self.get_dynamic_pheader(url)
        if type=='img':
            h=self.headers.copy() # 图片使用初始头
            
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
        return [200, data.headers['Content-Type'], data.content]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:return data

    # ... (e64, d64 保持不变)
