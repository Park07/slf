#!/usr/bin/env python3
import os
import subprocess
import json
import glob
import re
from datetime import datetime
import sys

# --- 1. FINAL CONFIGURATION ---
SLF_DIR = "/home/williamp/slf"
THESIS_DATA_ROOT = "/home/williamp/thesis_data"

# This dictionary defines all datasets for the final experimental run.
DATASETS_CONFIG = {
    "dblp": {
        "query_root": f"{THESIS_DATA_ROOT}/raw_datasets/dblp/query_graph",
        "data_graph": f"{THESIS_DATA_ROOT}/processed_datasets/dblp/data.graph"
    },
    "youtube": {
        "query_root": f"{THESIS_DATA_ROOT}/raw_datasets/youtube/query_graph",
        "data_graph": f"{THESIS_DATA_ROOT}/processed_datasets/youtube/data.graph"
    },
    "roadNet-CA": {
        "query_root": f"{THESIS_DATA_ROOT}/query_sets/roadNet-CA",
        "data_graph": f"{THESIS_DATA_ROOT}/processed_datasets/roadNet-CA/data.graph"
    },
    "enron": {
        "query_root": f"{THESIS_DATA_ROOT}/query_sets/enron",
        "data_graph": f"{THESIS_DATA_ROOT}/processed_datasets/enron/data.graph"
    },
    "lj": {
        "query_root": f"{THESIS_DATA_ROOT}/query_sets/lj",
        "data_graph": f"{THESIS_DATA_ROOT}/processed_datasets/lj/data.graph"
    },
    "wiki": {
        "query_root": f"{THESIS_DATA_ROOT}/query_sets/wiki",
        "data_graph": f"{THESIS_DATA_ROOT}/processed_datasets/wiki/data.graph"
    }
}
THREAD_COUNTS = [1, 4, 16, 32, 64]
QUERIES_PER_CATEGORY = 5

# --- 2. HELPER FUNCTIONS ---
def classify_query(vertices, edges):
    avg_degree = (2 * edges) / vertices if vertices > 0 else 0
    size_str = "small" if vertices < 10 else "medium" if vertices <= 20 else "large"
    density_str = "sparse" if avg_degree < 5 else "dense"

    if size_str == "small":
        return f"{size_str}_{density_str}_{vertices}v"
    return f"{size_str}_{density_str}"

def get_adaptive_config(vertices, edges):
    category = classify_query(vertices, edges)
    if "small" in category:
        return {"timeout": 300, "limit": 100000}
    else:
        return {"timeout": 1800, "limit": 100000}

def parse_slf_results(log_file, time_log_content):
    mappings, time_ms, timeout = 0, None, True
    try:
        with open(log_file, 'r') as f:
            content = f.read()
        mappings_match = re.search(r"Find mapping number \[(\d+)\]", content)
        time_match = re.search(r"Total Time cost: \[([0-9.]+)ms\]", content)
        if mappings_match:
            mappings = int(mappings_match.group(1))
            timeout = False
        if time_match:
            time_ms = float(time_match.group(1))
    except FileNotFoundError:
        pass

    mem_kb_match = re.search(r"Maximum resident set size \(kbytes\): (\d+)", time_log_content)
    mem_mb = f"{float(mem_kb_match.group(1)) / 1024.0:.1f}" if mem_kb_match else "N/A"

    return mappings, time_ms, timeout, mem_mb

