# GitHub Actions Workflows

This directory contains the GitHub Actions workflows for the OpenVibe project.

## Workflows

### Core Workflows

#### 🚀 `deploy.yml` - Main Deployment
- **Triggers**: Push to `main`, Pull Requests
- **Purpose**: Builds and deploys the application to Fly.io
- **Environments**:
  - **Production**: `openvibe` (main branch)
  - **Preview**: `openvibe-{branch-name}` (PRs and feature branches)
- **PR Updates**: Adds deployment status and preview URL to PR description

#### 🧹 `cleanup-pr.yml` - PR Cleanup
- **Triggers**: When Pull Requests are closed
- **Purpose**: Automatically cleans up feature deployments when PRs are closed
- **Actions**:
  - Deletes the associated Fly.io app (`openvibe-{branch-name}`)
  - Updates PR description with cleanup confirmation

#### 🔄 `ci.yml` - Continuous Integration
- **Triggers**: Pull Requests
- **Purpose**: Orchestrates all tests and checks
- **Actions**: Runs frontend/backend linting, unit tests, and E2E tests

### Test Workflows

#### 🎨 `frontend-lint.yml` & `frontend-tests.yml`
- **Purpose**: Frontend code quality and testing
- **Actions**: ESLint linting, Vitest testing with coverage
- **PR Updates**: Adds frontend test results and coverage to PR description

#### 🐍 `backend-lint.yml`, `backend-tests.yml`, & `backend-e2e-tests.yml`
- **Purpose**: Backend code quality and testing
- **Actions**: Black/Flake8/MyPy linting, pytest unit tests, E2E tests in mock mode
- **PR Updates**: Adds backend test results and coverage to PR description

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

### `scripts/update-pr-description.js`
Shared utility for updating PR descriptions idempotently. Each workflow can add or update its own section without affecting others.

**Features:**
- Uses HTML comment markers to identify sections
- Preserves existing PR description content
- Allows independent updates from multiple workflows
- Prevents duplicate sections

## Security

- All workflows use the `FLY_API_TOKEN` secret for Fly.io authentication
- PR cleanup only runs for PRs from the same repository (prevents cleanup from forks)
- Cron cleanup has safety checks to prevent accidental deletion of the main app
- Workflows follow the principle of least privilege with minimal required permissions

## PR Description Updates

Instead of posting comments on PRs, our workflows now update the PR description with status information. This provides a cleaner, more organized view of CI/CD status directly in the PR description.

### How It Works

Each workflow that needs to report status uses the shared script `.github/scripts/update-pr-description.js` to add or update sections in the PR description. Each section is:

- **Idempotent**: Running the same workflow multiple times will update the existing section rather than creating duplicates
- **Independent**: Each workflow manages its own section without affecting others
- **Persistent**: Information stays visible in the PR description rather than being buried in comments

### Sections Added to PR Descriptions

When a PR is created or updated, you'll see these sections automatically added to the bottom of the PR description:

1. **🚀 Deployment Status** - Shows preview deployment URL and management links
2. **✅ Frontend Tests** - Frontend test results and coverage information
3. **✅ Backend Unit Tests** - Backend unit test results and coverage
4. **🧪 Backend E2E Tests** - End-to-end test results and coverage
5. **🧹 Deployment Cleanup** - Confirmation when preview deployments are cleaned up (added when PR is closed)

## Monitoring

- PR descriptions are updated with status information from all workflows
- Cron cleanup creates GitHub issues with detailed reports
- All workflows link to their respective workflow runs for debugging
- Failed operations are logged and reported