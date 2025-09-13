from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return jsonify({
        'message': 'Hello World from Python Backend!',
        'status': 'success',
        'version': '1.0.0'
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'OpenVibe Backend'
    })

@app.route('/api/hello')
def api_hello():
    return jsonify({
        'message': 'Hello from the API!',
        'endpoint': '/api/hello'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)