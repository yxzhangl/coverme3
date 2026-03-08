#!/bin/bash
# distance_compare.sh - 修复最终版

set -e

# ============ 配置区域 ============
BENCHMARK="s_ceil"
N_ITER=100
OUTPUT_DIR="output"
# ==================================

mkdir -p "$OUTPUT_DIR"

declare -A DIST_MAP=(
    [0]="absolute"
    [1]="relative" 
    [3]="normalized"
    [4]="log"
    [99]="auto"
)

echo "🚀 Starting distance strategy comparison..."
echo "Benchmark: $BENCHMARK, Iterations: $N_ITER"
echo ""

for dist_id in "${!DIST_MAP[@]}"; do
    dist_name="${DIST_MAP[$dist_id]}"
    output_file="$OUTPUT_DIR/${BENCHMARK}_dist${dist_id}_${dist_name}.log"
    
    echo "▶️  Running with [$dist_id:$dist_name] ..."
    python3 bva.py \
        -r \
        -d "$dist_id" \
        -n "$N_ITER" \
        -v 1 \
        2>&1 | tee "$output_file"
    
    if grep -qi "coverage" "$output_file"; then
        coverage=$(grep -i "coverage" "$output_file" | tail -1 | grep -oE '[0-9]+\.?[0-9]*' | head -1)
        echo "   ✓ Coverage: ${coverage:-N/A}"
    else
        echo "   ⚠️  No coverage found (check $output_file for details)"
    fi
    echo ""
done

echo "✅ All strategies completed. Results in $OUTPUT_DIR/"