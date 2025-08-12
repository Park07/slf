#!/usr/bin/env python3

import sys

def convert_hku_to_slf_correct(input_file, output_file):
    with open(input_file, 'r') as f_in:
        lines = f_in.readlines()
        
        # Parse header
        header = lines[0].strip().split()
        if header[0] != 't':
            print("Error: Expected 't' in first line")
            return
        
        num_vertices = int(header[1])
        num_edges = int(header[2])
        
        print(f"Converting graph with {num_vertices} vertices and {num_edges} edges")
        
        # Collect edge information first
        vertex_edges = [[] for _ in range(num_vertices)]
        edge_start = num_vertices + 1
        
        # Read all edges
        for i in range(edge_start, len(lines)):
            line = lines[i].strip()
            if line and line.startswith('e'):
                parts = line.split()
                if len(parts) >= 3:
                    src = int(parts[1])
                    dst = int(parts[2])
                    vertex_edges[src].append(dst)
        
        # Write in SLF format
        with open(output_file, 'w') as f_out:
            # First line: number of vertices
            f_out.write(f"{num_vertices}\n")
            
            # For each vertex: write "vertex_id 1" (unlabeled, so all labels = 1)
            for i in range(num_vertices):
                f_out.write(f"{i} 1\n")
            
            # For each vertex: write edge count and edges
            for vertex_id in range(num_vertices):
                edges = vertex_edges[vertex_id]
                f_out.write(f"{len(edges)}\n")
                for target in edges:
                    f_out.write(f"{vertex_id} {target}\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 convert_hku_to_slf_fixed.py input.graph output.graph")
        sys.exit(1)
    
    convert_hku_to_slf_correct(sys.argv[1], sys.argv[2])
    print("Conversion completed!")
