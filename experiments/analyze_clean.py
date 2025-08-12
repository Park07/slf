#!/usr/bin/env python3

import os
import re
import pandas as pd
from pathlib import Path

def extract_results(log_dir="logs"):
    """Extract clean results from log files"""
    results = []
    
    for log_file in Path(log_dir).glob("experiment_*.log"):
        # Parse filename: experiment_{category}_{threads}_{query}.log
        parts = log_file.stem.replace('experiment_', '').split('_')
        if len(parts) < 3:
            continue
            
        category_parts = []
        threads = None
        
        # Find threads (should be a number)
        for i, part in enumerate(parts):
            if part.isdigit():
                threads = int(part)
                category_parts = parts[:i]
                query_parts = parts[i+1:]
                break
        
        if threads is None:
            continue
            
        category = '_'.join(category_parts)
        query_name = '_'.join(query_parts)
        
        # Extract vertices and density
        if 'dense_4_' in query_name:
            vertices, density = 4, 'Dense'
        elif 'sparse_4_' in query_name:
            vertices, density = 4, 'Sparse'
        elif 'dense_8_' in query_name:
            vertices, density = 8, 'Dense'
        elif 'sparse_8_' in query_name:
            vertices, density = 8, 'Sparse'
        elif 'dense_16_' in query_name:
            vertices, density = 16, 'Dense'
        elif 'sparse_16_' in query_name:
            vertices, density = 16, 'Sparse'
        elif 'dense_24_' in query_name:
            vertices, density = 24, 'Dense'
        elif 'sparse_24_' in query_name:
            vertices, density = 24, 'Sparse'
        elif 'dense_32_' in query_name:
            vertices, density = 32, 'Dense'
        elif 'sparse_32_' in query_name:
            vertices, density = 32, 'Sparse'
        else:
            continue
        
        # Parse log content
        try:
            with open(log_file, 'r') as f:
                content = f.read()
            
            mappings = 0
            time_ms = None
            
            if "Find mapping number" in content:
                match = re.search(r"Find mapping number \[(\d+)\]", content)
                if match:
                    mappings = int(match.group(1))
            
            if "Total Time cost" in content:
                match = re.search(r"Total Time cost: \[([0-9.]+)ms\]", content)
                if match:
                    time_ms = float(match.group(1))
            
            results.append({
                'vertices': vertices,
                'density': density,
                'threads': threads,
                'mappings': mappings,
                'time_ms': time_ms,
                'query': query_name,
                'category': category
            })
            
        except Exception as e:
            print(f"Error parsing {log_file}: {e}")
            continue
    
    return pd.DataFrame(results)

def main():
    # Change to experiments directory
    if Path("experiments/logs").exists():
        os.chdir("experiments")
        df = extract_results()
    else:
        df = extract_results(".")
    
    if df.empty:
        print("No results found!")
        return
    
    # Summary by category
    summary = df.groupby(['vertices', 'density', 'threads']).agg({
        'mappings': 'mean',
        'time_ms': 'mean',
        'query': 'count'
    }).round(1)
    
    print("=== SLF Performance Summary ===")
    print(summary)
    
    # Thread scaling analysis
    print("\n=== Thread Scaling Analysis ===")
    for vertices in sorted(df['vertices'].unique()):
        for density in ['Dense', 'Sparse']:
            subset = df[(df['vertices'] == vertices) & (df['density'] == density)]
            if len(subset) > 0:
                print(f"\n{vertices}v {density}:")
                scaling = subset.groupby('threads')['time_ms'].mean()
                for threads, time in scaling.items():
                    if not pd.isna(time):
                        speedup = scaling.get(1, time) / time if threads > 1 else 1.0
                        print(f"  {threads} threads: {time:.1f}ms (speedup: {speedup:.2f}x)")
    
    # Save to CSV
    df.to_csv('results/slf_performance.csv', index=False)
    summary.to_csv('results/slf_summary.csv')
    print(f"\n✅ Results saved to results/slf_performance.csv")

if __name__ == "__main__":
    main()
