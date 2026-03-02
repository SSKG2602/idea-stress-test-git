# DEPLOYMENT.md — Google Cloud Run Deployment Guide

This project is designed to run on Google Cloud Run.

## Target Deployment Shape

| Item | Value |
|---|---|
| GCP project | `YOUR_PROJECT_ID` |
| Region | `us-central1` |
| Backend service | `idea-stress-backend` |
| Backend URL | `https://YOUR_BACKEND_SERVICE_URL` |
| Frontend service | `idea-stress-frontend` |
| Frontend URL | `https://YOUR_FRONTEND_SERVICE_URL` |
| Artifact Registry repo | `us-central1-docker.pkg.dev/YOUR_PROJECT_ID/idea-stress-test/` |
| Database | Supabase via `DATABASE_URL` |
| LLM provider | Groq |
| Search provider | Serper |

## Runtime Settings

### Backend (`idea-stress-backend`)

- Memory: `1Gi`
- CPU: `1`
- Cloud Run concurrency: `4`
- Min instances: `0`
- Max instances: `3`
- Timeout: `180s`
- Startup CPU boost: enabled
- Runtime env highlights:
  - `APP_ENV=production`
  - `MAX_CONCURRENT_ANALYSES=2`
  - `ANALYSIS_TIMEOUT_SECONDS=120`
  - `HF_HOME=/app/hf_cache`

### Frontend (`idea-stress-frontend`)

- Memory: `256Mi`
- CPU: `1`
- Min instances: `0`
- Max instances: `3`
- Timeout: `60s`

## Required Secrets

Store these in Google Cloud Secret Manager:

- `GROQ_API_KEY`
- `SERPER_API_KEY`
- `DATABASE_URL`
- `SECRET_KEY`
- `HF_TOKEN`

`HF_TOKEN` is required in production because unauthenticated Hugging Face requests from GCP IP space can be rate-limited.

## Important Deployment Facts

- Hosting is Google Cloud Run, not Render or Vercel.
- Supabase stays unchanged; Cloud Run connects over the public Postgres connection string in `DATABASE_URL`.
- The backend Docker image pre-downloads `all-MiniLM-L6-v2` at build time.
- `HF_HOME=/app/hf_cache` is set so runtime uses the baked cache path.
- Frontend builds must receive `NEXT_PUBLIC_API_URL` as a Docker build arg.
- `cloudbuild.yaml` exists, but GitHub trigger automation may still need to be connected in your GCP project.

## 1. Prerequisites

Install and authenticate the standard tools:

```bash
gcloud version
docker version
node -v
python3 --version

gcloud auth login
gcloud auth application-default login
```

Recommended local versions from the repo:

- Node.js `20.x`
- Python `3.11`

## 2. One-Time GCP Setup

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1

gcloud config set project "$PROJECT_ID"

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com

gcloud artifacts repositories create idea-stress-test \
  --repository-format=docker \
  --location="$REGION"

gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

If the Artifact Registry repo already exists, the create command will fail harmlessly; skip it.

## 3. Create or Update Secrets

Create each secret once, then add new versions when rotating values.

```bash
export PROJECT_ID=YOUR_PROJECT_ID

echo -n 'your_groq_api_key' | \
  gcloud secrets create GROQ_API_KEY --data-file=-

echo -n 'your_serper_api_key' | \
  gcloud secrets create SERPER_API_KEY --data-file=-

echo -n 'postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres' | \
  gcloud secrets create DATABASE_URL --data-file=-

echo -n 'your-long-random-secret-key' | \
  gcloud secrets create SECRET_KEY --data-file=-

echo -n 'your_huggingface_token' | \
  gcloud secrets create HF_TOKEN --data-file=-
```

To rotate an existing secret:

```bash
echo -n 'new_value' | gcloud secrets versions add SECRET_NAME --data-file=-
```

Grant Secret Manager access to Cloud Build and the default Cloud Run runtime service account:

```bash
export PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 4. Database

Supabase remains the production database.

- No Cloud SQL migration exists.
- No proxy is used.
- The backend connects directly with `DATABASE_URL`.
- Use the async SQLAlchemy URL format:
  - `postgresql+asyncpg://postgres:[password]@db.[ref].supabase.co:5432/postgres`

If the password contains reserved URL characters like `@` or `$`, percent-encode them before storing `DATABASE_URL`.

Apply migrations in Supabase SQL Editor if bringing up a fresh environment:

1. Run `backend/migrations/001_initial_schema.sql`
2. Run `backend/migrations/002_usage_and_limits.sql`

## 5. Build the Backend Image on GCP

Do not build the production image on an Apple Silicon Mac if you plan to run it on Cloud Run. Local M1/M2 Docker builds default to ARM images; Cloud Run needs an AMD64-compatible image. Use Cloud Build.

Current working backend tag: `backend:v3`

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1
export BACKEND_IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/idea-stress-test/backend:v3

gcloud builds submit ./backend \
  --project="$PROJECT_ID" \
  --tag="$BACKEND_IMAGE"
```

Why this works:

- Cloud Build runs on GCP builders instead of your Mac.
- The backend Dockerfile already bakes `all-MiniLM-L6-v2` into the image.
- `HF_HOME=/app/hf_cache` keeps the cached model path stable at runtime.

## 6. Deploy the Backend to Cloud Run

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1
export BACKEND_IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/idea-stress-test/backend:v3

gcloud run deploy idea-stress-backend \
  --project="$PROJECT_ID" \
  --image="$BACKEND_IMAGE" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --concurrency=4 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=180 \
  --cpu-boost \
  --set-secrets=GROQ_API_KEY=GROQ_API_KEY:latest,SERPER_API_KEY=SERPER_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,HF_TOKEN=HF_TOKEN:latest \
  --set-env-vars='APP_ENV=production,MAX_CONCURRENT_ANALYSES=2,ANALYSIS_TIMEOUT_SECONDS=120,HF_HOME=/app/hf_cache'
```

