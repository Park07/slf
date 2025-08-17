import os
import sys
import argparse
import networkx as nx
from littleballoffur import RandomWalkSampler

def save_graph_hku(graph, output_path):
    """Saves a NetworkX graph to the HKU file format."""
    # Ensure nodes are mapped to a 0-indexed contiguous range
    node_map = {node: i for i, node in enumerate(graph.nodes())}
    num_vertices = len(node_map)
    num_edges = graph.number_of_edges()

    with open(output_path, 'w') as f:
        f.write(f"t {num_vertices} {num_edges}\n")
        for i in range(num_vertices):
            f.write(f"v {i} 1\n") # Assign dummy label 1
        for u, v in graph.edges():
            # Use the mapped, 0-indexed values
            f.write(f"e {node_map[u]} {node_map[v]} 1\n")

def main():
    parser = argparse.ArgumentParser(description="Generate query graphs by sampling from a large data graph.")
    parser.add_argument("--input-graph", required=True, help="Path to the large data graph (HKU or SNAP format).")
    parser.add_argument("--output-dir", required=True, help="Directory to save the generated query graphs.")
    parser.add_argument("--num-queries", type=int, default=20, help="Number of queries to generate.")
    parser.add_argument("--num-nodes", type=int, required=True, help="The target number of nodes for each query graph.")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    print(f"Reading large data graph from: {args.input-graph}")

    full_graph = nx.Graph()
    with open(args.input_graph, 'r') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            try:
                parts = line.strip().split()
                if parts[0] == 't' or parts[0] == 'v': continue
                u, v = (int(parts[1]), int(parts[2])) if parts[0] == 'e' else map(int, parts)
                full_graph.add_edge(u, v)
            except (ValueError, IndexError):
                continue

    print(f"Data graph loaded: {full_graph.number_of_nodes()} nodes, {full_graph.number_of_edges()} edges.")
    print(f"Generating {args.num_queries} queries with approx. {args.num_nodes} nodes each...")

    for i in range(1, args.num_queries + 1):
        sampler = RandomWalkSampler(number_of_nodes=args.num_nodes)
        subgraph = sampler.sample(full_graph)

        output_filename = f"query_sample_{args.num_nodes}v_{i}.graph"
        output_path = os.path.join(args.output_dir, output_filename)

        save_graph_hku(subgraph, output_path)
        print(f"  -> Saved {output_filename} ({subgraph.number_of_nodes()}v, {subgraph.number_of_edges()}e)")

    print(f"\n✅ Generation complete. Queries are in: {args.output_dir}")

if __name__ == "__main__":
    main()