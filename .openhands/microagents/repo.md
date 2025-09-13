# OpenVibe Repository

## Overview

OpenVibe is a modern React application built with Vite that serves as a starter template or showcase application. The project demonstrates best practices for React development with a clean, component-based architecture.

## Key Features

- **React 19**: Built with the latest React version using modern hooks and patterns
- **Vite**: Lightning-fast development server and build tool
- **React Router**: Client-side routing with multiple pages (Home, About, Contact)
- **Theme Context**: Built-in theme management system
- **Component Architecture**: Well-organized components (Header, Footer) and pages
- **Testing Setup**: Comprehensive testing with Vitest and React Testing Library
- **Modern Tooling**: ESLint configuration for code quality

## Project Structure

```
src/
├── components/          # Reusable UI components (Header, Footer)
├── pages/              # Route-based page components (Home, About, Contact)
├── context/            # React context providers (ThemeContext)
├── test/               # Test configuration and setup
├── App.jsx             # Main application component
└── main.jsx            # React entry point
```

## Development Workflow

**⚠️ IMPORTANT: Never run this application locally!**

Instead, always follow this workflow:
1. Make your changes to the codebase
2. Push changes to GitHub
3. Create a Pull Request
4. A preview will automatically run on Vercel

This ensures consistent deployment and testing environments for all contributors.

## Backend Development Guidelines

For any backend functionality, always use:

- **Vercel Serverless Functions**: Create API endpoints in the `/api` directory
- **Vercel KV**: Use Vercel's Redis-compatible key-value store for data persistence
- **No traditional servers**: Avoid Express.js, traditional databases, or any server infrastructure

### Backend Architecture
- Place API routes in `/api/` directory (Vercel convention)
- Use Vercel KV for caching, session storage, and simple data persistence
- Leverage serverless functions for authentication, data processing, and third-party integrations
- Keep functions stateless and lightweight

## Technology Stack

- **Frontend**: React 19, React Router DOM
- **Build Tool**: Vite
- **Testing**: Vitest, React Testing Library, jsdom
- **Code Quality**: ESLint with React-specific rules
- **Styling**: CSS with component-scoped styles
- **Deployment**: Vercel (via GitHub integration)
- **Backend**: Vercel Serverless Functions
- **Database**: Vercel KV (Redis-compatible key-value store)

## Available Scripts

- `npm run dev` - Start development server (DO NOT USE - see workflow above)
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests in watch mode
- `npm run test:run` - Run tests once
- `npm run lint` - Check code quality
- `npm run lint:fix` - Fix linting issues automatically