Set CORS after frontend deploy. On macOS zsh, keep the whole value in single quotes because the brackets are otherwise interpreted by the shell:

```bash
gcloud run services update idea-stress-backend \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --update-env-vars='ALLOWED_ORIGINS=["https://YOUR_FRONTEND_SERVICE_URL"]'
```

Notes:

- Use the frontend Cloud Run URL in `ALLOWED_ORIGINS`.
- If you use a redirect layer or custom domain, the browser origin still needs to match the actual deployed frontend origin.

Verify backend:

```bash
curl https://YOUR_BACKEND_SERVICE_URL/api/v1/health
```

Expected response:

```json
{"status":"ok","model_loaded":true,"env":"production"}
```

## 7. Build the Frontend Image on GCP

The frontend must be built on GCP as well, because:

- Apple Silicon local Docker builds produce ARM images by default.
- `NEXT_PUBLIC_API_URL` must be injected at build time.

Use a small temporary Cloud Build config so Docker can receive the build arg:

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1
export BACKEND_URL=https://YOUR_BACKEND_SERVICE_URL
export FRONTEND_IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/idea-stress-test/frontend:v1

cat > /tmp/cloudbuild.frontend.yaml <<'YAML'
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - build
      - -t
      - us-central1-docker.pkg.dev/$PROJECT_ID/idea-stress-test/frontend:v1
      - --build-arg
      - NEXT_PUBLIC_API_URL=https://YOUR_BACKEND_SERVICE_URL
      - .
images:
  - us-central1-docker.pkg.dev/$PROJECT_ID/idea-stress-test/frontend:v1
YAML

gcloud builds submit ./frontend \
  --project="$PROJECT_ID" \
  --config=/tmp/cloudbuild.frontend.yaml
```

If you change the backend URL in the future, rebuild the frontend image. Next.js public env vars are compiled into the client bundle.

## 8. Deploy the Frontend to Cloud Run

```bash
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=us-central1
export FRONTEND_IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/idea-stress-test/frontend:v1

gcloud run deploy idea-stress-frontend \
  --project="$PROJECT_ID" \
  --image="$FRONTEND_IMAGE" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=256Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=60
```

Frontend URL:

- `https://YOUR_FRONTEND_SERVICE_URL`

## 9. Manual Deployment Flow

1. Build backend on GCP with `gcloud builds submit`
2. Deploy backend manually with `gcloud run deploy`
3. Build frontend on GCP with `NEXT_PUBLIC_API_URL` baked in
4. Deploy frontend manually with `gcloud run deploy`
5. Update backend `ALLOWED_ORIGINS` if frontend origin changes

`cloudbuild.yaml` exists in the repo, but GitHub trigger setup depends on your GCP configuration.

## 10. Verify End-to-End

Backend health:

```bash
curl https://YOUR_BACKEND_SERVICE_URL/api/v1/health
```

Example analysis request:

```bash
curl -X POST https://YOUR_BACKEND_SERVICE_URL/api/v1/analyze \
  -H 'Content-Type: application/json' \
  -H 'X-Device-Id: test-device-001' \
  -d '{"idea":"A B2B SaaS tool that automates invoice reconciliation for small accounting firms.","tier":"free"}'
```

Open the live frontend:

```bash
open https://YOUR_FRONTEND_SERVICE_URL
```

## 11. CI/CD Status

- `cloudbuild.yaml` is in the repo
- GitHub trigger setup is optional and environment-specific
- Production deploys can be manual until CI/CD is fully wired

When wiring CI/CD later:

1. Connect the GitHub repo in Cloud Build
2. Make sure the live backend URL is the one passed into the frontend build
3. Verify `cloudbuild.yaml` matches the live Cloud Run settings before enabling auto-deploy

## 12. Local Development

Local development is unchanged.

```bash
cp backend/.env.example backend/.env
docker compose up
```

Frontend local env:

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Default local ports from the repo:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3001`

## 13. Lessons Learned During Deployment

- Apple Silicon Macs build ARM images by default; use `gcloud builds submit` for production images.
- Hugging Face requests from GCP can hit anonymous rate limits; keep `HF_TOKEN` in Secret Manager even though the model is baked into the image.
- `NEXT_PUBLIC_API_URL` must be provided during Docker build for the Next.js frontend.
- On macOS zsh, wrap env var values containing brackets in single quotes, especially `ALLOWED_ORIGINS=[...]`.

## 14. Common Issues

| Problem | Fix |
|---|---|
| Backend starts but model load fails | Confirm `HF_HOME=/app/hf_cache` is set and the image was built from the backend Dockerfile that pre-downloads the model |
| Backend unexpectedly tries to reach Hugging Face | Verify `HF_TOKEN` is present in Secret Manager and injected via `--set-secrets` |
| Frontend points at localhost in production | Rebuild the frontend image with `NEXT_PUBLIC_API_URL=https://YOUR_BACKEND_SERVICE_URL` |
| Cloud Run revision works locally but fails in prod after Mac build | Rebuild on GCP with `gcloud builds submit` |
| `/analyze` fails immediately with DB connection errors | Verify Supabase connection string uses `postgresql+asyncpg://` and percent-encode reserved password characters |
| Browser shows CORS errors | Update backend `ALLOWED_ORIGINS` to the exact frontend Cloud Run origin using single quotes in zsh |
