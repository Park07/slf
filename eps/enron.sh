cd ~/slf

mkdir -p test_runs/eps_experiments

cat > test_runs/eps_experiments/run_enron_tiered_EPS.sh << 'SCRIPT'
#!/bin/bash
cd ~/slf

# Tiered time limits by vertex size
declare -A TIME_LIMITS=(
    [8]=30
    [16]=180
    [24]=180
    [32]=600
)

THREADS="1 4 8 16 32 48 64"
TRIAL_COUNT=2

DATASET="enron"
EXECUTABLE="./build/slf"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="results/eps_${TIMESTAMP}"
CSV_FILE="${RESULTS_DIR}/enron_original_tiered_EPS.csv"
DATA_GRAPH="${DATASET}_converted/data.graph"
QUERY_DIR="${DATASET}_converted"

echo "=== Running Tiered EPS Experiment ==="
echo "Results: $RESULTS_DIR"
echo "Threads: $THREADS"
echo "Trials: $TRIAL_COUNT per query"
mkdir -p "$RESULTS_DIR"

echo "Dataset,Query,QuerySize,Threads,Trial,TimeLimit_s,Time_s,Count,Status,EPS" > $CSV_FILE

for threads in $THREADS; do
    echo "=== Threads: $threads ==="

    find "$QUERY_DIR" -name "query_sparse_*.graph" -o -name "query_dense_*.graph" | sort | while read query_path; do
        qname=$(basename "$query_path")
        vsize=$(echo "$qname" | grep -oP '(\d+)v' | grep -oP '\d+')

        TIME_LIMIT_S=${TIME_LIMITS[$vsize]}
        TIMEOUT_S=$((TIME_LIMIT_S + 10))

        echo "  $qname (${vsize}v, T=${TIME_LIMIT_S}s)"

        for trial in $(seq 1 $TRIAL_COUNT); do
            UNIQUE_LOG="${RESULTS_DIR}/temp_log_${threads}_${qname}_${trial}.log"
            CONFIG_FILE="${RESULTS_DIR}/tmp_config.json"

            > $UNIQUE_LOG
            cat > $CONFIG_FILE << EOF
{"log":{"path":"$UNIQUE_LOG"},"slf":{"thread_number":$threads,"graph_format":"grf","search_results_limitation":0,"search_time_limitation_seconds":$TIME_LIMIT_S,"tasks":[{"query":"$query_path","target":"$DATA_GRAPH"}]}}
EOF

            start=$(date +%s.%N)
            timeout $TIMEOUT_S $EXECUTABLE -c $CONFIG_FILE > /dev/null 2>&1
            status_code=$?
            end=$(date +%s.%N)

            time=$(echo "$end - $start" | bc)
            count=$(grep -oP 'Find mapping number \[\K[0-9]+' $UNIQUE_LOG | tail -n 1)
            [ -z "$count" ] && count=0

            status="SUCCESS"
            [ "$status_code" -eq 124 ] && status="TIMEOUT"
            [ "$count" -eq 0 ] && [ "$status" != "TIMEOUT" ] && status="ERROR"

            eps=0
            [ $(echo "$time > 0" | bc -l) -eq 1 ] && eps=$(echo "scale=2; $count / $time" | bc -l)

            echo "$DATASET,$qname,$vsize,$threads,$trial,$TIME_LIMIT_S,$time,$count,$status,$eps" >> $CSV_FILE

            rm -f $UNIQUE_LOG $CONFIG_FILE
        done
    done
done

echo "✅ TIERED EPS COMPLETE: $CSV_FILE"
SCRIPT

chmod +x test_runs/eps_experiments/run_enron_tiered_EPS.sh
