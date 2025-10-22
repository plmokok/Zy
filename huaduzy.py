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
        完全保持原版初始化
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
        'origin': 'https://jx.8852.top',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'zh-CN,zh;q=0.9',
        'priority': 'u=1, i',
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
        """
        播放内容获取 - 专门针对TVBox播放器优化的版本
        """
        try:
            # 获取播放页面
            play_page_url = f"{self.hsot}{id}"
            response = self.session.get(play_page_url)
            data = self.getpq(response)
            
            # 提取脚本内容
            jstr = data('.stui-player.col-pd script').eq(0).text()
            
            # 解析player_data
            player_data_match = re.search(r'player_data\s*=\s*({[^;]+});', jstr)
            if player_data_match:
                player_data = json.loads(player_data_match.group(1))
                
                # 获取加密URL
                encrypted_url = player_data.get('url', '')
                if encrypted_url:
                    # 双重URL解码
                    video_url = unquote(unquote(encrypted_url))
                    
                    # 确保URL是完整的
                    if not video_url.startswith('http'):
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                    
                    print(f"解密后的视频URL: {video_url}")
                    
                    # 对于TVBox，尝试不同的播放策略
                    return self.create_tvbox_play_result(video_url, play_page_url)
                else:
                    # 如果没有提取到URL，使用原版逻辑
                    jsdata = json.loads(jstr.split("=", maxsplit=1)[-1])
                    video_url = jsdata['url']
                    return self.create_tvbox_play_result(video_url, play_page_url)
            else:
                # 如果没有找到player_data，使用原版逻辑
                jsdata = json.loads(jstr.split("=", maxsplit=1)[-1])
                video_url = jsdata['url']
                return self.create_tvbox_play_result(video_url, play_page_url)
                    
        except Exception as e:
            print(f"{str(e)}")
            # 备用方案：直接返回页面URL让播放器解析
            return {
                'parse': 1, 
                'url': f"{self.hsot}{id}", 
                'header': self.pheader
            }

    def create_tvbox_play_result(self, video_url, play_page_url):
        """
        为TVBox创建播放结果 - 尝试多种策略
        """
        # 策略1: 直接返回解密后的m3u8地址
        if '.m3u8' in video_url:
            print("策略1: 直接返回m3u8地址")
            return {
                'parse': 0,
                'url': video_url,
                'header': self.get_tvbox_headers(video_url)
            }
        
        # 策略2: 如果视频地址不是m3u8，尝试其他格式
        elif any(ext in video_url for ext in ['.mp4', '.flv', '.avi']):
            print("策略2: 返回其他视频格式地址")
            return {
                'parse': 0,
                'url': video_url,
                'header': self.get_tvbox_headers(video_url)
            }
        
        # 策略3: 如果以上都不行，返回页面URL让播放器解析
        else:
            print("策略3: 返回页面URL让播放器解析")
            return {
                'parse': 1,
                'url': play_page_url,
                'header': self.pheader
            }

    def get_tvbox_headers(self, video_url):
        """
        获取TVBox播放器专用的头部信息
        """
        headers = self.pheader.copy()
        
        # 添加Referer，确保视频服务器能正确响应
        if 'hd.hdys' in video_url:
            headers['Referer'] = f'{self.hsot}/'
        elif 'cdnhdzy' in video_url or 'hdzy' in video_url:
            # 对于CDN地址，使用通用的Referer
            headers['Referer'] = 'https://hd.hdys2.com/'
        
        # 添加更多的兼容性头部
        headers.update({
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive',
            'Range': 'bytes=0-',
        })
        
        return headers

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
        ydata = requests.get(url, headers=self.pheader, proxies=self.proxies, allow_redirects=False)
        data = ydata.content.decode('utf-8')
        if ydata.headers.get('Location'):
            url = ydata.headers['Location']
            data = requests.get(url, headers=self.pheader, proxies=self.proxies).content.decode('utf-8')
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
        h=self.pheader.copy()
        if type=='img':h=self.headers.copy()
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
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
