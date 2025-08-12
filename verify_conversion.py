#!/usr/bin/env python3

def verify_conversion(original_file, converted_file):
    print("=== VERIFYING CONVERSION ACCURACY ===")
    
    # Read original HKU format
    with open(original_file, 'r') as f:
        orig_lines = f.readlines()
    
    # Parse original
    header = orig_lines[0].strip().split()
    orig_vertices = int(header[1])
    orig_edges = int(header[2])
    
    print(f"Original: {orig_vertices} vertices, {orig_edges} edges")
    
    # Extract edges from original
    orig_edge_set = set()
    for i in range(orig_vertices + 1, len(orig_lines)):
        line = orig_lines[i].strip()
        if line.startswith('e'):
            parts = line.split()
            src, dst = int(parts[1]), int(parts[2])
            orig_edge_set.add((src, dst))
    
    print(f"Original edges parsed: {len(orig_edge_set)}")
    
    # Read converted SLF format
    with open(converted_file, 'r') as f:
        conv_lines = f.readlines()
    
    conv_vertices = int(conv_lines[0].strip())
    print(f"Converted: {conv_vertices} vertices")
    
    # Extract edges from converted
    conv_edge_set = set()
    line_idx = conv_vertices + 1  # Skip vertex count + vertex list
    
    for vertex_id in range(conv_vertices):
        edge_count = int(conv_lines[line_idx].strip())
        line_idx += 1
        
        for _ in range(edge_count):
            parts = conv_lines[line_idx].strip().split()
            src, dst = int(parts[0]), int(parts[1])
            conv_edge_set.add((src, dst))
            line_idx += 1
    
    print(f"Converted edges parsed: {len(conv_edge_set)}")
    
    # Verify exact match
    if orig_vertices == conv_vertices:
        print("✅ Vertex count matches exactly")
    else:
        print("❌ Vertex count MISMATCH")
    
    if orig_edge_set == conv_edge_set:
        print("✅ Edge sets match exactly - 100% accurate conversion")
    else:
        print("❌ Edge sets DO NOT match")
        print(f"Original has {len(orig_edge_set)} edges")
        print(f"Converted has {len(conv_edge_set)} edges")
        missing = orig_edge_set - conv_edge_set
        extra = conv_edge_set - orig_edge_set
        if missing:
            print(f"Missing edges: {list(missing)[:5]}...")
        if extra:
            print(f"Extra edges: {list(extra)[:5]}...")

if __name__ == "__main__":
    verify_conversion(
        "/Users/williampark/desktop/dataset/dblp/data_graph/dblp.graph",
        "/Users/williampark/Ask-for-Sharing-SLF/data/dblp_target.graph"
    )
    
    verify_conversion(
        "/Users/williampark/desktop/dataset/dblp/query_graph/query_dense_8_185.graph", 
        "/Users/williampark/Ask-for-Sharing-SLF/data/dblp_query.graph"
    )
