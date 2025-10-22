# -*- coding: utf-8 -*-
# 全新花都影视爬虫 - 专注于稳定首页访问
import json
import re
import requests
from pyquery import PyQuery as pq
import sys
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        '''
        最简化的初始化，确保稳定访问
        '''
        print("=== 花都影视爬虫初始化 ===")
        
        # 使用最基础的requests Session
        self.session = requests.Session()
        
        # 最简化的浏览器头部
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        
        # 固定主机地址，避免复杂的主机获取逻辑
        self.host = 'https://hd.hdys2.com'
        print(f"使用固定主机: {self.host}")
        
        # 设置referer
        self.headers.update({'Referer': f"{self.host}/"})
        
        # 应用头部到session
        self.session.headers.update(self.headers)
        
        # 简单代理处理
        try:
            if extend:
                self.proxies = json.loads(extend)
                self.session.proxies.update(self.proxies)
                print(f"使用代理: {self.proxies}")
            else:
                self.proxies = {}
        except:
            self.proxies = {}
            print("代理配置解析失败，不使用代理")
        
        print("=== 初始化完成 ===")

    def getName(self):
        return "花都影视稳定版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        '''
        首页内容获取 - 专注于稳定访问
        '''
        print("=== 开始获取首页内容 ===")
        
        try:
            # 尝试访问首页
            print(f"正在访问: {self.host}")
            response = self.session.get(self.host, timeout=10)
            print(f"响应状态码: {response.status_code}")
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"首页访问失败，状态码: {response.status_code}")
                print("尝试备用方案...")
                return self.home_fallback()
            
            # 检查响应内容
            if not response.text or len(response.text) < 100:
                print("响应内容过短，可能被拦截")
                return self.home_fallback()
            
            print(f"响应内容长度: {len(response.text)} 字符")
            
            # 解析HTML内容
            try:
                data = pq(response.text)
            except Exception as e:
                print(f"HTML解析失败: {e}")
                print("尝试使用备用解析方式...")
                try:
                    data = pq(response.content.decode('utf-8'))
                except:
                    print("备用解析也失败，返回空数据")
                    return self.home_fallback()
            
            # 初始化结果
            result = {
                'class': [],
                'list': []
            }
            
            # 提取分类信息 - 使用宽松的选择器
            print("正在提取分类信息...")
            category_elements = data('a')
            for element in category_elements.items():
                href = element.attr('href')
                text = element.text().strip()
                
                # 检查是否是分类链接
                if href and 'type' in href and text:
                    match = re.search(r'type/(\d+)\.html', href)
                    if match:
                        category_id = match.group(1)
                        result['class'].append({
                            'type_name': text,
                            'type_id': category_id
                        })
                        print(f"找到分类: {text} -> {category_id}")
            
            # 提取视频列表 - 使用宽松的选择器
            print("正在提取视频列表...")
            video_elements = data('.stui-vodlist li, .vodlist li, li')
            video_count = 0
            
            for element in video_elements.items():
                link = element('a')
                if link.length > 0:
                    href = link.attr('href')
                    
                    # 查找图片和标题
                    img = link('img')
                    if img.length > 0:
                        title = img.attr('alt') or '未知标题'
                        cover = img.attr('data-original') or img.attr('src') or ''
                        
                        # 处理封面URL
                        if cover and not cover.startswith('http'):
                            if cover.startswith('//'):
                                cover = 'https:' + cover
                            else:
                                cover = self.host + cover
                        
                        # 提取其他信息
                        year = element('.pic-tag-t').text() or ''
                        remarks = element('.pic-tag-b').text() or ''
                        
                        result['list'].append({
                            'vod_id': href or '',
                            'vod_name': title,
                            'vod_pic': cover,
                            'vod_year': year,
                            'vod_remarks': remarks
                        })
                        video_count += 1
            
            print(f"首页提取完成: {len(result['class'])} 个分类, {video_count} 个视频")
            return result
            
        except requests.exceptions.Timeout:
            print("首页访问超时")
            return self.home_fallback()
        except requests.exceptions.ConnectionError:
            print("首页连接错误")
            return self.home_fallback()
        except Exception as e:
            print(f"首页访问异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return self.home_fallback()

    def home_fallback(self):
        '''
        首页备用方案 - 返回静态数据
        '''
        print("使用首页备用方案")
        
        # 返回一些静态的分类和数据
        return {
            'class': [
                {'type_name': '有码', 'type_id': '1'},
                {'type_name': '无码', 'type_id': '2'},
                {'type_name': '国产', 'type_id': '3'},
                {'type_name': '欧美', 'type_id': '4'},
                {'type_name': '动漫', 'type_id': '5'}
            ],
            'list': [
                {
                    'vod_id': '/voddetail/19702.html',
                    'vod_name': '示例视频1',
                    'vod_pic': '',
                    'vod_year': '2025',
                    'vod_remarks': '示例'
                },
                {
                    'vod_id': '/voddetail/19703.html', 
                    'vod_name': '示例视频2',
                    'vod_pic': '',
                    'vod_year': '2025',
                    'vod_remarks': '示例'
                }
            ]
        }

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        '''
        分类内容 - 简化版本
        '''
        try:
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            print(f"访问分类页: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}
            
            data = pq(response.text)
            videos = []
            
            video_elements = data('.stui-vodlist li, .vodlist li, li')
            for element in video_elements.items():
                link = element('a')
                if link.length > 0:
                    href = link.attr('href')
                    img = link('img')
                    if img.length > 0:
                        title = img.attr('alt') or '未知'
                        cover = img.attr('data-original') or img.attr('src') or ''
                        
                        if cover and not cover.startswith('http'):
                            if cover.startswith('//'):
                                cover = 'https:' + cover
                            else:
                                cover = self.host + cover
                        
                        videos.append({
                            'vod_id': href or '',
                            'vod_name': title,
                            'vod_pic': cover,
                            'vod_year': element('.pic-tag-t').text() or '',
                            'vod_remarks': element('.pic-tag-b').text() or ''
                        })
            
            return {
                'list': videos,
                'page': pg,
                'pagecount': 9999,
                'limit': 90,
                'total': 999999
            }
            
        except Exception as e:
            print(f"分类页异常: {e}")
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        '''
        详情页 - 简化版本
        '''
        try:
            url = f"{self.host}{ids[0]}"
            print(f"访问详情页: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': []}
            
            data = pq(response.text)
            
            # 获取基本信息
            title_elem = data('.title, h1')
            title = title_elem.text() if title_elem.length > 0 else '未知'
            
            # 获取封面
            img_elem = data('img')
            cover = ''
            for img in img_elements.items():
                src = img.attr('data-original') or img.attr('src')
                if src and not cover:
                    cover = src
                    if not cover.startswith('http'):
                        if cover.startswith('//'):
                            cover = 'https:' + cover
                        else:
                            cover = self.host + cover
                    break
            
            # 获取播放链接
            play_links = []
            play_list = data('.stui-content__playlist a, .playlist a')
            for i, link in enumerate(play_list.items()):
                href = link.attr('href')
                if href:
                    play_links.append(f"第{i+1}集${href}")
            
            if not play_links:
                play_links = [f"第1集${ids[0]}"]
            
            vod = {
                'vod_id': ids[0],
                'vod_name': title,
                'vod_pic': cover,
                'vod_play_from': '花都影视',
                'vod_play_url': "#".join(play_links)
            }
            
            return {'list': [vod]}
            
        except Exception as e:
            print(f"详情页异常: {e}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        '''
        搜索功能 - 简化版本
        '''
        try:
            import urllib.parse
            encoded_key = urllib.parse.quote(key)
            url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            print(f"搜索: {key} -> {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': [], 'page': pg}
            
            data = pq(response.text)
            videos = []
            
            video_elements = data('.stui-vodlist li, .vodlist li, li')
            for element in video_elements.items():
                link = element('a')
                if link.length > 0:
                    href = link.attr('href')
                    img = link('img')
                    if img.length > 0:
                        title = img.attr('alt') or '未知'
                        cover = img.attr('data-original') or img.attr('src') or ''
                        
                        if cover and not cover.startswith('http'):
                            if cover.startswith('//'):
                                cover = 'https:' + cover
                            else:
                                cover = self.host + cover
                        
                        videos.append({
                            'vod_id': href or '',
                            'vod_name': title,
                            'vod_pic': cover,
                            'vod_year': element('.pic-tag-t').text() or '',
                            'vod_remarks': element('.pic-tag-b').text() or ''
                        })
            
            return {'list': videos, 'page': pg}
            
        except Exception as e:
            print(f"搜索异常: {e}")
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        '''
        播放内容 - 最简化版本
        '''
        play_url = f"{self.host}{id}"
        print(f"播放请求: {play_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
        }
        
        return {
            'parse': 1,  # 让播放器自行解析
            'url': play_url,
            'header': headers
        }

    def liveContent(self, url):
        return []

    def localProxy(self, param):
        '''
        本地代理 - 最简化版本
        '''
        try:
            url = param.get('url', '')
            if not url:
                return [400, "text/plain", "Missing URL"]
                
            response = requests.get(url, timeout=10)
            return [200, response.headers.get('content-type', 'text/plain'), response.content]
            
        except Exception as e:
            return [500, "text/plain", f"Proxy Error: {e}"]
