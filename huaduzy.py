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
        如果一直访问不了，手动访问导航页:https://a.hdys.top，替换：
        self.host = 'https://xxx.xxx.xxx'
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
        try:self.proxies = json.loads(extend)
        except:self.proxies = {}
        self.hsot=self.gethost()
        # self.hsot='https://hd.hdys2.com'
        self.headers.update({'referer': f"{self.hsot}/"})
        self.session.proxies.update(self.proxies)
        self.session.headers.update(self.headers)
        pass

    def getName(self):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

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

    def detailContent(self, ids):
        data=self.getpq(self.session.get(f"{self.hsot}{ids[0]}"))
        v=data('.stui-vodlist__box a')
        vod = {
            'vod_play_from': '花都影视',
            'vod_play_url': f"{v('img').attr('alt')}${v.attr('href')}"
        }
        return {'list':[vod]}

    def searchContent(self, key, quick, pg="1"):
        data=self.getpq(self.session.get(f"{self.hsot}/vodsearch/{key}----------{pg}---.html"))
        return {'list':self.getlist(data('.stui-vodlist.clearfix li')),'page':pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容获取 - 终极调试版本
        """
        print("=== 播放调试开始 ===")
        
        try:
            # 获取播放页面
            play_page_url = f"{self.hsot}{id}"
            print(f"播放页面URL: {play_page_url}")
            
            response = self.session.get(play_page_url)
            data = self.getpq(response)
            
            # 提取脚本
            scripts = data('.stui-player.col-pd script')
            print(f"找到脚本数量: {scripts.length}")
            
            if scripts.length == 0:
                print("错误: 未找到播放脚本")
                raise Exception("未找到播放脚本")
            
            jstr = scripts.eq(0).text()
            print(f"原始脚本内容: {jstr[:200]}...")
            
            # 解析JSON
            json_part = jstr.split("=", maxsplit=1)[-1].strip()
            print(f"JSON部分: {json_part[:100]}...")
            
            jsdata = json.loads(json_part)
            print(f"解析后的JSON: {jsdata}")
            
            # 提取加密URL
            encrypted_url = jsdata['url']
            print(f"加密URL: {encrypted_url}")
            
            # 双重URL解码
            first_decode = unquote(encrypted_url)
            print(f"第一次解码: {first_decode}")
            
            video_url = unquote(first_decode)
            print(f"第二次解码(最终URL): {video_url}")
            
            # 验证URL
            if not video_url.startswith('http'):
                print(f"警告: URL不是有效的HTTP地址: {video_url}")
                # 尝试修复URL
                if video_url.startswith('//'):
                    video_url = 'https:' + video_url
                    print(f"修复后的URL: {video_url}")
                else:
                    print("无法修复URL，使用备用方案")
                    raise Exception("URL格式不正确")
            
            p = 0
            
            # 检查是否为m3u8
            if '.m3u8' in video_url:
                print("检测到M3U8格式")
                original_url = video_url
                video_url = self.proxy(video_url, 'm3u8')
                print(f"代理前: {original_url}")
                print(f"代理后: {video_url}")
            else:
                print(f"非M3U8格式: {video_url}")
            
            print("=== 播放调试成功 ===")
            return {'parse': p, 'url': video_url, 'header': self.pheader}
            
        except Exception as e:
            print(f"=== 播放调试失败 ===")
            print(f"错误信息: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 备用方案
            backup_url = f"{self.hsot}{id}"
            print(f"使用备用URL: {backup_url}")
            return {'parse': 1, 'url': backup_url, 'header': self.pheader}

    def liveContent(self, url):
        pass

    def localProxy(self, param):
        print(f"代理请求 - 类型: {param.get('type')}, URL: {param.get('url')[:100] if param.get('url') else 'None'}")
        
        try:
            url = self.d64(param['url'])
            print(f"解码后的URL: {url}")
            
            if param.get('type') == 'm3u8':
                return self.m3Proxy(url)
            else:
                return self.tsProxy(url,param['type'])
        except Exception as e:
            print(f"代理错误: {e}")
            return [500, "text/plain", f"Proxy Error: {e}"]

    def gethost(self):
        params = {
            'v': '1',
        }
        self.headers.update({'referer': 'https://a.hdys.top/'})
        response = self.session.get('https://a.hdys.top/assets/js/config.js',proxies=self.proxies, params=params, headers=self.headers)
        return self.host_late(response.text.split(';')[:-4])

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
        except Exception as e:
            print(f"{str(e)}")
            return pq(data.text.encode('utf-8'))

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
                url=re.findall(r'"([^"]*)"', url)[0]
                start_time = time.time()
                self.headers.update({'referer': f'{url}/'})
                response = requests.head(url,proxies=self.proxies,headers=self.headers,timeout=1.0, allow_redirects=False)
                delay = (time.time() - start_time) * 1000
                results[url] = delay
            except Exception as e:
                results[url] = float('inf')

        for url in urls:
            t = threading.Thread(target=test_host, args=(url,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return min(results.items(), key=lambda x: x[1])[0]

    def m3Proxy(self, url):
        print(f"M3U8代理 - 请求URL: {url}")
        
        try:
            ydata = requests.get(url, headers=self.pheader, proxies=self.proxies, allow_redirects=False)
            print(f"M3U8代理 - 响应状态: {ydata.status_code}")
            
            if ydata.headers.get('Location'):
                print(f"M3U8代理 - 重定向到: {ydata.headers['Location']}")
                url = ydata.headers['Location']
                ydata = requests.get(url, headers=self.pheader, proxies=self.proxies)
            
            data = ydata.content.decode('utf-8')
            print(f"M3U8代理 - 内容长度: {len(data)}")
            print(f"M3U8代理 - 内容预览: {data[:200]}...")
            
            lines = data.strip().split('\n')
            last_r = url[:url.rfind('/')]
            parsed_url = urlparse(url)
            durl = parsed_url.scheme + "://" + parsed_url.netloc
            for index, string in enumerate(lines):
                if '#EXT' not in string:
                    if 'http' not in string:
                        domain=last_r if string.count('/') < 2 else durl
                        string = domain + ('' if string.startswith('/') else '/') + string
                    lines[index] = self.proxy(string, string.split('.')[-1].split('?')[0])
            data = '\n'.join(lines)
            return [200, "application/vnd.apple.mpegur", data]
        except Exception as e:
            print(f"M3U8代理错误: {e}")
            return [500, "text/plain", f"M3U8 Proxy Error: {e}"]

    def tsProxy(self, url,type):
        print(f"TS代理 - 请求URL: {url}, 类型: {type}")
        
        try:
            h=self.pheader.copy()
            if type=='img':h=self.headers.copy()
            data = requests.get(url, headers=h, proxies=self.proxies, stream=True)
            print(f"TS代理 - 响应状态: {data.status_code}")
            return [200, data.headers['Content-Type'], data.content]
        except Exception as e:
            print(f"TS代理错误: {e}")
            return [500, "text/plain", f"TS Proxy Error: {e}"]

    def proxy(self, data, type='img'):
        if data and len(self.proxies):
            proxy_url = f"{self.getProxyUrl()}&url={self.e64(data)}&type={type}"
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
        except Exception as e:
            print(f"Base64编码错误: {str(e)}")
            return ""

    def d64(self,encoded_text):
        try:
            encoded_bytes = encoded_text.encode('utf-8')
            decoded_bytes = b64decode(encoded_bytes)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            print(f"Base64解码错误: {str(e)}")
            return ""
