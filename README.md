# OpenVibe

[![CI](https://github.com/rbren/OpenVibe/actions/workflows/ci.yml/badge.svg)](https://github.com/rbren/OpenVibe/actions/workflows/ci.yml)
[![Deploy](https://github.com/rbren/OpenVibe/actions/workflows/deploy.yml/badge.svg)](https://github.com/rbren/OpenVibe/actions/workflows/deploy.yml)

A basic React application built with Vite.

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm

### Installation

1. Clone the repository
2. Navigate to the frontend directory and install dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Development

To start the development server:

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:12000`

### Build

To build for production:

```bash
cd frontend
npm run build
```

### Preview

To preview the production build:

```bash
cd frontend
npm run preview
```

### Testing

To run tests:

```bash
cd frontend
npm test              # Run tests in watch mode
npm run test:run      # Run tests once
npm run test:coverage # Run tests with coverage report
```

### Linting

To lint the code:

```bash
cd frontend
npm run lint          # Check for linting errors
npm run lint:fix      # Fix linting errors automatically
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI Workflow** (`.github/workflows/ci.yml`): Runs on every push and pull request
  - Lints the code with ESLint
  - Builds the application
  - Runs all tests with coverage reporting
  - Provides a quality gate that must pass before merging

- **Deploy Workflow** (`.github/workflows/deploy.yml`): Deploys to Fly.io
  - Production deployment on pushes to `main`
  - Preview deployments for pull requests
  - Automatic cleanup of preview deployments when PRs are closed

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Route-based page components
│   ├── context/        # React context providers
│   ├── utils/          # Utility functions
│   ├── App.jsx         # Main App component
│   ├── main.jsx        # React entry point
│   └── index.css       # Global styles
├── index.html          # HTML template
├── package.json        # Frontend dependencies
├── vite.config.js      # Vite configuration
└── tailwind.config.js  # Tailwind CSS configuration
backend/
├── app.py              # Python backend application
├── projects.py         # Project management logic
├── keys.py             # API key management
└── pyproject.toml      # Python dependencies
```