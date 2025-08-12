import os

def convert_hku_to_slf_complete(hku_file, slf_file):
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
    
    with open(slf_file, 'w') as f:
        f.write(f"{len(vertices)}\n")
        for vid in sorted(vertices.keys()):
            f.write(f"{vid} {vertices[vid]}\n")
        for src, dst in edges:
            f.write(f"{src} {dst}\n")

# Convert DBLP target graph
print("Converting DBLP target...")
convert_hku_to_slf_complete('/Users/williampark/desktop/dataset/dblp/data_graph/dblp.graph', 'dblp_real_target.grf')

# Convert representative queries
patterns = [
    ('8v_dense', '/Users/williampark/desktop/dataset/dblp/query_graph/query_dense_8_1.graph'),
    ('8v_sparse', '/Users/williampark/desktop/dataset/dblp/query_graph/query_sparse_8_1.graph'),
]

for name, path in patterns:
    if os.path.exists(path):
        output = f'dblp_{name}.grf'
        convert_hku_to_slf_complete(path, output)
        print(f"Converted {name} -> {output}")
    else:
        print(f"File not found: {path}")

print("DBLP conversion complete")
