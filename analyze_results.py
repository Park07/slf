#!/usr/bin/env python3

import os
import re
from collections import defaultdict

def parse_log_file(log_file):
    """Extract results from a log file"""
    try:
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Extract mappings
        mappings = 0
        time_ms = None
        timeout = False
        
        if "Find mapping number" in content:
            match = re.search(r"Find mapping number \[(\d+)\]", content)
            if match:
                mappings = int(match.group(1))
        
        if "Total Time cost" in content:
            match = re.search(r"Total Time cost: \[([0-9.]+)ms\]", content)
            if match:
                time_ms = float(match.group(1))
        
        if "timeout" in content.lower() or "failed" in content.lower() or mappings == 0:
            timeout = True
            
        return mappings, time_ms, timeout
    except:
        return 0, None, True

def categorize_query(filename):
    """Categorize queries by size and density"""
    if "query_dense_4_" in filename or "query_sparse_4_" in filename:
        return "Small (4v)"
    elif "query_dense_8_" in filename or "query_sparse_8_" in filename:
        return "Small (8v)" 
    elif "query_dense_16_" in filename or "query_sparse_16_" in filename:
        return "Medium (16v)"
    elif "query_dense_24_" in filename or "query_sparse_24_" in filename:
        return "Large (24v)"
    elif "query_dense_32_" in filename or "query_sparse_32_" in filename:
        return "Large (32v)"
    else:
        return "Unknown"

def get_density(filename):
    """Get density type"""
    if "dense" in filename:
        return "Dense"
    elif "sparse" in filename:
        return "Sparse"
    return "Unknown"

def main():
    results = defaultdict(list)
    
    # Parse all log files
    for file in os.listdir('.'):
        if file.startswith('experiment_') and file.endswith('.log'):
            # Extract info from filename
            parts = file.replace('experiment_', '').replace('.log', '').split('_')
            if len(parts) >= 3:
                threads = parts[-2] if parts[-2].isdigit() else "1"
                query_file = '_'.join(parts[2:])  # Everything after category and threads
                
                category = categorize_query(query_file)
                density = get_density(query_file)
                
                mappings, time_ms, timeout = parse_log_file(file)
                
                results[(category, density, threads)].append({
                    'mappings': mappings,
                    'time_ms': time_ms,
                    'timeout': timeout,
                    'query': query_file
                })
    
    # Print summary
    print("Category,Density,Threads,Avg_Mappings,Avg_Time_ms,Timeout_Rate,Samples")
    print("=" * 80)
    
    for (category, density, threads), data in sorted(results.items()):
        if not data:
            continue
            
        # Calculate averages
        total_mappings = sum(d['mappings'] for d in data)
        valid_times = [d['time_ms'] for d in data if d['time_ms'] is not None]
        avg_time = sum(valid_times) / len(valid_times) if valid_times else None
        timeout_rate = sum(1 for d in data if d['timeout']) / len(data)
        
        avg_mappings = total_mappings / len(data)
        
        print(f"{category},{density},{threads},{avg_mappings:.0f},{avg_time:.1f if avg_time else 'N/A'},{timeout_rate:.2f},{len(data)}")

if __name__ == "__main__":
    main()
