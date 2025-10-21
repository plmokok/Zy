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
        初始化方法
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
        self.headers.update({'referer': f"{self.host}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视深度修复版"

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
        深度修复播放内容获取
        """
        try:
            print(f"=== 开始处理播放地址 ===")
            play_page_url = f"{self.host}{id}"
            print(f"播放页面: {play_page_url}")
            
            # 获取播放页面
            response = self.session.get(play_page_url)
            data = self.getpq(response)
            
            # 方法1: 从JavaScript中提取播放地址
            video_url = self.extract_video_url_advanced(data, play_page_url)
            if video_url and self.validate_video_url(video_url):
                print(f"成功提取播放地址: {video_url}")
                return self.create_play_result(video_url, 0)
            
            # 方法2: 尝试直接播放页面
            print("使用直接播放页面方案")
            return self.create_play_result(play_page_url, 1)
            
        except Exception as e:
            print(f"播放处理异常: {e}")
            import traceback
            traceback.print_exc()
            return self.create_play_result(f"{self.host}{id}", 1)

    def extract_video_url_advanced(self, data, play_page_url):
        """
        高级视频地址提取方法
        """
        # 策略1: 从脚本中提取标准JSON格式
        scripts = data('.stui-player.col-pd script')
        for script in scripts.items():
            script_text = script.text()
            print(f"检查脚本: {script_text[:100]}...")
            
            # 尝试提取标准JSON
            video_url = self.extract_standard_json(script_text)
            if video_url:
                return video_url
                
            # 尝试提取加密或编码的URL
            video_url = self.extract_encoded_url(script_text)
            if video_url:
                return video_url
                
            # 尝试提取变量赋值格式
            video_url = self.extract_variable_assignment(script_text)
            if video_url:
                return video_url
        
        # 策略2: 检查iframe
        iframe = data('iframe')
        if iframe.length > 0:
            iframe_src = iframe.attr('src')
            if iframe_src:
                print(f"找到iframe: {iframe_src}")
                # 处理相对URL
                if not iframe_src.startswith('http'):
                    if iframe_src.startswith('//'):
                        iframe_src = 'https:' + iframe_src
                    else:
                        iframe_src = self.host + iframe_src
                return iframe_src
        
        # 策略3: 检查视频标签
        video = data('video source')
        if video.length > 0:
            video_src = video.attr('src')
            if video_src:
                print(f"找到video标签: {video_src}")
                if not video_src.startswith('http'):
                    if video_src.startswith('//'):
                        video_src = 'https:' + video_src
                    else:
                        video_src = self.host + video_src
                return video_src
        
        # 策略4: 在页面HTML中搜索视频URL模式
        html_content = data.html()
        video_url = self.search_video_patterns(html_content)
        if video_url:
            return video_url
            
        return None

    def extract_standard_json(self, script_text):
        """提取标准JSON格式的播放地址"""
        try:
            # 匹配常见的JSON格式
            patterns = [
                r'player_data\s*=\s*({[^;]+});',
                r'var\s+player_\w+\s*=\s*({[^;]+});',
                r'video_info\s*=\s*({[^;]+});',
                r'=\s*({[^;]+})\.url',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, script_text)
                if match:
                    json_str = match.group(1)
                    # 修复常见的JSON格式问题
                    json_str = self.fix_json_format(json_str)
                    jsdata = json.loads(json_str)
                    
                    if 'url' in jsdata and jsdata['url']:
                        url = jsdata['url']
                        return self.process_extracted_url(url)
                        
        except Exception as e:
            print(f"标准JSON提取失败: {e}")
            
        return None

    def extract_encoded_url(self, script_text):
        """提取编码或加密的URL"""
        try:
            # 查找Base64编码的URL
            base64_patterns = [
                r'url\s*:\s*["\']([A-Za-z0-9+/=]+)["\']',
                r'="([A-Za-z0-9+/=]{20,})"',
            ]
            
            for pattern in base64_patterns:
                matches = re.findall(pattern, script_text)
                for match in matches:
                    try:
                        decoded = b64decode(match).decode('utf-8')
                        if self.validate_video_url(decoded):
                            return self.process_extracted_url(decoded)
                    except:
                        continue
            
            # 查找URL编码的地址
            encoded_patterns = [
                r'url\s*:\s*decodeURIComponent\(["\']([^"\']+)["\']\)',
                r'decodeURIComponent\(["\']([^"\']+)["\']\)',
            ]
            
            for pattern in encoded_patterns:
                matches = re.findall(pattern, script_text)
                for match in matches:
                    try:
                        decoded = unquote(match)
                        if self.validate_video_url(decoded):
                            return self.process_extracted_url(decoded)
                    except:
                        continue
                        
        except Exception as e:
            print(f"编码URL提取失败: {e}")
            
        return None

    def extract_variable_assignment(self, script_text):
        """提取变量赋值格式的URL"""
        try:
            # 查找直接赋值格式
            patterns = [
                r'player\.url\s*=\s*["\']([^"\']+)["\']',
                r'url\s*=\s*["\']([^"\']+)["\']',
                r'src\s*=\s*["\']([^"\']+)["\']',
                r'file\s*=\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, script_text, re.IGNORECASE)
                for match in matches:
                    if self.validate_video_url(match):
                        return self.process_extracted_url(match)
                        
        except Exception as e:
            print(f"变量赋值提取失败: {e}")
            
        return None

    def search_video_patterns(self, html_content):
        """在HTML内容中搜索视频URL模式"""
        try:
            # 直接搜索视频文件URL
            video_patterns = [
                r'https?://[^\s"\']+\.(m3u8|mp4|flv)[^\s"\']*',
                r'//[^\s"\']+\.(m3u8|mp4|flv)[^\s"\']*',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    url = match if isinstance(match, str) else match[0]
                    if not url.startswith('http'):
                        url = 'https:' + url if url.startswith('//') else self.host + url
                    
                    if self.validate_video_url(url):
                        return url
                        
        except Exception as e:
            print(f"模式搜索失败: {e}")
            
        return None

    def fix_json_format(self, json_str):
        """修复JSON格式问题"""
        # 修复常见的JSON格式错误
        json_str = re.sub(r',\s*}', '}', json_str)  # 移除尾随逗号
        json_str = re.sub(r',\s*]', ']', json_str)  # 移除尾随逗号
        json_str = re.sub(r"'", '"', json_str)  # 单引号转双引号
        return json_str

    def process_extracted_url(self, url):
        """处理提取到的URL"""
        if not url.startswith('http'):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = self.host + url
        
        # 对m3u8文件进行特殊处理
        if '.m3u8' in url:
            url = self.proxy(url, 'm3u8')
            
        return url

    def validate_video_url(self, url):
        """验证视频URL是否有效"""
        if not url:
            return False
            
        # 检查URL格式
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # 检查是否包含视频文件扩展名或特征
        video_indicators = ['.m3u8', '.mp4', '.flv', 'm3u8', 'index.m3u8']
        if not any(indicator in url.lower() for indicator in video_indicators):
            return False
            
        print(f"URL验证通过: {url}")
        return True

    def create_play_result(self, url, parse_type):
        """创建播放结果"""
        headers = self.get_player_headers()
        
        # 对于m3u8文件，确保使用正确的Content-Type
        if '.m3u8' in url and parse_type == 0:
            # 直接返回m3u8地址，让播放器处理
            return {
                'parse': parse_type,
                'url': url,
                'header': headers
            }
        else:
            return {
                'parse': parse_type,
                'url': url,
                'header': headers
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
