# OpenVibe Repository

## Overview

OpenVibe is a full-stack application combining a modern React frontend with a Python backend, designed for deployment on Fly.io. The project demonstrates best practices for React development with a clean, component-based architecture alongside a simple Python server.

## Key Features

- **React 19**: Built with the latest React version using modern hooks and patterns
- **Vite**: Lightning-fast development server and build tool
- **React Router**: Client-side routing with multiple pages (Home, About, Contact)
- **Theme Context**: Built-in theme management system
- **Component Architecture**: Well-organized components (Header, Footer) and pages
- **Testing Setup**: Comprehensive testing with Vitest and React Testing Library
- **Modern Tooling**: ESLint configuration for code quality
- **Python Backend**: Simple Flask/FastAPI server for API endpoints

## Project Structure

```
├── src/                 # React frontend
│   ├── components/      # Reusable UI components (Header, Footer)
│   ├── pages/          # Route-based page components (Home, About, Contact)
│   ├── context/        # React context providers (ThemeContext)
│   ├── test/           # Test configuration and setup
│   ├── App.jsx         # Main application component
│   └── main.jsx        # React entry point
├── server/             # Python backend
│   ├── app.py          # Main server application
│   └── requirements.txt # Python dependencies
├── fly.toml            # Fly.io deployment configuration
└── Dockerfile          # Container configuration
```

## Development Workflow

**⚠️ IMPORTANT: Never run this application locally!**

Instead, always follow this workflow:
1. Make your changes to the codebase
2. Push changes to GitHub
3. Create a Pull Request
4. Deploy to Fly.io for testing and preview

This ensures consistent deployment and testing environments for all contributors.

## Backend Development Guidelines

For any backend functionality, always use:

- **Python Server**: Flask or FastAPI for API endpoints
- **Fly.io Postgres**: Use Fly.io's managed PostgreSQL for data persistence
- **Fly.io Redis**: Use Fly.io's Redis for caching and sessions
- **Container-based deployment**: All services run in Docker containers on Fly.io

### Backend Architecture
- Place API routes in the `server/` directory
- Use Fly.io Postgres for persistent data storage
- Use Fly.io Redis for caching, session storage, and real-time features
- Keep the Python server lightweight and stateless where possible
- Use environment variables for configuration

## Technology Stack

- **Frontend**: React 19, React Router DOM
- **Build Tool**: Vite
- **Testing**: Vitest, React Testing Library, jsdom
- **Code Quality**: ESLint with React-specific rules
- **Styling**: CSS with component-scoped styles
- **Backend**: Python (Flask/FastAPI)
- **Database**: Fly.io Postgres
- **Cache/Sessions**: Fly.io Redis
- **Deployment**: Fly.io with Docker containers

## Available Scripts

### Frontend (React)
- `npm run dev` - Start development server (DO NOT USE - see workflow above)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests in watch mode
- `npm run test:run` - Run tests once
- `npm run lint` - Check code quality
- `npm run lint:fix` - Fix linting issues automatically

### Backend (Python)
- `python server/app.py` - Start Python server locally (DO NOT USE - see workflow above)

### Deployment (Fly.io)
- `fly deploy` - Deploy to Fly.io (after pushing to GitHub)
- `fly logs` - View application logs
- `fly status` - Check application status

## Fly.io Configuration

The application is configured for Fly.io deployment with:
- **Multi-stage Docker build**: Builds React frontend and Python backend
- **Static file serving**: Python server serves built React app
- **API endpoints**: All backend routes prefixed with `/api/`
- **Auto-scaling**: Configured to scale to zero when not in use
- **Health checks**: Built-in health endpoint at `/api/health`