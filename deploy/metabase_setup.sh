#!/usr/bin/env bash
# =============================================================================
# deploy/metabase_setup.sh
# Provisions the "Podcast Pipeline Monitor" dashboard in Metabase via REST API.
#
# Required env vars (set in your .env or Coolify environment):
#   MB_ADMIN_EMAIL     — Metabase admin email
#   MB_ADMIN_PASSWORD  — Metabase admin password
#   MB_URL             — Metabase base URL, e.g. http://localhost:3000
#   MB_DB_NAME         — PostgreSQL database name to query (default: podcast_db)
# =============================================================================

set -euo pipefail

MB_URL="${MB_URL:-http://localhost:3000}"
MB_DB_NAME="${MB_DB_NAME:-podcast_db}"

if [[ -z "${MB_ADMIN_EMAIL:-}" || -z "${MB_ADMIN_PASSWORD:-}" ]]; then
  echo "[ERROR] MB_ADMIN_EMAIL and MB_ADMIN_PASSWORD must be set."
  exit 1
fi

echo "==> Waiting for Metabase to be ready at ${MB_URL} ..."
for i in $(seq 1 30); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${MB_URL}/api/health" || true)
  if [[ "$STATUS" == "200" ]]; then
    echo "    Metabase is up."
    break
  fi
  echo "    Attempt ${i}/30 — status ${STATUS}, retrying in 10s..."
  sleep 10
done

# ---------------------------------------------------------------------------
# 1. Authenticate
# ---------------------------------------------------------------------------
echo "==> Authenticating..."
SESSION=$(curl -s -X POST "${MB_URL}/api/session" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"${MB_ADMIN_EMAIL}\", \"password\": \"${MB_ADMIN_PASSWORD}\"}")

TOKEN=$(echo "$SESSION" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [[ -z "$TOKEN" ]]; then
  echo "[ERROR] Failed to authenticate. Response: $SESSION"
  exit 1
fi
echo "    Session token obtained."
AUTH_HEADER="X-Metabase-Session: ${TOKEN}"

# ---------------------------------------------------------------------------
# 2. Find the podcast_db database ID
# ---------------------------------------------------------------------------
echo "==> Looking up database '${MB_DB_NAME}'..."
DATABASES=$(curl -s -H "$AUTH_HEADER" "${MB_URL}/api/database")
DB_ID=$(echo "$DATABASES" | python3 -c "
import json, sys
dbs = json.load(sys.stdin)
data = dbs.get('data', dbs) if isinstance(dbs, dict) else dbs
for db in data:
    if db.get('name') == '${MB_DB_NAME}' or db.get('details', {}).get('dbname') == '${MB_DB_NAME}':
        print(db['id'])
        break
")

if [[ -z "$DB_ID" ]]; then
  echo "[ERROR] Could not find database '${MB_DB_NAME}' in Metabase."
  echo "        Make sure you have connected the database via the Metabase UI first."
  exit 1
fi
echo "    Found database ID: ${DB_ID}"

# ---------------------------------------------------------------------------
# 3. Helper — create a native SQL question (card)
# ---------------------------------------------------------------------------
create_card() {
  local name="$1"
  local sql="$2"
  local display="$3"   # table | bar | line | row | pie

  curl -s -X POST "${MB_URL}/api/card" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"${name}\",
      \"display\": \"${display}\",
      \"visualization_settings\": {},
      \"dataset_query\": {
        \"type\": \"native\",
        \"database\": ${DB_ID},
        \"native\": {
          \"query\": \"${sql}\"
        }
      }
    }" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))"
}

# ---------------------------------------------------------------------------
# 4. Create the 4 questions
# ---------------------------------------------------------------------------
echo "==> Creating questions..."

CARD_1=$(create_card \
  "Episodes by Source" \
  "SELECT source, COUNT(*) AS episode_count FROM podcast_metadata GROUP BY source ORDER BY 2 DESC" \
  "bar")
echo "    Card 1 (Episodes by Source): ID=${CARD_1}"

CARD_2=$(create_card \
  "Episodes Added Over Time" \
  "SELECT DATE_TRUNC('day', created_at) AS day, COUNT(*) AS episode_count FROM podcast_metadata GROUP BY 1 ORDER BY 1" \
  "line")
echo "    Card 2 (Episodes Over Time): ID=${CARD_2}"

CARD_3=$(create_card \
  "Download Status Breakdown" \
  "SELECT status, COUNT(*) AS count FROM podcast_downloads GROUP BY status ORDER BY 2 DESC" \
  "pie")
echo "    Card 3 (Download Status): ID=${CARD_3}"

CARD_4=$(create_card \
  "Recent Downloads" \
  "SELECT guid, file_path, status, downloaded_at FROM podcast_downloads ORDER BY downloaded_at DESC LIMIT 50" \
  "table")
echo "    Card 4 (Recent Downloads): ID=${CARD_4}"

# ---------------------------------------------------------------------------
# 5. Create the dashboard
# ---------------------------------------------------------------------------
echo "==> Creating dashboard..."
DASHBOARD=$(curl -s -X POST "${MB_URL}/api/dashboard" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"name": "Podcast Pipeline Monitor", "description": "Auto-provisioned by metabase_setup.sh"}')

DASH_ID=$(echo "$DASHBOARD" | python3 -c "import json,sys; print(json.load(sys.stdin).get('id',''))")

if [[ -z "$DASH_ID" ]]; then
  echo "[ERROR] Failed to create dashboard."
  echo "$DASHBOARD"
  exit 1
fi
echo "    Dashboard created: ID=${DASH_ID}"

# ---------------------------------------------------------------------------
# 6. Add cards to the dashboard (2-column layout)
# ---------------------------------------------------------------------------
echo "==> Adding cards to dashboard..."

add_card_to_dashboard() {
  local dash_id="$1"
  local card_id="$2"
  local row="$3"
  local col="$4"

  curl -s -X POST "${MB_URL}/api/dashboard/${dash_id}/cards" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "{
      \"cardId\": ${card_id},
      \"row\": ${row},
      \"col\": ${col},
      \"size_x\": 9,
      \"size_y\": 6,
      \"parameter_mappings\": [],
      \"visualization_settings\": {}
    }" > /dev/null
}

add_card_to_dashboard "$DASH_ID" "$CARD_1" 0  0   # top-left
add_card_to_dashboard "$DASH_ID" "$CARD_2" 0  9   # top-right
add_card_to_dashboard "$DASH_ID" "$CARD_3" 6  0   # bottom-left
add_card_to_dashboard "$DASH_ID" "$CARD_4" 6  9   # bottom-right

echo ""
echo "============================================================"
echo "  ✅  Podcast Pipeline Monitor dashboard created!"
echo "  👉  Open: ${MB_URL}/dashboard/${DASH_ID}"
echo "============================================================"
