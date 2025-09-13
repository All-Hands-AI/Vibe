# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the OpenVibe project.

## Workflows

### 🚀 `deploy.yml` - Main Deployment
- **Triggers**: Push to `main`, Pull Requests
- **Purpose**: Builds and deploys the application to Fly.io
- **Environments**:
  - **Production**: `openvibe` (main branch)
  - **Preview**: `openvibe-{branch-name}` (PRs and feature branches)

### 🧹 `cleanup-pr.yml` - PR Cleanup
- **Triggers**: When Pull Requests are closed
- **Purpose**: Automatically cleans up feature deployments when PRs are closed
- **Actions**:
  - Deletes the associated Fly.io app (`openvibe-{branch-name}`)
  - Posts a cleanup confirmation comment on the PR

### 🗑️ `cleanup-cron.yml` - Scheduled Cleanup
- **Triggers**: 
  - Daily at 2 AM UTC (cron schedule)
  - Manual dispatch with configurable parameters
- **Purpose**: Cleans up old feature deployments that may have been missed
- **Features**:
  - Configurable maximum age (default: 7 days)
  - Dry run mode for testing
  - Detailed cleanup reports via GitHub issues
  - Safe filtering (only deletes `openvibe-*` apps, never the main `openvibe` app)

## Manual Cleanup

You can manually trigger the cleanup workflow with custom parameters:

1. Go to the **Actions** tab in your repository
2. Select **"Cleanup Old Deployments"**
3. Click **"Run workflow"**
4. Configure options:
   - **Max age**: How old deployments should be before deletion (default: 7 days)
   - **Dry run**: Preview what would be deleted without actually deleting

## App Naming Convention

Feature deployments follow this naming pattern:
- **Main app**: `openvibe`
- **Feature apps**: `openvibe-{clean-branch-name}`

The branch name cleaning logic:
1. Removes "github" (case insensitive)
2. Converts to lowercase
3. Replaces non-alphanumeric characters with hyphens
4. Removes consecutive/leading/trailing hyphens
5. Ensures it doesn't start with a number
6. Truncates to fit Fly.io's 63-character limit
7. Falls back to "feature" if empty

## Shared Scripts

### `scripts/get-app-name.sh`
Reusable script that generates clean Fly.io app names from branch names. Used by multiple workflows to ensure consistent naming.

**Usage:**
```bash
./.github/scripts/get-app-name.sh "feature/add-new-component"
# Output: openvibe-feature-add-new-component
```

## Security

- All workflows use the `FLY_API_TOKEN` secret for Fly.io authentication
- PR cleanup only runs for PRs from the same repository (prevents cleanup from forks)
- Cron cleanup has safety checks to prevent accidental deletion of the main app
- Workflows follow the principle of least privilege with minimal required permissions

## Monitoring

- PR cleanup posts status comments on closed PRs
- Cron cleanup creates GitHub issues with detailed reports
- All workflows link to their respective workflow runs for debugging
- Failed operations are logged and reported