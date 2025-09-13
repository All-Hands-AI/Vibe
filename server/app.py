from flask import Flask, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static')
CORS(app)

# API Routes
@app.route('/api/')
def api_hello():
    return jsonify({
        'message': 'Hello from OpenVibe Python server!',
        'status': 'running',
        'version': '1.0.0'
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'openvibe-backend'
    })

@app.route('/api/hello/<name>')
def hello_name(name):
    return jsonify({
        'message': f'Hello, {name}!',
        'from': 'OpenVibe Backend'
    })

# Serve React frontend
@app.route('/')
def serve_frontend():
    try:
        return send_file('static/index.html')
    except FileNotFoundError:
        return jsonify({'error': 'Frontend not built. Run npm run build first.'}), 404

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('static', path)
    except FileNotFoundError:
        # For React Router, serve index.html for any non-API routes
        if not path.startswith('api/'):
            try:
                return send_file('static/index.html')
            except FileNotFoundError:
                return jsonify({'error': 'Frontend not built. Run npm run build first.'}), 404
        return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)