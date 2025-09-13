import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({
  origin: true, // Allow all origins for development
  credentials: true
}));
app.use(express.json());

// Store API keys in memory (in production, use secure storage)
const apiKeys = {
  anthropic: null,
  github: null,
  fly: null
};

// Validation functions for each service
async function validateAnthropicKey(apiKey) {
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-3-haiku-20240307',
        max_tokens: 1,
        messages: [{ role: 'user', content: 'test' }]
      })
    });
    
    // If we get a 200 or 400 (bad request but valid auth), the key is valid
    return response.status === 200 || response.status === 400;
  } catch (error) {
    console.error('Anthropic validation error:', error);
    return false;
  }
}

async function validateGitHubKey(apiKey) {
  try {
    const response = await fetch('https://api.github.com/user', {
      headers: {
        'Authorization': `token ${apiKey}`,
        'User-Agent': 'OpenVibe-App'
      }
    });
    
    return response.status === 200;
  } catch (error) {
    console.error('GitHub validation error:', error);
    return false;
  }
}

async function validateFlyKey(apiKey) {
  try {
    const response = await fetch('https://api.fly.io/v1/apps', {
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.status === 200;
  } catch (error) {
    console.error('Fly.io validation error:', error);
    return false;
  }
}

// Routes for Anthropic integration
app.post('/integrations/anthropic', async (req, res) => {
  const { apiKey } = req.body;
  
  if (!apiKey) {
    return res.status(400).json({ error: 'API key is required' });
  }
  
  const isValid = await validateAnthropicKey(apiKey);
  
  if (isValid) {
    apiKeys.anthropic = apiKey;
    res.json({ valid: true, message: 'Anthropic API key is valid' });
  } else {
    res.status(400).json({ valid: false, error: 'Invalid Anthropic API key' });
  }
});

app.get('/integrations/anthropic', async (req, res) => {
  if (!apiKeys.anthropic) {
    return res.status(400).json({ valid: false, error: 'No Anthropic API key set' });
  }
  
  const isValid = await validateAnthropicKey(apiKeys.anthropic);
  res.json({ valid: isValid });
});

// Routes for GitHub integration
app.post('/integrations/github', async (req, res) => {
  const { apiKey } = req.body;
  
  if (!apiKey) {
    return res.status(400).json({ error: 'API key is required' });
  }
  
  const isValid = await validateGitHubKey(apiKey);
  
  if (isValid) {
    apiKeys.github = apiKey;
    res.json({ valid: true, message: 'GitHub API key is valid' });
  } else {
    res.status(400).json({ valid: false, error: 'Invalid GitHub API key' });
  }
});

app.get('/integrations/github', async (req, res) => {
  if (!apiKeys.github) {
    return res.status(400).json({ valid: false, error: 'No GitHub API key set' });
  }
  
  const isValid = await validateGitHubKey(apiKeys.github);
  res.json({ valid: isValid });
});

// Routes for Fly.io integration
app.post('/integrations/fly', async (req, res) => {
  const { apiKey } = req.body;
  
  if (!apiKey) {
    return res.status(400).json({ error: 'API key is required' });
  }
  
  const isValid = await validateFlyKey(apiKey);
  
  if (isValid) {
    apiKeys.fly = apiKey;
    res.json({ valid: true, message: 'Fly.io API key is valid' });
  } else {
    res.status(400).json({ valid: false, error: 'Invalid Fly.io API key' });
  }
});

app.get('/integrations/fly', async (req, res) => {
  if (!apiKeys.fly) {
    return res.status(400).json({ valid: false, error: 'No Fly.io API key set' });
  }
  
  const isValid = await validateFlyKey(apiKeys.fly);
  res.json({ valid: isValid });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Get all integration status
app.get('/integrations/status', async (req, res) => {
  const status = {
    anthropic: apiKeys.anthropic ? await validateAnthropicKey(apiKeys.anthropic) : false,
    github: apiKeys.github ? await validateGitHubKey(apiKeys.github) : false,
    fly: apiKeys.fly ? await validateFlyKey(apiKeys.fly) : false
  };
  
  res.json(status);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Backend server running on port ${PORT}`);
});