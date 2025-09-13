from http.server import BaseHTTPRequestHandler
import json
import sys
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Log to stderr (visible in Vercel function logs)
        print(f"[{datetime.now().isoformat()}] Hello API called from {self.client_address}", file=sys.stderr)
        print(f"[{datetime.now().isoformat()}] User-Agent: {self.headers.get('User-Agent', 'Unknown')}", file=sys.stderr)
        print(f"[{datetime.now().isoformat()}] Python backend is working! 🐍", file=sys.stderr)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_data = {
            'message': 'Hello from OpenVibe Python API!',
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'app': 'OpenVibe',
            'version': '1.0.0',
            'backend_logs': 'Check Vercel function logs to see backend activity',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
        self.wfile.write(json.dumps(response_data).encode())
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return