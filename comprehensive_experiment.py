#!/usr/bin/env python3

import os
import subprocess
import json
import glob
from pathlib import Path
from datetime import datetime
import re

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

def classify_query_bycategories(vertices, edges):
    avg_degree = (2 * edges) / vertices if vertices > 0 else 0

    if vertices < 10:
        size = "small"
    elif vertices <= 20:
        size = "medium"
    else:
        size = "large"

    density = "sparse" if avg_degree < 5 else "dense"

    return f"{size}_{density}"

def get_adaptive_config(vertices, edges):
    """Get adaptive timeout and mapping limit based on query complexity"""
    category = classify_query_bycategories(vertices, edges)

    if "small" in category:
        return {
            "timeout": 300,      # 5 minutes
            "limit": 100000,    # 100k mappings
            "priority": "high"   # Run these first
        }
    elif "medium" in category:
        return {
            "timeout": 1800,     # 30 minutes
            "limit": 100000,     # 100K mappings
            "priority": "medium"
        }
    else:  # large
        return {
            "timeout": 1800,     # 30 minutes
            "limit": 100000,      # 100K mappings
            "priority": "low"
        }

def get_all_queries():
    """Get all query files and categorize them by"""
    # Original patterns for backward compatibility
    original_patterns = {
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
    query_categories = {}  # Track which category each query belongs to

    for category, pattern in original_patterns.items():
        files = glob.glob(os.path.join(DBLP_QUERY_DIR, pattern))

        # Sort numerically by extracting the number from filename
        def extract_number(filepath):
            match = re.search(r'_(\d+)\.graph$', filepath)
            return int(match.group(1)) if match else 0

        all_queries[category] = sorted(files, key=extract_number)

        # Categorize each query file
        for query_file in all_queries[category]:
            try:
                with open(query_file, 'r') as f:
                    header = f.readline().strip().split()
                    vertices = int(header[1])
                    edges = int(header[2])
                    category = classify_query_bycategories(vertices, edges)
                    query_categories[query_file] = category
            except:
                query_categories[query_file] = "unknown"

        print(f"{category}: {len(files)} queries found")
        if files:
            print(f"  First 5: {[os.path.basename(f) for f in all_queries[category][:5]]}")

    return all_queries, query_categories

def run_comprehensive_test():
    """Run tests with Dr. Yang's adaptive configuration"""
    os.chdir(SLF_DIR)

    # Create timestamped test directory
    test_dir, timestamp = create_test_directory()
    print(f"Created test directory: {test_dir}")

    # Convert the full target to test directory
    target_path = convert_hku_target(test_dir)

    # Get all queries and their categories
    all_queries, query_categories = get_all_queries()

    # Create results file with additional metrics
    results_file = f"{test_dir}/results.csv"
    completion_file = f"{test_dir}/completion_stats.csv"

    print("Results will be saved to:", results_file)

    # Track completion statistics
    completion_stats = {
        "small_sparse": {"completed": 0, "timeout": 0, "total": 0},
        "small_dense": {"completed": 0, "timeout": 0, "total": 0},
        "medium_sparse": {"completed": 0, "timeout": 0, "total": 0},
        "medium_dense": {"completed": 0, "timeout": 0, "total": 0},
        "large_sparse": {"completed": 0, "timeout": 0, "total": 0},
        "large_dense": {"completed": 0, "timeout": 0, "total": 0},
    }

    with open(results_file, 'w') as rf:
        # Enhanced CSV header
        rf.write("Category,Query_File,Vertices,Edges,Avg_Degree,Y_Category,Threads,Mappings,Time_ms,Timeout,Timeout_Limit_s,Mapping_Limit\n")
        print("Category,Query_File,Vertices,Edges,Avg_Degree,Y_Category,Threads,Mappings,Time_ms,Timeout")

        for category, query_files in all_queries.items():
            # Test first 50 queries from each category (or fewer for testing)
            test_count = min(50, len(query_files))
            for query_file in query_files[:test_count]:
                query_name = os.path.basename(query_file)
                slf_query = f"{test_dir}/query_{category}_{query_name}"

                # Convert query
                print(f"Converting {query_name}...")
                cmd = f"python3 convert_hku_to_slf_fixed.py {query_file} {slf_query}"
                subprocess.run(cmd, shell=True, cwd=SLF_DIR)

                # Get vertex/edge count and classification
                with open(query_file, 'r') as f:
                    header = f.readline().strip().split()
                    vertices = int(header[1])
                    edges = int(header[2])
                    avg_degree = (2 * edges) / vertices if vertices > 0 else 0
                    y_category = query_categories.get(query_file, "unknown")

                # Get adaptive configuration
                config_params = get_adaptive_config(vertices, edges)

                # Update completion stats
                if y_category in completion_stats:
                    completion_stats[y_category]["total"] += 2  # 2 thread configs per query

                # Test with different thread counts - local Mac M2 testing
                for threads in [1, 2, 4]:  # Higher threads (8, 16, 32) for TODS server
                    config = {
                        "log": {"path": f"{test_dir}/test_{category}_{threads}_{query_name}.log", "level": "info"},
                        "slf": {
                            "thread_number": threads,
                            "graph_format": "grf",
                            "max_log_results": 0,
                            "search_results_limitation": config_params["limit"],
                            "search_time_limitation_seconds": config_params["timeout"],
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
                    print(f"Running {y_category} query {query_name} with {threads} threads...")
                    result = subprocess.run(f"./build/slf -c {config_file}",
                                          shell=True, capture_output=True, text=True)

                    # Parse results
                    log_file = f"{test_dir}/test_{category}_{threads}_{query_name}.log"
                    mappings, time_ms, timeout = parse_results(log_file)

                    # Update completion statistics
                    if y_category in completion_stats:
                        if timeout:
                            completion_stats[y_category]["timeout"] += 1
                        else:
                            completion_stats[y_category]["completed"] += 1

                    # Enhanced result line with Dr. Yang's categories
                    result_line = f"{category},{query_name},{vertices},{edges},{avg_degree:.2f},{y_category},{threads},{mappings},{time_ms},{timeout},{config_params['timeout']},{config_params['limit']}"
                    print(result_line)
                    rf.write(result_line + "\n")

    # Write completion statistics
    with open(completion_file, 'w') as cf:
        cf.write("Y_Category,Total_Tests,Completed,Timeout,Completion_Rate\n")
        for category, stats in completion_stats.items():
            if stats["total"] > 0:
                completion_rate = stats["completed"] / stats["total"]
                cf.write(f"{category},{stats['total']},{stats['completed']},{stats['timeout']},{completion_rate:.3f}\n")

    print(f"\nTest completed! Results saved in: {test_dir}")
    print(f"Main results: {results_file}")
    print(f"Completion stats: {completion_file}")

    # Print completion summary
    print(f"\n=== COMPLETION RATE SUMMARY ===")
    for category, stats in completion_stats.items():
        if stats["total"] > 0:
            completion_rate = stats["completed"] / stats["total"]
            print(f"{category}: {completion_rate:.1%} ({stats['completed']}/{stats['total']})")

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