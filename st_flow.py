# -*- coding: utf-8 -*-
"""
Created on Sat Mar  4 11:27:12 2023

@author: artim
"""

import streamlit as st
import networkx as nx
import pydot
import matplotlib.pyplot as plt
import pandas as pd

# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
TITLE = "Flow Analyzer"
ABOUT = "This app analyzes traffic flow in a network."
NO_RELATION = ":heavy_check_mark: No anomalies detected."
EXAMPLE_HELP = "Use built-in example to demo the app."
UPLOAD_FILE = "Upload a file"
EXAMPE_NETWORK = """
graph {
1 -- 2;
2 -- 3;
3 -- 4;
4 -- 1;
A -- 1;
B -- 2;
C -- 3;
D -- 4;
}
"""

def add_capacity(G, s, d, b):
    """Adds amount of traffic to edges and nodes along the shortest path"""
    
    nodes_list = nx.shortest_path(G, source=s, target=d)
    edges = list(zip(nodes_list[0:], nodes_list[1:]))

    # Add traffic to edges in both directions
    for x, y in edges:
        G[x][y]['tx'] += b
        G[y][x]['rx'] += b

        G[x][y]['bw'] = max(G[x][y]['tx'], G[y][x]['rx'],
                            G[x][y]['rx'], G[y][x]['tx'])
        G[y][x]['bw'] = G[x][y]['bw']

    # Add traffic to source and traget nodes
    # The source transmits only and target receives only
    G.nodes[d]['trx'] += b
    G.nodes[s]['ttx'] += b
    
    # All other intermediate nodes receive then transmit the same 
    # amount of traffic
    if len(nodes_list) > 2:
        for n in nodes_list[1:-1]:
            G.nodes[n]['trx'] += b
            G.nodes[n]['ttx'] += b
            


st.title(TITLE)

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

with st.expander("About", expanded=True):
    st.markdown(ABOUT)


# File upload
uploaded_file = st.file_uploader("Upload Network File", type="txt")

# The checkbox is enabled when no file is uploaded
show_ex = uploaded_file is not None
use_example = st.checkbox(
    'Use example network', value=False, disabled=show_ex, help=EXAMPLE_HELP)
if use_example:
    uploaded_file = EXAMPE_NETWORK


if uploaded_file is not None:
    # Read the graph string from the file
    if isinstance(uploaded_file, str):
        graph_str = uploaded_file
    else:
        graph_str = uploaded_file.read().decode("utf-8")

    # Parse the DOT format to create a Pydot graph object
    graph = pydot.graph_from_dot_data(graph_str)[0]

    # Create an empty NetworkX graph
    G = nx.DiGraph()

    # Add nodes and edges to the NetworkX graph based on the Pydot graph object,
    # and set the edge attributes and node attributes
    for node in graph.get_nodes():
        node_name = node.get_name()
        # Initialize the node's total attribute to 0
        G.add_node(node_name, ttx=0, trx=0)

    for edge in graph.get_edges():
        source_node = edge.get_source()
        dest_node = edge.get_destination()
        # Set the edge's capacity attribute
        G.add_edge(source_node, dest_node, tx=0, rx=0, bw=0)
        # Set the edge's capacity attribute
        G.add_edge(dest_node, source_node, tx=0, rx=0, bw=0)
        G.nodes[source_node]['ttx'] = 0
        G.nodes[source_node]['trx'] = 0
        G.nodes[dest_node]['ttx'] = 0
        G.nodes[dest_node]['trx'] = 0

    # Allow user to edit dataframe
    st.write('Edit the table below to add capacities to edges:')

    df = pd.DataFrame({'Source': [], 'Target': [], 'Flow': []})
    convert_dict = {'Source': str, 'Target': str}
    df = df.astype(convert_dict)

    df_flows = st.experimental_data_editor(
        df, num_rows="dynamic", use_container_width=True)

    for index, row in df_flows.iterrows():
        # Check for errors
        try:
            source = '' if row['Source'] is None else row['Source'][0]
            target = '' if row['Target'] is None else row['Target'][0]
            flow = 0 if row['Flow'] is None else row['Flow']

            if (source in G.nodes) and (target in G.nodes) and (flow > 0):
                add_capacity(G, row['Source'], row['Target'], row['Flow'])
            else:
                st.error(f"Input error in line {index}")
                continue
        except:
            st.error(f"Input error in line {index}")

    # Display the edge capacities
    edge_data = [[x, y, G[x][y]['tx'], G[x][y]['rx']] for x, y in G.edges]
    df_edge = pd.DataFrame(edge_data, columns=("Source", "Target", "Tx", "Rx"))

    # Display the node attributes
    node_data = [[n, G.nodes[n]['ttx'], G.nodes[n]['trx']] for n in G.nodes]
    df_node = pd.DataFrame(node_data, columns=("Node", "Outbound", "Inbound"))

    # display tables
    st.write("Edge Information")
    st.table(df_edge[(df_edge['Tx'] > 0) & (df_edge['Rx'] > 0)])

    st.write("Node Information")
    st.table(df_node[(df_node['Outbound'] > 0) | (df_node['Inbound'] > 0)])

    # Draw the graph
    st.write("Network Topology")
    # fig, ax = plt.subplots()
    fig = plt.figure()
    pos = nx.spring_layout(G)  # positions for all nodes
    nx.draw_networkx_nodes(G, pos, node_size=400)
    nx.draw_networkx_edges(G, pos, width=1)
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=nx.get_edge_attributes(G, 'bw'))
    nx.draw_networkx_labels(G, pos, font_size=16, font_family="sans-serif")
    st.pyplot(fig)

else:
    st.error(UPLOAD_FILE)
