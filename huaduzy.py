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

    # 【主要修改点 1：playerContent】
    def playerContent(self, flag, id, vipFlags):
        try:
            # 访问播放页面
            play_url = f"{self.hsot}{id}"
            print(f"正在访问播放页面: {play_url}")
            
            # 确保 Referer 正确设置
            temp_headers = self.session.headers.copy()
            temp_headers.update({'referer': play_url})
            
            # 【关键：禁用自动跳转】 避免被服务器 3xx 重定向或客户端 JS 影响
            response = self.session.get(play_url, headers=temp_headers, allow_redirects=False)
            
            # 检查是否发生重定向 (如果发生，说明是服务器端重定向，且原始内容可能不完整)
            if response.status_code in (301, 302, 307, 308):
                print(f"警告：检测到状态码 {response.status_code}，可能发生服务器端重定向。")
            
            data = self.getpq(response)
            
            # 查找包含player_data的脚本
            scripts = data('script')
            player_data_str = None
            
            for script in scripts.items():
                script_text = script.text()
                if script_text and 'player_data' in script_text:
                    player_data_str = script_text
                    break
            
            if not player_data_str:
                raise Exception("未找到player_data脚本，可能被广告或跳转影响。")
            
            print(f"找到player_data脚本")
            
            # 提取player_data JSON
            json_match = re.search(r'player_data\s*=\s*({.*?});', player_data_str, re.DOTALL)
            if not json_match:
                raise Exception("无法提取player_data JSON")
            
            player_data = json.loads(json_match.group(1))
            print(f"解析到的player_data: {player_data}")
            
            # 获取加密的URL
            encrypted_url = player_data.get('url', '')
            
            if not encrypted_url:
                raise Exception("player_data中未找到url字段")
            
            # 使用双重URL解码
            final_url = self.double_url_decode(encrypted_url)
            print(f"解码后的播放地址: {final_url}")
            
            # 【关键：CDN 替换】直接替换CDN域名为已验证可用的域名
            final_url = self.replace_cdn_domain(final_url)
            print(f"CDN替换后的播放地址: {final_url}")
            
            p = 0
            if '.m3u8' in final_url:
                final_url = self.proxy(final_url, 'm3u8')
                
            return {'parse': p, 'url': final_url, 'header': self.pheader}
                
        except Exception as e:
            print(f"播放地址解析失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 备用方案：返回播放页面URL，让播放器自行解析
            p, url = 1, f"{self.hsot}{id}"
            print(f"使用备用方案，parse={p}, url={url}")
            return {'parse': p, 'url': url, 'header': self.pheader}

    def double_url_decode(self, encrypted_url):
        """双重URL解码"""
        # 第一步URL解码
        step1 = unquote(encrypted_url)
        print(f"第一步URL解码: {step1}")
        
        # 第二步URL解码
        step2 = unquote(step1)
        print(f"第二步URL解码: {step2}")
        
        return step2

    # 【主要修改点 2：replace_cdn_domain】
    def replace_cdn_domain(self, video_url):
        """直接替换CDN域名为已验证可用的域名"""
        
        # 【根据测试结果设置新的有效域名】
        # 假设 cdn.hdys.xyz 是目前测试有效的域名
        new_valid_domain = 'cdn.hdys.xyz' 

        # 定义需要被替换的旧域名
        cdn_mappings = [
            'cdn.hdys.top', 
            'cdn1.hdys.xyz', 
            'cdn2.hdys.xyz', 
            'cdn3.hdys.xyz', 
            'cdn4.hdys.xyz',
            'cdn5.hdzy.xyz' # 这个是原代码中使用的失效替换目标，也应被替换
        ]
        
        # 如果原始 URL 中包含了新的有效域名，则不进行替换
        if new_valid_domain in video_url:
             print(f"URL已包含有效域名 {new_valid_domain}，跳过替换。")
             return video_url
        
        # 直接替换域名
        for old_domain in cdn_mappings:
            if old_domain in video_url:
                new_url = video_url.replace(old_domain, new_valid_domain)
                print(f"CDN域名替换: {old_domain} -> {new_valid_domain}")
                return new_url
        
        # 如果没有匹配的域名，返回原始URL
        print("未找到需要替换的CDN域名")
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
