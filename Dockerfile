# Multi-stage build for React frontend and Python backend
FROM node:18-alpine AS frontend-build

# Build React frontend
WORKDIR /app/frontend
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Python backend stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python server
COPY server/ ./

# Copy built frontend from previous stage
COPY --from=frontend-build /app/frontend/dist ./static

# Expose port
EXPOSE 8080

# Start the server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]