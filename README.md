# 🤙 OpenHands Vibe

OpenHands Vibe is an extremely opinionated vibecoding framework, oriented towards professional developers.

## Stack
* React for frontend
* Python for backend
* GitHub for source control
* GitHub Actions for CI/CD
* Fly.io for deployments
* Claude for the LLM
* OpenHands for the agents

## Workflow
When you create a new App, a corresponding GitHub repo will be created as well. It will start from the [template repo](https://github.com/rbren/openvibe-template)

Your first Riff (a change to the app) will be created automatically. It will do some renaming and bootstrapping from the default template.
Once the agent has finished and pushed its work, you should be able to see a hello world app running inside the Riff! You can go ahead and merge
that PR.

Create a new Riff for every change you want to make. Preview the change on fly.io, and examine the code changes on GitHub.
Once you're happy, merge and start a new Riff!

You can easily have several Riffs going at once. The agent can figure out how to deal with minor conflicts.
