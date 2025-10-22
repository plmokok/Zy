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
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
            print("代理配置解析失败，使用无代理模式")
        
        self.hsot = self.gethost()
        print(f"使用的主机地址: {self.hsot}")
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
        try:
            print(f"开始解析播放地址: {self.hsot}{id}")
            data = self.getpq(self.session.get(f"{self.hsot}{id}"))
            jstr = data('.stui-player.col-pd script').eq(0).text()
            print(f"原始脚本内容: {jstr[:200]}...")  # 只打印前200字符用于调试
            
            # 改进的JSON提取方法
            url = self.extract_video_url(jstr)
            
            if not url:
                raise Exception("无法从脚本中提取播放地址")
                
            print(f"提取的播放地址: {url}")
            p = 0
            
            # 检查地址类型并处理
            if '.m3u8' in url:
                url = self.proxy(url, 'm3u8')
            elif 'url=' in url:
                # 处理base64编码的地址
                url_match = re.search(r'url=([^&]+)', url)
                if url_match:
                    url = self.d64(url_match.group(1))
                    
        except Exception as e:
            print(f"播放地址解析失败: {str(e)}")
            # 备用方案：尝试其他选择器
            try:
                iframe_src = data('iframe').attr('src')
                if iframe_src:
                    url = iframe_src
                    p = 1
                else:
                    raise Exception("无备用播放地址")
            except:
                p, url = 1, f"{self.hsot}{id}"
                
        return {'parse': p, 'url': url, 'header': self.pheader}

    def extract_video_url(self, jstr):
        """改进的视频地址提取方法"""
        # 方法1: 直接提取JSON对象
        json_match = re.search(r'=\s*({.*?})\s*;', jstr, re.DOTALL)
        if json_match:
            try:
                jsdata = json.loads(json_match.group(1))
                return jsdata.get('url', '')
            except:
                pass
        
        # 方法2: 提取url字段
        url_match = re.search(r"url\s*:\s*['\"]([^'\"]+)['\"]", jstr)
        if url_match:
            return url_match.group(1)
            
        # 方法3: 提取var定义的url
        var_match = re.search(r"var\s+[^=]*=\s*['\"]([^'\"]+)['\"]", jstr)
        if var_match:
            return var_match.group(1)
            
        # 方法4: 尝试提取任何看起来像视频地址的URL
        video_patterns = [
            r"https?://[^'\"]+\.m3u8[^'\"]*",
            r"https?://[^'\"]+\.mp4[^'\"]*",
            r"https?://[^'\"]+/play[^'\"]*",
            r"https?://[^'\"]+/video[^'\"]*"
        ]
        
        for pattern in video_patterns:
            video_match = re.search(pattern, jstr)
            if video_match:
                return video_match.group(0)
                
        return None

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url,param['type'])

    def gethost(self):
        try:
            params = {
                'v': '1',
            }
            self.headers.update({'referer': 'https://a.hdys.top/'})
            response = self.session.get('https://a.hdys.top/assets/js/config.js', 
                                      proxies=self.proxies, params=params, headers=self.headers)
            print(f"获取主机配置状态码: {response.status_code}")
            
            if response.status_code != 200:
                print("使用备用主机地址")
                return 'https://hd.hdys2.com'
                
            return self.host_late(response.text.split(';')[:-4])
        except Exception as e:
            print(f"获取主机地址失败: {e}")
            return 'https://hd.hdys2.com'  # 备用地址

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
            print(f"解析HTML失败: {str(e)}")
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
                print(f"测试主机 {url}: {delay}ms")
            except Exception as e:
                results[url] = float('inf')
                print(f"测试主机 {url} 失败: {e}")

        for url in urls:
            t = threading.Thread(target=test_host, args=(url,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        best_host = min(results.items(), key=lambda x: x[1])[0]
        print(f"选择最佳主机: {best_host}")
        return best_host

    def m3Proxy(self, url):
        try:
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
        except Exception as e:
            print(f"m3u8代理处理失败: {e}")
            return [500, "text/plain", f"代理处理失败: {str(e)}"]

    def tsProxy(self, url,type):
        try:
            h=self.pheader.copy()
            if type=='img':h=self.headers.copy()
            data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
            return [200, data.headers['Content-Type'], data.content]
        except Exception as e:
            print(f"ts代理处理失败: {e}")
            return [500, "text/plain", f"代理处理失败: {str(e)}"]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:
            return data

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
