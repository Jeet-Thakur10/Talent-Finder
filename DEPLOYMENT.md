# Talent Finder GCP Deployment Guide

This document is the official deployment guide for the Talent Finder production system. Follow these step-by-step instructions to rebuild, push, and deploy services to Google Cloud Platform (GCP) Cloud Run.

---

## 1. Prerequisites

Before performing any deployments, ensure your local machine is properly set up:

*   **Docker**: Install and run Docker Desktop.
*   **Google Cloud SDK (gcloud)**: Install the GCP CLI.
*   **Authentication**: Authenticate your CLI session:
    ```powershell
    gcloud.cmd auth login
    ```
*   **Artifact Registry Login**: Configure Docker to use Google Cloud credentials for pushing images to Artifact Registry:
    ```powershell
    gcloud.cmd auth configure-docker us-east1-docker.pkg.dev
    ```
*   **Required Permissions**: Ensure your GCP user account or service principal has the following IAM roles:
    *   Cloud Run Admin (`roles/run.admin`)
    *   Artifact Registry Writer (`roles/artifactregistry.writer`)
    *   Service Account User (`roles/iam.serviceAccountUser`)
    *   Secret Manager Accessor (`roles/secretmanager.secretAccessor`)

---

## 2. Project Information

*   **GCP Project ID**: `gwx-internship-2026-01`
*   **Region**: `us-east1`
*   **Artifact Registry Repository**: `us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01`
*   **VPC Connector**: `gwx-vpc-conn-intern-01`
*   **Service Account**: `gwx-sa-intern-01@gwx-internship-2026-01.iam.gserviceaccount.com`
*   **Cloud SQL Instance**: `gwx-internship-2026-01:us-east1:gwx-csql-intern-01`
*   **Memorystore Redis IP**: `10.188.96.203:6379`
*   **Production Gateway URL**: `https://jt-talent-finder-gateway-488541434866.us-east1.run.app`
*   **Production Client URL**: `https://jt-talent-finder-client-488541434866.us-east1.run.app`

### Cloud Run Services

| Service Name | Context Directory | Dockerfile | Deployed Image |
| :--- | :--- | :--- | :--- |
| `jt-talent-finder-client` | `./client` | `Dockerfile` | `.../talent-finder-client:latest` |
| `jt-talent-finder-gateway` | `./apigateway` | `Dockerfile` | `.../talent-finder-gateway:latest` |
| `jt-talent-finder-server` | `./server` | `Dockerfile` | `.../talent-finder-server:latest` |
| `jt-talent-finder-worker` | `./server` | `Dockerfile.worker` | `.../talent-finder-worker:latest` |
| `jt-talent-finder-sourcing` | `./sourcing` | `Dockerfile` | `.../talent-finder-sourcing:latest` |

---

## 3. Deployment Architecture

The following diagram illustrates how the deployed components route requests and interact with GCP resources:

```
                      Client (jt-talent-finder-client)
                                     │
                                     ▼
                     Gateway (jt-talent-finder-gateway)
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
  Sourcing (jt-talent-finder-sourcing)     Server (jt-talent-finder-server)
                 │                                       │
                 ▼ (Cloud SQL)                           ├────────────────────────┐
             PostgreSQL                                  ▼ (VPC Connector)        ▼ (VPC Connector)
                                                     PostgreSQL                 Redis (Memorystore)
                                                   (Cloud SQL)                        ▲
                                                                                      │
                                                                                      ▼
                                                                           Worker (jt-talent-finder-worker)
```

*   **Ingress & Routing**: The **Client** and **Gateway** services are exposed to the public Internet (`ingress: all`). The **Server**, **Worker**, and **Sourcing** services are internal but accessible to the Gateway and each other.
*   **Database Connections**: The **Server** and **Sourcing** services connect to PostgreSQL using Unix Sockets mounted via GCP's Cloud SQL attachments.
*   **Task Queue**: The **Server** publishes jobs to Celery, using **Redis (Memorystore)** as a broker. The **Worker** polls Redis and processes candidate sourcing and scoring.

---

## 4. Deployment Process

Whenever changes are validated locally and ready for release, follow the deployment workflow:

### Step A: Identify Changed Services
Analyze the git commit history to determine which directories have changed since the last deployment. **Do not rebuild or redeploy services that have not changed.**

### Step B: Rebuild Docker Images
For each changed service, build its Docker image locally:

1.  **Gateway**:
    ```powershell
    docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-gateway:latest ./apigateway
    ```
2.  **Server**:
    ```powershell
    docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-server:latest ./server
    ```
3.  **Worker**:
    ```powershell
    docker build -f ./server/Dockerfile.worker -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-worker:latest ./server
    ```
4.  **Sourcing**:
    ```powershell
    docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-sourcing:latest ./sourcing
    ```
