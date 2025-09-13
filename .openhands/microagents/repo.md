# OpenVibe Repository

## Overview

OpenVibe is a modern React application built with Vite and deployed on Fly.io using Nginx. The project demonstrates best practices for React development with a clean, component-based architecture optimized for cloud deployment.

This project makes heavy use of the [OpenHands Agent SDK](https://github.com/All-Hands-AI/agent-sdk/). If asked to work with the SDK you may want to look at the docs there.

## Development Workflow

<IMPORTANT>
When installing python dependencies, create a virtual envirionment using `uv`! This is
very important or you will have import problems.
</IMPORTANT>

## State Management & Data Storage

**🚨 CRITICAL: OpenVibe uses FILE-BASED state management exclusively. NO SQL databases.**

## Lint and Testing Commands (from GitHub Actions)

## Test and Lint Commands

**Frontend:**
- Lint: `cd frontend && npm ci && npm run lint`
- Test: `cd frontend && npm ci && npm run test:run`
- Test with coverage: `cd frontend && npm ci && npm install --save-dev @vitest/coverage-v8 && npm run test:coverage`

**Backend:**
- Lint: `cd backend && uv venv && source .venv/bin/activate && uv pip install Flask==3.0.0 Flask-CORS==4.0.0 gunicorn==21.2.0 requests==2.31.0 PyNaCl==1.5.0 && uv pip install "openhands-sdk @ git+https://github.com/all-hands-ai/agent-sdk.git@main#subdirectory=openhands/sdk" && uv pip install pytest>=7.0.0 pytest-flask>=1.2.0 pytest-cov>=4.0.0 black>=23.0.0 flake8>=6.0.0 mypy>=1.0.0 && black --check --diff . && flake8 . && mypy .`
- Test: `cd backend && uv venv && source .venv/bin/activate && uv pip install Flask==3.0.0 Flask-CORS==4.0.0 gunicorn==21.2.0 requests==2.31.0 PyNaCl==1.5.0 && uv pip install "openhands-sdk @ git+https://github.com/all-hands-ai/agent-sdk.git@main#subdirectory=openhands/sdk" && uv pip install pytest>=7.0.0 pytest-flask>=1.2.0 pytest-cov>=4.0.0 black>=23.0.0 flake8>=6.0.0 mypy>=1.0.0 && mkdir -p /tmp/test-data && DATA_DIR=/tmp/test-data pytest --cov=. --cov-report=xml:coverage.xml --cov-report=html:htmlcov --cov-report=term-missing -v`
