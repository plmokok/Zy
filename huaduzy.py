# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse, quote
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
        # 使用更真实的浏览器头部
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
        
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
            
        self.host = self.gethost()
        print(f"使用的主机地址: {self.host}")
        self.headers.update({'referer': f"{self.host}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视修复版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        try:
            data = self.getpq(self.session.get(self.host))
            cdata = data('.stui-header__menu.type-slide li')
            ldata = data('.stui-vodlist.clearfix li')
            result = {}
            classes = []
            
            for k in cdata.items():
                i = k('a').attr('href')
                if i and 'type' in i:
                    match = re.search(r'\d+', i)
                    if match:
                        classes.append({
                            'type_name': k.text().strip(),
                            'type_id': match.group(0)
                        })
                        
            result['class'] = classes
            result['list'] = self.getlist(ldata)
            return result
        except Exception as e:
            print(f"首页加载失败: {e}")
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            data = self.getpq(self.session.get(url))
            result = {}
            result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
            result['page'] = pg
            result['pagecount'] = 9999
            result['limit'] = 90
            result['total'] = 999999
            return result
        except Exception as e:
            print(f"分类页面加载失败: {e}")
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        try:
            url = f"{self.host}{ids[0]}"
            data = self.getpq(self.session.get(url))
            
            # 获取视频标题
            title_elem = data('.stui-content__detail .title')
            vod_name = title_elem.text() if title_elem else "未知"
            
            # 获取播放链接
            play_links = []
            play_list = data('.stui-content__playlist a')
            for i, link in enumerate(play_list.items()):
                href = link.attr('href')
                if href:
                    play_links.append(f"第{i+1}集${href}")
            
            play_url = "##".join(play_links) if play_links else f"第1集${ids[0]}"
            
            vod = {
                'vod_id': ids[0],
                'vod_name': vod_name,
                'vod_pic': self.proxy(data('.stui-vodlist__thumb img').attr('data-original')),
                'vod_content': data('.stui-content__detail p.desc').text() or "",
                'vod_play_from': '花都影视',
                'vod_play_url': play_url
            }
            return {'list': [vod]}
        except Exception as e:
            print(f"详情页加载失败: {e}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        try:
            url = f"{self.host}/vodsearch/{quote(key)}----------{pg}---.html"
            data = self.getpq(self.session.get(url))
            return {'list': self.getlist(data('.stui-vodlist.clearfix li')), 'page': pg}
        except Exception as e:
            print(f"搜索失败: {e}")
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - 强化版本，使用多种策略获取播放地址
        """
        play_page_url = f"{self.host}{id}"
        print(f"正在处理播放地址: {play_page_url}")
        
        try:
            # 获取播放页面
            response = self.session.get(play_page_url, timeout=10)
            if response.status_code != 200:
                print(f"页面请求失败: {response.status_code}")
                return self.create_fallback_result(play_page_url)
            
            html_content = response.text
            data = self.getpq(html_content)
            
            # 策略1: 从JavaScript变量中提取
            play_url = self.extract_from_javascript(html_content)
            if play_url and self.validate_url(play_url):
                print(f"策略1成功: {play_url}")
                return self.create_success_result(play_url)
            
            # 策略2: 从iframe中提取
            play_url = self.extract_from_iframe(data)
            if play_url and self.validate_url(play_url):
                print(f"策略2成功: {play_url}")
                return self.create_success_result(play_url)
            
            # 策略3: 从视频标签中提取
            play_url = self.extract_from_video_tags(data)
            if play_url and self.validate_url(play_url):
                print(f"策略3成功: {play_url}")
                return self.create_success_result(play_url)
            
            # 策略4: 使用正则表达式搜索
            play_url = self.extract_with_regex(html_content)
            if play_url and self.validate_url(play_url):
                print(f"策略4成功: {play_url}")
                return self.create_success_result(play_url)
            
            # 策略5: 尝试直接播放页面的备用播放器
            play_url = self.extract_backup_player(data, play_page_url)
            if play_url and self.validate_url(play_url):
                print(f"策略5成功: {play_url}")
                return self.create_success_result(play_url)
                
            # 所有策略都失败，使用最终备用方案
            print("所有提取策略失败，使用最终备用方案")
            return self.create_fallback_result(play_page_url)
            
        except Exception as e:
            print(f"播放内容处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return self.create_fallback_result(play_page_url)

    def extract_from_javascript(self, html_content):
        """从JavaScript中提取播放地址"""
        try:
            # 匹配常见的JavaScript变量格式
            patterns = [
                r'url\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4))["\']',
                r'player\.url\s*=\s*["\']([^"\']+)["\']',
                r'src\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4))["\']',
                r'file\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4))["\']',
                r'video_url\s*[:=]\s*["\']([^"\']+\.(m3u8|mp4))["\']',
                r'var\s+url\s*=\s*["\']([^"\']+\.(m3u8|mp4))["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    url = match[0] if isinstance(match, tuple) else match
                    if url and not url.startswith('javascript'):
                        # 处理相对URL
                        if not url.startswith('http'):
                            if url.startswith('//'):
                                url = 'https:' + url
                            else:
                                url = self.host + '/' + url.lstrip('/')
                        return url
                        
            # 尝试解析JSON格式的播放信息
            json_patterns = [
                r'var\s+player_\w+\s*=\s*({[^}]+})',
                r'player_data\s*=\s*({[^}]+})',
                r'video_info\s*=\s*({[^}]+})',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if 'url' in data:
                            url = data['url']
                            if not url.startswith('http'):
                                if url.startswith('//'):
                                    url = 'https:' + url
                                else:
                                    url = self.host + '/' + url.lstrip('/')
                            return url
                    except:
                        continue
                        
        except Exception as e:
            print(f"JavaScript提取失败: {e}")
            
        return None

    def extract_from_iframe(self, data):
        """从iframe中提取播放地址"""
        try:
            iframes = data('iframe')
            for iframe in iframes.items():
                src = iframe.attr('src')
                if src and src.startswith('http'):
                    return src
                    
            # 检查embed标签
            embeds = data('embed')
            for embed in embeds.items():
                src = embed.attr('src')
                if src and src.startswith('http'):
                    return src
                    
        except Exception as e:
            print(f"iframe提取失败: {e}")
            
        return None

    def extract_from_video_tags(self, data):
        """从视频标签中提取播放地址"""
        try:
            # 检查video标签
            videos = data('video')
            for video in videos.items():
                src = video.attr('src')
                if src and src.startswith('http'):
                    return src
                    
            # 检查source标签
            sources = data('source')
            for source in sources.items():
                src = source.attr('src')
                if src and src.startswith('http'):
                    return src
                    
        except Exception as e:
            print(f"视频标签提取失败: {e}")
            
        return None

    def extract_with_regex(self, html_content):
        """使用正则表达式搜索播放地址"""
        try:
            # 直接搜索视频文件URL
            video_patterns = [
                r'https?://[^\s"\']+\.(m3u8|mp4|flv|avi|mkv|wmv)[^\s"\']*',
                r'//[^\s"\']+\.(m3u8|mp4|flv|avi|mkv|wmv)[^\s"\']*',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        url_part = match[0]
                    else:
                        url_part = match
                        
                    if not url_part.startswith('http'):
                        url_part = 'https:' + url_part if url_part.startswith('//') else self.host + '/' + url_part.lstrip('/')
                    
                    # 验证URL是否有效
                    if self.validate_url(url_part):
                        return url_part
                        
        except Exception as e:
            print(f"正则提取失败: {e}")
            
        return None

    def extract_backup_player(self, data, play_page_url):
        """提取备用播放器地址"""
        try:
            # 检查是否有备用播放器脚本
            scripts = data('script')
            for script in scripts.items():
                script_text = script.text()
                if 'player' in script_text and 'url' in script_text:
                    # 尝试提取播放器初始化代码中的URL
                    lines = script_text.split('\n')
                    for line in lines:
                        if 'url' in line and ('m3u8' in line or 'mp4' in line):
                            match = re.search(r'["\'](https?://[^"\']+\.(m3u8|mp4)[^"\']*)["\']', line)
                            if match:
                                return match.group(1)
                                
        except Exception as e:
            print(f"备用播放器提取失败: {e}")
            
        return None

    def validate_url(self, url):
        """验证URL是否有效"""
        if not url:
            return False
            
        # 检查URL格式
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # 检查是否包含视频文件扩展名
        video_extensions = ['.m3u8', '.mp4', '.flv', '.avi', '.mkv', '.wmv', '.ts']
        if not any(ext in url.lower() for ext in video_extensions):
            return False
            
        return True

    def create_success_result(self, url):
        """创建成功的播放结果"""
        headers = self.get_player_headers()
        
        # 如果是m3u8文件，可能需要特殊处理
        if '.m3u8' in url:
            return {
                'parse': 0,  # 0表示直接播放
                'url': url,
                'header': headers
            }
        else:
            return {
                'parse': 0,  # 0表示直接播放
                'url': url,
                'header': headers
            }

    def create_fallback_result(self, url):
        """创建备用播放结果"""
        print(f"使用备用播放方案: {url}")
        return {
            'parse': 1,  # 1表示需要解析
            'url': url,
            'header': self.get_player_headers()
        }

    def get_player_headers(self):
        """获取播放器头部信息"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

    def liveContent(self, url):
        return []

    def localProxy(self, param):
        """本地代理"""
        try:
            url = self.d64(param['url'])
            if param.get('type') == 'm3u8':
                return self.m3Proxy(url)
            else:
                return self.tsProxy(url, param.get('type', 'ts'))
        except Exception as e:
            print(f"代理处理错误: {e}")
            return [500, "text/plain", f"Proxy Error: {e}"]

    def gethost(self):
        """获取可用主机"""
        try:
            headers = self.headers.copy()
            headers['Referer'] = 'https://a.hdys.top/'
            response = requests.get('https://a.hdys.top/assets/js/config.js', headers=headers, timeout=10)
            urls = re.findall(r'"([^"]*)"', response.text)
            if urls:
                best_host = self.host_late(urls)
                print(f"自动选择最佳主机: {best_host}")
                return best_host
        except Exception as e:
            print(f"获取主机失败: {e}")
            
        # 备用主机列表
        backup_hosts = [
            'https://hd.hdys2.com',
            'https://hd.hdys1.com',
            'https://hd.hdys3.com'
        ]
        
        for host in backup_hosts:
            try:
                response = requests.head(host, timeout=3)
                if response.status_code == 200:
                    print(f"使用备用主机: {host}")
                    return host
            except:
                continue
                
        print("使用默认主机")
        return 'https://hd.hdys2.com'

    def getlist(self, data):
        """获取视频列表"""
        videos = []
        for i in data.items():
            vod_id = i('a').attr('href') or ''
            vod_name = i('img').attr('alt') or '未知'
            vod_pic = i('img').attr('data-original') or i('img').attr('src') or ''
            
            videos.append({
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': self.proxy(vod_pic),
                'vod_year': i('.pic-tag-t').text() or '',
                'vod_remarks': i('.pic-tag-b').text() or ''
            })
        return videos

    def getpq(self, data):
        """PyQuery包装器"""
        try:
            if hasattr(data, 'text'):
                return pq(data.text)
            else:
                return pq(data)
        except:
            try:
                return pq(data.content.decode('utf-8', errors='ignore'))
            except:
                return pq('')

    def host_late(self, url_list):
        """主机延迟测试"""
        if not url_list:
            return 'https://hd.hdys2.com'
            
        if len(url_list) == 1:
            return url_list[0]

        results = {}
        
        for url in url_list:
            try:
                start_time = time.time()
                response = requests.head(url, timeout=3, allow_redirects=False)
                delay = (time.time() - start_time) * 1000
                results[url] = delay
                print(f"主机 {url} 延迟: {delay:.2f}ms")
            except Exception as e:
                print(f"主机 {url} 测试失败: {e}")
                results[url] = float('inf')

        best_host = min(results.items(), key=lambda x: x[1])[0]
        return best_host

    def m3Proxy(self, url):
        """M3U8代理"""
        try:
            headers = self.get_player_headers()
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return [response.status_code, "text/plain", f"Failed to fetch M3U8: {response.status_code}"]
                
            content = response.text
            return [200, "application/vnd.apple.mpegurl", content]
        except Exception as e:
            print(f"M3U8代理错误: {e}")
            return [500, "text/plain", f"M3U8 Proxy Error: {e}"]

    def tsProxy(self, url, file_type):
        """TS文件代理"""
        try:
            headers = self.get_player_headers()
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            content_type = response.headers.get('content-type', 
                                              'video/mp2t' if file_type == 'ts' else 'image/jpeg')
            return [200, content_type, response.content]
        except Exception as e:
            print(f"TS代理错误: {e}")
            return [500, "text/plain", f"TS Proxy Error: {e}"]

    def proxy(self, url, file_type='img'):
        """代理URL生成"""
        if not url:
            return ""
            
        # 如果是完整URL且不需要代理，直接返回
        if url.startswith('http') and not self.proxies:
            return url
            
        # 相对路径转绝对路径
        if not url.startswith('http'):
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = self.host + url
            else:
                url = self.host + '/' + url
                
        # 如果需要代理，生成代理URL
        if self.proxies:
            encoded_url = self.e64(url)
            return f"http://127.0.0.1:9978/proxy?do=py&url={encoded_url}&type={file_type}"
        else:
            return url

    def e64(self, text):
        """Base64编码"""
        try:
            return b64encode(text.encode('utf-8')).decode('utf-8')
        except:
            return ""

    def d64(self, encoded_text):
        """Base64解码"""
        try:
            return b64decode(encoded_text.encode('utf-8')).decode('utf-8')
        except:
            return ""
