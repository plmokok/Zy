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
        '''
        保持原版初始化，并初始化动态Referer
        '''
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', # 统一使用 Windows UA，更通用
            'Accept': '*/*',
            'dnt': '1',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=2',
        }
        try:self.proxies = json.loads(extend)
        except:self.proxies = {}
        # 禁用requests的警告
        requests.packages.urllib3.disable_warnings() 
        
        self.hsot=self.gethost()
        self.headers.update({'referer': f"{self.hsot}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        self.dynamic_referer = None # 初始化动态Referer
        pass

    # ... (getName, isVideoFormat, manualVideoCheck, destroy 方法不变) ...

    pheader={
        # 专门用于视频流请求的通用头部，确保关键字段存在
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }

    # ... (homeContent, homeVideoContent, categoryContent, detailContent, searchContent 方法不变) ...

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - **最终修复版本**
        """
        try:
            # 1. 获取播放页面，确保 Session 捕获所有 Cookie
            play_page_url = f"{self.hsot}{id}"
            # 禁用 SSL 校验
            response = self.session.get(play_page_url, verify=False) 
            data = self.getpq(response)
            
            # 2. **设置精准动态 Referer** (指向播放页面而不是网站首页)
            parsed_play_url = urlparse(play_page_url)
            self.dynamic_referer = play_page_url # 使用完整的播放页面URL作为Referer

            # 3. 提取脚本内容并解密
            jstr = data('.stui-player.col-pd script').eq(0).text()
            
            player_data_match = re.search(r'player_data\s*=\s*({[^;]+});', jstr)
            if player_data_match:
                player_data = json.loads(player_data_match.group(1))
                
                encrypted_url = player_data.get('url', '')
                if encrypted_url:
                    # 关键：双重 URL 解码
                    video_url = unquote(unquote(encrypted_url)) 
                    p, url = 0, video_url
                    
                    if '.m3u8' in url:
                        url = self.proxy(url, 'm3u8')
                else:
                    # 备用旧逻辑
                    jsdata = json.loads(jstr.split("=", maxsplit=1)[-1])
                    p, url = 0, jsdata['url']
                    if '.m3u8' in url:
                        url = self.proxy(url, 'm3u8')
            else:
                # 备用旧逻辑
                jsdata = json.loads(jstr.split("=", maxsplit=1)[-1])
                p, url = 0, jsdata['url']
                if '.m3u8' in url:
                    url = self.proxy(url, 'm3u8')
                    
        except Exception as e:
            print(f"Player Content Error: {str(e)}")
            p, url = 1, f"{self.hsot}{id}"
            
        return {'parse': p, 'url': url, 'header': self.pheader}

    # ... (liveContent, localProxy 方法不变) ...

    def gethost(self):
        params = {
            'v': '1',
        }
        self.headers.update({'referer': 'https://a.hdys.top/'})
        # 禁用 SSL 校验，使用 self.session
        response = self.session.get('https://a.hdys.top/assets/js/config.js',proxies=self.proxies, params=params, headers=self.headers, verify=False)
        return self.host_late(response.text.split(';')[:-4])

    # ... (getlist, getpq 方法不变) ...

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
                # 禁用 SSL 校验
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
        # 【最终核心修改：强制使用 Session headers + 完整 Header 注入】
        m3u8_header = self.session.headers.copy() # 以 session 的所有 Header 为基础
        
        # 注入动态 Referer/Origin 和 Cache Control
        if self.dynamic_referer:
            m3u8_header.update({
                'Referer': self.dynamic_referer,
                'Origin': urlparse(self.dynamic_referer).scheme + '://' + urlparse(self.dynamic_referer).netloc,
                'Cache-Control': 'no-cache', # 禁用缓存
                'Pragma': 'no-cache',        # 禁用缓存
            })
        m3u8_header.update(self.pheader) # 确保通用视频流头部也被带上

        # 使用 self.session，并禁用 SSL 校验
        ydata = self.session.get(url, headers=m3u8_header, allow_redirects=False, verify=False)
        data = ydata.content.decode('utf-8')
        
        # 处理重定向
        if ydata.headers.get('Location'):
            url = ydata.headers['Location']
            # 重定向后的请求使用 self.session
            ydata = self.session.get(url, headers=m3u8_header, verify=False)
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
        # 【最终核心修改：强制使用 Session headers + 完整 Header 注入】
        h = self.session.headers.copy() # 以 session 的所有 Header 为基础
        
        if type=='img':
            h.update(self.headers.copy())
            
        # 注入动态 Referer/Origin 和 Cache Control
        if self.dynamic_referer:
            h.update({
                'Referer': self.dynamic_referer,
                'Origin': urlparse(self.dynamic_referer).scheme + '://' + urlparse(self.dynamic_referer).netloc,
                'Cache-Control': 'no-cache', # 禁用缓存
                'Pragma': 'no-cache',        # 禁用缓存
            })
        h.update(self.pheader) # 确保通用视频流头部也被带上

        # 使用 self.session，并禁用 SSL 校验
        data = self.session.get(url, headers=h, stream=True, verify=False)
        return [200, data.headers['Content-Type'], data.content]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:return data

    def getProxyUrl(self):
        """添加缺失的代理URL方法"""
        return "http://127.0.0.1:9978/proxy?do=py"

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
