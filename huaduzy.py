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
        初始化 - 保持稳定
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
        return "花都影视精确修复版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        '''
        首页内容 - 保持稳定
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
        分类内容 - 保持稳定
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
        详情页 - 保持稳定
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
        搜索功能 - 保持稳定
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
        播放内容获取 - 基于真实m3u8地址的精确修复
        """
        print("=== 基于真实m3u8的精确修复 ===")
        play_page_url = f"{self.host}{id}"
        print(f"播放页面: {play_page_url}")
        
        try:
            # 获取播放页面
            response = self.session.get(play_page_url, timeout=10)
            if response.status_code != 200:
                print(f"播放页面请求失败: {response.status_code}")
                return self.create_fallback_result(play_page_url)
            
            html_content = response.text
            data = pq(html_content)
            
            # 策略1: 精确提取类似真实m3u8地址的URL
            real_m3u8_url = self.extract_exact_m3u8_url(data, html_content)
            if real_m3u8_url:
                print(f"策略1成功 - 提取到真实m3u8地址: {real_m3u8_url}")
                return self.create_direct_play_result(real_m3u8_url, play_page_url)
            
            # 策略2: 从JavaScript配置中提取
            m3u8_url = self.extract_from_javascript_config(data, html_content)
            if m3u8_url:
                print(f"策略2成功 - 从JS配置提取: {m3u8_url}")
                return self.create_direct_play_result(m3u8_url, play_page_url)
            
            # 策略3: 使用原版逻辑但改进验证
            m3u8_url = self.improved_original_method(data)
            if m3u8_url:
                print(f"策略3成功 - 改进原版方法: {m3u8_url}")
                return self.create_direct_play_result(m3u8_url, play_page_url)
                
            # 所有策略失败，使用最终方案
            print("所有精确提取策略失败，使用最终方案")
            return self.create_fallback_result(play_page_url)
            
        except Exception as e:
            print(f"播放处理异常: {e}")
            import traceback
            traceback.print_exc()
            return self.create_fallback_result(play_page_url)

    def extract_exact_m3u8_url(self, data, html_content):
        """
        精确提取类似真实m3u8地址的URL
        基于: https://cdn5.hdzy.xyz/videos/2025/10/18/68f385c8c4dadc91a4f1de1b/11ae6c/index.m3u8
        """
        try:
            # 查找包含视频ID和路径的脚本
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                
                # 查找包含视频ID的模式（类似68f385c8c4dadc91a4f1de1b）
                video_id_pattern = r'[a-f0-9]{24}'
                video_ids = re.findall(video_id_pattern, script_text)
                
                for video_id in video_ids:
                    print(f"找到可能的视频ID: {video_id}")
                    
                    # 构建可能的m3u8地址模式
                    possible_patterns = [
                        # 直接匹配CDN地址
                        rf'https?://cdn\d+\.hdzy\.xyz/videos/\d+/\d+/\d+/{video_id}/[a-f0-9]+/index\.m3u8',
                        # 匹配相对路径
                        rf'/videos/\d+/\d+/\d+/{video_id}/[a-f0-9]+/index\.m3u8',
                        # 匹配其他可能的CDN变体
                        rf'https?://[^"\']*{video_id}[^"\']*\.m3u8',
                    ]
                    
                    for pattern in possible_patterns:
                        matches = re.findall(pattern, script_text, re.IGNORECASE)
                        for match in matches:
                            url = match
                            if not url.startswith('http'):
                                if url.startswith('//'):
                                    url = 'https:' + url
                                else:
                                    # 使用已知的CDN域名构建完整URL
                                    url = f"https://cdn5.hdzy.xyz{url}" if url.startswith('/') else url
                            
                            if self.validate_m3u8_url(url):
                                return url
            
            # 在整个HTML中搜索m3u8地址
            m3u8_patterns = [
                r'https?://cdn\d+\.hdzy\.xyz/videos/\d+/\d+/\d+/[a-f0-9]+/[a-f0-9]+/index\.m3u8',
                r'https?://[^"\']+\.hdzy\.xyz[^"\']+\.m3u8',
            ]
            
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if self.validate_m3u8_url(match):
                        return match
            
            return None
            
        except Exception as e:
            print(f"精确m3u8提取失败: {e}")
            return None

    def extract_from_javascript_config(self, data, html_content):
        """
        从JavaScript配置中提取m3u8地址
        """
        try:
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                
                # 查找常见的播放器配置模式
                config_patterns = [
                    r'var\s+player_\w+\s*=\s*({[^;]+});',
                    r'player_data\s*=\s*({[^;]+});',
                    r'video_info\s*=\s*({[^;]+});',
                    r'=\s*({[^;]+})\.url',
                ]
                
                for pattern in config_patterns:
                    matches = re.findall(pattern, script_text)
                    for match in matches:
                        try:
                            # 清理JSON格式
                            json_str = self.clean_json_string(match)
                            jsdata = json.loads(json_str)
                            
                            # 尝试多种可能的字段名
                            possible_url_fields = ['url', 'src', 'file', 'video_url', 'm3u8_url']
                            
                            for field in possible_url_fields:
                                if field in jsdata and jsdata[field]:
                                    url = jsdata[field]
                                    if self.validate_m3u8_url(url):
                                        return self.normalize_url(url)
                                        
                        except Exception as e:
                            continue
            
            return None
            
        except Exception as e:
            print(f"JavaScript配置提取失败: {e}")
            return None

    def improved_original_method(self, data):
        """
        改进的原版方法，但增加验证
        """
        try:
            scripts = data('.stui-player.col-pd script')
            if scripts.length > 0:
                jstr = scripts.eq(0).text()
                print(f"原版方法 - 脚本内容: {jstr[:200]}...")
                
                # 尝试多种分割方式
                json_parts = [
                    jstr.split("=", maxsplit=1)[-1].strip(),
                    jstr.split(":", maxsplit=1)[-1].strip() if ":" in jstr else "",
                ]
                
                for json_part in json_parts:
                    if not json_part:
                        continue
                        
                    # 清理JSON
                    if json_part.endswith(';'):
                        json_part = json_part[:-1]
                    
                    try:
                        jsdata = json.loads(json_part)
                        if 'url' in jsdata and jsdata['url']:
                            url = jsdata['url']
                            if self.validate_m3u8_url(url):
                                return self.normalize_url(url)
                    except:
                        continue
            
            return None
            
        except Exception as e:
            print(f"改进原版方法失败: {e}")
            return None

    def clean_json_string(self, json_str):
        """
        清理JSON字符串
        """
        # 替换单引号为双引号
        json_str = json_str.replace("'", '"')
        # 移除尾随逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        # 修复未转义的双引号
        json_str = re.sub(r'(?<!\\)"', '\\"', json_str)
        return json_str

    def validate_m3u8_url(self, url):
        """
        验证URL是否为有效的m3u8地址
        """
        if not url:
            return False
            
        # 基本格式检查
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # 内容检查
        url_lower = url.lower()
        m3u8_indicators = ['.m3u8', 'index.m3u8', '/videos/']
        
        return any(indicator in url_lower for indicator in m3u8_indicators)

    def normalize_url(self, url):
        """
        标准化URL
        """
        if not url.startswith('http'):
            if url.startswith('//'):
                url = 'https:' + url
            else:
                # 对于相对路径，使用已知的CDN域名
                if url.startswith('/videos/'):
                    url = 'https://cdn5.hdzy.xyz' + url
                else:
                    url = self.host + url
        
        return url

    def create_direct_play_result(self, url, referer):
        """
        创建直接播放结果
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': referer,
            'Origin': self.host,
        }
        
        print(f"创建直接播放结果: {url}")
        return {
            'parse': 0,  # 0表示直接播放
            'url': url,
            'header': headers
        }

    def create_fallback_result(self, url):
        """
        创建备用播放结果
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
        }
        
        return {
            'parse': 1,  # 1表示需要解析
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
