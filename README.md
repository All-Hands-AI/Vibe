# OpenVibe

A basic React application built with Vite.

![CI](https://github.com/rbren/OpenVibe/workflows/CI/badge.svg)

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
npm run test        # Run tests in watch mode
npm run test:run    # Run tests once
```

### Linting

To run the linter:

```bash
npm run lint        # Check for linting errors
npm run lint:fix    # Fix linting errors automatically
```

## CI/CD

This project uses GitHub Actions for continuous integration. The workflow:

- Runs on Node.js 18.x and 20.x
- Installs dependencies
- Runs linting checks
- Runs all tests
- Builds the application
- Uploads build artifacts

The CI runs on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

## Project Structure

```
src/
├── App.jsx          # Main App component
├── App.css          # App styles
├── main.jsx         # React entry point
└── index.css        # Global styles
```