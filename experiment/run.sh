#!/bin/bash

# デフォルトの圧縮率のリスト
COMPRESSION_RATES=(0.3 0.5 0.7)

# Directory for logs
LOG_DIR="output/logs"

# Create the logs directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "Created directory $LOG_DIR for logs."
fi

# Check if there are files in /input (or deeper)
if [ -z "$(find input -type f)" ]; then
    echo "No files found in /input directory. Running generate_networks.py."
    python generate_networks.py
else
    echo "Files found in /input directory. Skipping generate_networks.py."
fi

# Iterate over each compression rate and run main.py
for RATE in "${COMPRESSION_RATES[@]}"; do
    LOG_FILE="$LOG_DIR/main_compression_rate_${RATE}.log"
    echo "Running main.py with compression rate $RATE. Logging to $LOG_FILE"

    # Run main.py with the specified compression rate in the background
    nohup python main.py --compression_rate "$RATE" > "$LOG_FILE" 2>&1 &
    MAIN_PID=$!
    echo "main.py (PID: $MAIN_PID) is running with compression rate $RATE. Output is being written to $LOG_FILE"
done

# Wait for all background processes to finish
wait
echo "All main.py processes have finished."
