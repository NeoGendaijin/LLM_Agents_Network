#!/bin/bash

# デフォルトの圧縮率のリスト
COMPRESSION_RATES=(0.1 0.3 0.5 0.7 0.9 1.0)

# Check if there are files in /input (or deeper)
if [ -z "$(find input -type f)" ]; then
    echo "No files found in /input directory. Running generate_networks.py"
    python generate_networks.py
else
    echo "Files found in /input directory. Skipping generate_networks.py"
fi

PIDS=()

# Iterate over each compression rate and run main.py and analysis.py
for RATE in "${COMPRESSION_RATES[@]}"; do
    FORMATTED_RATE=$(echo "$RATE" | tr -d '.')

    # Define output and logs directories
    OUTPUT_DIR="outputs/output_${FORMATTED_RATE}/agent_responses"
    LOG_DIR="outputs/output_${FORMATTED_RATE}/logs"
    ANALYSIS_DIR="outputs/output_${FORMATTED_RATE}/analysis"

    # Create output and log directories
    mkdir -p "$OUTPUT_DIR" "$LOG_DIR"
    echo "Created directories $OUTPUT_DIR and $LOG_DIR"

    # Define log file inside the specific logs directory
    LOG_FILE="$LOG_DIR/main.log"
    echo "Running main.py with compression rate $RATE. Logging to $LOG_FILE"

    # Run main.py with the specified compression rate in the background
    nohup python main.py --compression_rate "$RATE" > "$LOG_FILE" 2>&1 &
    MAIN_PID=$!
    echo "main.py (PID: $MAIN_PID) is running with compression rate $RATE. Output is being written to $LOG_FILE"

    PIDS+=($MAIN_PID)
done

for PID in "${PIDS[@]}"; do
    wait $PID
    echo "Process with PID $PID has finished."
done

echo "All main.py processes have finished."
