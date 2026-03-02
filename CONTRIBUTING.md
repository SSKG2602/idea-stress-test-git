# Contributing

Thanks for considering a contribution. This repo is open to bug fixes, docs improvements, tests, UI polish, and analysis quality improvements. If you are new to open source, small documentation fixes and reproducible bug reports are good places to start.

## Good First Contributions

- Clarify setup steps or fix missing documentation.
- Improve empty, loading, or error states in the frontend.
- Add backend or frontend test coverage.
- Tighten validation, error messages, or developer ergonomics.
- Reproduce a reported bug and reduce it to a small fix.

## Fork and Clone

1. Fork the repository on GitHub.
2. Clone your fork locally:

```bash
git clone <your-fork-url>
cd idea-stress-test
```

3. Add the original repository as `upstream` if you want to keep your fork updated:

```bash
git remote add upstream <original-repo-url>
```

## Local Development Setup

### Recommended: Docker Compose for Backend + DB

1. Copy the backend environment template:

```bash
cp backend/.env.example backend/.env
```

2. Add real values for `GROQ_API_KEY`, `SERPER_API_KEY`, and `SECRET_KEY`. Add `HF_TOKEN` if you have one.

3. Start the backend and local Postgres:

```bash
docker compose up --build
```

4. In a second terminal, start the frontend:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

5. Open `http://localhost:3001`.

### Alternative: Manual Backend Setup

If you are not using Docker Compose for the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
python main.py
```

In that mode, you need a real `DATABASE_URL` in `backend/.env`.

## Branch Naming

Use one of these prefixes:

- `feat/`
- `fix/`
- `docs/`

Examples:

- `feat/add-result-export`
- `fix/improve-error-handling`
- `docs/update-deployment-guide`

## Pull Requests

1. Create a branch from the latest `main`.
2. Keep the change focused on one fix, feature, or documentation improvement.
3. Run the relevant local checks before opening the PR.
4. Push your branch to your fork.
5. Open a pull request against `main`.
6. Include a short summary, testing notes, and screenshots for UI changes.

## Code Style

- Python: follow the existing FastAPI and service-layer patterns already used in the repo.
- TypeScript: follow the existing ESLint configuration and match current Next.js conventions.

## Reporting Bugs

Please use GitHub Issues for bugs, regressions, and setup problems. Good bug reports include:

- what you expected
- what happened instead
- exact steps to reproduce
- logs or screenshots if relevant

## Questions

If you are unsure where to start, contact sskg@syperith.com.
