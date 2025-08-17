import sys, os

def convert_snap_to_hku(input_file, output_file):
    edges = set()
    max_node_id = -1
    print(f"Reading and converting graph: {os.path.basename(input_file)}...")

    with open(input_file, 'r') as f_in:
        for line in f_in:
            if line.startswith('#') or not line.strip():
                continue
            try:
                parts = line.strip().split()
                # Handle HKU format (t #V #E, v label, e src dst label)
                if parts[0] == 't': continue
                if parts[0] == 'v':
                    max_node_id = max(max_node_id, int(parts[1]))
                    continue
                if parts[0] == 'e':
                    u, v = int(parts[1]), int(parts[2])
                # Handle SNAP format (u v)
                else:
                    u, v = map(int, parts)

                edges.add(tuple(sorted((u, v))))
                max_node_id = max(max_node_id, u, v)
            except (ValueError, IndexError):
                continue

    num_vertices = max_node_id + 1
    num_edges = len(edges)

    with open(output_file, 'w') as f_out:
        f_out.write(f"t {num_vertices} {num_edges}\n")
        for i in range(num_vertices):
            f_out.write(f"v {i} 1\n") # Assign dummy label 1
        for u, v in sorted(list(edges)):
            f_out.write(f"e {u} {v} 1\n") # Assign dummy label 1

    print(f"Conversion complete. Output: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 snap_to_hku.py <input_file> <output_hku_file>")
        sys.exit(1)

    convert_snap_to_hku(sys.argv[1], sys.argv[2])