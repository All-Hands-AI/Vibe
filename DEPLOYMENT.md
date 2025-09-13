# Deployment Setup

This repository is configured with automated deployments to Fly.io using GitHub Actions.

## How it works

### Production Deployments
- **Trigger**: Push/merge to `main` branch
- **Environment**: Production (`openvibe.fly.dev`)
- **Behavior**: Deploys directly to the main production app

### Feature/Preview Deployments
- **Trigger**: Pull requests and commits to feature branches
- **Environment**: Feature-specific preview environment
- **Naming**: `openvibe-{branch-name}.fly.dev`
- **Behavior**: 
  - Creates a unique Fly.io app for each branch
  - Comments on PR with deployment link (like Vercel)
  - Automatically cleans up when PR is closed

## Setup Instructions

### 1. Fly.io Setup
1. Install the Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up/login: `flyctl auth signup` or `flyctl auth login`
3. Create your production app: `flyctl apps create openvibe`
4. Get your API token: `flyctl auth token`

### 2. GitHub Secrets
Add the following secret to your GitHub repository:

- `FLY_API_TOKEN`: Your Fly.io API token from step 1.4

**To add secrets:**
1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add `FLY_API_TOKEN` with your token value

### 3. First Deployment
The workflow will automatically deploy when you:
- Push to `main` (production deployment)
- Open a PR (preview deployment)

## Features

### 🚀 Automatic Deployments
- Production deployments on merge to main
- Preview deployments for every PR
- Automatic cleanup of preview environments

### 💬 PR Comments
- Deployment status updates
- Direct links to preview environments
- Build and deployment information

### 🧹 Cleanup
- Automatic cleanup of preview apps when PRs are closed
- No manual intervention required

## Workflow Details

The deployment workflow:
1. **Build**: Installs dependencies, runs tests, builds the app
2. **Volume Setup**: Creates required data volumes if they don't exist
3. **Deploy**: Deploys to appropriate environment (prod/preview)
4. **Comment**: Updates PR with deployment status and links
5. **Cleanup**: Removes preview environments when PRs close

## Troubleshooting

### Common Issues

**Deployment fails with "app not found"**
- Ensure the production app `openvibe` exists in your Fly.io account
- Check that `FLY_API_TOKEN` is correctly set in GitHub secrets

**Preview deployments fail**
- Verify your Fly.io account has sufficient resources
- Check the workflow logs for specific error messages

**PR comments not appearing**
- Ensure the GitHub token has proper permissions
- Check that the workflow has completed successfully

**Volume-related deployment failures**
- The workflow automatically creates required volumes (`data_volume`)
- If volumes already exist, the creation step is safely ignored
- Volumes are created in the `ewr` region with 2 instances for redundancy

### Manual Commands

**Deploy manually:**
```bash
flyctl deploy --remote-only
```

**Check app status:**
```bash
flyctl status -a openvibe
```

**View logs:**
```bash
flyctl logs -a openvibe
```

**List all apps:**
```bash
flyctl apps list
```

**Create volumes manually:**
```bash
flyctl volume create data_volume -r ewr -n 2 -a openvibe
```