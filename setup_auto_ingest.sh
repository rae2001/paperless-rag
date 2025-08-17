#!/bin/bash
# Setup automatic document ingestion for Paperless RAG

echo "Setting up automatic document ingestion..."

# Create the ingestion script
sudo tee /usr/local/bin/paperless-rag-ingest.sh > /dev/null << 'EOF'
#!/bin/bash
# Paperless RAG Auto-Ingestion Script
# This script ingests new/updated documents since last run

STATE_DIR="/var/lib/paperless-rag"
STATE_FILE="$STATE_DIR/last_ingest"
LOG_FILE="$STATE_DIR/ingest.log"

# Create state directory if it doesn't exist
mkdir -p "$STATE_DIR"

# Get last ingest timestamp (default to epoch if first run)
if [ -f "$STATE_FILE" ]; then
    LAST_INGEST=$(cat "$STATE_FILE")
else
    LAST_INGEST="1970-01-01T00:00:00Z"
fi

# Get current timestamp
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log the ingestion attempt
echo "[$(date)] Starting ingestion for documents updated after $LAST_INGEST" >> "$LOG_FILE"

# Call the ingest API
RESPONSE=$(curl -s -X POST http://localhost:8088/ingest \
    -H "Content-Type: application/json" \
    -d "{\"updated_after\": \"$LAST_INGEST\"}" 2>&1)

# Check if successful
if [ $? -eq 0 ]; then
    echo "[$(date)] Ingestion started successfully: $RESPONSE" >> "$LOG_FILE"
    # Update last ingest timestamp
    echo "$CURRENT_TIME" > "$STATE_FILE"
else
    echo "[$(date)] Ingestion failed: $RESPONSE" >> "$LOG_FILE"
fi

# Keep log file size under control (keep last 1000 lines)
tail -n 1000 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
EOF

# Make the script executable
sudo chmod +x /usr/local/bin/paperless-rag-ingest.sh

# Add cron job (every 10 minutes)
echo "Adding cron job for automatic ingestion..."
(sudo crontab -l 2>/dev/null; echo "*/10 * * * * /usr/local/bin/paperless-rag-ingest.sh") | sudo crontab -

echo "✅ Auto-ingestion setup complete!"
echo ""
echo "The system will now automatically:"
echo "- Check for new/updated documents every 10 minutes"
echo "- Only ingest documents that have changed since last run"
echo "- Log activity to /var/lib/paperless-rag/ingest.log"
echo ""
echo "To check ingestion status:"
echo "  sudo tail -f /var/lib/paperless-rag/ingest.log"
echo ""
echo "To manually trigger full re-ingestion:"
echo "  curl -X POST http://localhost:8088/ingest -H 'Content-Type: application/json' -d '{\"force_reindex\": true}'"
