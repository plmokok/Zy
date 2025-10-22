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
        初始化，禁用SSL校验
        '''
        self.session = requests.Session()
        # 统一使用一个明确的、通用的 UA
        self.common_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        
        self.headers = {
            'User-Agent': self.common_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'dnt': '1',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=0, i',
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

    def getName(self):
        return "花都影视"

    def isVideoFormat(self, url):
        return True if '.m3u8' in url else False

    def manualVideoCheck(self):
        return True

    def destroy(self):
        pass

    # 简化 pheader，只保留必要的 Accept 和 Connection
    pheader={
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }

    def homeContent(self, filter):
        data=self.getpq(self.session.get(self.hsot, verify=False))
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
        data=self.getpq(self.session.get(f"{self.hsot}/vodshow/{tid}--------{pg}---.html", verify=False))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        data=self.getpq(self.session.get(f"{self.hsot}{ids[0]}", verify=False))
        v=data('.stui-vodlist__box a')
        vod = {
            'vod_play_from': '花都影视',
            'vod_play_url': f"{v('img').attr('alt')}${v.attr('href')}"
        }
        return {'list':[vod]}

    def searchContent(self, key, quick, pg="1"):
        data=self.getpq(self.session.get(f"{self.hsot}/vodsearch/{key}----------{pg}---.html", verify=False))
        return {'list':self.getlist(data('.stui-vodlist.clearfix li')),'page':pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - 最终确定解码逻辑
        """
        try:
            play_page_url = f"{self.hsot}{id}"
            response = self.session.get(play_page_url, verify=False) 
            data = self.getpq(response)
            
            # 关键：设置动态 Referer为完整的播放页面 URL
            self.dynamic_referer = play_page_url 

            jstr = data('.stui-player.col-pd script').eq(0).text()
            
            player_data_match = re.search(r'player_data\s*=\s*({[^;]+});', jstr)
            if player_data_match:
                player_data = json.loads(player_data_match.group(1))
                
                encrypted_url = player_data.get('url', '')
                if encrypted_url:
                    # 关键：双重 URL 解码 (已验证算法)
                    video_url = unquote(unquote(encrypted_url)) 
                    p, url = 0, video_url
                    
                    if '.m3u8' in url:
                        url = self.proxy(url, 'm3u8')
                else:
                    jsdata = json.loads(jstr.split("=", maxsplit=1)[-1])
                    p, url = 0, jsdata['url']
                    if '.m3u8' in url:
                        url = self.proxy(url, 'm3u8')
            else:
                jsdata = json.loads(jstr.split("=", maxsplit=1)[-1])
                p, url = 0, jsdata['url']
                if '.m3u8' in url:
                    url = self.proxy(url, 'm3u8')
                    
        except Exception as e:
            print(f"Player Content Error: {str(e)}")
            p, url = 1, f"{self.hsot}{id}"
            
        # 注意：此处返回的 header 将被TVbox用于请求代理URL
        return {'parse': p, 'url': url, 'header': self.pheader}

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url,param['type'])

    def gethost(self):
        params = {'v': '1'}
        self.headers.update({'referer': 'https://a.hdys.top/'})
        # 禁用 SSL 校验
        response = self.session.get('https://a.hdys.top/assets/js/config.js',proxies=self.proxies, params=params, headers=self.headers, verify=False)
        return self.host_late(response.text.split(';')[:-4])

    def getlist(self,data):
        videos=[]
        for i in data.items():
            videos.append({
                'vod_id': i('a').attr('href'),
                'vod_name': i('img').attr('alt'),
                'vod_pic': self.proxy(i('img').attr('data-original')),
                'vod_year': i('.pic-tag-t').text(),
                'vod_remarks': i('.pic-tag-b').text()
            })
        return videos

    def getpq(self, data):
        try:
            return pq(data.text)
        except Exception as e:
            # 兼容非utf-8编码
            return pq(data.content)

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
        # 关键：构造最简且最精确的 Header 集合
        m3u8_header = {
            'User-Agent': self.common_ua,
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache', 
            'Pragma': 'no-cache',
        }
        
        # 动态注入 Referer 和 Origin
        if self.dynamic_referer:
            m3u8_header.update({
                'Referer': self.dynamic_referer,
                'Origin': urlparse(self.dynamic_referer).scheme + '://' + urlparse(self.dynamic_referer).netloc,
            })

        # 使用 self.session，禁用 SSL 校验
        # 此处的请求携带 session 中保持的 cookie
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
        
        # 替换 M3U8 内部的 TS/M3U8 链接为代理地址
        for index, string in enumerate(lines):
            if '#EXT' not in string:
                if 'http' not in string:
                    domain=last_r if string.count('/') < 2 else durl
                    string = domain + ('' if string.startswith('/') else '/') + string
                lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegur", data]

    def tsProxy(self, url,type):
        # 关键：构造最简且最精确的 Header 集合
        h = {
            'User-Agent': self.common_ua,
            'Accept': '*/*',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache', 
            'Pragma': 'no-cache',
        }
        
        # 动态注入 Referer 和 Origin
        if self.dynamic_referer:
            h.update({
                'Referer': self.dynamic_referer,
                'Origin': urlparse(self.dynamic_referer).scheme + '://' + urlparse(self.dynamic_referer).netloc,
            })

        # 使用 self.session，禁用 SSL 校验
        # 此处的请求携带 session 中保持的 cookie
        data = self.session.get(url, headers=h, stream=True, verify=False)
        return [200, data.headers['Content-Type'], data.content]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:return data

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy?do=py"

    def e64(self, text):
        try:
            text_bytes = text.encode('utf-8')
            encoded_bytes = b64encode(text_bytes)
            return encoded_bytes.decode('utf-8')
        except:
            return ""

    def d64(self,encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except:
            return ""
