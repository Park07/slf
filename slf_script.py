#!/usr/bin/env python3
import os
import subprocess
import json
import glob
import re
from datetime import datetime
import sys

# --- 1. CONFIGURATION TO MATCH GRAPHMINI ---
SLF_DIR = "/home/williamp/slf"
THESIS_DATA_ROOT = "/home/williamp/thesis_data"

# Updated to use SAME query sources as GraphMini
DATASETS_CONFIG = {
    "dblp": {
        "query_root": f"{THESIS_DATA_ROOT}/query_sets/dblp",  # Same as GraphMini
        "data_graph": f"{THESIS_DATA_ROOT}/processed_datasets/dblp/data.graph"
    },
    "youtube": {
        "query_root": f"{THESIS_DATA_ROOT}/query_sets/youtube",  # Same as GraphMini
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

# --- 2. MATCH GRAPHMINI'S PATTERN TESTING STRATEGY ---
def get_graphmini_pattern_categories():
    """Returns the same categories that GraphMini tests"""
    return ["small_dense_4v", "small_sparse_4v", "small_dense_8v", "small_sparse_8v",
            "medium_dense", "medium_sparse", "large_dense", "large_sparse"]

def get_pattern_indices_for_category(category):
    """Match GraphMini's pattern selection strategy but limit to 1 pattern"""
    if "4v" in category:
        # Test only 1 pattern for 4-vertex (fast testing)
        return [1]  # Just pattern 1
    else:
        # Test only 1 pattern for 8v+ (like GraphMini, due to known issues)
        return [1]

def classify_query_like_graphmini(query_file):
    """Classify queries to match GraphMini's categories"""
    # Extract category from path structure (same as GraphMini uses)
    path_parts = query_file.split('/')
    for part in path_parts:
        if part in get_graphmini_pattern_categories():
            return part

    # Fallback: classify by vertices/edges if not in structured path
    try:
        with open(query_file, 'r') as f:
            header = f.readline().strip().split()
            vertices, edges = int(header[1]), int(header[2])

        if vertices == 4:
            avg_degree = (2 * edges) / vertices
            density = "dense" if avg_degree >= 3 else "sparse"
            return f"small_{density}_4v"
        elif vertices == 8:
            avg_degree = (2 * edges) / vertices
            density = "dense" if avg_degree >= 4 else "sparse"
            return f"small_{density}_8v"
        else:
            avg_degree = (2 * edges) / vertices
            size = "medium" if vertices <= 20 else "large"
            density = "dense" if avg_degree >= 5 else "sparse"
            return f"{size}_{density}"
    except:
        return "unknown"

def get_adaptive_config(category):
    """Match GraphMini's timeout strategy"""
    if "4v" in category or "small" in category:
        return {"timeout": 240, "limit": -1}  # No limit for fair comparison
    else:
        return {"timeout": 240, "limit": -1}  # No limit for fair comparison

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

# --- 3. MAIN EXECUTION TO MATCH GRAPHMINI ---
def run_slf_tests_matching_graphmini():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parent_results_dir = f"{SLF_DIR}/results/slf_graphmini_match_{timestamp}"
    os.makedirs(parent_results_dir, exist_ok=True)

    print(f"✅ SLF Framework Initialized to match GraphMini patterns")
    print(f"📁 Results directory: {parent_results_dir}")
    print(f"🎯 Testing SAME patterns as GraphMini for fair comparison")

    for dataset_name, paths in DATASETS_CONFIG.items():
        dataset_results_dir = f"{parent_results_dir}/{dataset_name}"
        os.makedirs(dataset_results_dir, exist_ok=True)
        results_csv = f"{dataset_results_dir}/slf_results_{dataset_name}.csv"

        print(f"\n🚀 Dataset: {dataset_name}")
        print(f"📊 Query source: {paths['query_root']}")

        # Use GraphMini's CSV format for consistency
        with open(results_csv, 'w') as f:
            f.write("Dataset,PatternCategory,QueryFile,QueryVertices,QueryEdges,Threads,ExecutionTime_s,Result_Count,Memory_MB,Status,Notes\n")

        # Prepare data graph
        target_graph_grf_path = f"{dataset_results_dir}/data_graph_{dataset_name}.grf"
        subprocess.run(f"python3 {SLF_DIR}/hku_to_grf.py \"{paths['data_graph']}\" \"{target_graph_grf_path}\"", shell=True, check=True)

        # Test each category that GraphMini tests
        for category in get_graphmini_pattern_categories():
            category_path = f"{paths['query_root']}/{category}"

            if not os.path.exists(category_path):
                print(f"⚠️  Category {category} not found, skipping")
                continue

            print(f"\n--- Testing Category: {category} (matching GraphMini) ---")

            # Get pattern indices to test (same strategy as GraphMini)
            pattern_indices = get_pattern_indices_for_category(category)
            print(f"   Testing {len(pattern_indices)} patterns ({'all patterns' if len(pattern_indices) > 5 else 'limited patterns'})")

            for pattern_index in pattern_indices:
                # Find the pattern file (same naming as GraphMini expects)
                pattern_files = glob.glob(f"{category_path}/query_sample_*v_{pattern_index}.graph")

                if not pattern_files:
                    print(f"   Pattern {pattern_index} not found in {category}")
                    continue

                query_file = pattern_files[0]  # Take first match
                query_name = os.path.basename(query_file)

                # Get pattern info
                try:
                    with open(query_file, 'r') as f:
                        header = f.readline().strip().split()
                        vertices, edges = int(header[1]), int(header[2])
                except:
                    print(f"   Could not parse {query_name}, skipping")
                    continue

                print(f"   Pattern {pattern_index}: {query_name} ({vertices}v, {edges}e)")

                # Convert to GRF format
                query_path_grf = f"{dataset_results_dir}/query_{query_name}.grf"
                subprocess.run(f"python3 {SLF_DIR}/hku_to_grf.py \"{query_file}\" \"{query_path_grf}\"", shell=True, check=True)

                config = get_adaptive_config(category)

                for threads in THREAD_COUNTS:
                    print(f"     {threads}t: ", end="", flush=True)

                    log_file = f"{dataset_results_dir}/log_{query_name}_{threads}t.log"
                    config_data = {
                        "log": {"path": log_file, "level": "info"},
                        "slf": {
                            "thread_number": threads,
                            "graph_format": "grf",
                            "search_results_limitation": -1,  # No limit for fair comparison
                            "search_time_limitation_seconds": config["timeout"],
                            "tasks": [{"query": query_path_grf, "target": target_graph_grf_path}]
                        }
                    }

                    config_path = f"{dataset_results_dir}/config_run.json"
                    with open(config_path, 'w') as f:
                        json.dump(config_data, f, indent=2)

                    cmd = f"/usr/bin/time -v ./build/slf -c {config_path}"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=SLF_DIR)

                    status = "SUCCESS" if result.returncode == 0 else f"FAILED (code {result.returncode})"
                    mappings, time_ms, timeout, mem_mb = parse_slf_results(log_file, result.stderr)

                    if timeout:
                        status = "TIMEOUT"

                    exec_time_s = f"{time_ms / 1000.0:.4f}" if time_ms is not None else "N/A"

                    # Match GraphMini's success output format
                    if status == "SUCCESS":
                        print(f"✅ {exec_time_s}s, {mappings} matches")
                    else:
                        print(f"❌ {status}")

                    # Write in same format as GraphMini
                    pattern_name = f"{category}_{pattern_index}"
                    with open(results_csv, 'a') as f:
                        f.write(f"{dataset_name},{category},{pattern_name},{vertices},{edges},{threads},{exec_time_s},{mappings},{mem_mb},{status},limit={config['limit']}\n")

                # Stop testing more patterns in this category if we hit issues (like GraphMini does)
                if "8v" in category or "large" in category:
                    break  # Only test one pattern for problematic categories

    print("\n" + "="*60)
    print("✅ SLF TESTING COMPLETE - MATCHING GRAPHMINI PATTERNS")
    print("="*60)
    print(f"📊 Results saved in: {parent_results_dir}")
    print("🎯 Now you can fairly compare SLF vs GraphMini vs GraphMini-O!")

if __name__ == "__main__":
    run_slf_tests_matching_graphmini()