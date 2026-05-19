# TOOLS AND STACKS

This file lists what Genie workers must check for future projects.

## Project Types

JavaScript projects usually have package.json.

React projects usually have src/App.jsx or src/App.tsx.

Vite projects usually have vite.config.js or vite.config.ts.

Next projects usually have next.config.js or next.config.mjs.

Python projects usually have requirements.txt, pyproject.toml, app.py, main.py, or server.py.

FastAPI projects usually have requirements.txt with fastapi and a server.py or main.py file.

Django projects usually have manage.py.

Static web projects usually have index.html.

Docker projects usually have Dockerfile, docker-compose.yml, or compose.yaml.

Full stack projects often have frontend and backend folders.

## Common Ports

Frontend dev servers often use 5173, 5174, 3000, or 8080.

Backend APIs often use 8000, 5000, or 3001.

Use the exact URL printed by the tool running the project.

## Required Tools

Git.
Node.js.
npm.
Python 3.
pip.
Docker when a Dockerfile or compose file exists.
VS Code for editing.

## Worker Rule

If a command is missing, identify the missing tool first. Do not rebuild the project.
