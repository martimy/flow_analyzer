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

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt


EDGE_COLOR = "#AAAAAA"
NODE_COLOR = "#CFCFCF"
ROUTE_COLOR = "#1f78b4"
ROOT_COLOR = "#555555"

graph_layouts = ['Spring', 'Circular', 'Kamada-Kawai', 'Planar']


def get_graph_layout(G, layout):
    """
    Returns the layout of the graph according to the selected layout.

    Parameters:
    -----------
    G : nx.Graph
        The graph object for which the layout needs to be determined.
    layout : str
        The layout to be used for the graph. It can be 
        'Spring', 'Circular', 'Kamada-Kawai', or 'Planar'.

    Returns:
    --------
    pos : dict
        A dictionary containing the positions of the nodes.
    """

    if layout == 'Circular':
        pos = nx.circular_layout(G)
    elif layout == 'Kamada-Kawai':
        pos = nx.kamada_kawai_layout(G)
    elif layout == 'Planar':
        pos = nx.planar_layout(G)
    else:
        pos = nx.spring_layout(G)
    return pos


def plot_graph(ORG, G, flows, switching):
    """
    Plots a network graph with the given attributes.

    Parameters:
    -----------
    ORG : nx.Graph
        The original graph object that inlcude all nodes and edges
    G : nx.Graph
        The graph object representing active nodes and edges
    flows : pd.DataFrame
        The DataFrame containing information about the flows in the network.
    switching : bool
        A flag that determines whether or not the network is switched.

    Returns:
    --------
    None
    """

    st.header("Network Topology")
    fig, _ = plt.subplots()
    # fig = plt.figure()

    layout = st.sidebar.selectbox('Select Graph Layout', graph_layouts)

    # Get positions for all nodes and save in a session state
    if 'pos' not in st.session_state:
        st.session_state.pos = get_graph_layout(ORG, layout)
        # st.session_state.pos = nx.spring_layout(ORG)

    # Plot a plain graph
    pos = st.session_state.pos
    line_style = 'dotted' if switching else 'solid'
    nx.draw_networkx_edges(
        ORG, pos, width=1, edge_color=EDGE_COLOR, style=line_style).zorder = 0
    # Draw the STP over the NetworkX graph G
    if switching:
        nx.draw_networkx_edges(G, pos=pos, edgelist=G.edges(),
                               edge_color=EDGE_COLOR).zorder = 0.1
        nx.draw_networkx_nodes(G, pos, nodelist=[
                               G.graph["root"]], node_color=None, edgecolors=ROOT_COLOR, node_size=600).zorder = 2

    nx.draw_networkx_nodes(G, pos, node_color=NODE_COLOR,
                           edgecolors=EDGE_COLOR, node_size=500).zorder = 2

    # labels have have a zorder pf >3
    nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")

    # Disoplay filtering options in three columns
    checks = st.columns(3)
    with checks[0]:
        # If selected draw bandwidth labels
        if not flows.empty and st.checkbox("Link Bandwith", False):
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=nx.get_edge_attributes(G, 'bw'))

    with checks[1]:
        # If selected draw flows
        if not flows.empty and st.checkbox("Flows", False):
            flows.columns = flows.columns.str.lower()

            # Select filter type and value
            filter_type = st.sidebar.selectbox(
                'Filter by', ['none', 'source', 'target'])
            if filter_type != 'none':
                # Filter dataframe based on user selection
                filter_values = flows[filter_type].unique()
                # Select filter value from dropdown list
                filter_value = st.sidebar.selectbox('Value', filter_values)
                # Filter dataframe based on user selection
                flows = flows.loc[flows[filter_type] == filter_value]

            G2 = nx.from_pandas_edgelist(
                flows, edge_attr=True, create_using=nx.DiGraph)
            nx.draw_networkx_edges(
                G2, pos, width=2, edge_color='r', alpha=0.6)  # .zorder = 1
            nx.draw_networkx_edge_labels(
                G2, pos, edge_labels=nx.get_edge_attributes(G2, 'flow'))

    with checks[2]:
        # If selected draw all routes used by traffic flows
        # if the flows are filterd from above, the routes shown are belong
        # to selected flows.
        if not flows.empty and st.checkbox("Routes", False):
            flows.columns = flows.columns.str.lower()
            G2 = nx.from_pandas_edgelist(flows, edge_attr=True)
            for s, t in G2.edges:
                path = nx.shortest_path(G, source=s, target=t)
                path_edges = list(zip(path, path[1:]))
                nx.draw_networkx_edges(
                    G, pos, edgelist=path_edges, arrows=False,
                    edge_color=ROUTE_COLOR, width=3, alpha=0.6).zorder = 0.5
                nx.draw_networkx_nodes(
                    G, pos, nodelist=[s, t], node_color=ROUTE_COLOR,
                    node_size=500, alpha=0.6).zorder = 2.5

    st.pyplot(fig)
