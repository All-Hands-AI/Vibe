# OpenVibe Python Backend

A simple Flask-based backend API for the OpenVibe application.

## API Endpoints

### Health Check
- **GET** `/api/health` - Returns the health status of the backend service

### Hello World
- **GET** `/` - Basic hello world endpoint
- **GET** `/api/hello` - API hello endpoint

## Local Development

To run the backend locally:

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The backend will be available at `http://localhost:8000`

## Production Deployment

The backend is automatically deployed with the frontend using Docker and Fly.io. The nginx configuration proxies `/api/*` requests to the Python backend running on port 8000.

## Dependencies

- Flask 3.0.0 - Web framework
- Flask-CORS 4.0.0 - Cross-origin resource sharing
- Gunicorn 21.2.0 - WSGI HTTP Server for production