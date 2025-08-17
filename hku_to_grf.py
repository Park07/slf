import sys
import os

def convert_hku_to_grf(input_file, output_file):
    """
    Converts a graph from HKU format to the SLF-specific .grf format.
    """
    vertices = {}
    edges = []
    num_vertices = 0

    with open(input_file, 'r') as f_in:
        for line in f_in:
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == 't':
                num_vertices = int(parts[1])
            elif parts[0] == 'v':
                # HKU format: v vertex_id label
                vertex_id, label = int(parts[1]), int(parts[2])
                vertices[vertex_id] = label
            elif parts[0] == 'e':
                # HKU format: e src_id dst_id label
                u, v = int(parts[1]), int(parts[2])
                edges.append((u, v))

    # Ensure all vertices up to num_vertices are accounted for with a dummy label if missing
    for i in range(num_vertices):
        if i not in vertices:
            vertices[i] = 1 # Default label

    with open(output_file, 'w') as f_out:
        # Write header: number of vertices
        f_out.write(f"{num_vertices}\n")

        # Write vertex list: vertex_id label
        for i in range(num_vertices):
            f_out.write(f"{i} {vertices.get(i, 1)}\n")

        # Write edge list for each vertex
        adj = [[] for _ in range(num_vertices)]
        for u, v in edges:
            adj[u].append(v)
            adj[v].append(u) # Assuming undirected

        for i in range(num_vertices):
            f_out.write(f"{len(adj[i])}\n")
            for neighbor in sorted(adj[i]):
                f_out.write(f"{i} {neighbor}\n")

    # print(f"Successfully converted {input_file} to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python3 {sys.argv[0]} <input_hku_file> <output_grf_file>")
        sys.exit(1)

    convert_hku_to_grf(sys.argv[1], sys.argv[2])