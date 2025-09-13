# Setup Window Feature

## Overview

The Setup Window is a mandatory configuration screen that appears when users first access OpenVibe or when any of the required API keys are missing or invalid. It ensures that all necessary integrations are properly configured before allowing access to the main application.

## Features

### 🔐 Required API Keys
- **Anthropic API Key**: For AI/ML functionality
- **GitHub API Key**: For repository integrations
- **Fly.io API Key**: For deployment and infrastructure management

### ✨ User Experience
- **Modal overlay**: Cannot be closed until all keys are valid
- **Real-time validation**: Keys are validated as soon as they're entered
- **Visual feedback**: Clear status indicators (✅ valid, ❌ invalid, ⏳ validating)
- **Helpful links**: Direct links to obtain each API key
- **Responsive design**: Works on desktop and mobile devices
- **Dark/light theme support**: Matches the application theme

### 🔄 Validation Flow
1. User enters an API key
2. On blur (when they click away), the key is sent to the backend for validation
3. Backend makes a test API call to verify the key works
4. Status is displayed immediately with appropriate messaging
5. Continue button is only enabled when all three keys are valid

## Technical Implementation

### Frontend Components

#### `SetupWindow.jsx`
- Main setup window component
- Handles user input and validation states
- Communicates with backend API for key validation
- Prevents app access until setup is complete

#### `SetupContext.jsx`
- React context for managing setup state across the app
- Checks setup status on app initialization
- Provides setup completion methods

#### `App.jsx` (Modified)
- Conditionally renders setup window or main app
- Shows loading screen while checking setup status

### Backend API Endpoints

#### `POST /integrations/{provider}`
Validates and stores an API key for a specific provider.

**Parameters:**
- `provider`: One of `anthropic`, `github`, or `fly`
- Request body: `{"api_key": "your-key-here"}`

**Response:**
```json
{
  "valid": true,
  "message": "Anthropic API key is valid"
}
```

#### `GET /integrations/{provider}`
Checks if an API key is set and valid for a provider.

**Response:**
```json
{
  "valid": false,
  "message": "GitHub API key not set"
}
```

### Validation Methods

#### Anthropic API Key Validation
- Makes a test request to `https://api.anthropic.com/v1/messages`
- Uses Claude-3-Haiku model with minimal token request
- Validates API key format and permissions

#### GitHub API Key Validation
- Makes a test request to `https://api.github.com/user`
- Validates token has basic user access permissions
- Supports both classic and fine-grained personal access tokens

#### Fly.io API Key Validation
- Makes a test request to `https://api.fly.io/v1/apps`
- Validates token has basic app listing permissions
- Supports organization and personal access tokens

## Security Considerations

### API Key Storage
- **Development**: Keys stored in memory (lost on restart)
- **Production**: Should use secure storage (environment variables, secrets manager)
- Keys are never logged or exposed in client-side code

### Validation Security
- All validation happens server-side
- Minimal API calls to reduce quota usage
- Timeout protection (10 seconds max per validation)
- Error handling prevents information leakage

## Configuration

### Environment Variables
```bash
# Backend URL configuration
NODE_ENV=production  # Uses relative URLs in production
NODE_ENV=development # Uses http://localhost:8000 in development
```

### Nginx Configuration
The setup window requires the `/integrations/` endpoint to be proxied to the backend:

```nginx
location /integrations/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

## Testing

### Frontend Tests
- `SetupWindow.test.jsx`: Comprehensive component testing
- Tests validation flow, UI states, and user interactions
- Mocks backend API calls for reliable testing

### Backend Tests
- API endpoint validation
- Error handling scenarios
- Security boundary testing

### Integration Tests
- End-to-end setup flow
- Cross-browser compatibility
- Mobile responsiveness

## Usage Examples

### Getting API Keys

#### Anthropic API Key
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-`)

#### GitHub API Key
1. Visit [GitHub Settings > Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token"
3. Select appropriate scopes (minimum: `read:user`)
4. Generate and copy the token (starts with `ghp_`)

#### Fly.io API Key
1. Visit [Fly.io Personal Access Tokens](https://fly.io/user/personal_access_tokens)
2. Create a new token
3. Set appropriate permissions
4. Copy the token (starts with `fo1_`)

## Troubleshooting

### Common Issues

#### "API key is invalid" Error
- Verify the key is copied correctly (no extra spaces)
- Check that the key has appropriate permissions
- Ensure the key hasn't expired
- Verify network connectivity

#### Setup Window Won't Disappear
- All three API keys must be valid
- Check browser console for network errors
- Verify backend is running and accessible
- Clear browser cache if needed

#### Validation Takes Too Long
- Check network connectivity
- Verify API service status
- Backend has 10-second timeout protection

### Debug Mode
Enable debug logging by setting `DEBUG=true` in the backend environment.

## Future Enhancements

### Planned Features
- [ ] API key encryption at rest
- [ ] Key rotation workflow
- [ ] Usage monitoring and quotas
- [ ] Bulk key validation
- [ ] Setup wizard with guided steps
- [ ] Key testing with sample operations

### Potential Integrations
- [ ] Additional AI providers (OpenAI, Google)
- [ ] Cloud providers (AWS, Azure, GCP)
- [ ] Development tools (Docker, Kubernetes)
- [ ] Monitoring services (DataDog, New Relic)

## Contributing

When modifying the setup window:

1. Update tests for any new functionality
2. Ensure backward compatibility
3. Test with real API keys in development
4. Update documentation for new providers
5. Consider security implications of changes

## License

This feature is part of the OpenVibe project and follows the same licensing terms.