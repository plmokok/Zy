# -*- coding: utf-8 -*-
# 目标：解决 TVBox 环境下的兼容性问题，采用最保守的初始化策略。

import json
import re
import sys
from base64 import b64decode
from urllib.parse import unquote 
import requests
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider 


class Spider(Spider):

    # --- 核心配置 ---
    FIXED_HOST = "https://hd8.huaduzy.vip" 
    COMMON_USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    
    # 保持 self.session 和 self.headers 的初始化，但只在 TVBox 期待时使用
    session = None
    headers = {}
    proxies = {}
    pheader = {}


    def init(self, extend=""):
        """ TVBox 兼容性优先：只设置通用参数，不触碰 session 状态。 """
        
        # 1. 初始化头部
        self.headers = {
            'User-Agent': self.COMMON_USER_AGENT,
            'Referer': self.FIXED_HOST + '/', 
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': '*/*',
        }
        
        # 2. 处理代理配置
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
        
        # 3. 播放器专用的 header
        self.pheader = self.headers.copy()
        self.pheader.update({
            'Referer': self.FIXED_HOST,
            'Origin': self.FIXED_HOST
        })
        
        # 4. **关键：不在这里创建 requests.Session()**，避免覆盖或冲突
        # 如果 TVBox 在基类中创建了 self.session，我们不应该在这里重新创建它。
        # 如果它没有创建，我们将在 getpq 中使用原始 requests 库。


    def getName(self):
        return "花都影视（TVBox 兼容）"

    # --- 辅助函数：使用原始 requests ---

    def getpq(self, url, method='GET', data=None):
        """ 使用原始 requests.get/post 发送请求 """
        # 使用独立的 headers 副本，确保没有副作用
        request_headers = self.headers.copy()
        
        try:
            # 强制使用 requests.get，绕开任何可能被污染的 self.session
            if method == 'GET':
                response = requests.get(
                    url, 
                    headers=request_headers, 
                    proxies=self.proxies, 
                    timeout=15, 
                    verify=False, # **TVBox兼容：可能需要禁用SSL验证**
                    allow_redirects=True
                )
            else:
                response = requests.post(
                    url, 
                    headers=request_headers, 
                    proxies=self.proxies, 
                    data=data, 
                    timeout=15, 
                    verify=False, # **TVBox兼容：可能需要禁用SSL验证**
                    allow_redirects=True
                )
                
            response.raise_for_status() 
            
            # 安全解析内容
            encoding = response.apparent_encoding if response.apparent_encoding != 'ascii' else 'utf-8'
            return pq(response.content.decode(encoding, errors='ignore'))
            
        except requests.exceptions.RequestException as e:
            print(f"请求 {url} 失败: {str(e)}")
            return pq('<html></html>')

    def decode_url(self, encoded_text):
        """ 增强的解码器：Base64 解码，然后 URL 解码 """
        try:
            decoded_b64 = b64decode(encoded_text.encode('utf-8')).decode('utf-8')
            final_url = unquote(decoded_b64)
            return final_url
        except Exception:
            return encoded_text

    # --- 功能函数（保持简洁，使用 getpq） ---
    
    def homeContent(self, filter):
        data = self.getpq(self.FIXED_HOST)
        
        if not data('body'): 
            return {'class': [], 'list': []}

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
        
        return {'class': classes, 'list': self._parse_vod_list(ldata)}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.FIXED_HOST}/vodshow/{tid}--------{pg}---.html"
        data = self.getpq(url)
        
        list_items = self._parse_vod_list(data('.stui-vodlist.clearfix li'))

        return {
            'list': list_items,
            'page': pg,
            'pagecount': 9999,
            'limit': 90,
            'total': 999999
        }

    def detailContent(self, ids):
        url = f"{self.FIXED_HOST}{ids[0]}"
        data = self.getpq(url)
        
        vod_name = data('.stui-content__detail .title').text()
        vod_pic = data('.stui-content__thumb a img').attr('data-original')
        
        vod_play_from = []
        vod_play_url = []

        playlist_pannels = data('.stui-pannel-box.b.playlist .stui-pannel_bd')
        for i, pannel in enumerate(playlist_pannels.items()):
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
            'vod_director': data('.detail-row:nth-child(2) .detail-content:nth-child(2)').text().strip(),
            'vod_actor': data('.detail-row:nth-child(3) .detail-content:nth-child(2)').text().strip(),
            'vod_content': data('.stui-content__detail .detail-row:last-child').text().strip(),
            'vod_play_from': '+++'.join(vod_play_from),
            'vod_play_url': '+++'.join(vod_play_url)
        }
        return {'list': [vod]}

    def playerContent(self, flag, id, vipFlags):
        video_url = f"{self.FIXED_HOST}{id}"
        
        try:
            data = self.getpq(video_url)
            
            script_text = data('.stui-player.col-pd script').eq(0).text()
            match = re.search(r'player_data\s*=\s*({.*?})\s*;', script_text, re.DOTALL)
            
            if not match:
                return {'parse': 1, 'url': video_url, 'header': self.pheader}

            jsdata = json.loads(match.group(1))
            encoded_url = jsdata.get('url')
            
            if not encoded_url:
                return {'parse': 1, 'url': video_url, 'header': self.pheader}

            final_url = self.decode_url(encoded_url)
            
            return {'parse': 0, 'url': final_url, 'header': self.pheader}

        except Exception as e:
            print(f"播放链接解析失败: {str(e)}")
            return {'parse': 1, 'url': video_url, 'header': self.pheader}


    # --- 内部辅助函数（保持不变） ---
    
    def _parse_vod_list(self, data):
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

    # --- 其他兼容函数（保持不变） ---

    def searchContent(self, key, quick, pg="1"):
        url = f"{self.FIXED_HOST}/vodsearch/{key}----------{pg}---.html"
        data = self.getpq(url)
        return {'list': self._parse_vod_list(data('.stui-vodlist.clearfix li')), 'page': pg}

    def homeVideoContent(self):
        return {'list':''}

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        return [500, "text/plain", "Local proxy not implemented"]

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass
