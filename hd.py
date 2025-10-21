import json
import re
from urllib.parse import unquote
import requests
from pyquery import PyQuery as pq

# TV Box 接口类
class HuaduSpider:
    
    def __init__(self):
        self.name = "花都影视"
        self.host = "https://hd8.huaduzy.net"
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/'
        }
        self.session.headers.update(self.headers)

    def homeContent(self, filter):
        """
        首页内容
        """
        try:
            response = self.session.get(self.host)
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
                    'vod_remarks': item('.pic-tag-b').text() or ''
                })
            
            return {
                'class': classes,
                'list': videos
            }
            
        except Exception as e:
            return {'class': [], 'list': []}

    def homeVideoContent(self):
        """
        首页推荐视频
        """
        return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        """
        分类内容
        """
        try:
            url = f"{self.host}/vodshow/{tid}--------{pg}---.html"
            response = self.session.get(url)
            data = pq(response.text)
            
            videos = []
            ldata = data('.stui-vodlist.clearfix li')
            for item in ldata.items():
                vod_id = item('a').attr('href') or ''
                vod_name = item('img').attr('alt') or '未知'
                vod_pic = item('img').attr('data-original') or item('img').attr('src') or ''
                
                if vod_pic and not vod_pic.startswith('http'):
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
                    else:
                        vod_pic = self.host + vod_pic
                
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
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
            return {'list': [], 'page': pg, 'pagecount': 1, 'limit': 90, 'total': 0}

    def detailContent(self, ids):
        """
        详情页内容
        """
        try:
            url = f"{self.host}{ids}"
            response = self.session.get(url)
            data = pq(response.text)
            
            # 获取基本信息
            title_elem = data('.stui-content__detail .title')
            vod_name = title_elem.text() if title_elem.length > 0 else '未知'
            
            # 获取封面
            img_elem = data('.stui-vodlist__thumb img')
            vod_pic = img_elem.attr('data-original') or img_elem.attr('src') or ''
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
            
            if not play_links:
                play_links = [f"第1集${ids}"]
            
            vod = {
                'vod_id': ids,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_content': data('.stui-content__detail p.desc').text() or "",
                'vod_play_from': '花都影视',
                'vod_play_url': "#".join(play_links)
            }
            
            return {'list': [vod]}
            
        except Exception as e:
            return {'list': []}

    def searchContent(self, key, quick, pg=1):
        """
        搜索内容
        """
        try:
            import urllib.parse
            encoded_key = urllib.parse.quote(key)
            url = f"{self.host}/vodsearch/{encoded_key}----------{pg}---.html"
            
            response = self.session.get(url)
            data = pq(response.text)
            
            videos = []
            ldata = data('.stui-vodlist.clearfix li')
            for item in ldata.items():
                vod_id = item('a').attr('href') or ''
                vod_name = item('img').attr('alt') or '未知'
                vod_pic = item('img').attr('data-original') or item('img').attr('src') or ''
                
                if vod_pic and not vod_pic.startswith('http'):
                    if vod_pic.startswith('//'):
                        vod_pic = 'https:' + vod_pic
                    else:
                        vod_pic = self.host + vod_pic
                
                videos.append({
                    'vod_id': vod_id,
                    'vod_name': vod_name,
                    'vod_pic': vod_pic,
                    'vod_remarks': item('.pic-tag-b').text() or ''
                })
            
            return {'list': videos, 'page': pg}
            
        except Exception as e:
            return {'list': [], 'page': pg}

    def playerContent(self, flag, id, vipFlags):
        """
        播放内容 - 使用双重URL解码获取真实播放地址
        """
        try:
            play_page_url = f"{self.host}{id}"
            response = self.session.get(play_page_url)
            data = pq(response.text)
            
            # 提取player_data脚本
            scripts = data('.stui-player.col-pd script')
            if scripts.length == 0:
                return self._fallback_play_result(play_page_url)
            
            script_text = scripts.eq(0).text()
            
            # 解析player_data
            player_data = self._extract_player_data(script_text)
            if not player_data:
                return self._fallback_play_result(play_page_url)
            
            # 解密视频URL - 双重URL解码
            encrypted_url = player_data.get('url', '')
            if encrypted_url:
                # 关键解密步骤：双重URL解码
                video_url = unquote(unquote(encrypted_url))
                
                # 验证URL格式
                if video_url.startswith('http'):
                    return {
                        'parse': 0,  # 0表示直接播放
                        'url': video_url,
                        'header': self._get_player_headers()
                    }
            
            return self._fallback_play_result(play_page_url)
            
        except Exception as e:
            return self._fallback_play_result(f"{self.host}{id}")

    def _extract_player_data(self, script_text):
        """从脚本中提取player_data"""
        try:
            # 查找player_data变量
            match = re.search(r'var\s+player_data\s*=\s*({[^;]+});', script_text)
            if match:
                return json.loads(match.group(1))
            
            match = re.search(r'player_data\s*=\s*({[^;]+});', script_text)
            if match:
                return json.loads(match.group(1))
                
        except:
            pass
            
        return None

    def _fallback_play_result(self, url):
        """备用播放方案"""
        return {
            'parse': 1,  # 1表示需要解析
            'url': url,
            'header': self._get_player_headers()
        }

    def _get_player_headers(self):
        """获取播放器头部信息"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Referer': f'{self.host}/',
            'Origin': self.host
        }

    def localProxy(self, param):
        """本地代理（如果需要）"""
        try:
            url = param.get('url', '')
            if not url:
                return [400, "text/plain", "Missing URL"]
                
            response = requests.get(url, headers=self._get_player_headers(), timeout=10)
            return [200, response.headers.get('content-type', 'text/plain'), response.content]
            
        except Exception as e:
            return [500, "text/plain", f"Proxy Error: {e}"]


# TV Box 接口导出
if __name__ == '__main__':
    # 创建实例
    spider = HuaduSpider()
    
    # 测试功能
    print("=== 花都影视TV Box接口 ===")
    print(f"站点名称: {spider.name}")
    print(f"站点地址: {spider.host}")
    
    # 测试首页
    home_result = spider.homeContent({})
    print(f"首页分类数: {len(home_result['class'])}")
    print(f"首页视频数: {len(home_result['list'])}")
    
    # 如果有分类，测试第一个分类
    if home_result['class']:
        first_category = home_result['class'][0]
        print(f"测试分类: {first_category['type_name']} (ID: {first_category['type_id']})")
        
        category_result = spider.categoryContent(first_category['type_id'], 1, {}, {})
        print(f"分类页视频数: {len(category_result['list'])}")
        
        # 如果有视频，测试第一个视频的详情
        if category_result['list']:
            first_video = category_result['list'][0]
            print(f"测试视频: {first_video['vod_name']}")
            
            detail_result = spider.detailContent(first_video['vod_id'])
            if detail_result['list']:
                detail = detail_result['list'][0]
                print(f"详情页标题: {detail['vod_name']}")
                print(f"播放链接: {detail['vod_play_url']}")
