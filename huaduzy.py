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
        初始化 - 保持B版的稳定性
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
        return "花都影视播放修复版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        '''
        首页内容 - 保持B版的稳定性
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
        分类内容 - 保持B版的稳定性
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
        详情页 - 保持B版的稳定性
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
        搜索功能 - 保持B版的稳定性
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
        播放内容获取 - 重点修复版本
        使用多种策略获取真实的视频播放地址
        """
        print("=== 播放地址修复 ===")
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
            
            # 策略1: 从JavaScript中提取真实播放地址
            real_video_url = self.extract_real_video_url(data, html_content)
            if real_video_url:
                print(f"策略1成功: {real_video_url}")
                return self.create_play_result(real_video_url, 0)
            
            # 策略2: 检查是否有直接视频标签
            video_url = self.extract_direct_video_url(data)
            if video_url:
                print(f"策略2成功: {video_url}")
                return self.create_play_result(video_url, 0)
            
            # 策略3: 检查iframe中的播放器
            video_url = self.extract_iframe_player(data)
            if video_url:
                print(f"策略3成功: {video_url}")
                return self.create_play_result(video_url, 1)
            
            # 策略4: 在HTML中搜索视频文件模式
            video_url = self.search_video_patterns(html_content)
            if video_url:
                print(f"策略4成功: {video_url}")
                return self.create_play_result(video_url, 0)
                
            # 所有策略失败，使用最终方案
            print("所有策略失败，使用最终方案")
            return self.create_play_result(play_page_url, 1)
            
        except Exception as e:
            print(f"播放处理异常: {e}")
            return self.create_play_result(play_page_url, 1)

    def extract_real_video_url(self, data, html_content):
        """
        从JavaScript中提取真实的视频播放地址
        """
        try:
            # 查找包含播放信息的脚本
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                
                # 查找包含视频URL的JavaScript代码
                if 'url' in script_text and ('m3u8' in script_text or 'mp4' in script_text):
                    print(f"找到包含视频URL的脚本: {script_text[:200]}...")
                    
                    # 尝试多种提取模式
                    url_patterns = [
                        r'url\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                        r'player\.url\s*=\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                        r'file\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                        r'src\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                        r'video_url\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4)[^"\']*)["\']',
                    ]
                    
                    for pattern in url_patterns:
                        matches = re.findall(pattern, script_text, re.IGNORECASE)
                        for match in matches:
                            url = match[0] if isinstance(match, tuple) else match
                            if url and self.is_valid_video_url(url):
                                return self.normalize_url(url)
            
            # 查找JSON格式的播放信息
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
                        if 'url' in jsdata and jsdata['url']:
                            url = jsdata['url']
                            if self.is_valid_video_url(url):
                                return self.normalize_url(url)
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"提取真实视频URL失败: {e}")
            return None

    def extract_direct_video_url(self, data):
        """
        提取直接视频标签中的URL
        """
        try:
            # 检查video标签
            video_tags = data('video')
            for video in video_tags.items():
                src = video.attr('src')
                if src and self.is_valid_video_url(src):
                    return self.normalize_url(src)
            
            # 检查source标签
            source_tags = data('source')
            for source in source_tags.items():
                src = source.attr('src')
                if src and self.is_valid_video_url(src):
                    return self.normalize_url(src)
            
            return None
            
        except Exception as e:
            print(f"提取直接视频URL失败: {e}")
            return None

    def extract_iframe_player(self, data):
        """
        提取iframe播放器地址
        """
        try:
            iframes = data('iframe')
            for iframe in iframes.items():
                src = iframe.attr('src')
                if src and src.startswith('http'):
                    return self.normalize_url(src)
            
            return None
            
        except Exception as e:
            print(f"提取iframe播放器失败: {e}")
            return None

    def search_video_patterns(self, html_content):
        """
        在HTML中搜索视频文件模式
        """
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
                    if self.is_valid_video_url(url):
                        return self.normalize_url(url)
            
            return None
            
        except Exception as e:
            print(f"搜索视频模式失败: {e}")
            return None

    def is_valid_video_url(self, url):
        """
        验证URL是否为有效的视频地址
        """
        if not url:
            return False
            
        # 检查URL格式
        if url.startswith('javascript:') or url.startswith('data:'):
            return False
            
        # 检查是否包含视频文件特征
        video_indicators = ['.m3u8', '.mp4', '.flv', 'video', 'stream']
        url_lower = url.lower()
        
        return any(indicator in url_lower for indicator in video_indicators)

    def normalize_url(self, url):
        """
        标准化URL
        """
        if not url.startswith('http'):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                url = self.host + url
        
        return url

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
