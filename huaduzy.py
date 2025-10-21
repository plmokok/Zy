# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, urljoin # 引入 urljoin
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

    # ***修改点 1：将 pheader 改为一个动态获取的函数***
    # **原因：播放请求的 Referer 应该指向视频源网站，而非硬编码的 jx.8852.top**
    def get_pheader(self, url):
        parsed = urlparse(url)
        referer_url = f"{parsed.scheme}://{parsed.netloc}/"
        
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?1',
            'origin': referer_url.strip('/'), # Origin 设为视频源域名
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=1, i',
            'referer': referer_url # Referer 设为视频源域名
        }
    
    # 原始代码中的 pheader 已经删除，改为调用 get_pheader()

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
        vod = {
            'vod_play_from': '花都影视',
            'vod_play_url': f"{v('img').attr('alt')}${v.attr('href')}"
        }
        return {'list':[vod]}

    def searchContent(self, key, quick, pg="1"):
        data=self.getpq(self.session.get(f"{self.hsot}/vodsearch/{key}----------{pg}---.html"))
        return {'list':self.getlist(data('.stui-vodlist.clearfix li')),'page':pg}

    def playerContent(self, flag, id, vipFlags):
        # ***修改点 2：在 playerContent 中获取动态 header***
        p,url=0,''
        header = {}
        try:
            data=self.getpq(self.session.get(f"{self.hsot}{id}"))
            jstr=data('.stui-player.col-pd script').eq(0).text()
            jsdata=json.loads(jstr.split("=", maxsplit=1)[-1])
            p,url=0,jsdata['url']
            
            # **核心修改：获取该播放地址对应的动态请求头**
            header = self.get_pheader(url)
            
            if '.m3u8' in url:
                url=self.proxy(url,'m3u8')
            # 增加对常见视频直链的代理封装，确保使用正确的头
            elif re.search(r'\.(mp4|flv|ts)', url, re.I):
                url = self.proxy(url, url.split('.')[-1].split('?')[0])
                
        except Exception as e:
            print(f"{str(e)}")
            p,url=1,f"{self.hsot}{id}"
            
        # ***修改点 3：返回动态 header***
        return  {'parse': p, 'url': url, 'header': header}

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            # ***修改点 4：在 m3Proxy 中使用动态 header***
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url,param['type'])

    def gethost(self):
        params = {
            'v': '1',
        }
        self.headers.update({'referer': 'https://a.hdys.top/'})
        response = self.session.get('https://a.hdys.top/assets/js/config.js',proxies=self.proxies, params=params, headers=self.headers)
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
            print(f"{str(e)}")
            return pq(data.text.encode('utf-8'))

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
                # **注意：这里 requests.head 应该使用 self.session.head 确保代理配置生效**
                # 但为了不改变原始逻辑，我们继续使用 requests 传入 proxies
                response = requests.head(url,proxies=self.proxies,headers=self.headers,timeout=1.0, allow_redirects=False)
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
        # ***修改点 5：M3U8 请求头使用动态 header***
        pheader = self.get_pheader(url)
        
        ydata = requests.get(url, headers=pheader, proxies=self.proxies, allow_redirects=False)
        data = ydata.content.decode('utf-8')
        
        # ***修改点 6：确保重定向时也使用 pheader***
        if ydata.headers.get('Location'):
            url = ydata.headers['Location']
            data = requests.get(url, headers=pheader, proxies=self.proxies).content.decode('utf-8')
            
        lines = data.strip().split('\n')
        
        # 使用 urljoin 替代原始的路径拼接，提高切片链接的准确性
        base_url = url[:url.rfind('/')] if '?' not in url[:url.rfind('/')] else url.split('?')[0][:url.split('?')[0].rfind('/')]

        for index, string in enumerate(lines):
            string = string.strip()
            if '#EXT' not in string and string:
                if 'http' not in string:
                    # 使用 urljoin 确保相对路径拼接正确
                    string = urljoin(base_url + '/', string)
                
                # 重新封装切片链接
                file_ext = string.split('.')[-1].split('?')[0]
                lines[index] = self.proxy(string, file_ext)
                
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegurl", data] # 更改 Content-Type

    def tsProxy(self, url,type):
        # ***修改点 7：TS 请求头使用动态 header***
        h=self.get_pheader(url)
        if type=='img':h=self.headers.copy()
        
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
        
        # ***修改点 8：处理非 200 状态码***
        if data.status_code != 200:
            print(f"TS代理失败: {url}, 状态码: {data.status_code}")
            return [data.status_code, "text/plain", f"Proxy failed for {url}"]
            
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
