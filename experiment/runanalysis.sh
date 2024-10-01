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

for RATE in "${COMPRESSION_RATES[@]}"; do
    # フォーマットした圧縮率をディレクトリ名に使用（小数点を取り除く）
    FORMATTED_RATE=$(echo "$RATE" | tr -d '.')

    ANALYSIS_DIR="outputs/output_${FORMATTED_RATE}/analysis"

    mkdir -p "$ANALYSIS_DIR"
    echo "Created directory $ANALYSIS_DIR"

    # Run analysis.py for the current compression rate
    echo "Running analysis.py for compression rate $RATE"
    python analysis.py --compression_rate "$RATE" --root_dir "$(pwd)"
    echo "analysis.py for compression rate $RATE has finished."
done

echo "All analysis.py processes have finished."
