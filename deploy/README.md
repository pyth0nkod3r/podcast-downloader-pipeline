# Deployment Guide — Podcast Downloader Pipeline

This guide walks you through deploying the full pipeline stack on an Azure Debian VM using Coolify v4.

## Architecture

```
Azure Debian VM (B2s: 2 vCPU, 4 GB RAM)
├── Coolify (PaaS management layer)
│   ├── Kestra (workflow orchestrator) → :8089
│   ├── Kestra Postgres (internal DB) → internal
│   ├── App Postgres (podcast data) → :5432
│   ├── pgAdmin (DB admin UI) → :8085
│   └── Metabase (dashboard) → :3000
│       └── podcast_audio volume (MP3 files, persisted)
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

## Step 3: Register the VPS as a Server in Coolify

> This step is required before you can deploy any resources. Coolify must know about the server it is running on.

1. In the Coolify dashboard, click **Servers** in the left sidebar.
2. Click **Add Server**.
3. Select **Localhost** (since Coolify is running on the same VM as your stack).
4. Click **Save** — Coolify will validate the connection via the Docker socket automatically.
5. You will see your server appear as **Reachable** with a green indicator.

---

## Step 4: Create a Project and Environment

1. In the Coolify dashboard, click **Projects** in the left sidebar.
2. Click **+ Create New Project**.
3. Name it **Podcast Pipeline** → click **Create**.
4. Inside the project, click **+ New Environment**.
5. Name it **production** → click **Create**.

---

## Step 5: Add a Docker Compose Resource

1. Inside the **production** environment, click **+ Add New Resource**.
2. Choose **Docker Compose** as the resource type.
3. Choose **GitHub** as the source.
4. Click **Connect GitHub** and authorize Coolify to read your repositories (OAuth flow).
5. Select the repo: `pyth0nkod3r/podcast-downloader-pipeline`
6. Set **Branch:** `main`
7. Coolify auto-detects `docker-compose.yml` in the repo root — confirm the path is correct.
8. Click **Continue**.

---

## Step 6: Configure Environment Variables

In Coolify, go to your resource → **Environment Variables** tab and add the following:

### App Database
```
DB_USER=<your_postgres_user>
DB_PASSWORD=<your_postgres_password>
DB_NAME=podcast_db
PGADMIN_USER=<your_pgadmin_email>
PGADMIN_PASSWORD=<your_pgadmin_password>
```

### Kestra Secrets (base64-encoded)
```
SECRET_POSTGRES_USERNAME=<base64_encoded_db_user>
SECRET_POSTGRES_PASSWORD=<base64_encoded_db_password>
```
> **Tip:** Generate encoded values with: `echo -n "your_value" | base64`

### Metabase Admin
```
MB_ADMIN_EMAIL=<your_metabase_admin_email>
MB_ADMIN_PASSWORD=<your_metabase_admin_password>
MB_URL=http://localhost:3000
MB_DB_NAME=podcast_db
```

> **Note:** Mark all passwords as **Secret** using the lock icon in Coolify's UI — this prevents them from appearing in deployment logs.

---

## Step 7: Deploy

1. Click **Deploy** in Coolify.
2. Coolify will:
   - Clone the repository
   - Pull all container images
   - Create all named volumes (including `podcast_audio` for persisted MP3 files)
   - Start all 5 services
   - Set up internal networking between containers

Monitor the deployment logs in the Coolify dashboard.

**Expected running services:**
| Service | Port | Purpose |
|---|---|---|
| `kestra` | :8089 | Workflow orchestration |
| `pgdatabase` | :5432 | Podcast metadata + downloads DB |
| `kestra_postgres` | internal | Kestra's internal state DB |
| `pgadmin` | :8085 | Database admin UI |
| `metabase` | :3000 | Analytics dashboard |

---

## Step 8: Connect Metabase to PostgreSQL

> This one-time setup is done via the Metabase UI wizard on first boot.

1. Open `http://<vm-ip>:3000`
2. Complete the Metabase welcome wizard (language, admin account creation)
3. When asked **"Add your data"**, choose **PostgreSQL** and enter:
   | Field | Value |
   |---|---|
   | Host | `pgdatabase` |
   | Port | `5432` |
   | Database name | `podcast_db` |
   | Username | your `DB_USER` |
   | Password | your `DB_PASSWORD` |
