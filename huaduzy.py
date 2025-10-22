# -*- coding: utf-8 -*-
# 花都影视TVBox专用版
import json
import re
from urllib.parse import unquote
import requests
from pyquery import PyQuery as pq
import sys
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        '''
        TVBox专用初始化
        '''
        self.session = requests.Session()
        
        # TVBox兼容的头部信息
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; TV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # 简化代理处理
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
            
        # 固定主机，避免复杂逻辑
        self.host = 'https://hd.hdys2.com'
        
        # 设置referer
        self.headers.update({'Referer': f"{self.host}/"})
        
        # 应用配置
        if self.proxies:
            self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视TVBox版"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
        '''
        首页内容 - TVBox专用
        '''
        try:
            # 直接访问首页
            response = self.session.get(self.host, timeout=15)
            if response.status_code != 200:
                return self._get_static_home_data()
                
            data = pq(response.text)
            
            # 提取分类
            classes = []
            for item in data('.stui-header__menu li a').items():
                href = item.attr('href')
                if href and 'type' in href:
                    match = re.search(r'type/(\d+)\.html', href)
                    if match:
                        classes.append({
                            'type_name': item.text().strip(),
                            'type_id': match.group(1)
                        })
            
            # 提取视频列表
            videos = []
            for item in data('.stui-vodlist li').items():
                link = item('a')
                if link.length > 0:
                    href = link.attr('href')
                    img = link('img')
                    if img.length > 0:
                        title = img.attr('alt') or '未知'
                        cover = img.attr('data-original') or img.attr('src') or ''
                        
                        # 处理封面URL
                        if cover and not cover.startswith('http'):
                            if cover.startswith('//'):
                                cover = 'https:' + cover
                            else:
                                cover = self.host + cover
                        
                        videos.append({
                            'vod_id': href or '',
                            'vod_name': title,
                            'vod_pic': cover,
                            'vod_year': item('.pic-tag-t').text() or '',
                            'vod_remarks': item('.pic-tag-b').text() or ''
                        })
            
            return {
                'class': classes,
                'list': videos
            }
            
        except Exception as e:
            return self._get_static_home_data()

    def _get_static_home_data(self):
        '''备用首页数据'''
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
                    'vod_name': 'MIDV-770 高清超特写秘密角度绝顶高潮-石川堇',
                    'vod_pic': '',
                    'vod_year': '2025',
                    'vod_remarks': '160分钟'
                }
            ]
        }

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        '''
        分类内容
        '''
        try:
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}
                
            data = pq(response.text)
            videos = []
            
            for item in data('.stui-vodlist li').items():
                link = item('a')
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
            
        except:
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        '''
        详情页
        '''
        try:
            url = f"{self.host}{ids[0]}"
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {'list': []}
                
            data = pq(response.text)
            
            # 获取基本信息
            title_elem = data('.stui-content__detail .title')
            title = title_elem.text() if title_elem.length > 0 else '未知'
            
            # 获取封面
            thumb_img = data('.stui-vodlist__thumb img')
            cover = thumb_img.attr('data-original') or thumb_img.attr('src') or ''
            if cover and not cover.startswith('http'):
                if cover.startswith('//'):
                    cover = 'https:' + cover
                else:
                    cover = self.host + cover
            
            # 获取播放链接
            play_links = []
            play_list = data('.stui-content__playlist a')
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
                'vod_content': data('.stui-content__detail p.desc').text() or "",
                'vod_play_from': '花都影视',
                'vod_play_url': "#".join(play_links)
            }
            
            return {'list': [vod]}
            
        except:
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        '''
        搜索功能
        '''
        try:
            import urllib.parse
            encoded_key = urllib.parse.quote(key)
            url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {'list': [], 'page': pg}
                
            data = pq(response.text)
            videos = []
            
            for item in data('.stui-vodlist li').items():
                link = item('a')
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
                            'vod_year': item('.pic-tag-t').text() or '',
                            'vod_remarks': item('.pic-tag-b').text() or ''
                        })
            
            return {'list': videos, 'page': pg}
            
        except:
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        '''
        播放内容 - TVBox专用播放处理
        '''
        try:
            # 获取播放页面
            play_page_url = f"{self.host}{id}"
            response = self.session.get(play_page_url, timeout=15)
            data = pq(response.text)
            
            # 提取播放脚本
            scripts = data('.stui-player.col-pd script')
            if scripts.length == 0:
                # 如果找不到脚本，返回页面URL让TVBox解析
                return self._create_play_result(play_page_url, 1)
            
            script_text = scripts.eq(0).text()
            
            # 解析player_data
            player_data_match = re.search(r'player_data\s*=\s*({[^;]+});', script_text)
            if player_data_match:
                player_data = json.loads(player_data_match.group(1))
                encrypted_url = player_data.get('url', '')
                
                if encrypted_url:
                    # 双重URL解码
                    video_url = unquote(unquote(encrypted_url))
                    
                    # 验证URL格式
                    if self._is_valid_video_url(video_url):
                        # 直接返回视频URL，让TVBox处理
                        return self._create_play_result(video_url, 0)
            
            # 备用方案：返回页面URL
            return self._create_play_result(play_page_url, 1)
            
        except Exception as e:
            # 最终备用方案
            return self._create_play_result(f"{self.host}{id}", 1)

    def _create_play_result(self, url, parse_type):
        '''创建播放结果'''
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; TV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36',
            'Referer': f'{self.host}/',
        }
        
        return {
            'parse': parse_type,
            'url': url,
            'header': headers
        }

    def _is_valid_video_url(self, url):
        '''验证视频URL'''
        if not url:
            return False
            
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # 检查视频特征
        video_indicators = ['.m3u8', '.mp4', 'm3u8', 'index.m3u8', 'video', 'videos']
        return any(indicator in url.lower() for indicator in video_indicators)

    def liveContent(self, url):
        return []

    def localProxy(self, param):
        '''
        本地代理 - 简化版本
        '''
        try:
            url = param.get('url', '')
            if not url:
                return [400, "text/plain", "Missing URL"]
                
            response = requests.get(url, timeout=10)
            return [200, response.headers.get('content-type', 'text/plain'), response.content]
            
        except:
            return [500, "text/plain", "Proxy Error"]
