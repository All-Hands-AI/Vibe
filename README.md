# 🤙 OpenHands Vibe

OpenHands Vibe is **opinionated vibecoding** for **professional developers**.

It's powered by
[OpenHands](https://github.com/All-Hands-AI/OpenHands), a state-of-the-art coding agent,
using its [agent SDK](https://github.com/All-Hands-AI/agent-sdk/). And, of course,
we use OpenHands Vibe to make OpenHands Vibe.


![screenshot](screenshot.png)


## Stack
* **GitHub** for source control and CI/CD
* **Fly.io** for deployments
* **React** for frontend
* **Python** for backend
* **Claude** for inference
* **OpenHands** for agents

## Workflow
When you create a new App, a corresponding GitHub repo will be created as well.
It will start from the [template repo](https://github.com/rbren/openvibe-template), which contains a hello world React + Python app,
plus a standardized dev setup.

Your first Riff (a change to the app) will be created automatically. It will make some required edits to the default template.
Once the agent has finished and pushed its work, you should be able to see a hello world app running inside the Riff!
You can go ahead and merge that PR.

Create a new Riff for every change you want to make. Preview the change on fly.io, and examine the code changes on GitHub.
Once you're happy, merge and start a new Riff!

You can easily have several Riffs going at once. The agent can figure out how to deal with minor conflicts.

## Configuration

### Agent Server Configuration

OpenHands Vibe uses a hybrid approach for running agents:
- **Docker Mode**: Runs agent containers locally when Docker is available
- **Remote Mode**: Connects to external agent server when Docker is not available

#### Environment Variables

- `AGENT_SERVER_IMAGE`: Docker image for agent containers (default: `ghcr.io/all-hands-ai/agent-server:ea72d20@sha256:39c72c4796bb30f8d08d4cefbe3aa48b49f96c26eae6e7d79c4a8190fd10865f`)
- `AGENT_SERVER_URL`: URL for remote agent server (default: `https://agent-server.all-hands.dev`)
- `FORCE_REMOTE_AGENT`: Set to `true` to force remote mode even when Docker is available
- `DOCKER_HOST`: Docker daemon socket (default: `unix:///var/run/docker.sock`)

#### Docker-in-Docker Support

For local development or environments that support Docker-in-Docker:
```bash
# Use default Docker mode
docker run -v /var/run/docker.sock:/var/run/docker.sock openvibe

# Or specify custom agent image
docker run -e AGENT_SERVER_IMAGE=ghcr.io/all-hands-ai/agent-server:latest openvibe
```

#### Remote Agent Mode

For cloud deployments where Docker-in-Docker is not available (like Fly.io):
```bash
# Force remote mode
export FORCE_REMOTE_AGENT=true
export AGENT_SERVER_URL=https://your-agent-server.com
```

The system automatically detects Docker availability and falls back to remote mode when needed.
