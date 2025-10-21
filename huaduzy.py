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
        初始化方法
        '''
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
            
        self.host = self.gethost()
        self.headers.update({'referer': f"{self.host}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视"

    def isVideoFormat(self, url):
        return True

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def homeContent(self, filter):
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
                        'type_name': k.text(),
                        'type_id': match.group(0)
                    })
                    
        result['class'] = classes
        result['list'] = self.getlist(ldata)
        return result

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
        data = self.getpq(self.session.get(url))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        url = f"{self.host}{ids[0]}"
        data = self.getpq(self.session.get(url))
        v = data('.stui-vodlist__box a')
        
        vod = {
            'vod_id': ids[0],
            'vod_name': v('img').attr('alt') or '未知',
            'vod_pic': self.proxy(v('img').attr('data-original')),
            'vod_play_from': '花都影视',
            'vod_play_url': f"第1集${v.attr('href')}" if v.attr('href') else ""
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        url = f"{self.host}/vodsearch/{key}----------{pg}---.html"
        data = self.getpq(self.session.get(url))
        return {'list': self.getlist(data('.stui-vodlist.clearfix li')), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - 简化版本，专注于获取可播放的URL
        """
        try:
            # 直接构建播放页URL
            play_page_url = f"{self.host}{id}"
            print(f"正在获取播放页: {play_page_url}")
            
            # 获取播放页面
            response = self.session.get(play_page_url)
            if response.status_code != 200:
                print(f"页面请求失败: {response.status_code}")
                return self.fallback_player_content(play_page_url)
                
            data = self.getpq(response)
            
            # 方法1: 从脚本中提取播放地址
            play_url = self.extract_from_script(data)
            if play_url:
                return {'parse': 0, 'url': play_url, 'header': self.get_player_headers()}
                
            # 方法2: 从iframe中提取
            play_url = self.extract_from_iframe(data)
            if play_url:
                return {'parse': 1, 'url': play_url, 'header': self.get_player_headers()}
                
            # 方法3: 使用备用方案
            return self.fallback_player_content(play_page_url)
            
        except Exception as e:
            print(f"播放内容获取异常: {str(e)}")
            return self.fallback_player_content(f"{self.host}{id}")

    def extract_from_script(self, data):
        """从脚本中提取播放地址"""
        try:
            scripts = data('.stui-player.col-pd script')
            if scripts.length == 0:
                return None
                
            for script in scripts.items():
                script_text = script.text()
                if 'url' in script_text and '=' in script_text:
                    # 尝试提取JSON数据
                    json_part = script_text.split('=', 1)[-1].strip()
                    if json_part.endswith(';'):
                        json_part = json_part[:-1]
                        
                    jsdata = json.loads(json_part)
                    if 'url' in jsdata and jsdata['url']:
                        url = jsdata['url']
                        print(f"从脚本提取到播放URL: {url}")
                        return url
        except Exception as e:
            print(f"脚本提取失败: {e}")
            
        return None

    def extract_from_iframe(self, data):
        """从iframe中提取播放地址"""
        try:
            iframe = data('iframe')
            if iframe.length > 0:
                src = iframe.attr('src')
                if src and src.startswith('http'):
                    print(f"从iframe提取到播放URL: {src}")
                    return src
        except Exception as e:
            print(f"iframe提取失败: {e}")
            
        return None

    def fallback_player_content(self, url):
        """备用播放方案"""
        print(f"使用备用方案，直接返回页面URL: {url}")
        return {
            'parse': 1, 
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
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        }

    def liveContent(self, url):
        return []

    def localProxy(self, param):
        """本地代理 - 简化版本"""
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
            response = self.session.get('https://a.hdys.top/assets/js/config.js')
            urls = re.findall(r'"([^"]*)"', response.text)
            if urls:
                return self.host_late(urls)
        except Exception as e:
            print(f"获取主机失败: {e}")
            
        # 备用主机
        return 'https://hd.hdys2.com'

    def getlist(self, data):
        """获取视频列表"""
        videos = []
        for i in data.items():
            videos.append({
                'vod_id': i('a').attr('href') or '',
                'vod_name': i('img').attr('alt') or '未知',
                'vod_pic': self.proxy(i('img').attr('data-original') or ''),
                'vod_year': i('.pic-tag-t').text() or '',
                'vod_remarks': i('.pic-tag-b').text() or ''
            })
        return videos

    def getpq(self, data):
        """PyQuery包装器"""
        try:
            return pq(data.text)
        except:
            try:
                return pq(data.content.decode('utf-8'))
            except:
                return pq('')

    def host_late(self, url_list):
        """主机延迟测试"""
        if not url_list:
            return 'https://hd.hdys2.com'
            
        if len(url_list) == 1:
            return url_list[0]

        results = {}
        threads = []

        def test_host(url):
            try:
                start_time = time.time()
                response = requests.head(url, timeout=3, allow_redirects=False)
                delay = (time.time() - start_time) * 1000
                results[url] = delay
            except:
                results[url] = float('inf')

        for url in url_list:
            t = threading.Thread(target=test_host, args=(url,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=5)

        best_host = min(results.items(), key=lambda x: x[1])[0]
        print(f"选择最佳主机: {best_host}")
        return best_host

    def m3Proxy(self, url):
        """M3U8代理"""
        try:
            response = requests.get(url, headers=self.get_player_headers(), timeout=10)
            if response.status_code != 200:
                return [response.status_code, "text/plain", f"Failed to fetch M3U8: {response.status_code}"]
                
            content = response.text
            lines = content.split('\n')
            
            # 简单的M3U8处理 - 不修改内容，直接返回
            return [200, "application/vnd.apple.mpegurl", content]
        except Exception as e:
            print(f"M3U8代理错误: {e}")
            return [500, "text/plain", f"M3U8 Proxy Error: {e}"]

    def tsProxy(self, url, file_type):
        """TS文件代理"""
        try:
            headers = self.get_player_headers()
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            return [200, response.headers.get('content-type', 'video/mp2t'), response.content]
        except Exception as e:
            print(f"TS代理错误: {e}")
            return [500, "text/plain", f"TS Proxy Error: {e}"]

    def proxy(self, url, file_type='img'):
        """代理URL生成"""
        if not url:
            return url
            
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
