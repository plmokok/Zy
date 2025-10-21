# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
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
        初始化 - 保持稳定性
        '''
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
            
        self.host = self.gethost()
        self.headers.update({'referer': f"{self.host}/"})
        
        if self.proxies:
            self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视最终修复版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        '''
        首页内容 - 保持原版稳定性
        '''
        try:
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
        except Exception as e:
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        '''
        分类内容 - 保持原版稳定性
        '''
        data = self.getpq(self.session.get(f"{self.host}/vodshow/{tid}--------{pg}---.html"))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        '''
        详情页 - 保持原版稳定性
        '''
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
        '''
        搜索功能 - 保持原版稳定性
        '''
        data = self.getpq(self.session.get(f"{self.host}/vodsearch/{key}----------{pg}---.html"))
        return {'list': self.getlist(data('.stui-vodlist.clearfix li')), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - 最终修复版本
        专注于从播放页面提取真实的m3u8地址
        """
        print("=== 最终修复版本启动 ===")
        play_page_url = f"{self.host}{id}"
        print(f"播放页面: {play_page_url}")
        
        try:
            # 获取播放页面
            response = self.session.get(play_page_url)
            html_content = response.text
            data = self.getpq(html_content)
            
            # 策略1: 直接搜索整个HTML中的m3u8地址
            print("策略1: 直接搜索HTML中的m3u8")
            m3u8_urls = self.search_all_m3u8_urls(html_content)
            for url in m3u8_urls:
                if self.validate_m3u8_url(url):
                    print(f"找到有效m3u8: {url}")
                    return self.create_play_result(url, 0)
            
            # 策略2: 搜索JavaScript中的播放器配置
            print("策略2: 搜索JavaScript播放器配置")
            player_config = self.extract_player_config(html_content)
            if player_config and 'url' in player_config:
                url = player_config['url']
                if self.validate_m3u8_url(url):
                    print(f"从播放器配置找到m3u8: {url}")
                    return self.create_play_result(url, 0)
            
            # 策略3: 搜索Base64编码的URL
            print("策略3: 搜索Base64编码的URL")
            encoded_urls = self.find_base64_encoded_urls(html_content)
            for encoded_url in encoded_urls:
                decoded_url = self.decode_base64_url(encoded_url)
                if decoded_url and self.validate_m3u8_url(decoded_url):
                    print(f"Base64解码找到m3u8: {decoded_url}")
                    return self.create_play_result(decoded_url, 0)
            
            # 策略4: 搜索JSON数据中的播放地址
            print("策略4: 搜索JSON数据")
            json_urls = self.extract_urls_from_json(html_content)
            for url in json_urls:
                if self.validate_m3u8_url(url):
                    print(f"从JSON找到m3u8: {url}")
                    return self.create_play_result(url, 0)
            
            # 策略5: 搜索iframe和脚本中的URL
            print("策略5: 搜索iframe和脚本")
            iframe_urls = self.extract_urls_from_iframes_and_scripts(data, html_content)
            for url in iframe_urls:
                if self.validate_m3u8_url(url):
                    print(f"从iframe/脚本找到m3u8: {url}")
                    return self.create_play_result(url, 0)
                
            # 所有策略失败
            print("所有提取策略失败，使用备用方案")
            return self.create_play_result(play_page_url, 1)
            
        except Exception as e:
            print(f"播放处理异常: {e}")
            return self.create_play_result(play_page_url, 1)

    def search_all_m3u8_urls(self, html_content):
        """
        在整个HTML内容中搜索所有可能的m3u8 URL
        """
        urls = []
        
        # 搜索各种格式的m3u8链接
        patterns = [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',  # 标准URL
            r'//[^\s"\']+\.m3u8[^\s"\']*',         # 协议相对URL
            r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',  # 引号内的URL
            r'["\'](//[^"\']+\.m3u8[^"\']*)["\']',         # 引号内的协议相对URL
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # 标准化URL
                if match.startswith('//'):
                    url = 'https:' + match
                elif match.startswith('/'):
                    url = self.host + match
                else:
                    url = match
                
                if url not in urls:
                    urls.append(url)
                    print(f"找到m3u8 URL: {url}")
        
        return urls

    def extract_player_config(self, html_content):
        """
        提取播放器配置中的URL
        """
        try:
            # 查找ArtPlayer配置
            artplayer_patterns = [
                r'new\s+Artplayer\s*\(\s*({[^}]+}(?:[^}]+})*)',
                r'artplayer\s*\(\s*({[^}]+}(?:[^}]+})*)',
                r'var\s+player\s*=\s*new\s+Artplayer\s*\(\s*({[^}]+}(?:[^}]+})*)',
            ]
            
            for pattern in artplayer_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    print(f"找到ArtPlayer配置: {match[:200]}...")
                    # 尝试提取URL字段
                    url_match = re.search(r'url\s*:\s*["\']([^"\']+)["\']', match)
                    if url_match:
                        return {'url': url_match.group(1)}
            
            # 查找其他播放器配置
            player_patterns = [
                r'player_data\s*=\s*({[^}]+})',
                r'video_info\s*=\s*({[^}]+})',
                r'play_data\s*=\s*({[^}]+})',
            ]
            
            for pattern in player_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    try:
                        # 清理JSON格式
                        json_str = match.replace("'", '"')
                        json_str = re.sub(r',\s*}', '}', json_str)
                        data = json.loads(json_str)
                        if 'url' in data:
                            return {'url': data['url']}
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"提取播放器配置失败: {e}")
            return None

    def find_base64_encoded_urls(self, html_content):
        """
        查找Base64编码的URL
        """
        urls = []
        
        # 查找Base64编码的字符串
        base64_patterns = [
            r'["\']([A-Za-z0-9+/=]{20,})["\']',
            r'atob\s*\(\s*["\']([A-Za-z0-9+/=]+)["\']',
        ]
        
        for pattern in base64_patterns:
            matches = re.findall(pattern, html_content)
            for match in matches:
                urls.append(match)
                print(f"找到Base64字符串: {match[:50]}...")
        
        return urls

    def decode_base64_url(self, encoded_str):
        """
        解码Base64字符串
        """
        try:
            decoded = b64decode(encoded_str).decode('utf-8')
            print(f"Base64解码结果: {decoded}")
            
            # 检查解码后是否是有效的URL
            if decoded.startswith('http') and '.m3u8' in decoded:
                return decoded
            
            # 如果不是直接URL，可能在解码后的内容中
            m3u8_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', decoded)
            if m3u8_matches:
                return m3u8_matches[0]
                
            return None
        except:
            return None

    def extract_urls_from_json(self, html_content):
        """
        从JSON数据中提取URL
        """
        urls = []
        
        # 查找JSON格式的数据
        json_patterns = [
            r'var\s+[\w_]+\s*=\s*({[^;]+});',
            r'window\.\w+\s*=\s*({[^;]+});',
            r'=\s*({[^;]+})\s*;',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL)
            for match in matches:
                try:
                    # 尝试解析JSON
                    json_str = match.replace("'", '"')
                    json_str = re.sub(r',\s*}', '}', json_str)
                    data = json.loads(json_str)
                    
                    # 递归搜索JSON中的URL
                    def search_json(obj, path=""):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if isinstance(value, str) and '.m3u8' in value:
                                    urls.append(value)
                                    print(f"JSON路径 {path}.{key}: {value}")
                                elif isinstance(value, (dict, list)):
                                    search_json(value, f"{path}.{key}")
                        elif isinstance(obj, list):
                            for i, item in enumerate(obj):
                                if isinstance(item, str) and '.m3u8' in item:
                                    urls.append(item)
                                    print(f"JSON数组 {path}[{i}]: {item}")
                                elif isinstance(item, (dict, list)):
                                    search_json(item, f"{path}[{i}]")
                    
                    search_json(data)
                    
                except:
                    # 如果不是有效JSON，尝试在字符串中搜索m3u8
                    m3u8_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', match)
                    for url in m3u8_matches:
                        urls.append(url)
                        print(f"在JSON字符串中找到m3u8: {url}")
        
        return urls

    def extract_urls_from_iframes_and_scripts(self, data, html_content):
        """
        从iframe和脚本中提取URL
        """
        urls = []
        
        # 从iframe中提取
        iframes = data('iframe')
        for iframe in iframes.items():
            src = iframe.attr('src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = self.host + src
                urls.append(src)
                print(f"iframe URL: {src}")
        
        # 从脚本中提取
        scripts = data('script')
        for script in scripts.items():
            script_src = script.attr('src')
            if script_src:
                if script_src.startswith('//'):
                    script_src = 'https:' + script_src
                elif script_src.startswith('/'):
                    script_src = self.host + script_src
                urls.append(script_src)
                print(f"脚本URL: {script_src}")
            
            # 在脚本内容中搜索URL
            script_content = script.text()
            if script_content:
                m3u8_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', script_content)
                for url in m3u8_matches:
                    urls.append(url)
                    print(f"脚本内容中的m3u8: {url}")
        
        return urls

    def validate_m3u8_url(self, url):
        """
        验证m3u8 URL是否有效
        """
        if not url or '.m3u8' not in url:
            return False
        
        # 检查URL格式
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # 检查是否包含常见的视频CDN域名
        video_domains = ['hdzy.xyz', 'cdn', 'video', 'stream', 'm3u8']
        url_lower = url.lower()
        
        return any(domain in url_lower for domain in video_domains)

    def create_play_result(self, url, parse_type):
        """
        创建播放结果
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host,
        }
        
        print(f"创建播放结果 - URL: {url}, 解析类型: {parse_type}")
        return {
            'parse': parse_type,
            'url': url,
            'header': headers
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

    def tsProxy(self, url, type):
        try:
            headers = self.get_player_headers()
            data = requests.get(url, headers=headers, proxies=self.proxies, stream=True)
            return [200, data.headers.get('Content-Type', 'video/mp2t'), data.content]
        except Exception as e:
            return [500, "text/plain", f"TS Proxy Error: {e}"]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:
            return data

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy?do=py"

    def get_player_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host,
        }

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
