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
        初始化方法 - 保持A版不变
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
        return "花都影视诊断版"

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
        播放内容获取 - 诊断版本，详细记录每个关键节点
        """
        print("=== 播放诊断开始 ===")
        
        try:
            # 关键节点0：获取播放页面
            play_url = f"{self.host}{id}"
            print(f"关键节点0 - 播放页面URL: {play_url}")
            
            response = self.session.get(play_url)
            print(f"关键节点0 - 页面响应状态: {response.status_code}")
            
            data = self.getpq(response)
            
            # 关键节点1：查找脚本
            scripts = data('.stui-player.col-pd script')
            print(f"关键节点1 - 找到脚本数量: {scripts.length}")
            
            if scripts.length == 0:
                print("关键节点1 - 错误: 未找到脚本元素")
                raise Exception("未找到播放脚本")
            
            jstr = scripts.eq(0).text()
            print(f"关键节点1 - 脚本内容预览: {jstr[:200]}...")
            
            # 关键节点2：JSON解析
            json_part = jstr.split("=", maxsplit=1)[-1].strip()
            print(f"关键节点2 - JSON部分: {json_part[:100]}...")
            
            # 清理JSON格式
            if json_part.endswith(';'):
                json_part = json_part[:-1]
            
            jsdata = json.loads(json_part)
            print(f"关键节点2 - 解析后的JSON: {jsdata}")
            
            # 关键节点3：URL提取
            if 'url' not in jsdata:
                print(f"关键节点3 - 错误: JSON中未找到url字段，可用字段: {list(jsdata.keys())}")
                raise Exception("JSON中缺少url字段")
            
            url = jsdata['url']
            print(f"关键节点3 - 提取的URL: {url}")
            
            # 关键节点4：URL处理
            if not url.startswith('http'):
                if url.startswith('//'):
                    url = 'https:' + url
                    print(f"关键节点4 - 修复协议相对URL: {url}")
                else:
                    url = self.host + url
                    print(f"关键节点4 - 修复相对URL: {url}")
            
            p = 0
            
            # 关键节点5：m3u8检测和代理
            if '.m3u8' in url:
                print("关键节点5 - 检测到M3U8格式，启用代理")
                original_url = url
                url = self.proxy(url, 'm3u8')
                print(f"关键节点5 - 代理前URL: {original_url}")
                print(f"关键节点5 - 代理后URL: {url}")
            else:
                print(f"关键节点5 - 非M3U8格式，直接使用: {url}")
            
            print(f"=== 播放诊断成功 ===")
            print(f"最终播放URL: {url}")
            print(f"解析模式: {p}")
            
            return {'parse': p, 'url': url, 'header': self.get_player_headers()}
            
        except Exception as e:
            print(f"=== 播放诊断失败 ===")
            print(f"错误信息: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 关键节点6：备用方案
            print("使用备用方案")
            backup_url = f"{self.host}{id}"
            print(f"备用URL: {backup_url}")
            
            return {'parse': 1, 'url': backup_url, 'header': self.get_player_headers()}

    def get_player_headers(self):
        """获取播放器头部信息 - 诊断版本"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        print(f"播放器头部: {headers}")
        return headers

    def liveContent(self, url):
        return []

    def localProxy(self, param):
        try:
            url = self.d64(param['url'])
            print(f"代理请求 - URL: {url}, 类型: {param.get('type')}")
            
            if param.get('type') == 'm3u8':
                return self.m3Proxy(url)
            else:
                return self.tsProxy(url, param.get('type', 'ts'))
        except Exception as e:
            print(f"代理错误: {e}")
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
            print(f"M3U8代理 - 请求URL: {url}")
            ydata = requests.get(url, headers=self.get_player_headers(), proxies=self.proxies, allow_redirects=False)
            print(f"M3U8代理 - 响应状态: {ydata.status_code}")
            
            if ydata.headers.get('Location'):
                print(f"M3U8代理 - 重定向到: {ydata.headers['Location']}")
                url = ydata.headers['Location']
                ydata = requests.get(url, headers=self.get_player_headers(), proxies=self.proxies)
            
            data = ydata.content.decode('utf-8')
            print(f"M3U8代理 - 内容长度: {len(data)}")
            print(f"M3U8代理 - 内容预览: {data[:200]}...")
            
            return [200, "application/vnd.apple.mpegurl", data]
        except Exception as e:
            print(f"M3U8代理错误: {e}")
            return [500, "text/plain", f"M3U8 Proxy Error: {e}"]

    def tsProxy(self, url, file_type):
        try:
            print(f"TS代理 - 请求URL: {url}, 类型: {file_type}")
            headers = self.get_player_headers()
            data = requests.get(url, headers=headers, proxies=self.proxies, stream=True)
            print(f"TS代理 - 响应状态: {data.status_code}")
            return [200, data.headers.get('Content-Type', 'video/mp2t'), data.content]
        except Exception as e:
            print(f"TS代理错误: {e}")
            return [500, "text/plain", f"TS Proxy Error: {e}"]

    def proxy(self, data, file_type='img'):
        if data and len(self.proxies):
            proxy_url = f"{self.getProxyUrl()}&url={self.e64(data)}&type={file_type}"
            print(f"代理URL生成 - 原始: {data}")
            print(f"代理URL生成 - 代理: {proxy_url}")
            return proxy_url
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
