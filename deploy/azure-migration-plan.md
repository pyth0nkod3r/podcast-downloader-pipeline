# Azure Migration Plan — Podcast Pipeline

> Generated: May 12, 2026
> Skill level: Beginner-friendly
> Current state: Everything runs locally via Docker Compose
> Target state: Azure VM + Coolify + Azure Blob Storage + Custom Domain + SSL

---

## What Changes and Why

| Component | Current (Local) | Target (Azure) | Why |
|-----------|----------------|----------------|-----|
| Audio files | Docker volume `podcast_audio` | Azure Blob Storage container | Docker volumes are tied to one machine. Blob Storage is durable, cheap, and accessible from anywhere. |
| Kestra internal storage | Local filesystem `/app/storage` | Azure Blob Storage (separate container) | Same reason — cloud storage survives VM rebuilds. |
| Infrastructure host | Your laptop / dev machine | Azure VM (B2s) managed by Coolify | Always-on, accessible from internet, scheduled jobs run 24/7. |
| Access URLs | `localhost:8501`, `localhost:8089` | `dashboard.yourdomain.com`, `kestra.yourdomain.com` | Professional, memorable, shareable. |
| SSL/TLS | None (HTTP only) | Auto-provisioned via Let's Encrypt | Encrypted connections, browser trust, required for production. |
| CI/CD trigger | Manual | GitHub → Coolify webhook (already wired) | Push to `main` auto-deploys. |

---

## Prerequisites Checklist

Before you start, make sure you have:

- [ ] An **Azure account** (student subscription works — gives $100 free credits)
- [ ] A **domain name** (e.g., from Namecheap, Cloudflare, or Google Domains — ~$10/year)
- [ ] Your project **pushed to GitHub** (`pyth0nkod3r/podcast-downloader-pipeline`)
- [ ] A working local setup (you can run `docker compose up` and everything works)

---

## Stage 0 — Create Azure Resources

> **Goal:** Provision the Azure infrastructure you'll need.
> **Time:** ~20 minutes. All done via Azure Portal (no CLI required).

### 0a — Create a Resource Group

A Resource Group is just a folder that holds all your Azure resources together.

