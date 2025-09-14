/**
 * GitHub Action script to update PR descriptions idempotently
 * 
 * This script allows GitHub Actions to add or update sections in PR descriptions
 * instead of creating comments. Each section is identified by a unique marker
 * and can be updated independently.
 * 
 * Usage:
 *   updatePRDescription(github, context, sectionId, content)
 * 
 * Parameters:
 *   - github: GitHub API client
 *   - context: GitHub Actions context
 *   - sectionId: Unique identifier for this section (e.g., 'deployment', 'coverage')
 *   - content: The content to add/update in this section
 */

async function updatePRDescription(github, context, sectionId, content) {
  // Get the current PR
  const { data: pr } = await github.rest.pulls.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: context.issue.number,
  });

  const currentBody = pr.body || '';
  
  // Define section markers
  const startMarker = `<!-- GITHUB_ACTION_${sectionId.toUpperCase()}_START -->`;
  const endMarker = `<!-- GITHUB_ACTION_${sectionId.toUpperCase()}_END -->`;
  
  // Create the new section content
  const newSection = `${startMarker}\n${content}\n${endMarker}`;
  
  let newBody;
  
  // Check if the section already exists
  const startIndex = currentBody.indexOf(startMarker);
  const endIndex = currentBody.indexOf(endMarker);
  
  if (startIndex !== -1 && endIndex !== -1) {
    // Section exists, replace it
    const beforeSection = currentBody.substring(0, startIndex);
    const afterSection = currentBody.substring(endIndex + endMarker.length);
    newBody = beforeSection + newSection + afterSection;
  } else {
    // Section doesn't exist, add it at the end
    const separator = currentBody.trim() ? '\n\n---\n\n' : '';
    newBody = currentBody + separator + newSection;
  }
  
  // Update the PR description
  await github.rest.pulls.update({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: context.issue.number,
    body: newBody,
  });
  
  console.log(`Updated PR description section: ${sectionId}`);
}

// Export for use in GitHub Actions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { updatePRDescription };
}

// Make available globally for GitHub Actions script context
if (typeof global !== 'undefined') {
  global.updatePRDescription = updatePRDescription;
}