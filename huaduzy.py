# -*- coding: utf-8 -*-
# by @嗷呜
import json
import re
import sys
from base64 import b64encode, b64decode
import requests
from pyquery import PyQuery as pq
sys.path.append('..')
from base.spider import Spider


class Spider(Spider):

    def init(self, extend=""):
        '''
        初始化方法 - 简化版本
        '''
        self.session = requests.Session()
        # 简化头部信息
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
            
        # 使用固定的主机地址，避免自动获取的复杂性
        self.host = 'https://hd.hdys2.com'
        print(f"使用固定主机: {self.host}")
        
        self.headers.update({'referer': f"{self.host}/"})
        self.session.headers.update(self.headers)
        
        # 仅在需要时设置代理
        if self.proxies:
            self.session.proxies.update(self.proxies)

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
        首页内容 - 简化版本
        '''
        try:
            print(f"正在访问首页: {self.host}")
            response = self.session.get(self.host, timeout=10)
            print(f"首页响应状态: {response.status_code}")
            
            if response.status_code != 200:
                print(f"首页访问失败: {response.status_code}")
                return {'class': [], 'list': []}
                
            data = pq(response.text)
            
            # 提取分类
            classes = []
            cdata = data('.stui-header__menu.type-slide li a')
            for item in cdata.items():
                href = item.attr('href')
                if href and 'type' in href:
                    match = re.search(r'\d+', href)
                    if match:
                        classes.append({
                            'type_name': item.text().strip(),
                            'type_id': match.group(0)
                        })
            
            # 提取视频列表
            videos = []
            ldata = data('.stui-vodlist.clearfix li')
            for item in ldata.items():
                vod_id = item('a').attr('href') or ''
                vod_name = item('img').attr('alt') or '未知'
                vod_pic = item('img').attr('data-original') or item('img').attr('src') or ''
                
                # 处理图片URL
                if vod_pic and not vod_pic.startswith('http'):
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
                    else:
                        vod_pic = self.host + vod_pic
                
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': item('.pic-tag-t').text() or '',
                    'vod_remarks': item('.pic-tag-b').text() or ''
                })
            
            result = {
                'class': classes,
                'list': videos
            }
            
            print(f"首页加载成功: {len(classes)}个分类, {len(videos)}个视频")
            return result
            
        except Exception as e:
            print(f"首页加载异常: {str(e)}")
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        '''
        分类内容 - 简化版本
        '''
        try:
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            print(f"正在访问分类页: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"分类页访问失败: {response.status_code}")
                return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}
                
            data = pq(response.text)
            
            # 提取视频列表
            videos = []
            ldata = data('.stui-vodlist.clearfix li')
            for item in ldata.items():
                vod_id = item('a').attr('href') or ''
                vod_name = item('img').attr('alt') or '未知'
                vod_pic = item('img').attr('data-original') or item('img').attr('src') or ''
                
                # 处理图片URL
                if vod_pic and not vod_pic.startswith('http'):
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
                    else:
                        vod_pic = self.host + vod_pic
                
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': item('.pic-tag-t').text() or '',
                    'vod_remarks': item('.pic-tag-b').text() or ''
                })
            
            result = {
                'list': videos,
                'page': pg,
                'pagecount': 9999,
                'limit': 90,
                'total': 999999
            }
            
            print(f"分类页加载成功: {len(videos)}个视频")
            return result
            
        except Exception as e:
            print(f"分类页加载异常: {str(e)}")
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        '''
        详情页 - 简化版本
        '''
        try:
            url = f"{self.host}{ids[0]}"
            print(f"正在访问详情页: {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"详情页访问失败: {response.status_code}")
                return {'list': []}
                
            data = pq(response.text)
            
            # 获取基本信息
            title_elem = data('.stui-content__detail .title')
            vod_name = title_elem.text() or '未知'
            
            # 获取封面图
            thumb_img = data('.stui-vodlist__thumb img')
            vod_pic = thumb_img.attr('data-original') or thumb_img.attr('src') or ''
            if vod_pic and not vod_pic.startswith('http'):
                if vod_pic.startswith('//'):
                    vod_pic = 'https:' + vod_pic
                else:
                    vod_pic = self.host + vod_pic
            
            # 获取播放链接
            play_links = []
            play_list = data('.stui-content__playlist a')
            for i, link in enumerate(play_list.items()):
                href = link.attr('href')
                if href:
                    play_links.append(f"第{i+1}集${href}")
            
            # 如果没有找到播放链接，使用详情页URL作为播放页
            if not play_links:
                play_links = [f"第1集${ids[0]}"]
            
            play_url = "#".join(play_links)
            
            vod = {
                'vod_id': ids[0],
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_content': data('.stui-content__detail p.desc').text() or "",
                'vod_play_from': '花都影视',
                'vod_play_url': play_url
            }
            
            print(f"详情页加载成功: {vod_name}")
            return {'list': [vod]}
            
        except Exception as e:
            print(f"详情页加载异常: {str(e)}")
            return {'list': []}

    def searchContent(self, key, quick, pg="1"):
        '''
        搜索功能 - 简化版本
        '''
        try:
            # 对关键词进行URL编码
            import urllib.parse
            encoded_key = urllib.parse.quote(key)
            url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            print(f"正在搜索: {key} -> {url}")
            
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"搜索页访问失败: {response.status_code}")
                return {'list': [], 'page': pg}
                
            data = pq(response.text)
            
            # 提取搜索结果
            videos = []
            ldata = data('.stui-vodlist.clearfix li')
            for item in ldata.items():
                vod_id = item('a').attr('href') or ''
                vod_name = item('img').attr('alt') or '未知'
                vod_pic = item('img').attr('data-original') or item('img').attr('src') or ''
                
                # 处理图片URL
                if vod_pic and not vod_pic.startswith('http'):
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
                    else:
                        vod_pic = self.host + vod_pic
                
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_year': item('.pic-tag-t').text() or '',
                    'vod_remarks': item('.pic-tag-b').text() or ''
                })
            
            result = {
                'list': videos,
                'page': pg
            }
            
            print(f"搜索成功: 找到{len(videos)}个结果")
            return result
            
        except Exception as e:
            print(f"搜索异常: {str(e)}")
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        '''
        播放内容 - 最简化版本，直接返回页面URL让播放器解析
        '''
        play_url = f"{self.host}{id}"
        print(f"播放请求: {play_url}")
        
        # 简单头部信息
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host,
        }
        
        # 直接返回页面URL，让播放器自行解析
        return {
            'parse': 1,  # 1表示需要解析
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
                
            # 直接转发请求
            response = requests.get(url, timeout=10)
            return [200, response.headers.get('content-type', 'text/plain'), response.content]
            
        except Exception as e:
            print(f"代理错误: {e}")
            return [500, "text/plain", f"Proxy Error: {e}"]

    # 移除复杂的gethost方法，使用固定主机
    # 移除复杂的播放地址提取方法
    # 移除Base64编码解码方法（除非代理需要）
