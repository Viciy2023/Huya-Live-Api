"""
URL 代理 API - Vercel Serverless Function
用于代理获取被限制的订阅源
访问: /api/proxy?url=https://live.catvod.com/tv.m3u
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests


# 允许代理的域名白名单
ALLOWED_DOMAINS = [
    "live.catvod.com",
    "im5k.fun",
    "iptv.im5k.fun",
    "php.946985.filegear-sg.me",
    "catvod.com",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 解析查询参数
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        target_url = query_params.get("url", [None])[0]
        
        if not target_url:
            self.send_response(400)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("缺少 url 参数".encode("utf-8"))
            return
        
        # 检查域名白名单
        try:
            target_domain = urlparse(target_url).netloc
            if not any(domain in target_domain for domain in ALLOWED_DOMAINS):
                self.send_response(403)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"域名不在白名单: {target_domain}".encode("utf-8"))
                return
        except:
            self.send_response(400)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("无效的 URL".encode("utf-8"))
            return
        
        # 代理请求
        try:
            response = requests.get(target_url, headers=HEADERS, timeout=30)
            
            # 返回响应
            self.send_response(response.status_code)
            content_type = response.headers.get("Content-Type", "text/plain")
            self.send_header("Content-type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response.content)
            
        except requests.exceptions.Timeout:
            self.send_response(504)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("代理请求超时".encode("utf-8"))
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"代理请求失败: {str(e)}".encode("utf-8"))
