# OpenVibe Repository

## Overview

OpenVibe is a modern React application built with Vite and deployed on Fly.io using Nginx. The project demonstrates best practices for React development with a clean, component-based architecture optimized for cloud deployment.

## Key Features

- **React 19**: Built with the latest React version using modern hooks and patterns
- **Vite**: Lightning-fast development server and build tool
- **React Router**: Client-side routing with multiple pages (Home, About, Contact)
- **Theme Context**: Built-in theme management system
- **Component Architecture**: Well-organized components (Header, Footer) and pages
- **Testing Setup**: Comprehensive testing with Vitest and React Testing Library
- **Modern Tooling**: ESLint configuration for code quality
- **Nginx Deployment**: Optimized static file serving with Nginx

## Project Structure

```
├── src/                 # React frontend
│   ├── components/      # Reusable UI components (Header, Footer)
│   ├── pages/          # Route-based page components (Home, About, Contact)
│   ├── context/        # React context providers (ThemeContext)
│   ├── test/           # Test configuration and setup
│   ├── App.jsx         # Main application component
│   └── main.jsx        # React entry point
├── fly.toml            # Fly.io deployment configuration
├── Dockerfile          # Multi-stage Docker build (Node.js + Nginx)
└── .dockerignore       # Docker build optimization
```

## Development Workflow

<IMPORTANT>
Never run this application locally!
</IMPORTANT>

Instead, always follow this workflow:
1. Make your changes to the codebase
2. Push changes to GitHub
3. Create a Pull Request

This will create a fly.io deployment.

This ensures consistent deployment and testing environments for all contributors.

## State Management & Data Storage

**🚨 CRITICAL: OpenVibe uses FILE-BASED state management exclusively. NO SQL databases.**

### File-Based JSON Storage
- **ALL application state** is stored in JSON files on the filesystem
- **Persistent Volume**: Data is stored in `/data` directory (mounted from Fly.io volume)
- **No SQL databases**: Do not use PostgreSQL, MySQL, SQLite, or any SQL database
- **No NoSQL databases**: Do not use MongoDB, Redis for data storage, or similar
- **JSON files only**: All data persistence must use raw JSON files

### Data Storage Patterns
```python
# ✅ CORRECT: File-based JSON storage
import json
import os

# Read existing data
with open('/data/users.json', 'r') as f:
    user_data = json.load(f)

# Add new user
user_data.append(new_user)

# Write back to file
with open('/data/users.json', 'w') as f:
    json.dump(user_data, f, indent=2)

# ❌ WRONG: SQL database usage
# cursor.execute('INSERT INTO users VALUES (?)', (user_data,))
```

### File Organization
- **User data**: `/data/users.json`
- **Application settings**: `/data/settings.json`
- **Session data**: `/data/sessions.json`
- **Logs**: `/data/logs/` directory
- **Uploads**: `/data/uploads/` directory

### Implementation Guidelines
1. **Always use `/data` directory** for persistent storage
2. **Atomic writes**: Use temporary files and rename for data integrity
3. **JSON validation**: Validate JSON structure before writing
4. **Error handling**: Gracefully handle file read/write errors
5. **Backup strategy**: Consider periodic file backups to external storage

## Backend Development Guidelines

For any backend functionality, always use Fly.io's serverless and managed services:

- **Fly.io Machines**: For serverless backend functions and APIs
- **Fly.io Object Storage**: For file uploads and static assets
- **Container-based deployment**: All services run in Docker containers on Fly.io
- **Persistent Volumes**: Use Fly.io volumes for `/data` directory storage

### Backend Architecture Recommendations
- Create separate Fly.io apps for backend APIs if needed
- **Use file-based JSON storage** in `/data` directory for all data persistence
- Keep services lightweight and stateless where possible
- Use environment variables for configuration
- Connect frontend to backend APIs via HTTPS endpoints
- **Never use SQL or NoSQL databases** - files only!

## Technology Stack

- **Frontend**: React 19, React Router DOM
- **Build Tool**: Vite
- **Testing**: Vitest, React Testing Library, jsdom
- **Code Quality**: ESLint with React-specific rules
- **Styling**: CSS with component-scoped styles
- **Web Server**: Nginx (for static file serving)
- **Data Storage**: File-based JSON storage in `/data` directory
- **Persistent Storage**: Fly.io volumes (no SQL databases)
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

### Deployment (Fly.io)
- `fly deploy` - Deploy to Fly.io (after pushing to GitHub)
- `fly logs` - View application logs
- `fly status` - Check application status
- `fly open` - Open the deployed application in browser

## Fly.io Configuration

The application is configured for Fly.io deployment with:

### Multi-stage Docker Build
1. **Build Stage**: Node.js environment builds the React application
2. **Production Stage**: Nginx serves the built static files

### Deployment Features
- **Static file serving**: Nginx optimized for React SPA
- **Auto-scaling**: Configured to scale to zero when not in use
- **HTTPS**: Force HTTPS enabled for security
- **Geographic distribution**: Deployed in `ewr` region with global edge caching
- **Resource optimization**: 1GB memory, shared CPU for cost efficiency

### Container Configuration
- **Port 80**: Internal Nginx port
- **Auto-stop/start**: Machines automatically stop when idle and start on demand
- **Minimal resource usage**: Optimized for cost-effective hosting

## Adding Backend Services

When you need backend functionality:

1. **Create a separate Fly.io app** for your API server
2. **Use file-based JSON storage** in `/data` directory (never SQL databases)
3. **Mount persistent volumes** for data storage across deployments
4. **Connect via environment variables** and HTTPS endpoints
5. **Deploy backend and frontend independently** for better scalability
6. **Use CORS configuration** to allow frontend-backend communication

This architecture keeps the frontend fast and lightweight while providing flexibility for backend services as needed, all while maintaining our file-based storage approach.
