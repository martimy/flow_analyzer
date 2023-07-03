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

from io import StringIO
import networkx as nx

# define a mapping between the 'speed' attribute and the 'weight' attribute
speed_to_weight = {"10": 100, "100": 19, "1000": 4, "10000": 2, "100000": 1}


def assign_stp_attributes(ORG):
    """
    Assigns ID and weight attributes to nodes and edges of the input graph, respectively.

    Parameters:
    ORG (networkx.Graph): Input graph to assign attributes to.

    Returns:
    None
    """

    for node in ORG.nodes:
        ORG.nodes[node]["ID"] = int(
            ORG.nodes[node].get("ID", "".join(map(str, map(ord, node))))
        )

    # Read the edge's speed and set its weight attribute
    for edge in ORG.edges:
        # get the 'speed' attribute of the edge
        edge_speed = ORG.edges[edge].get("speed", "100")

        # map the 'speed' attribute to a 'weight' attribute using the speed_to_weight dictionary
        ORG.edges[edge]["weight"] = speed_to_weight[edge_speed]


def assign_flow_attributes(G):
    """
    Assigns flow attributes to nodes and edges of the input graph.

    Parameters:
    G (networkx.Graph): Input graph to assign attributes to.

    Returns:
    None
    """

    for s, t in G.edges:
        G.edges[s, t]["dr"] = f"{s},{t}"
        G.edges[s, t]["fw"] = 0
        G.edges[s, t]["bk"] = 0
        G.edges[s, t]["bw"] = 0

    for node in G.nodes:
        G.nodes[node]["tx"] = 0
        G.nodes[node]["rx"] = 0


def assign_bipartite_attributes(G):
    """
    Assigns bipartite attributes to nodes of the input graph.

    Parameters:
    G (networkx.Graph): Input graph to assign attributes to.

    Returns:
    None
    """

    for node in G.nodes:
        G.nodes[node]["bipartite"] = int(G.nodes[node].get("bipartite", "1"))


def add_capacity(G, s, d, b):
    """
    Adds a specified amount of traffic to the edges and nodes along the shortest path from
    source to destination nodes.

    Parameters:
    G (networkx.Graph): Input graph to add capacity to.
    s (int): Source node ID.
    d (int): Destination node ID.
    b (float): Amount of traffic to be added to the graph.

    Returns:
    None
    """

    nodes_list = nx.shortest_path(G, source=s, target=d)
    edges = list(zip(nodes_list, nodes_list[1:]))

    # Add traffic to edges in both directions
    for x, y in edges:
        if G[x][y]["dr"] == f"{x},{y}":
            G[x][y]["fw"] += b
        else:
            G[x][y]["bk"] += b
        G[x][y]["bw"] = max(G[x][y]["fw"], G[x][y]["bk"])

    # Add traffic to source and traget nodes
    # The source transmits only and target receives only
    G.nodes[d]["rx"] += b
    G.nodes[s]["tx"] += b

    # All other intermediate nodes receive then transmit the same
    # amount of traffic
    if len(nodes_list) > 2:
        for n in nodes_list[1:-1]:
            G.nodes[n]["rx"] += b
            G.nodes[n]["tx"] += b


def get_dot_graph(dot_data):
    """
    Reads a DOT graph description string and returns a NetworkX graph object.

    Parameters:
    dot_data (str): A string containing the DOT graph description.

    Returns:
    networkx.Graph: The graph object created from the DOT graph description.
    """
    return nx.Graph(nx.drawing.nx_pydot.read_dot(StringIO(dot_data)))
