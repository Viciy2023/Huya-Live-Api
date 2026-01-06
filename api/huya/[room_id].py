"""
虎牙直播源解析 API - Vercel Serverless Function
访问: /api/huya/660000
"""
from http.server import BaseHTTPRequestHandler
import requests
import re
import base64
import urllib.parse
import hashlib
import time
import random
import json


def get_anonymous_uid():
    """获取匿名用户ID"""
    url = "https://udblgn.huya.com/web/anonymousLogin"
    payload = {"appId": 5002, "byPass": 3, "context": "", "version": "2.4", "data": {}}
    headers = {"Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        data = r.json()
        return str(data.get("data", {}).get("uid", "0"))
    except:
        return "0"


def new_uuid():
    """生成新的 uuid"""
    now = int(time.time() * 1000)
    rand = random.randint(0, 999)
    return ((now % 10000000000) * 1000 + rand) % 4294967295


def parse_anticode(code, uid, streamname):
    """解析并重新计算签名"""
    params = dict(urllib.parse.parse_qsl(code))
    params["ver"] = "1"
    params["sv"] = "2110211124"
    params["seqid"] = str(int(uid) + int(time.time() * 1000))
    params["uid"] = uid
    params["uuid"] = str(new_uuid())

    ss = hashlib.md5(
        f"{params['seqid']}|{params['ctype']}|{params['t']}".encode()
    ).hexdigest()

    fm = params.get("fm", "")
    if fm:
        try:
            decoded_fm = base64.b64decode(fm).decode("utf-8")
            decoded_fm = decoded_fm.replace("$0", params["uid"])
            decoded_fm = decoded_fm.replace("$1", streamname)
            decoded_fm = decoded_fm.replace("$2", ss)
            decoded_fm = decoded_fm.replace("$3", params["wsTime"])
            params["wsSecret"] = hashlib.md5(decoded_fm.encode()).hexdigest()
        except:
            pass

    if "fm" in params:
        del params["fm"]
    if "txyp" in params:
        del params["txyp"]

    return urllib.parse.urlencode(params)


def get_huya_url(room_id):
    """获取虎牙直播真实地址"""
    try:
        # 获取房间信息
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # 获取真实房间ID
        url = f"https://m.huya.com/{room_id}"
        resp = requests.get(url, headers=headers, timeout=10)
        html = resp.text
        
        stream_match = re.search(r'stream: (\{.+"iFrameRate":\d+\})', html)
        if stream_match:
            stream_data = json.loads(stream_match.group(1))
            real_room_id = stream_data["data"][0]["gameLiveInfo"]["profileRoom"]
        else:
            real_room_id = str(room_id)

        # 获取直播流信息
        api_url = f"https://mp.huya.com/cache.php?m=Live&do=profileRoom&roomid={real_room_id}"
        resp = requests.get(api_url, headers=headers, timeout=10)
        data = resp.json()

        if data.get("status") != 200:
            return None, "API错误"

        live_data = data.get("data", {})
        live_status = live_data.get("liveStatus")

        if live_status == "OFF":
            return None, "未开播"

        # 获取匿名UID
        uid = get_anonymous_uid()

        # 解析直播流
        stream_info = live_data.get("stream", {})
        base_stream_list = stream_info.get("baseSteamInfoList", [])

        if not base_stream_list:
            return None, "无直播流"

        item = base_stream_list[0]
        stream_name = item.get("sStreamName", "")

        # 生成 M3U8 地址
        hls_anti = item.get("sHlsAntiCode", "")
        if hls_anti:
            anticode = parse_anticode(hls_anti, uid, stream_name)
            hls_url = f"{item['sHlsUrl']}/{stream_name}.{item['sHlsUrlSuffix']}?{anticode}"
            return hls_url, None

        return None, "解析失败"

    except Exception as e:
        return None, str(e)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 从路径提取房间号 (Vercel 动态路由: /api/huya/[room_id])
        path_parts = self.path.rstrip("/").split("/")
        # 路径格式: /api/huya/660000 或 /api/huya/660000?xxx
        room_id = path_parts[-1].split("?")[0] if path_parts else ""

        if not room_id or not room_id.isdigit():
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid room_id")
            return

        real_url, error = get_huya_url(room_id)

        if real_url:
            # 302 重定向到真实地址
            self.send_response(302)
            self.send_header("Location", real_url)
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"获取失败: {error}".encode("utf-8"))
