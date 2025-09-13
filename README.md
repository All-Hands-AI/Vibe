# OpenVibe

A modern React application built with Vite, featuring routing, theming, and Python serverless API integration for Vercel deployment.

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

## Features

- ⚛️ **React 19** with Vite for fast development
- 🎨 **Theme Context** with light/dark mode support
- 🧭 **React Router** for client-side navigation
- 🐍 **Python API** serverless functions for Vercel
- 🚀 **Vercel Ready** deployment configuration
- 📱 **Responsive Design** with modern CSS
- 🧪 **Testing Setup** with Vitest and React Testing Library

## Deployment to Vercel

This app is configured for seamless deployment to Vercel:

1. **Push to GitHub**: Ensure your code is in a GitHub repository
2. **Connect to Vercel**: Import your repository in the Vercel dashboard
3. **Deploy**: Vercel automatically detects the configuration and deploys

### Vercel Configuration

The app includes:
- `vercel.json` - Deployment configuration for React + Python
- `requirements.txt` - Python dependencies
- API endpoints in `/api/` directory

### API Endpoints

- `/api/hello` - Simple greeting endpoint with app info
- `/api/vibes` - Returns randomly generated mood/vibe data

Visit the **API Demo** page in the app to test these endpoints!

## Project Structure

```
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── Header.jsx       # Navigation header
│   │   └── Footer.jsx       # Site footer
│   ├── pages/               # Route components
│   │   ├── Home.jsx         # Landing page
│   │   ├── About.jsx        # About page
│   │   ├── Contact.jsx      # Contact page
│   │   └── ApiDemo.jsx      # API demonstration page
│   ├── context/             # React contexts
│   │   └── ThemeContext.jsx # Theme management
│   ├── test/                # Test utilities
│   ├── App.jsx              # Main App component with routing
│   ├── App.css              # Global app styles
│   ├── main.jsx             # React entry point
│   └── index.css            # Base styles
├── api/                     # Python serverless functions
│   ├── hello.py             # Greeting API endpoint
│   └── vibes.py             # Vibes data API endpoint
├── vercel.json              # Vercel deployment config
├── requirements.txt         # Python dependencies
└── vite.config.js           # Vite configuration
```

## Technology Stack

- **Frontend**: React 19, Vite, React Router, CSS3
- **Backend**: Python (serverless functions)
- **Deployment**: Vercel
- **Testing**: Vitest, React Testing Library
- **Development**: Hot reload, CORS enabled, responsive design