4. Click **Connect database** → Metabase will sync the schema automatically.

---

## Step 9: Provision the Dashboard via Script

After Metabase is connected to PostgreSQL and the Kestra flow has run at least once (so that `podcast_metadata` and `podcast_downloads` tables exist), run the provisioning script:

```bash
# SSH into your VM
ssh your-user@<your-vm-ip>

# Set credentials (or export from your .env)
export MB_ADMIN_EMAIL="your_metabase_email"
export MB_ADMIN_PASSWORD="your_metabase_password"
export MB_URL="http://localhost:3000"
export MB_DB_NAME="podcast_db"

# Run the script
bash /path/to/podcast-downloader-pipeline/deploy/metabase_setup.sh
```

The script will create a **"Podcast Pipeline Monitor"** dashboard with 4 panels:
- 📊 **Episodes by Source** (bar chart)
- 📅 **Episodes Added Over Time** (line chart)
- ✅ **Download Status Breakdown** (pie chart)
- 🕐 **Recent Downloads** (table)

Open the dashboard at the URL printed by the script.

> **Tip:** You can add this script as a **Post-Deploy Command** in Coolify (Resource → Settings → Post-Deploy Command) so it runs automatically after each deployment:
> ```
> bash deploy/metabase_setup.sh
> ```

---

## Step 10: Configure Domains & SSL (Optional)

If you have a domain name:

1. In your DNS provider, create A records pointing to your Azure VM IP:
   - `kestra.yourdomain.com` → `<vm-ip>`
   - `dashboard.yourdomain.com` → `<vm-ip>`
2. In Coolify, go to each service and set the domain under **Settings**
3. Coolify auto-provisions Let's Encrypt SSL certificates

---

## Step 11: Set Up Coolify Webhook for CI/CD

1. In Coolify: **Project** → your resource → **Settings** → **Deploy Webhook**
2. Copy the **Deploy Webhook URL**
3. In GitHub: **Settings** → **Secrets and variables** → **Actions** → Add secret:
   - Name: `COOLIFY_WEBHOOK_URL`
   - Value: the webhook URL from Coolify

---

## Step 12: Configure GitHub Secrets

Add these secrets in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `KESTRA_URL` | `http://<vm-ip>:8089` (or `https://kestra.yourdomain.com`) |
| `KESTRA_USER` | `admin@kestra.io` |
| `KESTRA_PASSWORD` | Your Kestra password |
| `COOLIFY_WEBHOOK_URL` | From Step 11 |
| `SMTP_SERVER` | e.g., `smtp.gmail.com` |
| `SMTP_PORT` | e.g., `587` |
| `SMTP_USERNAME` | Your email address |
| `SMTP_PASSWORD` | App password (not your regular password) |
| `NOTIFY_EMAIL` | Where to receive failure alerts |

---

## Verification Checklist

- [ ] Coolify dashboard accessible at `:8000`
- [ ] VPS server registered as **Localhost** in Coolify (green / Reachable)
- [ ] All 5 services show as **Running** in Coolify project
- [ ] Kestra UI accessible at `:8089`
- [ ] Metabase accessible at `:3000`
- [ ] pgAdmin accessible at `:8085`
- [ ] Metabase connected to `pgdatabase:5432/podcast_db`
- [ ] Kestra flow runs manually without errors
- [ ] Audio `.mp3` files appear in the `podcast_audio` Docker volume
- [ ] `podcast_downloads` table populated in PostgreSQL
- [ ] `metabase_setup.sh` runs successfully → dashboard visible
- [ ] Push to `main` triggers CI/CD pipeline
- [ ] Flow changes deploy without container restart

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

### Audio files not appearing
```bash
# Check the podcast_audio volume contents from inside the Kestra container
docker exec -it <kestra-container-name> ls /app/storage/audio
```

### Metabase setup script fails — database not found
- Make sure you connected PostgreSQL in the Metabase UI (Step 8) **before** running the script.
- The script looks for a database named `podcast_db`. Verify the name matches your `DB_NAME`.
