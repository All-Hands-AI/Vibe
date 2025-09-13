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
# Install uv if not already installed
pip install uv

# Install dependencies using uv
uv pip install .

# Or for development with optional dependencies
uv pip install .[dev]

# Run the application
python app.py
```

The backend will be available at `http://localhost:8000`

## Production Deployment

The backend is automatically deployed with the frontend using Docker and Fly.io. The nginx configuration proxies `/api/*` requests to the Python backend running on port 8000.

## Dependencies

Dependencies are managed using `pyproject.toml` and installed with `uv` for faster, more reliable package management.

### Core Dependencies
- Flask 3.0.0 - Web framework
- Flask-CORS 4.0.0 - Cross-origin resource sharing
- Gunicorn 21.2.0 - WSGI HTTP Server for production
- Requests 2.31.0 - HTTP library
- PyNaCl 1.5.0 - Cryptographic library

### Development Dependencies (optional)
- pytest - Testing framework
- black - Code formatter
- flake8 - Linting
- mypy - Type checking

## Package Management

This project uses `uv` instead of `pip` for faster dependency resolution and installation. The `pyproject.toml` file contains all project metadata and dependencies.

### Docker Deployment
In the Docker build process, we use `uv pip compile` to generate a requirements file from `pyproject.toml`, then install dependencies with `uv pip install`. This approach provides the speed benefits of `uv` while avoiding package build complexity for web service deployments.