#!/usr/bin/env python3

import os
import subprocess
import json
import glob
import re
from datetime import datetime
import sys

# --- 1. CONFIGURATION ---
SLF_DIR = "/Users/williampark/slf"
DATASETS = {
    "dblp": {
        "query_root": "/Users/williampark/desktop/dataset/dblp/query_graph",
        "data_graph": "/Users/williampark/desktop/dataset/dblp/data_graph/dblp.graph"
    }
    #"roadNet-CA": {
    #    "query_root": "/Users/williampark/desktop/dataset/roadNet-CA/query_graph",
    #    "data_graph": "/Users/williampark/graphmini/dataset/GraphMini/roadNet-CA/snap.graph"
    #}
}

# --- 2. HELPER FUNCTIONS (unchanged) ---
def classify_query(vertices, edges):
    avg_degree = (2 * edges) / vertices if vertices > 0 else 0
    if vertices < 10: size = "small"
    elif vertices <= 20: size = "medium"
    else: size = "large"
    density = "sparse" if avg_degree < 5 else "dense"
    return f"{size}_{density}"

def get_adaptive_config(vertices, edges):
    category = classify_query(vertices, edges)
    if "small" in category:
        return {"timeout": 300, "limit": 100000}
    else:
        return {"timeout": 1800, "limit": 100000}

def parse_slf_results(log_file):
    try:
        with open(log_file, 'r') as f: content = f.read()
        mappings_match = re.search(r"Find mapping number \[(\d+)\]", content)
        time_match = re.search(r"Total Time cost: \[([0-9.]+)ms\]", content)
        mappings = int(mappings_match.group(1)) if mappings_match else 0
        time_ms = float(time_match.group(1)) if time_match else None
        timeout = False if mappings_match else True
        return mappings, time_ms, timeout
    except FileNotFoundError:
        return 0, None, True

# --- 3. MAIN EXECUTION SCRIPT ---
def run_slf_tests():
    # MODIFIED: Create a single parent directory for the entire run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parent_results_dir = f"{SLF_DIR}/results/slf_unified_run_{timestamp}"
    os.makedirs(parent_results_dir, exist_ok=True)
    print(f"✅ SLF Framework Initialized. All results will be saved in: {parent_results_dir}")

    for dataset_name, paths in DATASETS.items():
        # MODIFIED: Create a subdirectory for each dataset
        dataset_results_dir = f"{parent_results_dir}/{dataset_name}"
        os.makedirs(dataset_results_dir, exist_ok=True)

        results_csv = f"{dataset_results_dir}/slf_results_{dataset_name}.csv"
        print(f"\n🚀 Starting test run for dataset: '{dataset_name}'")
        print(f"   Results will be saved in: {results_csv}")
        with open(results_csv, 'w') as f:
            f.write("Dataset,PatternCategory,QueryFile,QueryVertices,QueryEdges,Threads,ExecutionTime_s,Result_Count,Status,Notes\n")

        print(f"   Preparing data graph '{dataset_name}' for GRF format...")
        target_graph_grf_path = f"{dataset_results_dir}/data_graph_{dataset_name}.grf"
        subprocess.run(f"python3 {SLF_DIR}/hku_to_grf.py \"{paths['data_graph']}\" \"{target_graph_grf_path}\"", shell=True, check=True)

        query_files = glob.glob(os.path.join(paths['query_root'], "*.graph"))
        categorized_queries = { "small_sparse": [], "small_dense": [], "medium_sparse": [], "medium_dense": [], "large_sparse": [], "large_dense": [] }
        for qf in query_files:
            try:
                with open(qf, 'r') as f:
                    header = f.readline().strip().split()
                    vertices, edges = int(header[1]), int(header[2])
                    category = classify_query(vertices, edges)
                    if category in categorized_queries:
                        categorized_queries[category].append(qf)
            except Exception as e:
                print(f"  Could not parse {os.path.basename(qf)}: {e}")

        processing_order = ["small_dense", "small_sparse", "medium_dense", "medium_sparse", "large_dense", "large_sparse"]
        for category in processing_order:
            files = categorized_queries.get(category, [])
            if not files: continue

            print(f"\n====================== Processing Category: {category} ======================")
            def extract_number(filepath):
                match = re.search(r'_(\d+)\.graph$', filepath)
                return int(match.group(1)) if match else 0
            sorted_files = sorted(files, key=extract_number)

            for query_file in sorted_files[:50]:
                query_name = os.path.basename(query_file)
                with open(query_file, 'r') as f:
                    header = f.readline().strip().split()
                    vertices, edges = int(header[1]), int(header[2])
                print(f"\n--- Testing: {query_name} ({vertices}v, {edges}e) ---")

                query_path_grf = f"{dataset_results_dir}/query_{query_name}.grf"
                subprocess.run(f"python3 {SLF_DIR}/hku_to_grf.py \"{query_file}\" \"{query_path_grf}\"", shell=True, check=True)

                config = get_adaptive_config(vertices, edges)
                for threads in [1, 2, 4]:
                    print(f"  -> Running with {threads} threads...")
                    config_data = {
                        "log": {"path": f"{dataset_results_dir}/log_{query_name}_{threads}t.log", "level": "info"},
                        "slf": {
                            "thread_number": threads, "graph_format": "grf",
                            "search_results_limitation": config["limit"],
                            "search_time_limitation_seconds": config["timeout"],
                            "tasks": [{"query": query_path_grf, "target": target_graph_grf_path}]
                        }
                    }
                    config_path = f"{dataset_results_dir}/config_run.json"
                    with open(config_path, 'w') as f: json.dump(config_data, f, indent=2)

                    cmd = f"./build/slf -c {config_path}"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=SLF_DIR)

                    status = "SUCCESS" if result.returncode == 0 else f"FAILED (code {result.returncode})"
                    mappings, time_ms, timeout = parse_slf_results(f"{dataset_results_dir}/log_{query_name}_{threads}t.log")
                    if timeout: status = "TIMEOUT"
                    exec_time_s = time_ms / 1000.0 if time_ms is not None else "N/A"
                    print(f"     -> Status: {status}, Time: {exec_time_s}s, Results: {mappings}")
                    with open(results_csv, 'a') as f:
                        f.write(f"{dataset_name},{category},{query_name},{vertices},{edges},{threads},{exec_time_s},{mappings},{status},limit={config['limit']}\n")

    print("\n=========================================\n COMPLETE\n=========================================")

if __name__ == "__main__":
    run_slf_tests()