# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
import threading
import time
from base64 import b64encode, b64decode
from urllib.parse import urlparse
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        '''
        最简化的初始化，专注于基础访问
        '''
        self.session = requests.Session()
        
        # 使用最基础的浏览器头部
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        
        # 简化代理处理
        try:
            self.proxies = json.loads(extend) if extend else {}
        except:
            self.proxies = {}
            
        # 使用固定主机，避免复杂的自动获取
        self.host = 'https://hd.hdys2.com'
        
        # 设置基础referer
        self.headers.update({'referer': f"{self.host}/"})
        
        # 应用配置到session
        if self.proxies:
            self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

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
        首页内容 - 最简化版本
        '''
        try:
            print(f"尝试访问首页: {self.host}")
            response = self.session.get(self.host, timeout=10)
            print(f"首页响应状态: {response.status_code}")
            
            if response.status_code != 200:
                print(f"首页访问失败，状态码: {response.status_code}")
                # 尝试不带https
                if self.host.startswith('https://'):
                    http_host = self.host.replace('https://', 'http://')
                    print(f"尝试HTTP访问: {http_host}")
                    response = self.session.get(http_host, timeout=10)
                    if response.status_code == 200:
                        self.host = http_host
                        print(f"切换到HTTP主机: {self.host}")
            
            if response.status_code != 200:
                return {'class': [], 'list': []}
                
            # 使用更宽松的HTML解析
            try:
                data = pq(response.text)
            except:
                data = pq(response.content)
            
            result = {'class': [], 'list': []}
            
            # 提取分类 - 使用更宽松的选择器
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
            
            # 提取视频列表 - 使用更宽松的选择器
            ldata = data('li')
            for item in ldata.items():
                link = item('a')
                if link.length > 0:
                    href = link.attr('href')
                    img = link('img')
                    if img.length > 0:
                        vod_name = img.attr('alt') or '未知'
                        vod_pic = img.attr('data-original') or img.attr('src') or ''
                        
                        # 处理图片URL
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
            
            print(f"首页加载成功: {len(result['class'])}个分类, {len(result['list'])}个视频")
            return result
            
        except Exception as e:
            print(f"首页加载异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        '''
        分类内容 - 最简化版本
        '''
        try:
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            print(f"访问分类页: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}
                
            try:
                data = pq(response.text)
            except:
                data = pq(response.content)
            
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
            print(f"分类页异常: {str(e)}")
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        '''
        详情页 - 最简化版本
        '''
        try:
            url = f"{self.host}{ids[0]}"
            print(f"访问详情页: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': []}
                
            try:
                data = pq(response.text)
            except:
                data = pq(response.content)
            
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
                play_links = [f"第1集{ids[0]}"]
            
            vod = {
                'vod_id': ids[0],
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_play_from': '花都影视',
                'vod_play_url': "#".join(play_links)
            }
            
            return {'list': [vod]}
            
        except Exception as e:
            print(f"详情页异常: {str(e)}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        '''
        搜索功能 - 最简化版本
        '''
        try:
            import urllib.parse
            encoded_key = urllib.parse.quote(key)
            url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            print(f"搜索: {key} -> {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return {'list': [], 'page': pg}
                
            try:
                data = pq(response.text)
            except:
                data = pq(response.content)
            
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
            print(f"搜索异常: {str(e)}")
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        '''
        播放内容 - 最简化版本，直接返回页面URL
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
