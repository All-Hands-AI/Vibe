# Automatic Initial Riff Creation Implementation

## Overview

This implementation adds automatic riff creation and initial message sending when a new app is created in OpenVibe.

## What happens when an app is created:

1. **App Creation**: User creates a new app via the `/api/apps` POST endpoint
2. **Slug Validation**: App slug is validated to ensure proper format (lowercase, numbers, hyphens only)
3. **GitHub Repository**: A GitHub repository is created from the template
4. **Fly.io App**: A Fly.io app is created (if possible)
5. **Automatic Riff Creation**: A new riff is automatically created with the name "rename-to-{app_slug}"
6. **Initial Message**: An initial user message is sent to the riff with instructions
7. **Agent Setup**: An agent is created for the riff and the initial message is sent to it

## Initial Message Content

The initial message sent to the agent contains:

```
Please follow the instructions in TEMPLATE.md to change the app name everywhere from the template name to "{app_name}". After making all the necessary changes, delete the TEMPLATE.md file and push your changes to the repository.
```

## Slug Validation

All slugs (app slugs and riff slugs) are now validated to ensure they:
- Contain only lowercase letters, numbers, and hyphens
- Do not start or end with hyphens
- Do not contain consecutive hyphens
- Are not empty

## Implementation Details

### Files Modified

- `backend/routes/apps.py`: Added automatic riff creation functionality and slug validation
- `backend/routes/riffs.py`: Added slug validation to riff creation

### New Functions Added

1. `is_valid_slug(slug)`: Validates slug format (added to both apps.py and riffs.py)
2. `save_user_riff(user_uuid, app_slug, riff_slug, riff_data)`: Saves riff data
3. `add_user_message(user_uuid, app_slug, riff_slug, message)`: Adds message to riff
4. `create_agent_for_riff(user_uuid, app_slug, riff_slug, github_url)`: Creates agent for riff
5. `create_initial_riff_and_message(user_uuid, app_slug, app_name, github_url)`: Main orchestration function

### Integration Point

The `create_app()` function now calls `create_initial_riff_and_message()` after the app is successfully saved but before returning the response.

## Error Handling

- If riff creation fails, it's logged as a warning but doesn't fail the app creation
- If agent creation fails (e.g., no Anthropic API key), the riff and message are still created
- If workspace setup fails, it's handled gracefully with appropriate error messages

## API Response Changes

The app creation response now includes:
- `warnings`: Array of any warnings (including riff creation failures)
- `initial_riff`: Information about the created riff (if successful)

## Requirements

- User must have GitHub and Fly.io API keys configured
- For agent functionality, user should have Anthropic API key configured
- The template repository should contain a TEMPLATE.md file with renaming instructions

## Testing

The implementation has been tested for:
- Syntax correctness
- Import compatibility  
- Code style compliance (black, flake8)
- Existing functionality preservation

## Future Considerations

- The template repository (`rbren/openvibe-template`) should be created with appropriate TEMPLATE.md instructions
- Consider adding configuration options to enable/disable automatic riff creation
- Consider making the initial message content configurable