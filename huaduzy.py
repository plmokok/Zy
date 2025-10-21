# -*- coding: utf-8 -*-
# 目标：解决网站无法访问和视频解码问题，采用更简洁可靠的逻辑。

import json
import re
import sys
import time
from base64 import b64encode, b64decode
from urllib.parse import unquote 
import requests
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider # 假设这是您的宿主环境需要的基类


class Spider(Spider):

    def init(self, extend=""):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': 'https://a.hdys.top/', # 初始Referer用于获取域名配置
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
        
        # 1. 核心步骤：获取当前可用的主机名
        self.host = self.gethost()
        
        # 2. 更新 Referer 为最终主机名
        self.headers['Referer'] = self.host + '/' 
        
        # 3. 创建一个通用的 requests Session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.proxies.update(self.proxies)

    def getName(self):
        return "花都影视（修正版）"

    # --- 核心辅助函数 ---

    def gethost(self):
        """ 简化并稳定 gethost 逻辑：只提取域名列表，返回第一个。 """
        config_url = 'https://a.hdys.top/assets/js/config.js'
        
        # 复制 headers，确保 Referer 正确
        host_headers = self.headers.copy()
        host_headers['Referer'] = 'https://a.hdys.top/' 
        
        try:
            response = requests.get(config_url, headers=host_headers, proxies=self.proxies, timeout=5)
            response.raise_for_status() 
            
            # 从 JS 代码中提取域名列表
            urls = re.findall(r'"(https?://[^"]*?)"', response.text)
            
            # 返回第一个检测到的有效域名作为主域名
            if urls:
                # 确保返回的域名不带末尾斜杠
                return urls[0].rstrip('/')
            
        except Exception as e:
            print(f"获取主机配置失败，使用默认：{str(e)}")
        
        # 如果获取失败，返回一个备用域名（假设是原始代码中的）
        return "https://huaduys.com" 

    def getpq(self, response):
        """ 安全地将响应转换为 PyQuery 对象 """
        try:
            return pq(response.text)
        except:
            return pq(response.content.decode('utf-8', errors='ignore'))

    def decode_url(self, encoded_text):
        """ 增强的解码器：Base64 解码，然后 URL 解码 """
        try:
            # 1. Base64 解码
            decoded_b64 = b64decode(encoded_text.encode('utf-8')).decode('utf-8')
            
            # 2. 尝试 URL 百分号解码
            final_url = unquote(decoded_b64)
            return final_url
        except Exception as e:
            # 如果 Base64 或 URL 解码失败，则返回原始编码文本，让外部尝试解析
            return encoded_text


    # --- 播放函数 (核心修复) ---

    def playerContent(self, flag, id, vipFlags):
        """ 视频播放页解析，专注于解码获取到的 URL """
        video_url = f"{self.host}{id}"
        
        try:
            response = self.session.get(video_url, timeout=10)
            data = self.getpq(response)
            
            # 1. 提取 player_data 变量的 JSON 字符串
            script_text = data('.stui-player.col-pd script').eq(0).text()
            match = re.search(r'player_data\s*=\s*({.*?})\s*;', script_text, re.DOTALL)
            
            if not match:
                print("未找到 player_data 变量")
                return {'parse': 1, 'url': video_url, 'header': self.headers}

            jsdata = json.loads(match.group(1))
            encoded_url = jsdata.get('url')
            
            if not encoded_url:
                print("player_data 中缺少 'url' 字段")
                return {'parse': 1, 'url': video_url, 'header': self.headers}

            # 2. 核心：使用增强解码器
            final_url = self.decode_url(encoded_url)
            
            # 3. 检查是否为代理播放
            if '.m3u8' in final_url:
                # 注意：由于我不知道您的代理函数 localProxy 是如何实现的，
                # 这里假设您会使用宿主App提供的代理功能
                return {'parse': 0, 'url': final_url, 'header': self.headers, 'proxy_type': 'm3u8'}
            
            return {'parse': 0, 'url': final_url, 'header': self.headers}

        except Exception as e:
            print(f"播放链接解析失败: {str(e)}")
            # 播放失败时，返回 p=1 (让宿主App尝试使用外部解析器)
            return {'parse': 1, 'url': video_url, 'header': self.headers}


    # --- 首页/分类/详情 (沿用标准结构) ---
    
    def homeContent(self, filter):
        # 您的原始 homeContent 逻辑，确保使用 self.session
        response = self.session.get(self.host, timeout=10)
        data = self.getpq(response)
        
        cdata = data('.stui-header__menu.type-slide li')
        ldata = data('.stui-vodlist.clearfix li')
        
        classes = []
        for k in cdata.items():
            i = k('a').attr('href')
            if i and 'type' in i:
                classes.append({
                    'type_name': k.text(),
                    'type_id': re.search(r'\d+', i).group(0)
                })
        
        # 假设 self.getlist 存在于您的基类或其它地方，这里简化
        list_items = self._parse_vod_list(ldata) 
        
        return {'class': classes, 'list': list_items}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
        response = self.session.get(url, timeout=10)
        data = self.getpq(response)
        
        list_items = self._parse_vod_list(data('.stui-vodlist.clearfix li'))

        return {
            'list': list_items,
            'page': pg,
            'pagecount': 9999,
            'limit': 90,
            'total': 999999
        }

    def detailContent(self, ids):
        url = f"{self.host}{ids[0]}"
        response = self.session.get(url, timeout=10)
        data = self.getpq(response)
        
        vod_name = data('.stui-content__detail .title').text()
        vod_pic = data('.stui-content__thumb a img').attr('data-original')
        
        vod_play_from = []
        vod_play_url = []

        # 遍历所有线路和剧集
        playlist_pannels = data('.stui-pannel-box.b.playlist .stui-pannel_bd')
        for i, pannel in enumerate(playlist_pannels.items()):
            # 找到线路名称（通常在播放列表上方的 head 中，这里简化为默认线路）
            line_name = f"线路{i+1}"
            
            episodes = []
            for item in pannel.find('li a').items():
                ep_name = item.text()
                ep_url = item.attr('href')
                episodes.append(f"{ep_name}${ep_url}")

            if episodes:
                vod_play_from.append(line_name)
                vod_play_url.append('$$$'.join(episodes))

        vod = {
            'vod_id': ids[0],
            'vod_name': vod_name,
            'vod_pic': vod_pic,
            'vod_director': '',
            'vod_actor': '',
            'vod_content': data('.stui-content__detail .detail-row:last-child').text().strip(),
            'vod_play_from': '+++'.join(vod_play_from),
            'vod_play_url': '+++'.join(vod_play_url)
        }
        return {'list': [vod]}


    # --- 内部辅助函数（模仿您的结构） ---
    def _parse_vod_list(self, data):
        """ 解析视频列表项 """
        videos=[]
        for i in data.items():
            videos.append({
                'vod_id': i('a').attr('href'),
                'vod_name': i('img').attr('alt'),
                'vod_pic': i('img').attr('data-original'),
                'vod_year': i('.pic-tag-t').text(),
                'vod_remarks': i('.pic-tag-b').text()
            })
        return videos
