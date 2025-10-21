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
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Android"',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
            'dnt': '1',
            'sec-ch-ua-mobile': '?1',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-dest': 'script',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=2',
        }
        try:self.proxies = json.loads(extend)
        except:self.proxies = {}
        
        # 步骤1：获取主机名
        self.hsot=self.gethost() 
        
        # 步骤2：更新会话的默认 Referer 和代理
        self.headers.update({'referer': f"{self.hsot}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        pass

    def getName(self):
        return "花都影视" 

    # ... 其他基本函数保持不变 ...

    def gethost(self):
        params = {
            'v': '1',
        }
        
        # 复制一份 headers 用于这次请求，避免修改全局 self.headers
        host_headers = self.headers.copy()
        host_headers.update({'referer': 'https://a.hdys.top/'}) 
        
        try:
            # 使用 requests 库而非 session，确保请求独立性
            response = requests.get('https://a.hdys.top/assets/js/config.js',
                                    proxies=self.proxies, 
                                    params=params, 
                                    headers=host_headers,
                                    timeout=5) # 增加超时时间，避免卡死
            response.raise_for_status() # 如果状态码不是 200，抛出异常

            # 传递原始 headers，让 host_late 使用
            return self.host_late(response.text.split(';')[:-4], self.proxies, self.headers.copy()) 

        except Exception as e:
            print(f"获取主机配置失败: {str(e)}")
            # 失败时，返回一个备用域名（如果已知）或空字符串
            return '' # 网站连不上的根本原因就在这里，如果 gethost 失败，init 就失败了

    def host_late(self, url_list, proxies, base_headers):
        if isinstance(url_list, str):
            urls = [u.strip() for u in url_list.split(',')]
        else:
            urls = url_list

        if len(urls) <= 1:
            return urls[0] if urls else ''

        results = {}
        
        # 移除多线程，改为串行，消除竞态条件风险
        for url_item in urls:
            try:
                # 提取实际的URL
                url=re.findall(r'"([^"]*)"', url_item)[0]
                
                # 为每次请求创建独立的 headers 副本
                test_headers = base_headers.copy()
                test_headers.update({'referer': f'{url}/'}) 
                
                start_time = time.time()
                # 使用 requests.head 进行快速测试
                response = requests.head(url,
                                         proxies=proxies,
                                         headers=test_headers,
                                         timeout=1.0, 
                                         allow_redirects=False)
                delay = (time.time() - start_time) * 1000
                results[url] = delay
            except Exception:
                results[url] = float('inf')

        # 确保 results 不为空
        if not results:
             return urls[0] if urls else ''

        # 返回延迟最小的 host
        best_host = min(results.items(), key=lambda x: x[1])[0]
        return best_host


    # --- 以下是播放相关函数，保持上次修正后的逻辑 ---

    def detailContent(self, ids):
        # 修复：确保 detailContent 返回正确的播放列表格式
        data=self.getpq(self.session.get(f"{self.hsot}{ids[0]}"))
        
        # 提取基础信息
        vod_name = data('.stui-content__detail .title').text()
        vod_pic = data('.stui-content__thumb a img').attr('data-original')
        vod_director = data('.detail-row:nth-child(2) .detail-content:nth-child(2) a').text()
        vod_actor = data('.detail-row:nth-child(3) .detail-content:nth-child(2) a').text()
        vod_content = data('.detail-row:nth-child(5) .detail-content:nth-child(2)').text().strip()

        vod_play_from = []
        vod_play_url = []

        # 解析播放线路和剧集列表
        play_area = data('.stui-player__detail:eq(0)')
        line_names = play_area.find('.stui-vodlist__head h3')
        play_lists = play_area.find('.stui-content__list') # 通常是 ul 列表

        # 遍历所有线路
        for i, line_name_item in enumerate(line_names.items()):
            line_flag = line_name_item.text()
            vod_play_from.append(line_flag)
            
            episodes = []
            current_list = play_lists.eq(i).find('li a') 
            
            for item in current_list.items():
                ep_name = item.text()
                ep_url = item.attr('href')
                episodes.append(f"{ep_name}${ep_url}")

            vod_play_url.append('$$$'.join(episodes))

        vod = {
            'vod_id': ids[0],
            'vod_name': vod_name,
            'vod_pic': self.proxy(vod_pic),
            'vod_director': vod_director,
            'vod_actor': vod_actor,
            'vod_content': vod_content,
            'vod_play_from': '+++'.join(vod_play_from),
            'vod_play_url': '+++'.join(vod_play_url)
        }
        return {'list':[vod]}

    def playerContent(self, flag, id, vipFlags):
        # 修复：对 jsdata['url'] 进行解码
        try:
            data=self.getpq(self.session.get(f"{self.hsot}{id}"))
            jstr=data('.stui-player.col-pd script').eq(0).text()
            jsdata=json.loads(jstr.split("=", maxsplit=1)[-1].strip())
            
            encoded_url = jsdata['url']
            
            # 尝试 Base64 解码
            url = self.d64(encoded_url) 
            
            # 检查是否需要 URL 百分号解码
            if '%' in url:
                url = unquote(url)

            p = 0
            if '.m3u8' in url:
                url=self.proxy(url,'m3u8')
                
        except Exception as e:
            print(f"播放链接解析失败: {str(e)}")
            p,url=1,f"{self.hsot}{id}"
            
        return  {'parse': p, 'url': url, 'header': self.pheader}

    # ... 其他辅助函数（homeContent, categoryContent, searchContent, m3Proxy, tsProxy, proxy, e64, d64）保持不变 ...
    # 为了完整性，我将所有函数都包含在下面：

    pheader={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Android"',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="130", "Google Chrome";v="130"',
        'dnt': '1',
        'sec-ch-ua-mobile': '?1',
        'origin': 'https://jx.8852.top',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'zh-CN,zh;q=0.9',
        'priority': 'u=1, i',
    }

    def homeContent(self, filter):
        data=self.getpq(self.session.get(self.hsot))
        cdata=data('.stui-header__menu.type-slide li')
        ldata=data('.stui-vodlist.clearfix li')
        result = {}
        classes = []
        for k in cdata.items():
            i=k('a').attr('href')
            if i and 'type' in i:
                classes.append({
                    'type_name': k.text(),
                    'type_id': re.search(r'\d+', i).group(0)
                })
        result['class'] = classes
        result['list'] = self.getlist(ldata)
        return result

    def homeVideoContent(self):
        return {'list':''}

    def categoryContent(self, tid, pg, filter, extend):
        data=self.getpq(self.session.get(f"{self.hsot}/vodshow/{tid}--------{pg}---.html"))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def searchContent(self, key, quick, pg="1"):
        data=self.getpq(self.session.get(f"{self.hsot}/vodsearch/{key}----------{pg}---.html"))
        return {'list':self.getlist(data('.stui-vodlist.clearfix li')),'page':pg}


    def liveContent(self, url):
        pass

    def localProxy(self, param):
        url = self.d64(param['url'])
        if param.get('type') == 'm3u8':
            return self.m3Proxy(url)
        else:
            return self.tsProxy(url,param['type'])


    def getlist(self,data):
        videos=[]
        for i in data.items():
            videos.append({
                'vod_id': i('a').attr('href'),
                'vod_name': i('img').attr('alt'),
                'vod_pic': self.proxy(i('img').attr('data-original')),
                'vod_year': i('.pic-tag-t').text(),
                'vod_remarks': i('.pic-tag-b').text()
            })
        return videos

    def getpq(self, data):
        try:
            return pq(data.text)
        except Exception:
            return pq(data.content.decode('utf-8', errors='ignore')) # 容错性更强的解码

    def m3Proxy(self, url):
        ydata = requests.get(url, headers=self.pheader, proxies=self.proxies, allow_redirects=False)
        data = ydata.content.decode('utf-8')
        if ydata.headers.get('Location'):
            url = ydata.headers['Location']
            data = requests.get(url, headers=self.pheader, proxies=self.proxies).content.decode('utf-8')
        lines = data.strip().split('\n')
        last_r = url[:url.rfind('/')]
        parsed_url = urlparse(url)
        durl = parsed_url.scheme + "://" + parsed_url.netloc
        for index, string in enumerate(lines):
            if '#EXT' not in string:
                if 'http' not in string:
                    domain = durl if string.startswith('/') else last_r
                    string = domain + ('' if string.startswith('/') else '/') + string
                lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
        data = '\n'.join(lines)
        return [200, "application/vnd.apple.mpegurl", data]

    def tsProxy(self, url,type):
        h=self.pheader.copy()
        if type=='img':h=self.headers.copy()
        data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
        return [200, data.headers['Content-Type'], data.content]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):return f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
        else:return data

    def e64(self, text):
        try:
            text_bytes = text.encode('utf-8')
            encoded_bytes = b64encode(text_bytes)
            return encoded_bytes.decode('utf-8')
        except Exception as e:
            # print(f"Base64编码错误: {str(e)}")
            return ""

    def d64(self,encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            # print(f"Base64解码错误: {str(e)}")
            return ""
