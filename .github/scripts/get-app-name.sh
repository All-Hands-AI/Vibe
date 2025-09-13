#!/bin/bash

# Script to generate a clean Fly.io app name from a branch name
# Usage: ./get-app-name.sh <branch_name>

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <branch_name>"
    exit 1
fi

branch_name="$1"

# Strip "github" from branch name (case insensitive)
branch_name=$(echo "$branch_name" | sed 's/github//gi')

# Convert to lowercase
clean_branch=$(echo "$branch_name" | tr '[:upper:]' '[:lower:]')

# Replace any non-alphanumeric characters with hyphens
clean_branch=$(echo "$clean_branch" | sed 's/[^a-z0-9]/-/g')

# Remove multiple consecutive hyphens
clean_branch=$(echo "$clean_branch" | sed 's/-\+/-/g')

# Remove leading and trailing hyphens
clean_branch=$(echo "$clean_branch" | sed 's/^-\+\|-\+$//g')

# Ensure it doesn't start with a number (Fly.io requirement)
if [[ "$clean_branch" =~ ^[0-9] ]]; then
  clean_branch="br-$clean_branch"
fi

# Truncate to 25 chars to leave room for "openvibe-" prefix (Fly.io 63 char limit)
clean_branch=$(echo "$clean_branch" | cut -c1-25)

# Remove trailing hyphen if truncation created one
clean_branch=$(echo "$clean_branch" | sed 's/-$//')

# Ensure we have a valid name (fallback if empty)
if [[ -z "$clean_branch" ]]; then
  clean_branch="feature"
fi

# Output the full app name
echo "openvibe-$clean_branch"