# Idea Stress-Test Engine

Idea Stress-Test Engine is an open-source web app that takes a business idea and returns structured feedback on market demand, competition, monetization, audit confidence, and downside risk. The frontend is built with Next.js, the backend is built with FastAPI, and the analysis pipeline combines Groq-powered agents with live search results from Serper. You can run it locally without Google Cloud; Cloud Run deployment is optional.

## Live Demo

https://bit.ly/idea-stress

## Quick Start

This is the fastest path for a first-time user. It runs the backend and Postgres with Docker Compose, then runs the frontend locally with Next.js.

1. Clone the repository:

```bash
git clone https://github.com/SSKG2602/idea-stress-test.git
cd idea-stress-test
```

2. Make sure you have these tools installed:
   - Docker Desktop
   - Node.js 20.x

3. Create the backend env file:

```bash
cp backend/.env.example backend/.env
```

4. Edit `backend/.env` and set these values:
   - `GROQ_API_KEY`
   - `SERPER_API_KEY`
   - `SECRET_KEY`
   - `HF_TOKEN` (recommended; helps avoid Hugging Face rate limits when the model is downloaded)

   If you are using the Docker Compose quick start, you do not need to set `DATABASE_URL` to a hosted database. Docker Compose overrides it and starts a local Postgres container for you.

5. Start the backend and local Postgres from the repo root:

```bash
docker compose up --build
```

6. In a second terminal, start the frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

7. Open the app:
   - Frontend: `http://localhost:3001`
   - Backend API: `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`

## What You Need

### Required Accounts and Keys

For the local quick start, you need:

| Service | Why it is needed | Where to get it |
|---|---|---|
| Groq API key | Runs the LLM agents | https://console.groq.com/keys/ |
| Serper API key | Fetches live search results | https://serper.dev/ |
| Secret key | Signs backend sessions and security-sensitive values | Generate any long random string locally |

Recommended:

| Service | Why it helps | Where to get it |
|---|---|---|
| Hugging Face token | Reduces model download/auth friction for the embedding model | https://huggingface.co/settings/tokens |

Advanced or non-Docker backend setup:

| Service | Why it is needed | Where to get it |
|---|---|---|
| Postgres connection string | Required if you are not using Docker Compose for the database | https://supabase.com/docs/reference/postgres/connection-strings |

## Tech Stack

- FastAPI
- Next.js
- Groq
- Serper
- Supabase
- Docker
- Google Cloud Run

## Architecture

```text
User in browser
   |
   v
Next.js frontend (port 3001)
   |
   | HTTP requests using NEXT_PUBLIC_API_URL
   v
FastAPI backend (port 8000)
   |
   +--> Query generator
   +--> Serper search API
   +--> Groq-backed analysis agents
   +--> Audit and scoring pipeline
   +--> Postgres database
   +--> Local embedding model cache

Returned output
   -> structured analysis
   -> viability score
   -> market / competition / monetization / failure results
```

## Local Development

### Recommended Path: Docker Compose + Local Frontend

Use this if you want the easiest setup.

- `docker compose up --build` starts:
  - the FastAPI backend
  - a local Postgres container
- `npm run dev` inside `frontend/` starts the Next.js app

Important: `docker compose` does not start the frontend. You still need the second terminal for `frontend/`.

### Alternative Path: Run the Backend Without Docker

Use this only if you want to manage Python and Postgres yourself.

1. Create a Python virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
```

2. Install backend dependencies:

```bash
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
```

3. Set a real `DATABASE_URL` in `backend/.env`.

4. Start the backend:

```bash
python main.py
```

5. Start the frontend in a separate terminal:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## Deployment

Local development does not require Google Cloud. If you want to deploy this project to Google Cloud Run, follow [DEPLOYMENT.md](./DEPLOYMENT.md).

## Contributing

Contributions are welcome. For fork, branch, and pull request steps, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE).

## Built By
Built by Shreyas Gowda (https://www.linkedin.com/in/shreyasshashi/) — open to feedback, collaboration, and contributions.
Contact: sskg@syperith.com
