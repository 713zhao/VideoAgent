# Scheduler Guide

The news bot includes an automated scheduler that can run the bot at specified times and intervals.

## Configuration

Edit `config.yaml` to configure the scheduler:

```yaml
scheduler:
  enabled: true  # Set to true to enable scheduling
  mode: "daily"  # Options: "daily", "hourly", "interval"
  time: "08:00"  # For daily mode: 24-hour format (HH:MM)
  interval_minutes: 60  # For interval mode: minutes between runs
  run_on_start: false  # If true, runs immediately when scheduler starts
```

## Schedule Modes

### 1. Daily Mode
Runs once per day at a specific time.

```yaml
scheduler:
  enabled: true
  mode: "daily"
  time: "08:00"  # Runs every day at 8:00 AM
```

**Example times:**
- `"08:00"` - 8:00 AM
- `"14:30"` - 2:30 PM
- `"23:00"` - 11:00 PM

### 2. Hourly Mode
Runs every hour on the hour.

```yaml
scheduler:
  enabled: true
  mode: "hourly"
```

### 3. Interval Mode
Runs at regular intervals (in minutes).

```yaml
scheduler:
  enabled: true
  mode: "interval"
  interval_minutes: 120  # Every 2 hours
```

**Common intervals:**
- `30` - Every 30 minutes
- `60` - Every hour
- `120` - Every 2 hours
- `360` - Every 6 hours

## Running the Scheduler

### Basic Usage

```bash
# Activate virtual environment (if using)
.\env\Scripts\Activate.ps1  # Windows
# or
source env/bin/activate  # Linux/Mac

# Start the scheduler
python scheduler.py
```

### With Custom Config

```bash
python scheduler.py --config my_config.yaml
```

### Output

When the scheduler starts, you'll see:

```
================================================================================
🔄 SCHEDULER STARTED
================================================================================
Mode: daily
Schedule: Daily at 08:00
Next run: 2026-02-09 08:00:00

⏰ Scheduler running... Press Ctrl+C to stop
================================================================================
```

### Stopping the Scheduler

Press `Ctrl+C` to stop the scheduler gracefully.

## Running on Startup

To keep the scheduler running continuously (e.g., on a server):

### Windows - Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "When the computer starts")
4. Action: Start a program
   - Program: `C:\path\to\python.exe`
   - Arguments: `C:\path\to\scheduler.py`
   - Start in: `C:\path\to\project`

### Linux - systemd Service

Create `/etc/systemd/system/news-bot.service`:

```ini
[Unit]
Description=AI News Bot Scheduler
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/python /path/to/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable news-bot
sudo systemctl start news-bot
sudo systemctl status news-bot
```

### Linux - cron (Alternative)

For simple daily runs, use cron:

```bash
# Edit crontab
crontab -e

# Add line (runs daily at 8:00 AM)
0 8 * * * cd /path/to/project && /path/to/venv/bin/python scheduler.py
```

## Run on Start Option

If you want the bot to run immediately when the scheduler starts (useful for testing or ensuring first run):

```yaml
scheduler:
  enabled: true
  mode: "daily"
  time: "08:00"
  run_on_start: true  # Runs immediately, then follows schedule
```

## Examples

### Morning News Digest
```yaml
scheduler:
  enabled: true
  mode: "daily"
  time: "07:00"
  run_on_start: false
```

### Frequent Updates
```yaml
scheduler:
  enabled: true
  mode: "interval"
  interval_minutes: 180  # Every 3 hours
  run_on_start: true
```

### Hourly News Monitoring
```yaml
scheduler:
  enabled: true
  mode: "hourly"
  run_on_start: false
```

## Troubleshooting

### Scheduler won't start

**Check if enabled:**
```yaml
scheduler:
  enabled: true  # Must be true
```

### Time format errors

Use 24-hour format with leading zeros:
- ✅ `"08:00"`, `"14:30"`, `"23:45"`
- ❌ `"8:00"`, `"2:30 PM"`, `"11:45pm"`

### Missed runs

The scheduler uses the system time. If your computer is off or sleeping when a scheduled run should occur, that run will be skipped.

For critical schedules, use `run_on_start: true` to ensure at least one run when the scheduler restarts.

### Logs

The scheduler prints status messages to stdout. To save logs:

**Windows:**
```powershell
python scheduler.py > logs\scheduler.log 2>&1
```

**Linux/Mac:**
```bash
python scheduler.py > logs/scheduler.log 2>&1 &
```

## Combining with Video Disable

To run frequently without generating videos (faster):

```yaml
video:
  enabled: false  # Skip video generation

scheduler:
  enabled: true
  mode: "interval"
  interval_minutes: 30  # Run every 30 minutes
```

This will generate summaries and send emails quickly without the overhead of video rendering.
