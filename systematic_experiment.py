#!/usr/bin/env python3

import os
import subprocess
import json
import time
from pathlib import Path

# Configuration
DBLP_QUERY_DIR = "/Users/williampark/desktop/dataset/dblp/query_graph"
SLF_DIR = "/Users/williampark/slf"
CONVERTER_SCRIPT = "convert_hku_to_slf_fixed.py"

# Categories as requested by supervisor
categories = {
    "small_dense": {"pattern": "query_dense_4_*.graph", "vertices": 4},
    "small_sparse": {"pattern": "query_sparse_4_*.graph", "vertices": 4},
    "small_dense_8": {"pattern": "query_dense_8_*.graph", "vertices": 8},
    "small_sparse_8": {"pattern": "query_sparse_8_*.graph", "vertices": 8},
    "medium_dense": {"pattern": "query_dense_16_*.graph", "vertices": 16},
    "medium_sparse": {"pattern": "query_sparse_16_*.graph", "vertices": 16},
    "large_dense": {"pattern": "query_dense_24_*.graph", "vertices": 24},
    "large_sparse": {"pattern": "query_sparse_24_*.graph", "vertices": 24},
    "large_dense_32": {"pattern": "query_dense_32_*.graph", "vertices": 32},
    "large_sparse_32": {"pattern": "query_sparse_32_*.graph", "vertices": 32},
}

def convert_query(hku_file, slf_file):
    """Convert HKU format to SLF format"""
    cmd = f"python3 {CONVERTER_SCRIPT} {hku_file} {slf_file}"
    subprocess.run(cmd, shell=True, cwd=SLF_DIR)

def create_config(query_file, log_file, threads=4, time_limit=300):
    """Create SLF config file"""
    config = {
        "log": {"path": log_file, "level": "info"},
        "slf": {
            "thread_number": threads,
            "graph_format": "grf",
            "max_log_results": 0,
            "search_results_limitation": 100000,
            "search_time_limitation_seconds": time_limit,
            "tasks": [{
                "query": query_file,
                "target": "data/dblp_target.graph"
            }]
        }
    }
    return config

def run_experiment(config_file):
    """Run SLF experiment"""
    start_time = time.time()
    result = subprocess.run(
        f"./build/slf -c {config_file}",
        shell=True, cwd=SLF_DIR, capture_output=True, text=True
    )
    end_time = time.time()
    return result, end_time - start_time

def extract_results(log_file):
    """Extract results from log file"""
    try:
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        # Extract mappings found
        if "Find mapping number" in log_content:
            line = [l for l in log_content.split('\n') if "Find mapping number" in l][0]
            mappings = int(line.split('[')[1].split(']')[0])
        else:
            mappings = 0
            
        # Extract time
        if "Total Time cost" in log_content:
            line = [l for l in log_content.split('\n') if "Total Time cost" in l][0]
            time_ms = float(line.split('[')[1].split('ms')[0])
        else:
            time_ms = None
            
        # Check for timeout
        timeout = "timeout" in log_content.lower() or "failed" in log_content.lower()
        
        return mappings, time_ms, timeout
    except:
        return 0, None, True

def main():
    os.chdir(SLF_DIR)
    
    print("Category,Query_File,Vertices,Edges,Threads,Mappings,Time_ms,Timeout")
    
    # Sample a few queries from each category
    for category, info in categories.items():
        import glob
        query_files = glob.glob(os.path.join(DBLP_QUERY_DIR, info["pattern"]))
        
        # Sample first 3 queries from each category for testing
        for query_file in sorted(query_files)[:3]:
            query_name = os.path.basename(query_file)
            slf_query = f"data/experiment_{category}_{query_name}"
            
            # Convert to SLF format
            convert_query(query_file, slf_query)
            
            # Test with different thread counts
            for threads in [1, 2, 4]:
                config_file = f"data/config_{category}_{threads}_{query_name}.json"
                log_file = f"experiment_{category}_{threads}_{query_name}.log"
                
                # Create config
                config = create_config(slf_query, log_file, threads)
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                # Run experiment
                result, wall_time = run_experiment(config_file)
                
                # Extract results
                mappings, time_ms, timeout = extract_results(log_file)
                
                # Count edges from original file
                with open(query_file, 'r') as f:
                    first_line = f.readline().strip().split()
                    edges = int(first_line[2]) if len(first_line) > 2 else 0
                
                print(f"{category},{query_name},{info['vertices']},{edges},{threads},{mappings},{time_ms},{timeout}")

if __name__ == "__main__":
    main()