- [ ] Go to [Azure Portal](https://portal.azure.com) → **Resource groups** → **Create**
- [ ] Name: `rg-podcast-pipeline`
- [ ] Region: Pick the one closest to you (e.g., `UK South`, `East US`)
- [ ] Click **Review + Create** → **Create**

### 0b — Create an Azure Storage Account

This is where your audio files and Kestra's internal files will live.

- [ ] Azure Portal → **Storage accounts** → **Create**
- [ ] Configure:

  | Setting | Value | Why |
  |---------|-------|-----|
  | Resource group | `rg-podcast-pipeline` | Keeps everything together |
  | Storage account name | `podcastpipelinestorage` | Must be globally unique, lowercase, no dashes |
  | Region | Same as your Resource Group | Data stays close together |
  | Performance | **Standard** | Cheapest option, plenty fast for audio files |
  | Redundancy | **LRS** (Locally-redundant) | Cheapest. Fine for a learning project |

- [ ] Click **Review + Create** → **Create**
- [ ] Wait for deployment to complete, then click **Go to resource**

### 0c — Create Blob Containers

A container in Azure Blob Storage is like a top-level folder.

- [ ] In your Storage Account, click **Containers** in the left sidebar
- [ ] Create two containers:

  | Container name | Access level | Purpose |
  |---------------|-------------|---------|
  | `podcast-audio` | **Private** | Stores downloaded MP3 files |
  | `kestra-storage` | **Private** | Kestra's internal file storage |

### 0d — Get Your Storage Credentials

You'll need these for the `docker-compose.yml` and Kestra config.

- [ ] In your Storage Account → **Access keys** (left sidebar, under Security + networking)
- [ ] Click **Show** next to Key 1
- [ ] Copy and save these two values somewhere safe:
  - **Storage account name** (e.g., `podcastpipelinestorage`)
  - **Key** (a long base64 string)
- [ ] Also copy the **Connection string** — you'll need it for the Python scripts

> [!CAUTION]
> Never commit these keys to Git. They go in `.env` (which is gitignored) and in Coolify's environment variables.

### 0e — Provision the Azure VM

- [ ] Azure Portal → **Virtual machines** → **Create** → **Azure virtual machine**
- [ ] Configure:

  | Setting | Value |
  |---------|-------|
  | Resource group | `rg-podcast-pipeline` |
  | VM name | `vm-podcast-pipeline` |
  | Region | Same as storage account |
  | Image | **Debian 12 (Bookworm) — x64** |
  | Size | **B2s** (2 vCPU, 4 GB RAM) — ~$15/month, covered by student credits |
  | Authentication | **SSH public key** |
  | Username | Your choice (e.g., `azureuser`) |

- [ ] **Networking** → ensure a public IP is assigned
- [ ] **NSG (Network Security Group)** — open these inbound ports:

  | Port | Protocol | Purpose |
  |------|----------|---------|
  | 22 | TCP | SSH access |
  | 80 | TCP | HTTP (Traefik / Let's Encrypt validation) |
  | 443 | TCP | HTTPS (your services) |
  | 8000 | TCP | Coolify dashboard |

  > [!TIP]
  > You do NOT need to open 8089, 8501, or 8085 individually. Traefik will route all traffic through ports 80/443 using your domain names. This is more secure.

- [ ] Click **Review + Create** → **Create**
- [ ] Download the SSH key if you generated a new one
- [ ] Note your VM's **Public IP address**

---

## Stage 1 — Install Coolify on the VM

> **Goal:** Get Coolify running so it can manage your Docker services.
> **Time:** ~10 minutes.

### Tasks

- [ ] SSH into your VM:
  ```bash
  ssh -i ~/.ssh/your-key.pem azureuser@<your-vm-ip>
  ```

- [ ] Install Coolify (one command):
  ```bash
  curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
  ```
  This installs Docker, Docker Compose, and Coolify. Takes ~2-3 minutes.

- [ ] Open Coolify in your browser: `http://<your-vm-ip>:8000`

- [ ] Create your admin account on first visit (email + password)

- [ ] Register the server:
  1. Click **Servers** in the sidebar
  2. Click **Add Server** → select **Localhost**
  3. Click **Save** — you should see a green "Reachable" indicator

- [ ] 🧪 **Verify:** Coolify dashboard loads, server shows as Reachable

---

## Stage 2 — Point Your Domain to the VM

> **Goal:** Set up DNS so `dashboard.yourdomain.com`, `kestra.yourdomain.com`, etc. resolve to your Azure VM.
> **Time:** ~5 minutes (but DNS propagation can take up to 1 hour).

### Tasks

- [ ] Log into your domain registrar / DNS provider (Cloudflare, Namecheap, etc.)
- [ ] Create **A records** pointing to your VM's public IP:

  | Type | Name | Value | TTL |
  |------|------|-------|-----|
  | A | `dashboard` | `<your-vm-ip>` | 300 |
  | A | `kestra` | `<your-vm-ip>` | 300 |
  | A | `pgadmin` | `<your-vm-ip>` | 300 |
  | A | `coolify` | `<your-vm-ip>` | 300 |

  > [!NOTE]
  > If using **Cloudflare**, set the proxy status to **DNS only** (grey cloud) initially. Cloudflare's proxy can interfere with Coolify's SSL provisioning. You can enable the orange cloud later.

- [ ] 🧪 **Verify DNS propagation:**
  ```bash
  nslookup dashboard.yourdomain.com
  # Should return your VM's IP
  ```
  If it doesn't resolve yet, wait 15-60 minutes and try again.

---

## Stage 3 — Update Code for Azure Blob Storage

> **Goal:** Modify the download script to upload audio files to Azure Blob Storage instead of writing to a local Docker volume.
> **Time:** ~30 minutes. This is the biggest code change.

### 3a — Add the Azure SDK to the Python environment

- [ ] The download script runs inside Kestra's Python Script task. Kestra uses a Docker container for Python tasks, so you need to install the Azure SDK at runtime. In `download-audio.yaml`, add `beforeCommands` to install the package:

  ```yaml
  - id: download_audio
    type: io.kestra.plugin.scripts.python.Script
    beforeCommands:
      - pip install azure-storage-blob
    inputFiles:
      pending.ion: "{{ outputs.fetch_pending_episodes.uri }}"
    outputFiles:
      - download_results.csv
    script: |
      # ... (updated script below)
  ```

### 3b — Rewrite the download script to use Blob Storage

- [ ] Replace the download script in `flows/download-audio.yaml` to upload to Azure Blob Storage instead of writing to `/app/storage/audio`. The key changes:
  - **Remove** `AUDIO_DIR` and local `os.path.exists()` checks
  - **Add** Azure Blob client that uploads each downloaded file
  - **Check** if blob already exists before downloading (replaces the local file check)
  - Store the **blob URL** in `file_path` instead of a local path

  The new script should:
  ```python
  from azure.storage.blob import BlobServiceClient
  import os

  AZURE_CONN_STR = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "{{ secret('AZURE_STORAGE_CONNECTION_STRING') }}")
  CONTAINER_NAME = "podcast-audio"
  blob_service = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
  container = blob_service.get_container_client(CONTAINER_NAME)

  # Check if blob exists:
  blob_client = container.get_blob_client(filename)
  if blob_client.exists():
      # skip — already uploaded
  else:
      # Download from RSS, upload to blob
      resp = requests.get(url, stream=True, timeout=60)
      blob_client.upload_blob(resp.content)
  ```

  > [!IMPORTANT]
  > The full script is provided in Stage 3d below as a complete replacement file.

### 3c — Also update `rss-podcast-poc.yaml` (the legacy combined flow)

- [ ] Apply the same Azure Blob changes to the audio download section in `rss-podcast-poc.yaml`, if you plan to keep using it. Otherwise, disable its trigger and rely on the split flows (`ingest-metadata.yaml` + `download-audio.yaml`).

### 3d — Complete replacement `download-audio.yaml` script section

- [ ] Replace the `script: |` block in `download-audio.yaml` with:

  ```python
  import json, os, re, time, csv
  import requests
  from azure.storage.blob import BlobServiceClient

  AZURE_CONN_STR = "{{ secret('AZURE_STORAGE_CONNECTION_STRING') }}"
  CONTAINER_NAME = "podcast-audio"
  MAX_RETRIES = 3

  blob_service = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
  container = blob_service.get_container_client(CONTAINER_NAME)

  def sanitize(title):
    safe = re.sub(r'[^\w\s-]', '', title or 'unknown')
    safe = re.sub(r'[\s_]+', '_', safe).strip('_')
    return safe[:100]

  # Read ION-format rows from Kestra STORE output
  items = []
  try:
    import amazon.ion.simpleion as ion
    with open("pending.ion", "rb") as f:
      for val in ion.load(f, single_value=False):
        items.append(dict(val))
  except ImportError:
    with open("pending.ion", "r", encoding="utf-8") as f:
      for line in f:
        line = line.strip()
        if line:
          try:
            row = json.loads(line.replace("'", '"'))
            items.append(row)
          except:
            pass

  print(f"Episodes to download: {len(items)}")
  results = []

  for item in items:
    guid = str(item.get("guid",""))
    url = str(item.get("audio_url",""))
    title = str(item.get("title", guid))
    filename = sanitize(title) + ".mp3"

    # Check if blob already exists
    blob_client = container.get_blob_client(filename)
    if blob_client.exists():
      blob_url = blob_client.url
      results.append({"guid": guid, "file_path": blob_url, "status": "skipped"})
      continue

    # Download with retry logic
    success = False
    for attempt in range(1, MAX_RETRIES + 1):
      try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        audio_data = resp.content
        blob_client.upload_blob(audio_data, overwrite=False)
        blob_url = blob_client.url
        print(f"[OK] Uploaded: {filename}")
        results.append({"guid": guid, "file_path": blob_url, "status": "success"})
        success = True
        break
      except Exception as e:
        print(f"[RETRY {attempt}/{MAX_RETRIES}] {filename}: {e}")
        if attempt < MAX_RETRIES:
          time.sleep(2)

    if not success:
      print(f"[FAIL] {filename}: all {MAX_RETRIES} retries exhausted")
      results.append({"guid": guid, "file_path": "", "status": "failed"})

  with open("download_results.csv", "w", newline="", encoding="utf-8") as rf:
    w = csv.DictWriter(rf, fieldnames=["guid","file_path","status"])
    w.writeheader()
    w.writerows(results)

  ok = sum(1 for r in results if r["status"]=="success")
  skip = sum(1 for r in results if r["status"]=="skipped")
  fail = sum(1 for r in results if r["status"]=="failed")
  print(f"=== AUDIO DOWNLOAD SUMMARY ===")
  print(f"Uploaded: {ok} | Skipped: {skip} | Failed: {fail}")
  ```

### 3e — Update Kestra's internal storage to Azure Blob

- [ ] In `docker-compose.yml`, update the Kestra `KESTRA_CONFIGURATION` block to use Azure Blob Storage instead of local storage:

  ```yaml
  # Replace this:
  storage:
    type: local
    local:
      basePath: "/app/storage"

  # With this:
  storage:
    type: azure
    azure:
      container: kestra-storage
      endpoint: "https://podcastpipelinestorage.blob.core.windows.net"
      connectionString: "${AZURE_STORAGE_CONNECTION_STRING}"
  ```

- [ ] Remove the `kestra_data` and `podcast_audio` volumes from `docker-compose.yml` (they're no longer needed — everything goes to Blob Storage):

  ```yaml
  # REMOVE these two lines from the volumes: section:
  kestra_data:
    driver: local
  podcast_audio:
    driver: local

  # REMOVE these from the kestra service volumes:
  - kestra_data:/app/storage
  - podcast_audio:/app/storage/audio
  ```

### 3f — Add the Azure connection string to environment config

- [ ] Add to `.env`:
  ```
  AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=podcastpipelinestorage;AccountKey=<your-key>;EndpointSuffix=core.windows.net
  ```

- [ ] Add to `.env_encoded` (base64-encoded, with `SECRET_` prefix):
  ```bash
  echo -n "DefaultEndpointsProtocol=https;AccountName=..." | base64
  ```
  Then add: `SECRET_AZURE_STORAGE_CONNECTION_STRING=<base64_value>`

- [ ] Update `.env.example` to document the new variable (without real values)

- [ ] 🧪 **Test locally first:** Run `docker compose up` and trigger the download-audio flow. Check that files appear in Azure Portal → Storage Account → Containers → `podcast-audio`.

---

## Stage 4 — Deploy to Azure via Coolify

> **Goal:** Get the full stack running on your Azure VM via Coolify.
> **Time:** ~20 minutes.

### 4a — Create a Coolify Project

- [ ] In Coolify dashboard (`http://<vm-ip>:8000`):
  1. Click **Projects** → **+ Create New Project**
  2. Name: `Podcast Pipeline` → **Create**
  3. Inside the project, click **+ New Environment**
  4. Name: `production` → **Create**

### 4b — Connect GitHub

- [ ] Inside the production environment → **+ Add New Resource**
- [ ] Choose **Docker Compose** as resource type
- [ ] Choose **GitHub (App)** as source
- [ ] Authorize Coolify to access your GitHub repositories
- [ ] Select: `pyth0nkod3r/podcast-downloader-pipeline`
- [ ] Branch: `main`
- [ ] Coolify auto-detects `docker-compose.yml` — confirm the path

### 4c — Configure Environment Variables in Coolify

- [ ] Go to your resource → **Environment Variables** tab
- [ ] Add all variables (Coolify will inject them into all services):

  ```
  DB_USER=<your_postgres_user>
  DB_PASSWORD=<your_strong_password>
  DB_NAME=podcast_db
  PGADMIN_USER=<your_email>
  PGADMIN_PASSWORD=<your_pgadmin_password>
  AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
  ```

- [ ] For the Kestra encoded secrets, also add:
  ```
  SECRET_DB_HOST=<base64 of "pgdatabase">
  SECRET_DB_PORT=<base64 of "5432">
  SECRET_DB_NAME=<base64 of "podcast_db">
  SECRET_DB_USER=<base64 of your db user>
  SECRET_DB_PASSWORD=<base64 of your db password>
  SECRET_AZURE_STORAGE_CONNECTION_STRING=<base64 of the full connection string>
  ```

  > [!TIP]
  > Generate base64 values: `echo -n "your_value" | base64`

### 4d — Deploy

- [ ] Click **Deploy** in Coolify
- [ ] Monitor the deployment logs — wait for all 5 services to show as Running
- [ ] 🧪 **Verify:** SSH into VM and run:
  ```bash
  docker ps
  # Should show: pgdatabase, kestra_postgres, kestra, pgadmin, streamlit
  ```

---

## Stage 5 — Configure Domains and SSL

> **Goal:** Access services via `https://dashboard.yourdomain.com` etc. with auto-SSL.
> **Time:** ~15 minutes.

### 5a — Assign domains to services in Coolify

Coolify uses Traefik as a reverse proxy. You assign a domain to each service, and Traefik handles routing + SSL.

- [ ] In Coolify → your resource → find the **streamlit** service
  1. Click on it → **Settings** (or the domain/URL field)
  2. Set domain: `https://dashboard.yourdomain.com`
  3. Save

- [ ] Repeat for **kestra**:
  - Domain: `https://kestra.yourdomain.com`

- [ ] Repeat for **pgadmin**:
  - Domain: `https://pgadmin.yourdomain.com`

  > [!NOTE]
  > Coolify maps the domain to the container's internal port automatically. For example, `dashboard.yourdomain.com` → streamlit container port 8501.

### 5b — SSL is automatic

- [ ] Coolify + Traefik auto-provisions **Let's Encrypt** SSL certificates when:
  1. The domain's DNS A record points to the VM ✅ (you did this in Stage 2)
  2. Port 80 is open ✅ (for the ACME HTTP-01 challenge)
  3. Port 443 is open ✅ (for serving HTTPS)

- [ ] Certificates auto-renew every 60 days. No action needed.

### 5c — Remove raw port exposure

Once domains are working, you should stop exposing raw ports for security:

- [ ] In `docker-compose.yml`, **remove** the `ports:` sections from services that are now behind Traefik. Change:

  ```yaml
  # BEFORE (exposed to internet):
  streamlit:
    ports:
      - "8501:8501"

  # AFTER (Traefik handles routing):
  streamlit:
    expose:
      - "8501"
  ```

- [ ] Apply the same change to `kestra` (remove `8089:8080`) and `pgadmin` (remove `8085:80`)
- [ ] **Keep** the `pgdatabase` port mapping only if you need external DB access. For production, remove it too.

  > [!WARNING]
  > After removing port mappings, services are ONLY accessible through the Traefik reverse proxy (your domain names). This is the correct production setup — don't expose ports to the internet.

### 5d — Update Kestra's internal URL

- [ ] In `docker-compose.yml`, update the Kestra config:
  ```yaml
  # Change:
  url: http://localhost:8080/
  # To:
  url: https://kestra.yourdomain.com/
  ```

### 5e — Verify everything

- [ ] 🧪 Open `https://dashboard.yourdomain.com` — dashboard loads with HTTPS padlock ✅
- [ ] 🧪 Open `https://kestra.yourdomain.com` — Kestra login page with HTTPS ✅
- [ ] 🧪 Open `https://pgadmin.yourdomain.com` — pgAdmin login with HTTPS ✅
- [ ] 🧪 Check certificate: click the padlock icon → certificate should show "Let's Encrypt"

---

## Stage 6 — Update CI/CD and GitHub Secrets

> **Goal:** Update the GitHub Actions pipeline to point to the Azure deployment.
> **Time:** ~10 minutes.

### Tasks

- [ ] In GitHub → **Settings** → **Secrets and variables** → **Actions**, update/add:

  | Secret | Value |
  |--------|-------|
  | `KESTRA_URL` | `https://kestra.yourdomain.com` |
  | `KESTRA_USER` | `admin@kestra.io` |
  | `KESTRA_PASSWORD` | Your Kestra password |
  | `COOLIFY_WEBHOOK_URL` | Copy from Coolify → Project → Resource → Settings → Deploy Webhook |

- [ ] Set up the Coolify webhook:
  1. In Coolify → your resource → **Settings** → **Deploy Webhook**
  2. Copy the webhook URL
  3. Add as `COOLIFY_WEBHOOK_URL` secret in GitHub

- [ ] 🧪 **Test CI/CD:** Push a small change to `main`. Verify:
  - GitHub Actions triggers the deploy workflow
  - Flows are deployed to Kestra via the API
  - If `docker-compose.yml` changed, Coolify redeploys containers

---

## Stage 7 — Run the Pipeline and Verify End-to-End

> **Goal:** Confirm everything works together in production.
> **Time:** ~15 minutes.

### Tasks

- [ ] Open `https://kestra.yourdomain.com` → log in
- [ ] Run **`init-schema`** manually → verify tables and views are created
- [ ] Run **`seed-feeds`** → verify feeds appear in pgAdmin
- [ ] Run **`ingest-metadata`** → verify episodes appear in `podcast_metadata`
- [ ] Run **`download-audio`** → verify:
  - Files appear in Azure Portal → Storage Account → `podcast-audio` container
  - `podcast_downloads` table has rows with blob URLs as `file_path`
- [ ] Open `https://dashboard.yourdomain.com` → verify all 4 tabs render data:
  - 📊 Overview — KPIs, charts populated
  - 🎙️ Shows — feed selector works, charts render
  - 📅 Trends — heatmap, weekly volume, scatter plot
  - 🔧 Pipeline Health — run logs show your manual runs

---

## Post-Migration Checklist

- [ ] All services accessible via HTTPS on custom domains
- [ ] SSL certificates show "Let's Encrypt" issuer
- [ ] Audio files are in Azure Blob Storage (not Docker volumes)
- [ ] Kestra internal storage is Azure Blob (not local filesystem)
- [ ] Hourly metadata ingestion runs on schedule
- [ ] 6-hourly audio downloads run on schedule
- [ ] GitHub push triggers CI/CD pipeline
- [ ] No raw ports (8089, 8501, 8085) exposed to internet
- [ ] Dashboard shows live data from the Azure-hosted Postgres
- [ ] Pipeline run logs appear in the Pipeline Health tab

---

## Cost Estimate (Azure Student Credits)

| Resource | Monthly Cost | Notes |
|----------|-------------|-------|
| VM B2s | ~$15 | 2 vCPU, 4 GB RAM |
| Storage (LRS) | ~$1-3 | Depends on audio volume (50 GB ≈ $1) |
| Network egress | ~$0-2 | First 100 GB/month free |
| **Total** | **~$16-20/month** | Covered by $100 student credits for 5+ months |

---

## Troubleshooting

### "Connection refused" on domain
- Verify DNS: `nslookup dashboard.yourdomain.com` should return your VM IP
- Check ports 80/443 are open in Azure NSG
- Check Traefik is running: `docker logs <traefik-container>`

### SSL certificate not provisioning
- Ensure DNS is propagated (A records resolve to VM IP)
- Ensure Cloudflare proxy is OFF (grey cloud, DNS only) during initial setup
- Check Traefik logs: `docker logs <traefik-container> 2>&1 | grep -i acme`

### Azure Blob upload fails
- Verify connection string in environment variables
- Test manually: `az storage blob list --container-name podcast-audio --connection-string "..."`
- Check the Kestra task logs for the exact error message

### Out of memory on VM
```bash
free -h
docker stats
```
If services are OOM-killed, upgrade VM to B2ms (8 GB RAM, ~$30/month).

### Coolify not detecting docker-compose.yml
- Ensure the file is in the repo root
- Ensure the GitHub App has read access to the repository
- Try re-connecting GitHub in Coolify settings

---

## Files Modified in This Migration

| File | Change |
|------|--------|
| `docker-compose.yml` | Remove audio/kestra volumes, add Azure Blob config to Kestra, remove raw port mappings |
| `flows/download-audio.yaml` | Replace local file writes with Azure Blob uploads |
| `flows/rss-podcast-poc.yaml` | Same Azure Blob change (if keeping this flow) |
| `.env` / `.env_encoded` | Add `AZURE_STORAGE_CONNECTION_STRING` |
| `.env.example` | Document the new Azure variable |

---

*End of migration plan. Take it one stage at a time — each stage leaves you in a working state.*