5.  **Client** (Note: must inject the production gateway URL as a build argument):
    ```powershell
    docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-client:latest --build-arg VITE_API_BASE_URL=https://jt-talent-finder-gateway-488541434866.us-east1.run.app ./client
    ```

### Step C: Push Images to Artifact Registry
Push the successfully built images to GCP:
```powershell
docker push us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/<IMAGE-NAME>:latest
```

### Step D: Redeploy to Cloud Run
Deploy only the affected services using revision updates, preserving existing configurations:
```powershell
gcloud.cmd run deploy <SERVICE-NAME> --image=us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/<IMAGE-NAME>:latest --region=us-east1
```

---

## 5. Incremental Deployments

To update a specific service without modifying the rest of the application stack, run the corresponding sequence:

### Deploying Client Only
Use this command sequence if you only updated client layouts, assets, or React components:
```powershell
docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-client:latest --build-arg VITE_API_BASE_URL=https://jt-talent-finder-gateway-488541434866.us-east1.run.app ./client
docker push us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-client:latest
gcloud.cmd run deploy jt-talent-finder-client --image=us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-client:latest --region=us-east1
```

### Deploying Gateway Only
Use this command sequence if you added a new route proxy or updated CORS settings:
```powershell
docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-gateway:latest ./apigateway
docker push us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-gateway:latest
gcloud.cmd run deploy jt-talent-finder-gateway --image=us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-gateway:latest --region=us-east1
```

### Deploying Server Only
Use this command sequence if you changed API routes, database schemas, or schemas in the server application:
```powershell
docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-server:latest ./server
docker push us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-server:latest
gcloud.cmd run deploy jt-talent-finder-server --image=us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-server:latest --region=us-east1
```

### Deploying Worker Only
Use this command sequence if you modified background worker tasks or Celery jobs:
```powershell
docker build -f ./server/Dockerfile.worker -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-worker:latest ./server
docker push us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-worker:latest
gcloud.cmd run deploy jt-talent-finder-worker --image=us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-worker:latest --region=us-east1
```

### Deploying Sourcing Only
Use this command sequence if you updated candidate scraping algorithms or candidate repository code:
```powershell
docker build -t us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-sourcing:latest ./sourcing
docker push us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-sourcing:latest
gcloud.cmd run deploy jt-talent-finder-sourcing --image=us-east1-docker.pkg.dev/gwx-internship-2026-01/gwx-gar-intern-01/talent-finder-sourcing:latest --region=us-east1
```

---

## 6. Verification Checklist

Perform these checks immediately after any service deployment:

1.  **Cloud Run Service Health**: Verify that the deployed service state is `Ready` and 100% of traffic is allocated to the latest revision.
2.  **App Logs**: Check logs via `gcloud.cmd logging read` for any runtime errors or startup exceptions.
3.  **Client Loading**: Navigate to the client URL and verify that the React Single Page Application loads without any console errors.
4.  **Login**: Check that logging in works and does not return CORS or unauthorized errors.
5.  **Existing Authenticated Session**: Refresh the browser and verify that you remain logged in (cookie/token persistence).
6.  **Scoring Trigger**: Open a Job Description and click "Start Scoring". Verify that the progress UI appears and updates in real-time.
7.  **Worker Processing**: Verify that the Celery worker connects to Redis and begins the scoring pipeline.
8.  **Candidate Viewing**: Click on scored candidates and verify their detailed profiles (experience, skill breakdown, and matching scores) load.
9.  **Shortlist Generation**: Verify the shortlist selection updates on the recruiter screen and can be shared successfully.

---

## 7. Troubleshooting

Below are common issues encountered during this project, along with their root causes and resolutions:

### Issue A: Cloud Run Scaling Limits (`--max=2`)
*   **Symptoms**: Service responses are extremely slow, or clients receive `503 Service Unavailable` errors during periods of concurrent requests.
*   **Root Cause**: Cloud Run services are throttled by a cost-saving maximum scale limit of 2 instances. Under sudden concurrency spikes, new requests queue up and time out before new container instances boot.
*   **Resolution**: If workload demands higher concurrency, adjust the max instances limit (e.g. to 5 or 10):
    ```powershell
    gcloud.cmd run services update <SERVICE-NAME> --max-instances=5 --region=us-east1
    ```

### Issue B: Secret Manager Mappings
*   **Symptoms**: Service crashes on boot with environment errors like `DATABASE_URL not found` or `SECRET_KEY is empty`.
*   **Root Cause**: The service attempts to load keys directly from environmental references but is missing bindings to Secret Manager variables, or the Service Account does not have permissions to read them.
*   **Resolution**: Bind variables using secret references. Verify that secrets exist and map them on deploy:
    ```powershell
    gcloud.cmd run deploy jt-talent-finder-server --image=... --set-secrets="DATABASE_URL=jt-tf-usecase-db-url:latest" ...
    ```

