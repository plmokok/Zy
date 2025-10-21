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
            
        self.host = 'https://hd.hdys2.com'
        self.headers.update({'referer': f"{self.host}/"})
        
        if self.proxies:
            self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视嗅探版"

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
        播放内容获取 - 基于网络请求嗅探的版本
        模拟VIA浏览器的视频嗅探行为
        """
        print("=== 视频嗅探模式启动 ===")
        play_page_url = f"{self.host}{id}"
        print(f"播放页面: {play_page_url}")
        
        try:
            # 获取播放页面
            response = self.session.get(play_page_url, timeout=10)
            if response.status_code != 200:
                print(f"播放页面请求失败: {response.status_code}")
                return self.create_play_result(play_page_url, 1)
            
            html_content = response.text
            data = pq(html_content)
            
            # 策略1: 直接搜索HTML中的m3u8链接
            m3u8_urls = self.find_m3u8_in_html(html_content)
            if m3u8_urls:
                print(f"在HTML中找到{len(m3u8_urls)}个m3u8链接")
                for url in m3u8_urls:
                    if self.validate_m3u8_url(url):
                        print(f"使用有效的m3u8链接: {url}")
                        return self.create_play_result(url, 0)
            
            # 策略2: 从JavaScript变量中提取
            m3u8_url = self.extract_m3u8_from_scripts(data, html_content)
            if m3u8_url and self.validate_m3u8_url(m3u8_url):
                print(f"从脚本中提取到m3u8: {m3u8_url}")
                return self.create_play_result(m3u8_url, 0)
            
            # 策略3: 模拟播放器请求获取m3u8
            m3u8_url = self.simulate_player_request(data, html_content, play_page_url)
            if m3u8_url and self.validate_m3u8_url(m3u8_url):
                print(f"模拟播放器请求获取到m3u8: {m3u8_url}")
                return self.create_play_result(m3u8_url, 0)
            
            # 策略4: 尝试直接请求播放器API
            m3u8_url = self.request_player_api(data, html_content, play_page_url)
            if m3u8_url and self.validate_m3u8_url(m3u8_url):
                print(f"从播放器API获取到m3u8: {m3u8_url}")
                return self.create_play_result(m3u8_url, 0)
                
            # 所有策略失败
            print("所有嗅探策略失败，使用备用方案")
            return self.create_play_result(play_page_url, 1)
            
        except Exception as e:
            print(f"播放处理异常: {e}")
            import traceback
            traceback.print_exc()
            return self.create_play_result(play_page_url, 1)

    def find_m3u8_in_html(self, html_content):
        """
        在HTML内容中直接搜索m3u8链接
        """
        m3u8_urls = []
        
        # 搜索各种格式的m3u8链接
        patterns = [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',  # 标准m3u8链接
            r'//[^\s"\']+\.m3u8[^\s"\']*',         # 协议相对m3u8链接
            r'/[^\s"\']+\.m3u8[^\s"\']*',          # 绝对路径m3u8链接
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
                
                if url not in m3u8_urls:
                    m3u8_urls.append(url)
        
        return m3u8_urls

    def extract_m3u8_from_scripts(self, data, html_content):
        """
        从JavaScript脚本中提取m3u8地址
        """
        try:
            # 查找所有脚本
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                
                # 在脚本中搜索m3u8
                m3u8_patterns = [
                    r'url\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'file\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'src\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'video_url\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
                ]
                
                for pattern in m3u8_patterns:
                    matches = re.findall(pattern, script_text, re.IGNORECASE)
                    for match in matches:
                        url = match
                        if not url.startswith('http'):
                            if url.startswith('//'):
                                url = 'https:' + url
                            else:
                                url = self.host + url
                        return url
            
            # 搜索JSON格式的播放信息
            json_patterns = [
                r'var\s+player_data\s*=\s*({[^;]+});',
                r'player_data\s*=\s*({[^;]+});',
                r'video_info\s*=\s*({[^;]+});',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    try:
                        # 清理JSON格式
                        json_str = match.replace("'", '"')
                        json_str = re.sub(r',\s*}', '}', json_str)
                        json_str = re.sub(r',\s*]', ']', json_str)
                        
                        jsdata = json.loads(json_str)
                        if 'url' in jsdata and jsdata['url'] and '.m3u8' in jsdata['url']:
                            url = jsdata['url']
                            if not url.startswith('http'):
                                if url.startswith('//'):
                                    url = 'https:' + url
                                else:
                                    url = self.host + url
                            return url
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"脚本提取失败: {e}")
            return None

    def simulate_player_request(self, data, html_content, play_page_url):
        """
        模拟播放器请求获取m3u8地址
        """
        try:
            # 查找可能的播放器配置
            player_configs = self.find_player_configs(data, html_content)
            
            # 如果有播放器配置，尝试模拟请求
            for config in player_configs:
                m3u8_url = self.try_player_config(config, play_page_url)
                if m3u8_url:
                    return m3u8_url
            
            return None
            
        except Exception as e:
            print(f"模拟播放器请求失败: {e}")
            return None

    def find_player_configs(self, data, html_content):
        """
        查找播放器配置信息
        """
        configs = []
        
        # 查找常见的播放器初始化代码
        player_patterns = [
            r'player\s*=\s*new\s+\w+Player\s*\(([^)]+)\)',
            r'\$\(\s*["\']#\w+["\']\s*\)\.player\s*\(([^)]+)\)',
            r'videojs\s*\([^)]*,\s*([^)]+)\)',
        ]
        
        for pattern in player_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                configs.append(match)
        
        return configs

    def try_player_config(self, config, play_page_url):
        """
        尝试根据播放器配置获取m3u8地址
        """
        try:
            # 这里可以根据具体的播放器配置发送请求
            # 由于我们不知道具体的API格式，先返回None
            return None
        except:
            return None

    def request_player_api(self, data, html_content, play_page_url):
        """
        尝试直接请求播放器API
        """
        try:
            # 查找可能的API端点
            api_patterns = [
                r'https?://[^\s"\']+\.php[^\s"\']*',
                r'https?://[^\s"\']+\.json[^\s"\']*',
                r'https?://[^\s"\']+/api/[^\s"\']*',
            ]
            
            for pattern in api_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if 'm3u8' in match or 'video' in match or 'play' in match:
                        try:
                            # 尝试请求这个API端点
                            response = self.session.get(match, timeout=10)
                            if response.status_code == 200:
                                # 在响应中搜索m3u8
                                m3u8_urls = self.find_m3u8_in_html(response.text)
                                if m3u8_urls:
                                    return m3u8_urls[0]
                        except:
                            continue
            
            return None
            
        except Exception as e:
            print(f"请求播放器API失败: {e}")
            return None

    def validate_m3u8_url(self, url):
        """
        验证m3u8 URL是否有效
        """
        if not url or '.m3u8' not in url:
            return False
        
        # 检查URL格式
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # 可以进一步验证，比如发送HEAD请求检查是否存在
        # 但为了性能，我们暂时只做基本验证
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
