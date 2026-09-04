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