# --- 3. MAIN EXECUTION SCRIPT ---
def run_all_slf_tests():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parent_results_dir = f"{SLF_DIR}/results/slf_unified_run_{timestamp}"
    os.makedirs(parent_results_dir, exist_ok=True)
    print(f"✅ SLF Framework Initialized. All results will be saved in: {parent_results_dir}")

    for dataset_name, paths in DATASETS_CONFIG.items():
        dataset_results_dir = f"{parent_results_dir}/{dataset_name}"
        os.makedirs(dataset_results_dir, exist_ok=True)
        results_csv = f"{dataset_results_dir}/slf_results_{dataset_name}.csv"
        print(f"\n🚀 Starting test run for dataset: '{dataset_name}'")
        print(f"   Results will be saved in: {results_csv}")
        with open(results_csv, 'w') as f:
            f.write("Dataset,PatternCategory,QueryFile,QueryVertices,QueryEdges,Threads,ExecutionTime_s,Result_Count,Memory_MB,Status,Notes\n")

        print(f"   Preparing data graph '{dataset_name}' for SLF's GRF format...")
        target_graph_grf_path = f"{dataset_results_dir}/data_graph_{dataset_name}.grf"
        subprocess.run(f"python3 {SLF_DIR}/hku_to_grf.py \"{paths['data_graph']}\" \"{target_graph_grf_path}\"", shell=True, check=True)

        query_files = glob.glob(os.path.join(paths['query_root'], "**/*.graph"), recursive=True)

        categorized_queries = {}
        for qf in query_files:
            try:
                with open(qf, 'r') as f:
                    header = f.readline().strip().split()
                    vertices, edges = int(header[1]), int(header[2])
                category = classify_query(vertices, edges)
                if category not in categorized_queries: categorized_queries[category] = []
                categorized_queries[category].append(qf)
            except Exception as e:
                print(f"⚠️  Could not parse {os.path.basename(qf)}: {e}", file=sys.stderr)

        processing_order = sorted(categorized_queries.keys())
        for category in processing_order:
            files = categorized_queries[category]
            print(f"\n====================== Processing Category: {category} ======================")

            def extract_number(filepath):
                match = re.search(r'_(\d+)\.graph$', filepath)
                return int(match.group(1)) if match else 0
            sorted_files = sorted(files, key=extract_number)

            queries_to_run = sorted_files[:QUERIES_PER_CATEGORY]
            for i, query_file in enumerate(queries_to_run, 1):
                query_name = os.path.basename(query_file)
                with open(query_file, 'r') as f:
                    header = f.readline().strip().split()
                    vertices, edges = int(header[1]), int(header[2])

                print(f"\n--- [{dataset_name} | {category}] Query {i} of {len(queries_to_run)}: {query_name} ({vertices}v, {edges}e) ---")

                query_path_grf = f"{dataset_results_dir}/query_{query_name}.grf"
                subprocess.run(f"python3 {SLF_DIR}/hku_to_grf.py \"{query_file}\" \"{query_path_grf}\"", shell=True, check=True)

                config = get_adaptive_config(vertices, edges)
                for threads in THREAD_COUNTS:
                    print(f"  -> Running with {threads} threads...")
                    log_file = f"{dataset_results_dir}/log_{query_name}_{threads}t.log"
                    config_data = {
                        "log": {"path": log_file, "level": "info"},
                        "slf": { "thread_number": threads, "graph_format": "grf", "search_results_limitation": config["limit"],
                                 "search_time_limitation_seconds": config["timeout"], "tasks": [{"query": query_path_grf, "target": target_graph_grf_path}]}
                    }
                    config_path = f"{dataset_results_dir}/config_run.json"
                    with open(config_path, 'w') as f: json.dump(config_data, f, indent=2)

                    cmd = f"/usr/bin/time -v ./build/slf -c {config_path}"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=SLF_DIR)

                    status = "SUCCESS" if result.returncode == 0 else f"FAILED (code {result.returncode})"
                    mappings, time_ms, timeout, mem_mb = parse_slf_results(log_file, result.stderr)
                    if timeout: status = "TIMEOUT"
                    exec_time_s = f"{time_ms / 1000.0:.4f}" if time_ms is not None else "N/A"

                    print(f"     -> Status: {status}, Time: {exec_time_s}s, Results: {mappings}, Memory: {mem_mb} MB")
                    with open(results_csv, 'a') as f:
                        f.write(f"{dataset_name},{category},{query_name},{vertices},{edges},{threads},{exec_time_s},{mappings},{mem_mb},{status},limit={config['limit']}\n")

    print("\n=========================================\n✅ SLF ANALYSIS COMPLETE\n=========================================")

if __name__ == "__main__":
    run_all_slf_tests()
    