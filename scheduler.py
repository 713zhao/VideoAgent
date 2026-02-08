#!/usr/bin/env python3
"""
Scheduler for automated news bot runs.
Supports daily, hourly, and interval-based scheduling.
"""
import argparse
import time
import schedule
from datetime import datetime
from pathlib import Path

from app.config import load_config
from app.main import run_once


def job(config_path: str):
    """Run the bot once."""
    try:
        print("\n" + "="*80)
        print(f"🤖 SCHEDULED RUN STARTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        run_once(config_path)
        
        print("\n" + "="*80)
        print(f"✅ SCHEDULED RUN COMPLETED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ SCHEDULED RUN FAILED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Error: {e}")
        print("="*80 + "\n")
        # Don't raise - let scheduler continue


def main():
    parser = argparse.ArgumentParser(description="Run news bot on schedule")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()
    
    # Load config
    cfg = load_config(args.config)
    
    if not cfg.scheduler.enabled:
        print("⚠️  Scheduler is disabled in config.yaml")
        print("Set 'scheduler.enabled: true' to enable automatic scheduling")
        return
    
    # Setup schedule based on mode
    mode = cfg.scheduler.mode
    
    print("\n" + "="*80)
    print("🔄 SCHEDULER STARTED")
    print("="*80)
    print(f"Mode: {mode}")
    
    if mode == "daily":
        schedule.every().day.at(cfg.scheduler.time).do(job, args.config)
        print(f"Schedule: Daily at {cfg.scheduler.time}")
        print(f"Next run: {schedule.next_run()}")
        
    elif mode == "hourly":
        schedule.every().hour.do(job, args.config)
        print(f"Schedule: Every hour")
        print(f"Next run: {schedule.next_run()}")
        
    elif mode == "interval":
        minutes = cfg.scheduler.interval_minutes
        schedule.every(minutes).minutes.do(job, args.config)
        print(f"Schedule: Every {minutes} minutes")
        print(f"Next run: {schedule.next_run()}")
        
    else:
        print(f"❌ Unknown schedule mode: {mode}")
        return
    
    # Run immediately if configured
    if cfg.scheduler.run_on_start:
        print("\n▶️  Running immediately (run_on_start is enabled)...")
        job(args.config)
    
    print(f"\n⏰ Scheduler running... Press Ctrl+C to stop")
    print("="*80 + "\n")
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n" + "="*80)
        print("🛑 SCHEDULER STOPPED")
        print("="*80)


if __name__ == "__main__":
    main()
