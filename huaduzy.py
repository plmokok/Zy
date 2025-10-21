# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, urljoin # <-- 引入 urljoin
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):
    
    # ... (init, getName, isVideoFormat, manualVideoCheck, destroy 保持不变)

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
        'origin': 'https://jx.8852.top', # <-- 维持原始值
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'zh-CN,zh;q=0.9',
        'priority': 'u=1, i',
        # **新增：添加一个默认的 referer 字段，将在播放时被覆盖**
        'referer': 'https://jx.8852.top/' 
    }

    # **新增辅助函数：用于动态生成播放头，注入正确的 Referer**
    def get_dynamic_pheader(self, url):
        pheader = self.pheader.copy()
        
        # 默认使用主站的详情页作为 Referer，这是最保险的策略
        # 播放器 ID (id) 在 playerContent 中是可用的
        # pheader['referer'] = f"{self.hsot}{self.current_video_id}" # 复杂，暂时不用

        # **修复策略 A：将 Referer 设置为视频源的根域名 (通用防盗链)**
        try:
            parsed = urlparse(url)
            referer_root = f"{parsed.scheme}://{parsed.netloc}/"
            pheader['referer'] = referer_root
            pheader['origin'] = referer_root.strip('/') # 同时修正 origin
        except Exception:
            # 如果解析失败，回退到主站
            pheader['referer'] = f"{self.hsot}/"
            pheader['origin'] = self.hsot

        return pheader

    # ... (homeContent, categoryContent, detailContent, searchContent 保持不变)
    
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

    def homeVideoContent(self):
        return {'list':''}

    def categoryContent(self, tid, pg, filter, extend):
        data=self.getpq(self.session.get(f"{self.hsot}/vodshow/{tid}--------{pg}---.html"))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        data=self.getpq(self.session.get(f"{self.hsot}{ids[0]}"))
        v=data('.stui-vodlist__box a')
        
        # **新增：临时存储当前视频 ID，以便在 playerContent 中生成 Referer**
        # self.current_video_id = ids[0] # 这是一个更复杂的方案，暂不使用
        
        vod = {
            'vod_play_from': '花都影视',
            'vod_play_url': f"{v('img').attr('alt')}${v.attr('href')}"
        }
        return {'list':[vod]}

    def searchContent(self, key, quick, pg="1"):
        data=self.getpq(self.session.get(f"{self.hsot}/vodsearch/{key}----------{pg}---.html"))
        return {'list':self.getlist(data('.stui-vodlist.clearfix li')),'page':pg}

    def playerContent(self, flag, id, vipFlags):
        dynamic_header = self.pheader.copy() # 默认使用原始 pheader 副本
        try:
            data=self.getpq(self.session.get(f"{self.hsot}{id}"))
            jstr=data('.stui-player.col-pd script').eq(0).text()
            jsdata=json.loads(jstr.split("=", maxsplit=1)[-1])
            p,url=0,jsdata['url']
            
            # **核心修复 1：获取包含正确 Referer 的 header**
            dynamic_header = self.get_dynamic_pheader(url)
            
            if '.m3u8' in url:
                url=self.proxy(url,'m3u8')
            # 增加对常见视频直链的代理封装
            elif re.search(r'\.(mp4|flv|ts)', url, re.I):
                url = self.proxy(url, url.split('.')[-1].split('?')[0])
                
        except Exception as e:
            print(f"{str(e)}")
            p,url=1,f"{self.hsot}{id}"
            
        # **核心修复 2：返回动态生成的 header**
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
        # **核心修复 3：M3U8 请求使用动态 header**
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
        
        # **核心修复 4：M3U8 切片链接拼接使用 urljoin**
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
        # **核心修复 5：TS/MP4/图片 请求使用动态 header**
        h=self.get_dynamic_pheader(url)
        if type=='img':
            h=self.headers.copy()
            
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
        return [200, data.headers['Content-Type'], data.content]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:return data

    def e64(self, text):
        try:
            text_bytes = text.encode('utf-8')
            encoded_bytes = b64encode(text_bytes)
            return encoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64编码错误: {str(e)}")
            return ""

    def d64(self,encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64解码错误: {str(e)}")
            return ""