### Issue C: Cloud SQL Unix Socket Attachment
*   **Symptoms**: Server logs contain error: `Connection refused: database file /cloudsql/INSTANCE_CONNECTION_NAME/.s.PGSQL.5432 does not exist`.
*   **Root Cause**: The container is attempting to connect to PostgreSQL via local Unix sockets, but the SQL instance has not been attached to the Cloud Run service.
*   **Resolution**: Redeploy or update the service by attaching the instance:
    ```powershell
    gcloud.cmd run services update jt-talent-finder-server --add-cloudsql-instances=gwx-internship-2026-01:us-east1:gwx-csql-intern-01 --region=us-east1
    ```

### Issue D: Worker Deployment and Background Execution
*   **Symptoms**: Scoring pipeline tasks are sent, but Celery workers never pick them up; task statuses remain `PENDING`.
*   **Root Cause**: In Cloud Run, CPU is throttled by default when no HTTP request is active. Background Celery processes do not process HTTP traffic, causing the container CPU to freeze.
*   **Resolution**: Deploy the worker service with `--no-cpu-throttling` (CPU always allocated):
    ```powershell
    gcloud.cmd run services update jt-talent-finder-worker --no-cpu-throttling --region=us-east1
    ```

### Issue E: Gateway Cookie Forwarding
*   **Symptoms**: Recruiter logs in but is immediately redirected back to the login screen. Gateway endpoints return `401 Unauthorized` because cookies are not forwarded.
*   **Root Cause**: The API Gateway acts as a proxy. If it doesn't forward headers like `Cookie` or `Set-Cookie` in CORS settings, browser session cookies are rejected.
*   **Resolution**: Configure the API Gateway middleware to include credentials, and match CORS allowed origins to the Client URL.

### Issue F: React SPA Refresh (Nginx 404)
*   **Symptoms**: Reloading the client URL on pages like `https://.../recruiter/tasks` triggers a generic Nginx `404 Not Found` page.
*   **Root Cause**: React utilizes client-side routing. Nginx attempts to look up the path `/recruiter/tasks` on the file system and fails.
*   **Resolution**: Ensure `nginx.conf` is configured to rewrite all nonexistent file requests back to `/index.html`:
    ```nginx
    location / {
        try_files $uri $uri/ /index.html;
    }
    ```

### Issue G: Cookie `SameSite=None`
*   **Symptoms**: Session cookie is missing or ignored by the browser in production, preventing authenticated API routing.
*   **Root Cause**: Modern browsers block third-party cookies (Client and Gateway running on different domains) unless they are sent with `SameSite=None` and `Secure=True`.
*   **Resolution**: Configure the FastAPI server environment variables:
    *   `COOKIE_SAMESITE`: `none`
    *   `COOKIE_SECURE`: `True`

### Issue H: Celery Worker Startup (Port 8080 binding)
*   **Symptoms**: Deployed Celery worker revision fails to boot, reporting startup failures or health check timeouts.
*   **Root Cause**: Cloud Run expects container instances to bind to a port (usually `8080`) and respond to HTTP health probes. A default Celery worker does not handle HTTP.
*   **Resolution**: Ensure `Dockerfile.worker` starts the Celery task runner using `celery_worker_runner.py`, which initializes a lightweight HTTP thread alongside the Celery worker:
    ```python
    # celery_worker_runner.py
    # Runs Celery on one thread, and a simple HTTP server on port 8080 on another.
    ```

### Issue I: Redis Connectivity
*   **Symptoms**: Server or worker logs show connection timeouts to `10.188.96.203:6379`.
*   **Root Cause**: Redis is inside the VPC networks and blocked from the public web. Cloud Run services can only reach it if connected to a Serverless VPC Access Connector.
*   **Resolution**: Attach the connector (`gwx-vpc-conn-intern-01`) during deployment:
    ```powershell
    gcloud.cmd run services update jt-talent-finder-server --vpc-connector=gwx-vpc-conn-intern-01 --egress=private-ranges-only --region=us-east1
    ```

---

## 8. Future Deployments

Follow this concise checklist for all future releases:

1.  [ ] **Identify Changed Services**: Check git history (`git diff`) to isolate which components have modified source code.
2.  [ ] **Build Affected Images**: Rebuild the Docker images of changed services using their corresponding Dockerfiles.
3.  [ ] **Push Images**: Push the newly built Docker images to the Artifact Registry repository.
4.  [ ] **Redeploy Services**: Deploy the pushed images to Cloud Run revisions.
5.  [ ] **Verify Revisions**: Confirm all updated revisions have a state of `Ready` and serve 100% of traffic.
6.  [ ] **Run Post-Deployment Checklist**: Verify end-to-end user journeys (login, scoring, candidate views, and shortlist).
7.  [ ] **Inspect Logs**: Check logs for any startup exceptions or unexpected warnings.
