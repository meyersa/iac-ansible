#!/bin/bash
# Script to check WARP CLI status and restart the service if needed

status=$(warp-cli status | grep "Status update: Connected")

if [[ -z "$status" ]]; then
  # Restart the WARP service if not connected
  systemctl restart warp-svc.service
fi
