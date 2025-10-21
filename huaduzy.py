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
        # 统一 User-Agent，确保模拟浏览器访问
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'dnt': '1',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=1',
        }
        try:self.proxies = json.loads(extend)
        except:self.proxies = {}
        
        # 获取最新的host
        self.hsot=self.gethost()
        
        # **优化：统一设置全局 Referer，指向主站，增强请求通过率**
        self.headers.update({'referer': f"{self.hsot}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        pass

    def getName(self):
        return '花都影视' # 增加一个名称方便调试

    def isVideoFormat(self, url):
        return re.search(r'\.m3u8|\.mp4|\.flv|\.ts', url, re.I) is not None

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    # **优化：简化 pheader，确保 Referer 和 Origin 指向正确的播放页或主站**
    # 播放器的请求头可以沿用 self.session.headers，但 TVBox 需要这个字典来传递给播放内核
    def get_pheader(self, url):
        parsed = urlparse(url)
        # 针对播放地址生成一个 Referer，通常设置为视频所在的网页域名
        referer_url = f"{parsed.scheme}://{parsed.netloc}/"
        
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Origin': referer_url.strip('/'),
            'Referer': referer_url,
        }

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
        # 播放列表（如果有多个播放源）应该在这里提取，但目前只提取第一个
        data=self.getpq(self.session.get(f"{self.hsot}{ids[0]}"))
        
        # 默认只提取第一个播放源的第一集（如果网站只有一个播放源）
        vod_play_from = '花都影视'
        
        # 尝试提取播放列表
        play_list = data('.stui-content__playlist ul:eq(0) li a')
        
        # **优化：构造更标准的播放地址，用于后续的 playerContent 解析**
        vod_play_url = []
        for v in play_list.items():
            vod_play_url.append(f"{v.text()}${v.attr('href')}")
            
        vod = {
            'vod_id': ids[0],
            'vod_name': data('.stui-content__detail h3').text() or 'N/A', # 提取视频名称
            'vod_pic': data('.stui-content__thumb img').attr('data-original') or '',
            'vod_year': data('.detail-info p:eq(1)').text() or '', # 提取年份等信息
            'vod_remarks': data('.pic-text').text() or '', # 提取备注
            'vod_play_from': vod_play_from,
            'vod_play_url': '#'.join(vod_play_url) if vod_play_url else ''
        }
        return {'list':[vod]}

    def searchContent(self, key, quick, pg="1"):
        data=self.getpq(self.session.get(f"{self.hsot}/vodsearch/{key}----------{pg}---.html"))
        return {'list':self.getlist(data('.stui-vodlist.clearfix li')),'page':pg}

    def playerContent(self, flag, id, vipFlags):
        p,url=0,''
        header = {}
        try:
            data=self.getpq(self.session.get(f"{self.hsot}{id}"))
            jstr=data('.stui-player.col-pd script').eq(0).text()
            jsdata=json.loads(jstr.split("=", maxsplit=1)[-1])
            p,url=0,jsdata['url']
            
            # **优化：统一使用 get_pheader 获取播放头，并传递给播放器**
            header = self.get_pheader(url)
            
            if '.m3u8' in url:
                # M3U8 链接通过代理转发，强制使用自定义代理
                url = self.proxy(url,'m3u8')
                # 代理后不需要将解析标志 p 设为 1，仍为 0 (无需二次解析)
            elif '.mp4' in url or '.flv' in url or '.ts' in url:
                # 普通直链也通过代理，确保请求头正确传递
                url = self.proxy(url, url.split('.')[-1].split('?')[0])
                
        except Exception as e:
            # 如果解析失败，尝试将 ID 作为播放链接，并设置解析标志 p=1
            # p=1 表示让播放器尝试进行二次解析，通常用于解析外部播放器链接
            print(f"解析失败: {str(e)}")
            p,url=1,f"{self.hsot}{id}"
            
        return  {'parse': p, 'url': url, 'header': header}

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        proxy_type = param.get('type')
        if proxy_type == 'm3u8':
            # **重点优化 M3U8 代理**
            return self.m3Proxy(url)
        elif proxy_type in ['mp4', 'flv', 'ts', 'img']:
            return self.tsProxy(url, proxy_type)
        else:
            return [404, "text/plain", "Invalid proxy type"]

    # **重点优化 m3Proxy，确保 M3U8 切片链接的正确性**
    def m3Proxy(self, url):
        # 使用 get_pheader 获取播放请求头
        pheader = self.get_pheader(url)
        
        # 确保使用会话请求，以便使用已配置的代理
        ydata = self.session.get(url, headers=pheader, allow_redirects=True)
        
        if ydata.status_code != 200:
            print(f"M3U8下载失败，状态码: {ydata.status_code}")
            return [ydata.status_code, "text/plain", "M3U8 content download failed"]
            
        data = ydata.content.decode('utf-8', errors='ignore')
        
        lines = data.strip().split('\n')
        
        base_url = url[:url.rfind('/')] if '?' not in url[:url.rfind('/')] else url.split('?')[0][:url.split('?')[0].rfind('/')]
        parsed_url = urlparse(url)
        durl = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for index, string in enumerate(lines):
            string = string.strip()
            if not string.startswith('#') and string: # 排除注释行和空行
                # 如果切片链接不是完整URL（不含http）
                if not string.lower().startswith('http'):
                    # 使用 urljoin 确保相对路径被正确地拼接
                    # base_url 是 M3U8 文件自身的目录
                    string = urljoin(base_url + '/', string) 
                
                # **核心逻辑：将切片链接再次封装成代理链接**
                # 切片文件通常是 ts 类型，或者可能是 m3u8（二级m3u8）
                file_ext = string.split('.')[-1].split('?')[0].lower()
                proxy_type = 'ts' if file_ext in ['ts', 'mpeg'] else 'm3u8' if file_ext == 'm3u8' else 'mp4'
                
                lines[index] = self.proxy(string, proxy_type)
                
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegurl", data]

    def tsProxy(self, url, type):
        # **优化：统一使用 get_pheader 获取请求头**
        h = self.get_pheader(url)
        if type=='img':h=self.headers.copy() # 图片使用初始头
        
        # 使用 session.get 保证代理配置有效
        data = self.session.get(url, headers=h, stream=True)
        
        if data.status_code != 200:
            print(f"代理请求失败: {url}, 状态码: {data.status_code}")
            return [data.status_code, "text/plain", f"Proxy request failed for {url}"]
            
        return [200, data.headers.get('Content-Type', 'application/octet-stream'), data.content]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):
            # 使用 self.getProxyUrl() 来获取 TVBox 代理地址
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:
            return data
            
    # 其余辅助函数保持不变 (gethost, getlist, getpq, host_late, e64, d64)
    # ... (此处省略未修改的辅助函数，但它们需要在实际文件中)
    def gethost(self):
        params = {
            'v': '1',
        }
        self.headers.update({'referer': 'https://a.hdys.top/'})
        # **优化：确保在gethost时也使用self.session和self.proxies**
        response = self.session.get('https://a.hdys.top/assets/js/config.js',params=params, headers=self.headers)
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
        
        # **优化：确保测速时也使用 session 的配置**
        temp_session = requests.Session()
        temp_session.headers.update(self.headers)
        temp_session.proxies.update(self.proxies)

        def test_host(url):
            try:
                url=re.findall(r'"([^"]*)"', url)[0]
                start_time = time.time()
                # 使用 session.head
                response = temp_session.head(url, timeout=1.0, allow_redirects=False)
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
