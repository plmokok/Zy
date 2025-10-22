# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, unquote
import binascii
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
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
        self.hsot = self.gethost()
        # self.hsot='https://hd.hdys2.com'
        self.headers.update({'referer': f"{self.hsot}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        
        # 初始化CDN域名优化
        self.fastest_cdn = self.select_fastest_cdn()
        print(f"选择的CDN域名: {self.fastest_cdn}")
        
        pass

    def getName(self):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    pheader = {
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
        data = self.getpq(self.session.get(self.hsot))
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
        return {'list': ''}

    def categoryContent(self, tid, pg, filter, extend):
        data = self.getpq(self.session.get(f"{self.hsot}/vodshow/{tid}--------{pg}---.html"))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        data = self.getpq(self.session.get(f"{self.hsot}{ids[0]}"))
        v = data('.stui-vodlist__box a')
        vod = {
            'vod_play_from': '花都影视',
            'vod_play_url': f"{v('img').attr('alt')}${v.attr('href')}"
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        data = self.getpq(self.session.get(f"{self.hsot}/vodsearch/{key}----------{pg}---.html"))
        return {'list': self.getlist(data('.stui-vodlist.clearfix li')), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        try:
            # 访问播放页面而不是详情页
            play_url = f"{self.hsot}{id}"
            print(f"正在访问播放页面: {play_url}")
            
            data = self.getpq(self.session.get(play_url))
            
            # 查找包含player_data的脚本
            scripts = data('script')
            player_data_str = None
            
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'player_data' in script_text:
                    player_data_str = script_text
                    break
            
            if not player_data_str:
                raise Exception("未找到player_data脚本")
            
            print(f"找到player_data脚本: {player_data_str[:200]}...")
            
            # 提取player_data JSON
            json_match = re.search(r'player_data\s*=\s*({.*?});', player_data_str, re.DOTALL)
            if not json_match:
                raise Exception("无法提取player_data JSON")
            
            player_data = json.loads(json_match.group(1))
            print(f"解析到的player_data: {player_data}")
            
            # 获取加密的URL
            encrypted_url = player_data.get('url', '')
            encrypt_type = player_data.get('encrypt', 0)
            
            if not encrypted_url:
                raise Exception("player_data中未找到url字段")
            
            # 解码播放地址
            final_url = self.decode_video_url(encrypted_url, encrypt_type)
            print(f"解码后的播放地址: {final_url}")
            
            # 使用最优CDN域名
            optimized_url = self.optimize_cdn_domain(final_url)
            print(f"CDN优化后的播放地址: {optimized_url}")
            
            p = 0
            if '.m3u8' in optimized_url:
                optimized_url = self.proxy(optimized_url, 'm3u8')
                
            return {'parse': p, 'url': optimized_url, 'header': self.pheader}
                
        except Exception as e:
            print(f"播放地址解析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 备用方案：返回播放页面URL，让播放器自行解析
            p, url = 1, f"{self.hsot}{id}"
            print(f"使用备用方案，parse={p}, url={url}")
            return {'parse': p, 'url': url, 'header': self.pheader}

    def decode_video_url(self, encrypted_url, encrypt_type):
        """解码视频URL"""
        if encrypt_type == 2:
            # URL解码
            decoded_url = unquote(encrypted_url)
            print(f"URL解码后: {decoded_url}")
            
            # 检查是否是十六进制编码
            try:
                # 移除可能的空格和非十六进制字符
                hex_str = ''.join(c for c in decoded_url if c in '0123456789abcdefABCDEF')
                if len(hex_str) == len(decoded_url):
                    # 完整的十六进制字符串
                    url_bytes = binascii.unhexlify(hex_str)
                    final_url = url_bytes.decode('utf-8')
                    print(f"十六进制解码后: {final_url}")
                    return final_url
            except Exception as e:
                print(f"十六进制解码失败: {str(e)}")
            
            # 如果不是十六进制，直接返回URL解码结果
            return decoded_url
        else:
            return encrypted_url

    def select_fastest_cdn(self):
        """选择最快的CDN域名"""
        # 已知的CDN域名列表
        cdn_domains = [
            'cdn5.hdzy.xyz',
            'cdn.hdys.xyz', 
            'cdn.hdys.top',
            'cdn1.hdys.xyz',
            'cdn2.hdys.xyz',
            'cdn3.hdys.xyz',
            'cdn4.hdys.xyz',
        ]
        
        # 测试文件路径（使用一个小的测试文件）
        test_path = "/videos/2025/10/14/68edb0317a1db507cf9584d2/1461a4/index.m3u8"
        
        results = {}
        threads = []
        
        def test_cdn(cdn_domain):
            try:
                test_url = f"https://{cdn_domain}{test_path}"
                start_time = time.time()
                
                # 发送HEAD请求测试响应时间
                response = requests.head(
                    test_url, 
                    headers=self.pheader, 
                    timeout=5,
                    allow_redirects=True
                )
                
                # 计算响应时间
                delay = (time.time() - start_time) * 1000
                
                # 检查状态码
                if response.status_code in [200, 302, 301]:
                    results[cdn_domain] = delay
                    print(f"CDN域名 {cdn_domain} 测试成功，响应时间: {delay:.2f}ms")
                else:
                    results[cdn_domain] = float('inf')
                    print(f"CDN域名 {cdn_domain} 返回状态码: {response.status_code}")
                    
            except Exception as e:
                results[cdn_domain] = float('inf')
                print(f"CDN域名 {cdn_domain} 测试失败: {str(e)}")
        
        # 使用多线程测试所有CDN域名
        for cdn in cdn_domains:
            t = threading.Thread(target=test_cdn, args=(cdn,))
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 选择最快的CDN域名
        if results:
            fastest_cdn = min(results.items(), key=lambda x: x[1])[0]
            print(f"最快的CDN域名: {fastest_cdn} (响应时间: {results[fastest_cdn]:.2f}ms)")
            return fastest_cdn
        else:
            print("所有CDN域名测试失败，使用默认域名")
            return 'cdn5.hdzy.xyz'  # 默认域名

    def optimize_cdn_domain(self, video_url):
        """优化CDN域名，使用最快的域名"""
        try:
            from urllib.parse import urlparse, urlunparse
            
            parsed = urlparse(video_url)
            current_domain = parsed.netloc
            
            # 如果当前域名不是最快的域名，则替换
            if current_domain != self.fastest_cdn:
                optimized_url = urlunparse((
                    parsed.scheme,
                    self.fastest_cdn,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                print(f"CDN域名优化: {current_domain} -> {self.fastest_cdn}")
                return optimized_url
            else:
                print(f"当前已使用最快CDN域名: {current_domain}")
                return video_url
                
        except Exception as e:
            print(f"CDN域名优化失败: {str(e)}")
            return video_url

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url, param['type'])

    def gethost(self):
        params = {
            'v': '1',
        }
        self.headers.update({'referer': 'https://a.hdys.top/'})
        response = self.session.get('https://a.hdys.top/assets/js/config.js', proxies=self.proxies, params=params, headers=self.headers)
        return self.host_late(response.text.split(';')[:-4])

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
                url = re.findall(r'"([^"]*)"', url)[0]
                start_time = time.time()
                self.headers.update({'referer': f'{url}/'})
                response = requests.head(url, proxies=self.proxies, headers=self.headers, timeout=1.0, allow_redirects=False)
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
                    domain = last_r if string.count('/') < 2 else durl
                    string = domain + ('' if string.startswith('/') else '/') + string
                lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegur", data]

    def tsProxy(self, url, type):
        h = self.pheader.copy()
        if type == 'img':
            h = self.headers.copy()
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
        return [200, data.headers['Content-Type'], data.content]

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

    def d64(self, encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64解码错误: {str(e)}")
            return ""
