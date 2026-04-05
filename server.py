#!/usr/bin/env python3
"""
北京高考议论文思路训练器 - 本地服务器
用法：python server.py
然后浏览器打开 http://localhost:8080
"""
import http.server
import json
import urllib.request
import urllib.error
import os
import sys
import ssl

# macOS Python 3.13 often lacks bundled certs; use system certs or skip verify locally
def _ssl_ctx():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    # Try macOS system keychain certs via homebrew openssl
    for cafile in [
        '/etc/ssl/cert.pem',
        '/usr/local/etc/openssl/cert.pem',
        '/opt/homebrew/etc/openssl@3/cert.pem',
        '/opt/homebrew/etc/ca-certificates/cert.pem',
    ]:
        if os.path.exists(cafile):
            return ssl.create_default_context(cafile=cafile)
    # Fallback: skip verification (local dev only)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

SSL_CTX = _ssl_ctx()

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/chat':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            api_key = os.environ.get('KIMI_API_KEY', '')
            payload = {
                'model': data.get('model', 'kimi-k2.5'),
                'max_tokens': data.get('max_tokens', 2000),
                'messages': data.get('messages', [])
            }

            req = urllib.request.Request(
                'https://api.moonshot.cn/v1/chat/completions',
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                },
                method='POST'
            )

            try:
                with urllib.request.urlopen(req, timeout=120, context=SSL_CTX) as resp:
                    result = resp.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(result)
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8', errors='replace')
                sys.stderr.write(f"[API ERROR {e.code}] {error_body}\n")
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': {'message': error_body}}).encode('utf-8'))
            except Exception as e:
                sys.stderr.write(f"[API EXCEPTION] {e}\n")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': {'message': str(e)}}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        msg = str(args[0]) if args else ''
        if '/api/' in msg:
            sys.stderr.write(f"[API] {msg}\n")

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.')
    server = http.server.HTTPServer(('', PORT), Handler)
    print(f"""
╔══════════════════════════════════════════╗
║   北京高考议论文思路训练器               ║
║                                          ║
║   浏览器打开: http://localhost:{PORT}      ║
║   按 Ctrl+C 停止服务器                   ║
╚══════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()
