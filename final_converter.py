def convert_hku_to_slf_final(hku_file, slf_file):
    """Convert HKU to SLF format - vertices then edges"""
    
    vertices = {}
    edges = []
    
    with open(hku_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
                
            if parts[0] == 't':  
                continue
            elif parts[0] == 'v':  # v id label degree
                vertex_id = int(parts[1])
                label = int(parts[2])
                vertices[vertex_id] = label
            elif parts[0] == 'e':  # e src dst edge_label
                src = int(parts[1])
                dst = int(parts[2])
                edges.append((src, dst))
    
    # Write SLF format
    with open(slf_file, 'w') as f:
        f.write(f"{len(vertices)}\n")
        # Write all vertices first
        for vid in sorted(vertices.keys()):
            f.write(f"{vid} {vertices[vid]}\n")
        # Write all edges after vertices
        for src, dst in edges:
            f.write(f"{src} {dst}\n")

# Convert a simple 8-vertex query
convert_hku_to_slf_final('/Users/williampark/desktop/dataset/dblp/query_graph/query_dense_8_1.graph', 'fixed_query.grf')

print("Fixed conversion done")
