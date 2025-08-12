def graphmini_to_slf(snap_file, slf_file):
    """Convert GraphMini snap.txt to SLF format"""
    
    edges = []
    vertices = set()
    
    # Read edges from snap.txt
    with open(snap_file, 'r') as f:
        for line in f:
            if line.strip():
                u, v = map(int, line.strip().split())
                edges.append((u, v))
                vertices.add(u)
                vertices.add(v)
    
    # Write SLF format
    with open(slf_file, 'w') as f:
        # Header: vertex_count
        f.write(f"{len(vertices)}\n")
        
        # Vertices: vertex_id label (use vertex_id as label for simplicity)
        for v in sorted(vertices):
            f.write(f"{v} {v}\n")
        
        # Edges
        for u, v in edges:
            f.write(f"{u} {v}\n")

# Convert our 8v test graph
graphmini_to_slf('/Users/williampark/CMAKE/small_datasets/8v_24e_dense/snap.txt', 'test_8v_target.graph')

print("Converted 8v test graph to SLF format")
print("Target graph: test_8v_target.graph")
