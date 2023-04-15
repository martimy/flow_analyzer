# -*- coding: utf-8 -*-
"""
Copyright 2023 Maen Artimy

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import networkx as nx

MAX_INT = 2**63-1


def get_stp(G):
    """
    Apply the IEEE Spanning Tree Protocol for a graph G using ID and
    weight attributes of the nodes and edges, respectively.
    """

    # Find the root node with the smallest ID
    root_id = min(G.nodes, key=lambda n: G.nodes[n]["ID"])

    # Find the shortest path length from the root node
    distances = nx.shortest_path_length(G, source=root_id)

    # Sort nodes based on their distance from the root
    sorted_nodes = sorted(G.nodes, key=lambda n: distances[n])

    # Find the shortest path to the root node for each node in order of distance
    short_routes = []
    for node in sorted_nodes:
        paths = list(nx.all_shortest_paths(G, node, root_id, weight='weight'))

        # If there are more than one equal path, choose the path through the
        # the switch with lowest ID
        selected_path = paths[0]
        for path in paths[1:]:
            if path < selected_path:
                selected_path = path
        short_routes.append(selected_path)

    # Create a new graph for the spanning tree
    st = nx.Graph(root=root_id)

    # The first two nodes in each path form an edges in the STP.
    # Ignore the first path which includes only the root
    edges = [tuple(r[0:2]) for r in short_routes[1:]]
    st.add_edges_from(edges)

    return st
