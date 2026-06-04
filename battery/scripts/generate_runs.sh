#!/bin/bash

# Automation script to trigger 100 runs for 100 days
# Usage: ./generate_runs.sh [setup_id] [start_date]
# Example: ./generate_runs.sh 1 2025-01-01

SETUP_ID=${1:-1}
START_DATE=${2:-"2025-01-01"}
API_URL="http://localhost:8000/api/jobs/trigger-full"

echo "🚀 Starting 100 runs for Setup ID $SETUP_ID starting from $START_DATE..."

current_date="$START_DATE"

for i in {1..100}; do
    # Calculate next day for a 1-day range (start to end is same day in our inclusive logic)
    # or we can do 1-day increments
    end_date="$current_date"
    
    echo "[$i/100] Triggering job for $current_date..."
    
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"setup_id\": $SETUP_ID,
            \"start_date\": \"$current_date\",
            \"end_date\": \"$end_date\",
            \"alpha\": 0.001,
            \"grid_fee\": 0.01
        }")
    
    echo "   Response: $response"
    
    # Increment date using date command (OSX/BSD syntax vs Linux handled)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        current_date=$(date -j -v+1d -f "%Y-%m-%d" "$current_date" +"%Y-%m-%d")
    else
        current_date=$(date -I -d "$current_date + 1 day")
    fi
    
    # Small sleep to avoid overwhelming the task queue instantly
    sleep 0.5
done

echo "✅ Finished triggering 100 jobs."
