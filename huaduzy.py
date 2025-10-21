# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, unquote, parse_qs
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
            
        self.host = 'https://hd.hdys2.com'
        self.player_host = 'https://hd8.huaduzz.com'  # 播放器实际主机
        self.headers.update({'referer': f"{self.host}/"})
        
        if self.proxies:
            self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视prestrain修复版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        '''
        首页内容 - 保持稳定性
        '''
        try:
            response = self.session.get(self.host, timeout=10)
            if response.status_code != 200:
                return {'class': [], 'list': []}
                
            data = pq(response.text)
            result = {'class': [], 'list': []}
            
            # 提取分类
            cdata = data('li a')
            for item in cdata.items():
                href = item.attr('href')
                text = item.text().strip()
                if href and 'type' in href and text:
                    match = re.search(r'\d+', href)
                    if match:
                        result['class'].append({
                            'type_name': text,
                            'type_id': match.group(0)
                        })
            
            # 提取视频列表
            ldata = data('li')
            for item in ldata.items():
                link = item('a')
                if link.length > 0:
                    href = link.attr('href')
                    img = link('img')
                    if img.length > 0:
                        vod_name = img.attr('alt') or '未知'
                        vod_pic = img.attr('data-original') or img.attr('src') or ''
                        
                        if vod_pic and not vod_pic.startswith('http'):
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            else:
                                vod_pic = self.host + vod_pic
                        
                        result['list'].append({
                            'vod_id': href or '',
                            'vod_name': vod_name,
                            'vod_pic': vod_pic,
                            'vod_year': item('.pic-tag-t').text() or '',
                            'vod_remarks': item('.pic-tag-b').text() or ''
                        })
            
            return result
            
        except Exception as e:
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        '''
        分类内容 - 保持稳定性
        '''
        try:
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}
                
            data = pq(response.text)
            videos = []
            ldata = data('li')
            for item in ldata.items():
                link = item('a')
                if link.length > 0:
                    href = link.attr('href')
                    img = link('img')
                    if img.length > 0:
                        vod_name = img.attr('alt') or '未知'
                        vod_pic = img.attr('data-original') or img.attr('src') or ''
                        
                        if vod_pic and not vod_pic.startswith('http'):
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            else:
                                vod_pic = self.host + vod_pic
                        
                        videos.append({
                            'vod_id': href or '',
                            'vod_name': vod_name,
                            'vod_pic': vod_pic,
                            'vod_year': item('.pic-tag-t').text() or '',
                            'vod_remarks': item('.pic-tag-b').text() or ''
                        })
            
            return {
                'list': videos,
                'page': pg,
                'pagecount': 9999,
                'limit': 90,
                'total': 999999
            }
            
        except Exception as e:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        '''
        详情页 - 保持稳定性
        '''
        try:
            url = f"{self.host}{ids[0]}"
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': []}
                
            data = pq(response.text)
            
            # 获取标题
            title_elem = data('.title') or data('h1') or data('title')
            vod_name = title_elem.text() if title_elem.length > 0 else '未知'
            
            # 获取封面
            img_elem = data('img')
            vod_pic = ''
            for img in img_elem.items():
                src = img.attr('data-original') or img.attr('src')
                if src and not vod_pic:
                    vod_pic = src
                    if not vod_pic.startswith('http'):
                        if vod_pic.startswith('//'):
                            vod_pic = 'https:' + vod_pic
                        else:
                            vod_pic = self.host + vod_pic
                    break
            
            # 获取播放链接
            play_links = []
            links = data('a')
            for link in links.items():
                href = link.attr('href')
                if href and 'play' in href:
                    play_links.append(f"第1集${href}")
                    break
            
            if not play_links:
                play_links = [f"第1集${ids[0]}"]
            
            vod = {
                'vod_id': ids[0],
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_play_from': '花都影视',
                'vod_play_url': "#".join(play_links)
            }
            
            return {'list': [vod]}
            
        except Exception as e:
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        '''
        搜索功能 - 保持稳定性
        '''
        try:
            import urllib.parse
            encoded_key = urllib.parse.quote(key)
            url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': [], 'page': pg}
                
            data = pq(response.text)
            videos = []
            ldata = data('li')
            for item in ldata.items():
                link = item('a')
                if link.length > 0:
                    href = link.attr('href')
                    img = link('img')
                    if img.length > 0:
                        vod_name = img.attr('alt') or '未知'
                        vod_pic = img.attr('data-original') or img.attr('src') or ''
                        
                        if vod_pic and not vod_pic.startswith('http'):
                            if vod_pic.startswith('//'):
                                vod_pic = 'https:' + vod_pic
                            else:
                                vod_pic = self.host + vod_pic
                        
                        videos.append({
                            'vod_id': href or '',
                            'vod_name': vod_name,
                            'vod_pic': vod_pic,
                            'vod_year': item('.pic-tag-t').text() or '',
                            'vod_remarks': item('.pic-tag-b').text() or ''
                        })
            
            return {'list': videos, 'page': pg}
            
        except Exception as e:
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - 基于prestrain.html的修复版本
        直接模拟访问播放器实际工作页面
        """
        print("=== prestrain.html模式启动 ===")
        play_page_url = f"{self.host}{id}"
        print(f"原始播放页面: {play_page_url}")
        
        try:
            # 首先获取原始播放页面，提取prestrain.html的参数
            prestrain_url, params = self.extract_prestrain_info(play_page_url)
            if not prestrain_url:
                print("无法提取prestrain信息，使用备用方案")
                return self.create_play_result(play_page_url, 1)
            
            print(f"prestrain页面: {prestrain_url}")
            print(f"参数: {params}")
            
            # 访问prestrain.html页面
            m3u8_url = self.get_m3u8_from_prestrain(prestrain_url, params, play_page_url)
            if m3u8_url and self.validate_m3u8_url(m3u8_url):
                print(f"从prestrain获取到m3u8: {m3u8_url}")
                return self.create_play_result(m3u8_url, 0)
            
            # 如果prestrain方法失败，尝试其他方法
            print("prestrain方法失败，尝试其他方法")
            return self.try_alternative_methods(play_page_url)
            
        except Exception as e:
            print(f"播放处理异常: {e}")
            import traceback
            traceback.print_exc()
            return self.create_play_result(play_page_url, 1)

    def extract_prestrain_info(self, play_page_url):
        """
        从播放页面提取prestrain.html的URL和参数
        """
        try:
            response = self.session.get(play_page_url, timeout=10)
            if response.status_code != 200:
                return None, None
            
            html_content = response.text
            data = pq(html_content)
            
            # 方法1: 查找iframe中的prestrain
            iframes = data('iframe')
            for iframe in iframes.items():
                src = iframe.attr('src')
                if src and 'prestrain.html' in src:
                    print(f"找到prestrain iframe: {src}")
                    return self.parse_prestrain_url(src)
            
            # 方法2: 查找脚本中的prestrain
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if 'prestrain.html' in script_text:
                    print("在脚本中找到prestrain引用")
                    # 提取prestrain URL
                    prestrain_matches = re.findall(r'["\'](https?://[^"\']*prestrain\.html[^"\']*)["\']', script_text)
                    for match in prestrain_matches:
                        print(f"脚本中的prestrain: {match}")
                        return self.parse_prestrain_url(match)
            
            # 方法3: 直接构造prestrain URL
            # 基于观察，prestrain URL可能有固定模式
            prestrain_base = "https://hd8.huaduzz.com/static/player/prestrain.html"
            # 尝试从播放URL提取参数
            play_id_match = re.search(r'/(\d+-\d+-\d+)\.html', play_page_url)
            if play_id_match:
                play_id = play_id_match.group(1)
                params = {
                    'url': play_page_url,
                    'id': play_id,
                    'referer': self.host
                }
                return prestrain_base, params
            
            return None, None
            
        except Exception as e:
            print(f"提取prestrain信息失败: {e}")
            return None, None

    def parse_prestrain_url(self, url):
        """
        解析prestrain URL和参数
        """
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            params = parse_qs(parsed.query)
            
            # 简化参数格式
            simple_params = {}
            for key, value in params.items():
                if value:
                    simple_params[key] = value[0]
            
            return base_url, simple_params
        except Exception as e:
            print(f"解析prestrain URL失败: {e}")
            return url, {}

    def get_m3u8_from_prestrain(self, prestrain_url, params, referer_url):
        """
        从prestrain.html页面获取m3u8地址
        """
        try:
            # 设置prestrain页面的请求头
            prestrain_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Referer': referer_url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
            
            # 访问prestrain页面
            response = requests.get(prestrain_url, params=params, headers=prestrain_headers, timeout=10)
            if response.status_code != 200:
                print(f"prestrain页面访问失败: {response.status_code}")
                return None
            
            prestrain_content = response.text
            print(f"prestrain页面内容长度: {len(prestrain_content)}")
            
            # 在prestrain页面中搜索m3u8地址
            m3u8_urls = self.search_m3u8_in_prestrain(prestrain_content)
            for url in m3u8_urls:
                if self.validate_m3u8_url(url):
                    return url
            
            # 如果没有找到，尝试查找API请求
            api_url = self.find_api_in_prestrain(prestrain_content)
            if api_url:
                print(f"找到API URL: {api_url}")
                m3u8_url = self.request_video_api(api_url, params, prestrain_headers)
                if m3u8_url:
                    return m3u8_url
            
            return None
            
        except Exception as e:
            print(f"从prestrain获取m3u8失败: {e}")
            return None

    def search_m3u8_in_prestrain(self, prestrain_content):
        """
        在prestrain页面内容中搜索m3u8地址
        """
        m3u8_urls = []
        
        # 搜索各种格式的m3u8链接
        patterns = [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'url\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'file\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, prestrain_content, re.IGNORECASE)
            for match in matches:
                url = match
                if url not in m3u8_urls:
                    m3u8_urls.append(url)
                    print(f"在prestrain中找到m3u8: {url}")
        
        return m3u8_urls

    def find_api_in_prestrain(self, prestrain_content):
        """
        在prestrain页面中查找API请求
        """
        try:
            # 查找可能的API端点
            api_patterns = [
                r'https?://[^"\']+\.php[^"\']*',
                r'https?://[^"\']+\.json[^"\']*',
                r'https?://[^"\']+/api/[^"\']*',
                r'fetch\s*\(\s*["\']([^"\']+)["\']',
                r'axios\.get\s*\(\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, prestrain_content, re.IGNORECASE)
                for match in matches:
                    if any(keyword in match for keyword in ['video', 'play', 'vod', 'm3u8', 'url']):
                        return match
            
            return None
            
        except Exception as e:
            print(f"查找API失败: {e}")
            return None

    def request_video_api(self, api_url, params, headers):
        """
        请求视频API获取m3u8地址
        """
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                # 尝试解析JSON响应
                try:
                    data = response.json()
                    if 'url' in data:
                        return data['url']
                    if 'm3u8' in data:
                        return data['m3u8']
                except:
                    # 如果不是JSON，在响应中搜索m3u8
                    m3u8_matches = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', response.text)
                    if m3u8_matches:
                        return m3u8_matches[0]
            
            return None
            
        except Exception as e:
            print(f"请求视频API失败: {e}")
            return None

    def try_alternative_methods(self, play_page_url):
        """
        备用方法：如果prestrain方法失败，尝试其他方法
        """
        try:
            response = self.session.get(play_page_url, timeout=10)
            if response.status_code != 200:
                return self.create_play_result(play_page_url, 1)
            
            html_content = response.text
            
            # 方法1: 直接搜索HTML中的m3u8
            m3u8_urls = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html_content, re.IGNORECASE)
            for url in m3u8_urls:
                if self.validate_m3u8_url(url):
                    print(f"备用方法找到m3u8: {url}")
                    return self.create_play_result(url, 0)
            
            # 方法2: 搜索JavaScript中的变量
            scripts = re.findall(r'<script[^>]*>([^<]*)</script>', html_content, re.IGNORECASE)
            for script in scripts:
                url_matches = re.findall(r'url\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']', script, re.IGNORECASE)
                for match in url_matches:
                    if self.validate_m3u8_url(match):
                        print(f"脚本中找到m3u8: {match}")
                        return self.create_play_result(match, 0)
            
            # 所有方法都失败
            return self.create_play_result(play_page_url, 1)
            
        except Exception as e:
            print(f"备用方法失败: {e}")
            return self.create_play_result(play_page_url, 1)

    def validate_m3u8_url(self, url):
        """
        验证m3u8 URL是否有效
        """
        if not url or '.m3u8' not in url:
            return False
        
        # 检查URL格式
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        return True

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
            url = param.get('url', '')
            if not url:
                return [400, "text/plain", "Missing URL"]
                
            response = requests.get(url, timeout=10)
            return [200, response.headers.get('content-type', 'text/plain'), response.content]
            
        except Exception as e:
            return [500, "text/plain", f"Proxy Error: {e}"]
