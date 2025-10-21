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
        保持原版初始化，只修复明显问题
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
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
        self.host = self.gethost()
        # 修复拼写错误：hsot -> host
        self.headers.update({'referer': f"{self.host}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视修复版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        data = self.getpq(self.session.get(self.host))
        cdata = data('.stui-header__menu.type-slide li')
        ldata = data('.stui-vodlist.clearfix li')
        result = {}
        classes = []
        for k in cdata.items():
            i = k('a').attr('href')
            if i and 'type' in i:
                classes.append({
                    'type_name': k.text(),
                    'type_id': re.search(r'\d+', i).group(0)
                })
        result['class'] = classes
        result['list'] = self.getlist(ldata)
        return result

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        data = self.getpq(self.session.get(f"{self.host}/vodshow/{tid}--------{pg}---.html"))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        data = self.getpq(self.session.get(f"{self.host}{ids[0]}"))
        v = data('.stui-vodlist__box a')
        
        vod = {
            'vod_id': ids[0],
            'vod_name': v('img').attr('alt'),
            'vod_pic': self.proxy(v('img').attr('data-original')),
            'vod_play_from': '花都影视',
            'vod_play_url': f"第1集${v.attr('href')}"
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        data = self.getpq(self.session.get(f"{self.host}/vodsearch/{key}----------{pg}---.html"))
        return {'list': self.getlist(data('.stui-vodlist.clearfix li')), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        修复播放内容获取 - 简化但有效的版本
        """
        try:
            # 获取播放页面
            play_url = f"{self.host}{id}"
            response = self.session.get(play_url)
            data = self.getpq(response)
            
            # 方法1: 尝试从脚本获取播放地址
            scripts = data('.stui-player.col-pd script')
            if scripts.length > 0:
                script_text = scripts.eq(0).text()
                
                # 尝试多种JSON提取方式
                json_patterns = [
                    r'var\s+player_\w+\s*=\s*({[^;]+});?',
                    r'player_data\s*=\s*({[^;]+});?',
                    r'=\s*({[^;]+});?'
                ]
                
                for pattern in json_patterns:
                    match = re.search(pattern, script_text)
                    if match:
                        try:
                            jsdata = json.loads(match.group(1))
                            if 'url' in jsdata and jsdata['url']:
                                video_url = jsdata['url']
                                # 确保URL是完整的
                                if not video_url.startswith('http'):
                                    if video_url.startswith('//'):
                                        video_url = 'https:' + video_url
                                    else:
                                        video_url = self.host + video_url
                                
                                return {
                                    'parse': 0, 
                                    'url': video_url, 
                                    'header': self.get_player_headers()
                                }
                        except:
                            continue
            
            # 方法2: 尝试从iframe获取
            iframe = data('iframe')
            if iframe.length > 0:
                iframe_src = iframe.attr('src')
                if iframe_src:
                    return {
                        'parse': 1, 
                        'url': iframe_src, 
                        'header': self.get_player_headers()
                    }
                    
        except Exception as e:
            print(f"播放内容获取错误: {e}")
        
        # 备用方案: 直接返回页面URL
        return {
            'parse': 1, 
            'url': f"{self.host}{id}", 
            'header': self.get_player_headers()
        }

    def get_player_headers(self):
        """获取播放器头部信息"""
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

    def liveContent(self, url):
        return []

    def localProxy(self, param):
        try:
            url = self.d64(param['url'])
            if param.get('type') == 'm3u8':
                return self.m3Proxy(url)
            else:
                return self.tsProxy(url, param.get('type', 'ts'))
        except Exception as e:
            return [500, "text/plain", f"Proxy Error: {e}"]

    def gethost(self):
        try:
            params = {'v': '1'}
            self.headers.update({'referer': 'https://a.hdys.top/'})
            response = self.session.get('https://a.hdys.top/assets/js/config.js', proxies=self.proxies, params=params, headers=self.headers)
            return self.host_late(response.text.split(';')[:-4])
        except:
            return 'https://hd.hdys2.com'

    def getlist(self, data):
        videos = []
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
        except:
            return pq(data.content.decode('utf-8'))

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
                url = re.findall(r'"([^"]*)"', url)[0]
                start_time = time.time()
                self.headers.update({'referer': f'{url}/'})
                response = requests.head(url, proxies=self.proxies, headers=self.headers, timeout=1.0, allow_redirects=False)
                delay = (time.time() - start_time) * 1000
                results[url] = delay
            except:
                results[url] = float('inf')

        for url in urls:
            t = threading.Thread(target=test_host, args=(url,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return min(results.items(), key=lambda x: x[1])[0]

    def m3Proxy(self, url):
        try:
            ydata = requests.get(url, headers=self.get_player_headers(), proxies=self.proxies, allow_redirects=False)
            data = ydata.content.decode('utf-8')
            if ydata.headers.get('Location'):
                url = ydata.headers['Location']
                data = requests.get(url, headers=self.get_player_headers(), proxies=self.proxies).content.decode('utf-8')
            return [200, "application/vnd.apple.mpegurl", data]
        except Exception as e:
            return [500, "text/plain", f"M3U8 Proxy Error: {e}"]

    def tsProxy(self, url, file_type):
        try:
            headers = self.get_player_headers()
            data = requests.get(url, headers=headers, proxies=self.proxies, stream=True)
            return [200, data.headers.get('Content-Type', 'video/mp2t'), data.content]
        except Exception as e:
            return [500, "text/plain", f"TS Proxy Error: {e}"]

    def proxy(self, data, file_type='img'):
        if data and len(self.proxies):
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={file_type}"
        else:
            return data

    def getProxyUrl(self):
        """添加缺失的代理URL方法"""
        return "http://127.0.0.1:9978/proxy?do=py"

    def e64(self, text):
        try:
            text_bytes = text.encode('utf-8')
            encoded_bytes = b64encode(text_bytes)
            return encoded_bytes.decode('utf-8')
        except:
            return ""

    def d64(self, encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except:
            return ""
