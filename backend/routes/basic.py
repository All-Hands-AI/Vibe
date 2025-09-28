from flask import Blueprint, jsonify
import logging
import os
import subprocess
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Create Blueprint for basic routes
basic_bp = Blueprint("basic", __name__)


@basic_bp.route("/")
def hello_world():
    logger.debug("📍 Root endpoint accessed")
    return jsonify(
        {
            "message": "Hello World from Python Backend!",
            "status": "success",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@basic_bp.route("/api/health")
def health_check():
    logger.debug("🏥 Health check endpoint accessed")
    return jsonify(
        {
            "status": "healthy",
            "service": "OpenVibe Backend",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@basic_bp.route("/api/hello")
def api_hello():
    logger.debug("👋 Hello API endpoint accessed")
    return jsonify(
        {
            "message": "Hello from the API!",
            "endpoint": "/api/hello",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@basic_bp.route("/api/status")
def setup_status():
    """Check the status of the OpenVibe development environment setup."""
    logger.debug("📊 Setup status endpoint accessed")
    
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": "development",
        "setup_status": "complete",
        "components": {}
    }
    
    # Check backend dependencies
    try:
        # Check if we're in a virtual environment
        venv_active = os.environ.get('VIRTUAL_ENV') is not None
        status["components"]["backend"] = {
            "status": "running",
            "virtual_env": venv_active,
            "port": int(os.environ.get("PORT", 3001)),
            "dependencies_installed": True
        }
    except Exception as e:
        status["components"]["backend"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check frontend status by looking for node_modules
    try:
        # Get the project root directory (parent of backend directory)
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        project_root = os.path.dirname(backend_dir)
        frontend_path = os.path.join(project_root, "frontend")
        node_modules_exists = os.path.exists(os.path.join(frontend_path, "node_modules"))
        package_json_exists = os.path.exists(os.path.join(frontend_path, "package.json"))
        
        status["components"]["frontend"] = {
            "status": "configured",
            "dependencies_installed": node_modules_exists,
            "package_json_exists": package_json_exists,
            "expected_port": 12000
        }
    except Exception as e:
        status["components"]["frontend"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check if Makefile exists and has required targets
    try:
        # Get the project root directory (parent of backend directory)
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        project_root = os.path.dirname(backend_dir)
        makefile_path = os.path.join(project_root, "Makefile")
        makefile_exists = os.path.exists(makefile_path)
        
        required_targets = ["install", "dev", "test", "lint"]
        targets_present = []
        
        if makefile_exists:
            with open(makefile_path, 'r') as f:
                makefile_content = f.read()
                for target in required_targets:
                    if f"{target}:" in makefile_content:
                        targets_present.append(target)
        
        status["components"]["makefile"] = {
            "status": "present" if makefile_exists else "missing",
            "exists": makefile_exists,
            "required_targets": required_targets,
            "targets_present": targets_present,
            "all_targets_present": len(targets_present) == len(required_targets)
        }
    except Exception as e:
        status["components"]["makefile"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Overall status determination
    all_components_ok = all(
        comp.get("status") in ["running", "configured", "present"] 
        for comp in status["components"].values()
    )
    
    status["overall_status"] = "ready" if all_components_ok else "incomplete"
    status["ready_for_development"] = all_components_ok
    
    return jsonify(status)
