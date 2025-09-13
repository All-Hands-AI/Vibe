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
2. Install dependencies:
   ```bash
   npm install
   ```

### Development

To start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:12000`

### Build

To build for production:

```bash
npm run build
```

### Preview

To preview the production build:

```bash
npm run preview
```

### Testing

To run tests:

```bash
npm test              # Run tests in watch mode
npm run test:run      # Run tests once
npm run test:coverage # Run tests with coverage report
```

### Linting

To lint the code:

```bash
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
src/
├── App.jsx          # Main App component
├── App.css          # App styles
├── main.jsx         # React entry point
└── index.css        # Global styles
```