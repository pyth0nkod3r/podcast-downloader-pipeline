# Deployment Guide — Podcast Downloader Pipeline

This guide walks you through deploying the full pipeline stack on an Azure Debian VM using Coolify.

## Architecture

```
Azure Debian VM (B2s: 2 vCPU, 4 GB RAM)
├── Coolify (PaaS management layer)
│   ├── Kestra (workflow orchestrator) → :8089
│   ├── Kestra Postgres (internal DB) → internal
│   ├── App Postgres (podcast data) → :5432
│   ├── pgAdmin (DB admin UI) → :8085
│   └── Metabase (dashboard) → :3000
└── Traefik (reverse proxy + auto-SSL)
```

---

## Prerequisites

- Azure account with student subscription
- A domain name (optional but recommended for SSL)
- GitHub repository: `pyth0nkod3r/podcast-downloader-pipeline`

---

## Step 1: Provision Azure VM

1. Go to [Azure Portal](https://portal.azure.com) → **Create a resource** → **Virtual Machine**
2. Configure:
   - **Image:** Debian 12 (Bookworm)
   - **Size:** B2s (2 vCPU, 4 GB RAM) — included in student credits
   - **Disk:** 30 GB SSD
   - **Authentication:** SSH public key
3. **Networking** — Open the following ports in the Network Security Group (NSG):
   | Port | Service |
   |---|---|
   | 22 | SSH |
   | 80 | HTTP (Coolify/Traefik) |
   | 443 | HTTPS (Coolify/Traefik) |
   | 8000 | Coolify Dashboard |
   | 8089 | Kestra UI |
   | 3000 | Metabase |
4. Note the **Public IP** of your VM

---

## Step 2: Install Coolify

SSH into your VM and run the one-liner installer:

```bash
ssh your-user@<your-vm-ip>

curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
```

This installs Docker, Docker Compose, and Coolify. Wait for it to complete (~2-3 minutes).

Access Coolify at: `http://<your-vm-ip>:8000`

Create your admin account on first visit.

---

## Step 3: Connect GitHub Repository

1. In Coolify dashboard: **Projects** → **New Project** → give it a name (e.g., "Podcast Pipeline")
2. **Add Resource** → **Docker Compose** → **GitHub Repository**
3. Connect your GitHub account (Coolify will guide you through OAuth)
4. Select repo: `pyth0nkod3r/podcast-downloader-pipeline`
5. Set **branch:** `main`
6. Coolify will auto-detect the `docker-compose.yml`

---

## Step 4: Configure Environment Variables

In Coolify, go to your project → **Environment Variables** and add:

### From `.env` (app database)
```
DB_USER=<your_postgres_user>
DB_PASSWORD=<your_postgres_password>
DB_NAME=podcast_db
PGADMIN_USER=<your_pgadmin_email>
PGADMIN_PASSWORD=<your_pgadmin_password>
```

### From `.env_encoded` (Kestra secrets)
```
SECRET_POSTGRES_USERNAME=<base64_encoded_value>
SECRET_POSTGRES_PASSWORD=<base64_encoded_value>
```

> **Tip:** Generate encoded values with: `echo -n "your_password" | base64`

---

## Step 5: Deploy

Click **Deploy** in Coolify. It will:
1. Pull the repository
2. Read `docker-compose.yml`
3. Pull all container images
4. Start all services
5. Set up networking between containers

Monitor the deployment logs in the Coolify dashboard.

---

## Step 6: Configure Domains & SSL (Optional)

If you have a domain name:

1. In your DNS provider, create A records pointing to your Azure VM IP:
   - `kestra.yourdomain.com` → `<vm-ip>`
   - `dashboard.yourdomain.com` → `<vm-ip>`
2. In Coolify, go to each service and set the domain under **Settings**
3. Coolify auto-provisions Let's Encrypt SSL certificates

---

## Step 7: Set Up Coolify Webhook for CI/CD

1. In Coolify: **Project** → **Settings** → **Webhooks**
2. Copy the **Deploy Webhook URL**
3. In GitHub: **Settings** → **Secrets and variables** → **Actions** → Add secret:
   - Name: `COOLIFY_WEBHOOK_URL`
   - Value: the webhook URL from Coolify

---

## Step 8: Configure GitHub Secrets

Add these secrets in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `KESTRA_URL` | `http://<vm-ip>:8089` (or `https://kestra.yourdomain.com`) |
| `KESTRA_USER` | `admin@kestra.io` |
| `KESTRA_PASSWORD` | Your Kestra password |
| `COOLIFY_WEBHOOK_URL` | From Step 7 |
| `SMTP_SERVER` | e.g., `smtp.gmail.com` |
| `SMTP_PORT` | e.g., `587` |
| `SMTP_USERNAME` | Your email address |
| `SMTP_PASSWORD` | App password (not your regular password) |
| `NOTIFY_EMAIL` | Where to receive failure alerts |

---

## Step 9: Set Up Metabase

1. Open `http://<vm-ip>:3000` (or `https://dashboard.yourdomain.com`)
2. Complete the Metabase setup wizard
3. When asked for database connection:
   - **Type:** PostgreSQL
   - **Host:** `pgdatabase`
   - **Port:** `5432`
   - **Database:** `podcast_db` (your `DB_NAME`)
   - **Username:** your `DB_USER`
   - **Password:** your `DB_PASSWORD`
4. Metabase auto-discovers `podcast_metadata` table
5. Build your dashboard panels (see main README)

---

## Verification Checklist

- [ ] Coolify dashboard accessible at `:8000`
- [ ] Kestra UI accessible at `:8089`
- [ ] Metabase accessible at `:3000`
- [ ] pgAdmin accessible at `:8085`
- [ ] Kestra flows are running on schedule
- [ ] Push to `main` triggers CI/CD pipeline
- [ ] Flow changes deploy without container restart
- [ ] Infrastructure changes trigger Coolify redeploy
- [ ] Email notification arrives on failure

---

## Troubleshooting

### Services won't start
```bash
# SSH into VM and check Docker logs
docker ps -a
docker logs <container-name>
```

### Out of memory
```bash
# Check memory usage
free -h
docker stats
```
If Kestra or Metabase are OOM-killed, consider upgrading to B2ms (8 GB RAM).

### Kestra API unreachable from GitHub Actions
- Ensure port 8089 is open in Azure NSG
- Check Kestra is running: `curl http://localhost:8089/api/v1/flows`
