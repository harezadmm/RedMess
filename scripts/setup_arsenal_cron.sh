#!/bin/bash
# Setup cron job for daily arsenal scraping
# Runs every day at 3 AM WIB (20:00 UTC previous day)

SCRAPER_SCRIPT="/root/daily_arsenal_scraper.py"
LOG_DIR="/root/.cache/arsenal_scraper/logs"
CRON_TIME="0 20 * * *"  # 3 AM WIB = 20:00 UTC (UTC+7)

# Create log directory
mkdir -p "$LOG_DIR"

# Create wrapper script with logging
cat > /root/arsenal_scraper_wrapper.sh << 'EOF'
#!/bin/bash
LOG_DIR="/root/.cache/arsenal_scraper/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/scraper_$TIMESTAMP.log"

echo "=== Arsenal Scraper Started at $(date) ===" >> "$LOG_FILE"
python3 /root/daily_arsenal_scraper.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
echo "=== Arsenal Scraper Finished at $(date) with exit code $EXIT_CODE ===" >> "$LOG_FILE"

# Keep only last 30 days of logs
find "$LOG_DIR" -name "scraper_*.log" -mtime +30 -delete

exit $EXIT_CODE
EOF

chmod +x /root/arsenal_scraper_wrapper.sh

# Add to crontab
(crontab -l 2>/dev/null | grep -v "arsenal_scraper_wrapper.sh"; echo "$CRON_TIME /root/arsenal_scraper_wrapper.sh") | crontab -

echo "[+] Cron job installed successfully"
echo "[+] Schedule: Daily at 3:00 AM WIB (20:00 UTC)"
echo "[+] Logs: $LOG_DIR"
echo ""
echo "Current crontab:"
crontab -l
