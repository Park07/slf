#!/usr/bin/env python3

import os
import subprocess
import json
import glob
from pathlib import Path
from datetime import datetime

DBLP_QUERY_DIR = "/Users/williampark/desktop/dataset/dblp/query_graph"
SLF_DIR = "/Users/williampark/slf"

def create_test_directory():
    """Create a timestamped directory for test outputs"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir = f"data/test_runs/run_{timestamp}"
    os.makedirs(test_dir, exist_ok=True)
    return test_dir, timestamp

def convert_hku_target(test_dir):
    """Convert the full HKU DBLP target graph"""
    print("Converting full HKU DBLP target graph...")
    target_path = f"{test_dir}/dblp_target_full.graph"
    cmd = f"python3 convert_hku_to_slf_fixed.py /Users/williampark/desktop/dataset/dblp/data_graph/dblp.graph {target_path}"
    subprocess.run(cmd, shell=True, cwd=SLF_DIR)
    return target_path

def get_all_queries():
    """Get all query files by category"""
    categories = {
        "small_dense_4": "query_dense_4_*.graph",
        "small_sparse_4": "query_sparse_4_*.graph",
        "small_dense_8": "query_dense_8_*.graph",
        "small_sparse_8": "query_sparse_8_*.graph",
        "medium_dense_16": "query_dense_16_*.graph",
        "medium_sparse_16": "query_sparse_16_*.graph",
        "large_dense_24": "query_dense_24_*.graph",
        "large_sparse_24": "query_sparse_24_*.graph",
        "large_dense_32": "query_dense_32_*.graph",
        "large_sparse_32": "query_sparse_32_*.graph",
    }

    all_queries = {}
    for category, pattern in categories.items():
        files = glob.glob(os.path.join(DBLP_QUERY_DIR, pattern))
        all_queries[category] = sorted(files)
        print(f"{category}: {len(files)} queries found")

    return all_queries

def run_comprehensive_test():
    """Run tests on a representative sample from each category"""
    os.chdir(SLF_DIR)

    # Create timestamped test directory
    test_dir, timestamp = create_test_directory()
    print(f"Created test directory: {test_dir}")

    # Convert the full target to test directory
    target_path = convert_hku_target(test_dir)

    # Get all queries
    all_queries = get_all_queries()

    # Create results file
    results_file = f"{test_dir}/results.csv"

    print(f"\nRunning comprehensive test on representative samples...")
    print("Results will be saved to:", results_file)

    with open(results_file, 'w') as rf:
        rf.write("Category,Query_File,Vertices,Edges,Threads,Mappings,Time_ms,Timeout\n")
        print("Category,Query_File,Vertices,Edges,Threads,Mappings,Time_ms,Timeout")

        for category, query_files in all_queries.items():
            # Test first 5 queries from each category
            for query_file in query_files[:5]:
                query_name = os.path.basename(query_file)
                slf_query = f"{test_dir}/query_{category}_{query_name}"

                # Convert query
                cmd = f"python3 convert_hku_to_slf_fixed.py {query_file} {slf_query}"
                subprocess.run(cmd, shell=True, cwd=SLF_DIR)

                # Get vertex/edge count from original
                with open(query_file, 'r') as f:
                    header = f.readline().strip().split()
                    vertices = int(header[1])
                    edges = int(header[2])

                # Test with different thread counts
                for threads in [1, 4]:
                    config = {
                        "log": {"path": f"{test_dir}/test_{category}_{threads}_{query_name}.log", "level": "info"},
                        "slf": {
                            "thread_number": threads,
                            "graph_format": "grf",
                            "max_log_results": 0,
                            "search_results_limitation": 100000,
                            "search_time_limitation_seconds": 180,
                            "tasks": [{
                                "query": slf_query,
                                "target": target_path
                            }]
                        }
                    }

                    config_file = f"{test_dir}/config_{category}_{threads}_{query_name}.json"
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)

                    # Run experiment
                    result = subprocess.run(f"./build/slf -c {config_file}",
                                          shell=True, capture_output=True, text=True)

                    # Parse results
                    log_file = f"{test_dir}/test_{category}_{threads}_{query_name}.log"
                    mappings, time_ms, timeout = parse_results(log_file)

                    result_line = f"{category},{query_name},{vertices},{edges},{threads},{mappings},{time_ms},{timeout}"
                    print(result_line)
                    rf.write(result_line + "\n")

    print(f"\nTest completed! Results saved in: {test_dir}")
    print(f"Summary file: {results_file}")

def parse_results(log_file):
    """Parse results from log file"""
    try:
        with open(log_file, 'r') as f:
            content = f.read()

        mappings = 0
        time_ms = None
        timeout = True

        if "Find mapping number" in content:
            import re
            match = re.search(r"Find mapping number \[(\d+)\]", content)
            if match:
                mappings = int(match.group(1))
                timeout = False

        if "Total Time cost" in content:
            import re
            match = re.search(r"Total Time cost: \[([0-9.]+)ms\]", content)
            if match:
                time_ms = float(match.group(1))

        return mappings, time_ms, timeout
    except:
        return 0, None, True

if __name__ == "__main__":
    run_comprehensive_test()