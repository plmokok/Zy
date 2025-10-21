# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse
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
        
        # --- 【修改点 1】：初始化 pheader 为基础模板，Referer 留空或通用 ---
        self.pheader_base={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?1',
            'origin': f'{self.hsot}', # 使用主站作为 Origin
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=1, i',
            'Referer': f'{self.hsot}/' # 初始设置主站 Referer，备用
        }
        pass

    # def getName(self):
    #     pass

    # def isVideoFormat(self, url):
    #     pass

    # def manualVideoCheck(self):
    #     pass

    # def destroy(self):
    #     pass

    # def homeContent(self, filter):
    #     data=self.getpq(self.session.get(self.hsot))
    #     # ... (保持不变) ...

    # def homeVideoContent(self):
    #     return {'list':''}

    # def categoryContent(self, tid, pg, filter, extend):
    #     # ... (保持不变) ...

    # def detailContent(self, ids):
    #     # ... (保持不变) ...

    # def searchContent(self, key, quick, pg="1"):
    #     # ... (保持不变) ...

    # --- 【修改点 3】：修改 playerContent，动态设置 Referer 并在 URL 中传递 ---
    def playerContent(self, flag, id, vipFlags):
        # 1. 动态生成播放页的 Referer URL
        referer_url = f"{self.hsot}{id}"
        
        # 2. 拷贝基础 Header 并更新 Referer
        pheader_dynamic = self.pheader_base.copy()
        pheader_dynamic['Referer'] = referer_url # 确保 Referer 是当前播放页
        pheader_dynamic['Origin'] = self.hsot # 确保 Origin 是主站

        try:
            # 3. 正常抓取解析逻辑
            data=self.getpq(self.session.get(referer_url)) # 使用 referer_url 访问播放页
            jstr=data('.stui-player.col-pd script').eq(0).text()
            jsdata=json.loads(jstr.split("=", maxsplit=1)[-1])
            p,url=0,jsdata['url']
            
            # 4. 如果是 m3u8，交给代理处理，并在 URL 中附加 Referer (核心修复点 A)
            if '.m3u8' in url:
                # 在 URL 中附加 Referer 和 User-Agent 的 Base64 编码字符串
                header_str = f"Referer={referer_url}&User-Agent={pheader_dynamic['User-Agent']}"
                url = url + '|' + self.e64(header_str)
                
                url=self.proxy(url,'m3u8')
            
        except Exception as e:
            print(f"解析错误: {str(e)}")
            p,url=1,referer_url # 解析失败，直接返回播放页 URL (p=1 代表外部解析)
            
        # 5. 返回动态的 Header
        return  {'parse': p, 'url': url, 'header': pheader_dynamic}

    # def liveContent(self, url):
    #     pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url,param['type'])
        
    def gethost(self):
        # 此处省略 gethost 原始实现
        pass # 保持原始逻辑

    def getlist(self,data):
        # 此处省略 getlist 原始实现
        pass # 保持原始逻辑

    def getpq(self, data):
        # 此处省略 getpq 原始实现
        pass # 保持原始逻辑

    def host_late(self, url_list):
        # 此处省略 host_late 原始实现
        pass # 保持原始逻辑

    # --- 修改 m3Proxy，解析并使用 URL 中传递的 Referer (核心修复点 B & C) ---
    def m3Proxy(self, url):
        # 1. 从 URL 中解析附加的 Header（Referer 和 User-Agent）
        real_url = url
        custom_headers = self.pheader_base.copy() # 默认使用基础 header
        if '|' in url:
            real_url = url.split('|')[0]
            try:
                # 解析 URL 后的 Base64 编码的 Header 字符串
                header_str = self.d64(url.split('|')[-1])
                # 提取 Referer 和 User-Agent
                parts = header_str.split('&')
                for part in parts:
                    if part.startswith('Referer='):
                        custom_headers['Referer'] = part.split('=')[-1]
                    elif part.startswith('User-Agent='):
                        custom_headers['User-Agent'] = part.split('=')[-1]
            except:
                pass # 解析失败则使用默认 Header
        
        # 2. 使用解析到的 Header 请求 M3U8 文件
        ydata = requests.get(real_url, headers=custom_headers, proxies=self.proxies, allow_redirects=False)
        
        data = ydata.content.decode('utf-8')
        if ydata.headers.get('Location'):
            real_url = ydata.headers['Location']
            data = requests.get(real_url, headers=custom_headers, proxies=self.proxies).content.decode('utf-8') # 重定向时也使用自定义 Header

        lines = data.strip().split('\n')
        last_r = real_url[:real_url.rfind('/')]
        parsed_url = urlparse(real_url)
        durl = parsed_url.scheme + "://" + parsed_url.netloc

        # 3. 构造要传递给 TS 分段代理的 Header 字符串
        ts_header_str = f"Referer={custom_headers.get('Referer', self.pheader_base.get('Referer', ''))}&User-Agent={custom_headers.get('User-Agent', self.pheader_base.get('User-Agent', ''))}"

        for index, string in enumerate(lines):
            if '#EXT' not in string:
                if 'http' not in string:
                    domain=last_r if string.count('/') < 2 else durl
                    string = domain + ('' if string.startswith('/') else '/') + string
                
                # 4. 在 TS 分段的代理 URL 中，也附加 Referer 和 User-Agent 信息 (核心修复点 C)
                string = string + '|' + self.e64(ts_header_str)
                
                lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
        
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegur", data]

    # --- 修改 tsProxy，解析并使用 URL 中传递的 Referer (核心修复点 D) ---
    def tsProxy(self, url,type):
        
        # 1. 从 URL 中解析附加的 Header（Referer 和 User-Agent）
        real_url = url
        h = self.pheader_base.copy() # 默认使用基础 header
        if '|' in url:
            real_url = url.split('|')[0]
            try:
                # 解析 URL 后的 Base64 编码的 Header 字符串
                header_str = self.d64(url.split('|')[-1])
                # 提取 Referer 和 User-Agent
                parts = header_str.split('&')
                for part in parts:
                    if part.startswith('Referer='):
                        h['Referer'] = part.split('=')[-1]
                    elif part.startswith('User-Agent='):
                        h['User-Agent'] = part.split('=')[-1]
            except:
                pass # 解析失败则使用默认 Header

        # 2. 使用解析到的 Header 请求 TS/分段文件
        if type=='img':h=self.headers.copy() # 针对图片使用通用 header
        data = requests.get(real_url, headers=h, proxies=self.proxies, stream=True)
        
        return [200, data.headers['Content-Type'], data.content]

    def proxy(self, data, type='img'):
        parse = urlparse(data)
        uri = parse.scheme + "://" + parse.netloc + parse.path
        param = {'url': self.e64(data), 'type': type}
        return '/proxy/' + self.e64(json.dumps(param)) + '.' + uri.split('.')[-1].split('?')[0]
    
    def e64(self, s):
        return b64encode(s.encode('utf8')).decode('utf8')

    def d64(self, s):
        return b64decode(s.encode('utf8')).decode('utf8')
