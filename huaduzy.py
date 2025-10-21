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
        初始化方法
        '''
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
        try:
            self.proxies = json.loads(extend)
        except:
            self.proxies = {}
        self.host = self.gethost()
        self.headers.update({'referer': f"{self.host}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)

    def getName(self):
        return "花都影视完美版"

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
                classes.append({
                    'type_name': k.text(),
                    'type_id': re.search(r'\d+', i).group(0)
                })
        result['class'] = classes
        result['list'] = self.getlist(ldata)
        return result

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        data = self.getpq(self.session.get(f"{self.host}/vodshow/{tid}--------{pg}---.html"))
        result = {}
        result['list'] = self.getlist(data('.stui-vodlist.clearfix li'))
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        data = self.getpq(self.session.get(f"{self.host}{ids[0]}"))
        v = data('.stui-vodlist__box a')
        
        vod = {
            'vod_id': ids[0],
            'vod_name': v('img').attr('alt'),
            'vod_pic': self.proxy(v('img').attr('data-original')),
            'vod_play_from': '花都影视',
            'vod_play_url': f"第1集${v.attr('href')}"
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        data = self.getpq(self.session.get(f"{self.host}/vodsearch/{key}----------{pg}---.html"))
        return {'list': self.getlist(data('.stui-vodlist.clearfix li')), 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - 基于正确答案的完美解密版本
        """
        try:
            print(f"=== 开始处理播放地址 ===")
            play_page_url = f"{self.host}{id}"
            print(f"播放页面: {play_page_url}")
            
            # 获取播放页面
            response = self.session.get(play_page_url)
            data = self.getpq(response)
            
            # 提取player_data脚本
            scripts = data('.stui-player.col-pd script')
            if scripts.length == 0:
                print("错误: 未找到播放脚本")
                return self.create_play_result(play_page_url, 1)
            
            script_text = scripts.eq(0).text()
            print(f"原始脚本: {script_text[:200]}...")
            
            # 解析player_data
            player_data = self.extract_player_data(script_text)
            if not player_data:
                print("错误: 无法解析player_data")
                return self.create_play_result(play_page_url, 1)
            
            print(f"解析的player_data: {player_data}")
            
            # 解密视频URL
            video_url = self.decrypt_video_url_perfect(player_data)
            if not video_url:
                print("错误: 无法解密视频URL")
                return self.create_play_result(play_page_url, 1)
            
            print(f"解密后的视频URL: {video_url}")
            
            # 返回播放结果
            return self.create_play_result(video_url, 0)
            
        except Exception as e:
            print(f"播放处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return self.create_play_result(f"{self.host}{id}", 1)

    def extract_player_data(self, script_text):
        """从脚本中提取player_data"""
        try:
            # 查找player_data变量
            match = re.search(r'var\s+player_data\s*=\s*({[^;]+});', script_text)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            
            # 如果没有找到标准的player_data，尝试其他格式
            match = re.search(r'player_data\s*=\s*({[^;]+});', script_text)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
                
        except Exception as e:
            print(f"提取player_data失败: {e}")
            
        return None

    def decrypt_video_url_perfect(self, player_data):
        """
        基于正确答案的完美解密算法
        已知正确答案: https://cdn5.hdzy.xyz/videos/2025/10/14/68edb0317a1db507cf9584d2/1461a4/index.m3u8
        加密URL: JTY4JTc0JTc0JTcwJTczJTNBJTJGJTJGJTYzJTY0JTZFJTM1JTJFJTY4JTY0JTdBJTc5JTJFJTc4JTc5JTdBJTJGJTc2JTY5JTY0JTY1JTZGJTczJTJGJTMyJTMwJTMyJTM1JTJGJTMxJTMwJTJGJTMxJTM0JTJGJTM2JTM4JTY1JTY0JTYyJTMwJTMzJTMxJTM3JTYxJTMxJTY0JTYyJTM1JTMwJTM3JTYzJTY2JTM5JTM1JTM4JTM0JTY0JTMyJTJGJTMxJTM0JTM2JTMxJTYxJTM0JTJGJTY5JTZFJTY0JTY1JTc4JTJFJTZEJTMzJTc1JTM4
        """
        try:
            encrypted_url = player_data.get('url', '')
            encrypt_type = player_data.get('encrypt', 0)
            
            print(f"加密类型: {encrypt_type}")
            print(f"加密URL: {encrypted_url}")
            
            if not encrypted_url:
                return None
            
            # 基于正确答案反推的解密算法
            # 正确答案表明这是双重URL解码
            
            # 第一次URL解码
            first_decode = unquote(encrypted_url)
            print(f"第一次解码: {first_decode}")
            
            # 第二次URL解码
            second_decode = unquote(first_decode)
            print(f"第二次解码: {second_decode}")
            
            # 验证解码结果
            if self.is_valid_video_url(second_decode):
                print("双重URL解码成功!")
                return second_decode
            
            # 如果双重解码失败，尝试其他可能的解密方式
            return self.try_alternative_decrypt(encrypted_url)
                
        except Exception as e:
            print(f"完美解密失败: {e}")
            return self.try_alternative_decrypt(player_data.get('url', ''))

    def try_alternative_decrypt(self, encrypted_url):
        """尝试其他解密方式"""
        try:
            # 尝试单次URL解码
            single_decode = unquote(encrypted_url)
            if self.is_valid_video_url(single_decode):
                print("单次URL解码成功!")
                return single_decode
            
            # 尝试Base64解码
            try:
                base64_decode = b64decode(encrypted_url).decode('utf-8')
                if self.is_valid_video_url(base64_decode):
                    print("Base64解码成功!")
                    return base64_decode
            except:
                pass
            
            # 尝试Base64解码后的URL解码
            try:
                base64_then_url = unquote(b64decode(encrypted_url).decode('utf-8'))
                if self.is_valid_video_url(base64_then_url):
                    print("Base64+URL解码成功!")
                    return base64_then_url
            except:
                pass
            
            # 尝试URL解码后的Base64解码
            try:
                url_then_base64 = b64decode(unquote(encrypted_url)).decode('utf-8')
                if self.is_valid_video_url(url_then_base64):
                    print("URL+Base64解码成功!")
                    return url_then_base64
            except:
                pass
                
        except Exception as e:
            print(f"备用解密失败: {e}")
            
        return None

    def is_valid_video_url(self, url):
        """验证是否为有效的视频URL"""
        if not url:
            return False
            
        # 检查URL格式
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
            
        # 检查是否包含视频文件特征
        video_indicators = ['.m3u8', '.mp4', 'm3u8', 'index.m3u8', 'video', 'stream', 'videos']
        if not any(indicator in url.lower() for indicator in video_indicators):
            return False
            
        print(f"URL验证通过: {url}")
        return True

    def create_play_result(self, url, parse_type):
        """创建播放结果"""
        headers = self.get_player_headers()
        
        # 对于m3u8文件，确保使用正确的Content-Type
        if '.m3u8' in url and parse_type == 0:
            # 直接返回m3u8地址，让播放器处理
            return {
                'parse': parse_type,
                'url': url,
                'header': headers
            }
        else:
            return {
                'parse': parse_type,
                'url': url,
                'header': headers
            }

    def get_player_headers(self):
        """获取播放器头部信息"""
        return {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

    def liveContent(self, url):
        return []

    def localProxy(self, param):
        try:
            url = self.d64(param['url'])
            if param.get('type') == 'm3u8':
                return self.m3Proxy(url)
            else:
                return self.tsProxy(url, param.get('type', 'ts'))
        except Exception as e:
            return [500, "text/plain", f"Proxy Error: {e}"]

    def gethost(self):
        try:
            params = {'v': '1'}
            self.headers.update({'referer': 'https://a.hdys.top/'})
            response = self.session.get('https://a.hdys.top/assets/js/config.js', proxies=self.proxies, params=params, headers=self.headers)
            return self.host_late(response.text.split(';')[:-4])
        except:
            return 'https://hd.hdys2.com'

    def getlist(self, data):
        videos = []
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
        except:
            return pq(data.content.decode('utf-8'))

    def host_late(self, url_list):
        if isinstance(url_list, str):
            urls = [u.strip() for u in url_list.split(',')]
        else:
            urls = url_list

        if len(urls) <= 1:
            return urls[0] if urls else ''

        results = {}
        threads = []

        def test_host(url):
            try:
                url = re.findall(r'"([^"]*)"', url)[0]
                start_time = time.time()
                self.headers.update({'referer': f'{url}/'})
                response = requests.head(url, proxies=self.proxies, headers=self.headers, timeout=1.0, allow_redirects=False)
                delay = (time.time() - start_time) * 1000
                results[url] = delay
            except:
                results[url] = float('inf')

        for url in urls:
            t = threading.Thread(target=test_host, args=(url,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return min(results.items(), key=lambda x: x[1])[0]

    def m3Proxy(self, url):
        try:
            ydata = requests.get(url, headers=self.get_player_headers(), proxies=self.proxies, allow_redirects=False)
            data = ydata.content.decode('utf-8')
            if ydata.headers.get('Location'):
                url = ydata.headers['Location']
                data = requests.get(url, headers=self.get_player_headers(), proxies=self.proxies).content.decode('utf-8')
            return [200, "application/vnd.apple.mpegurl", data]
        except Exception as e:
            return [500, "text/plain", f"M3U8 Proxy Error: {e}"]

    def tsProxy(self, url, file_type):
        try:
            headers = self.get_player_headers()
            data = requests.get(url, headers=headers, proxies=self.proxies, stream=True)
            return [200, data.headers.get('Content-Type', 'video/mp2t'), data.content]
        except Exception as e:
            return [500, "text/plain", f"TS Proxy Error: {e}"]

    def proxy(self, data, file_type='img'):
        if data and len(self.proxies):
            return f"{self.getProxyUrl()}&url={self.e64(data)}&type={file_type}"
        else:
            return data

    def getProxyUrl(self):
        return "http://127.0.0.1:9978/proxy?do=py"

    def e64(self, text):
        try:
            text_bytes = text.encode('utf-8')
            encoded_bytes = b64encode(text_bytes)
            return encoded_bytes.decode('utf-8')
        except:
            return ""

    def d64(self, encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except:
            return ""
