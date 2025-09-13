from http.server import BaseHTTPRequestHandler
import json
import random
import sys
from datetime import datetime, timedelta

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Log to stderr (visible in Vercel function logs)
        print(f"[{datetime.now().isoformat()}] Vibes API called from {self.client_address}", file=sys.stderr)
        print(f"[{datetime.now().isoformat()}] Generating random vibes data... 🎨", file=sys.stderr)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # Generate sample vibes data
        vibes_list = [
            'Happy', 'Excited', 'Calm', 'Energetic', 'Peaceful', 
            'Motivated', 'Creative', 'Focused', 'Inspired', 'Relaxed',
            'Confident', 'Grateful', 'Optimistic', 'Joyful', 'Serene'
        ]
        
        sample_vibes = []
        for i in range(random.randint(5, 10)):
            vibe = random.choice(vibes_list)
            sample_vibes.append({
                'id': i + 1,
                'vibe': vibe,
                'intensity': random.randint(1, 10),
                'color': f'#{random.randint(0, 0xFFFFFF):06x}',
                'description': f'Feeling {vibe.lower()} today',
                'created_at': (datetime.now() - timedelta(hours=random.randint(0, 48))).isoformat()
            })
        
        response_data = {
            'vibes': sample_vibes,
            'total': len(sample_vibes),
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'app': 'OpenVibe',
            'backend_logs': 'Check Vercel function logs to see backend activity'
        }
        
        print(f"[{datetime.now().isoformat()}] Generated {len(sample_vibes)} vibes successfully! ✨", file=sys.stderr)
        
        self.wfile.write(json.dumps(response_data).encode())
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return