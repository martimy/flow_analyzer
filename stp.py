# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 08:37:16 2023

@author: artim
"""

import networkx as nx

MAX_INT = 2**63-1

def get_stp(G):
    """
    Find the IEEE Spanning Tree Protocol
    """

    # Find the root node with the smallest ID
    root_id = min(G.nodes, key=lambda n: G.nodes[n]["ID"])

    # Cache the shortest path length from the root node
    if "distances" not in G.graph:
        G.graph["distances"] = nx.shortest_path_length(G, source=root_id)
    distances = G.graph["distances"]

    # Sort nodes based on their distance from the root
    sorted_nodes = sorted(G.nodes, key=lambda n: distances[n])

    # Find the shortest path to the root node for each node in order of distance
    tree = []
    for node in sorted_nodes:
        paths = nx.all_shortest_paths(G, node, root_id, weight='weight')

        selected_path = None
        short = MAX_INT
        for path in paths:
            if len(path) > 1:
                if G.nodes[path[1]]["ID"] < short:
                    selected_path = path
                    short = G.nodes[path[1]]["ID"]
            else:
                selected_path = path
        tree.append(selected_path)

    # Create a new graph for the STP
    spanning = nx.Graph()
    for branch in tree:
        if len(branch) > 1:
            s, t = branch[0:2]
            spanning.add_edge(s, t)


    return spanning
