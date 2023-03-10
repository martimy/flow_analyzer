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
UPLOAD_HELP = "Upload a network topology in DOT format."
UPLOAD_FLOW_HELP = "Upload traffic flow information in csv format."
UPLOAD_FILE = "Upload a file or use demo network."
EXAMPE_NETWORK = "graph {1 -- 2;2 -- 3;3 -- 4;4 -- 1;A -- 1;B -- 2;C -- 3;D -- 4;}"


def add_capacity(G, s, d, b):
    """Adds amount of traffic to edges and nodes along the shortest path"""

    nodes_list = nx.shortest_path(G, source=s, target=d)
    edges = list(zip(nodes_list, nodes_list[1:]))

    # Add traffic to edges in both directions
    for x, y in edges:
        G[x][y]['tx'] += b
        # G[y][x]['rx'] += b

        G[x][y]['bw'] = max(G[x][y]['tx'], G[y][x]['tx'])
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


# File upload
with st.sidebar:
    uploaded_file = st.file_uploader(
        "Upload Network", type="dot", help=UPLOAD_HELP)

    # The checkbox is enabled when no file is uploaded
    show_ex = uploaded_file is not None
    use_demo_network = st.checkbox(
        'Use demo network', value=False, disabled=show_ex)
    if use_demo_network:
        uploaded_file = EXAMPE_NETWORK

    flow_file = st.file_uploader(
        "Upload Flow Information", type="csv", help=UPLOAD_FLOW_HELP)


st.title(TITLE)
st.markdown(ABOUT)

# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)


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
        G.add_edge(source_node, dest_node, tx=0, bw=0)
        # Set the edge's capacity attribute
        G.add_edge(dest_node, source_node, tx=0, bw=0)
        G.nodes[source_node]['ttx'] = 0
        G.nodes[source_node]['trx'] = 0
        G.nodes[dest_node]['ttx'] = 0
        G.nodes[dest_node]['trx'] = 0

    # Allow user to edit dataframe
    st.write('Edit the table below to enter traffic information:')

    if flow_file is None:
        df = pd.DataFrame({'Source': [], 'Target': [], 'Flow': []})
        convert_dict = {'Source': str, 'Target': str}
        df = df.astype(convert_dict)
    else:
        df = pd.read_csv(flow_file)

    df_flows = st.experimental_data_editor(
        df, num_rows="dynamic", use_container_width=True)

    for index, row in df_flows.iterrows():
        # Check for errors
        try:
            source = row.get('Source', '')
            target = row.get('Target', '')
            flow = row.get('Flow', 0)

            if (source in G.nodes) and (target in G.nodes) and (flow > 0):
                add_capacity(G, row['Source'], row['Target'], row['Flow'])
            else:
                st.error(f"Input error in line {index}.")
                continue
        except:
            st.error(f"Input error in line {index}")

    # Display the edge capacities
    edge_data = [[x, y, G[x][y]['tx']] for x, y in G.edges]
    df_edge = pd.DataFrame(edge_data, columns=("Source", "Target", "Tx"))
    st.write("Edge Traffic")
    st.table(df_edge[(df_edge['Tx'] > 0)])

    # Display the node attributes
    node_data = [[n, G.nodes[n]['ttx'], G.nodes[n]['trx']] for n in G.nodes]
    df_node = pd.DataFrame(node_data, columns=("Node", "Outbound", "Inbound"))
    st.write("Node Traffic")
    st.table(df_node[(df_node['Outbound'] > 0) | (df_node['Inbound'] > 0)])

    # Draw the graph
    st.write("Network Topology")
    fig, _ = plt.subplots()
    # fig = plt.figure()

    # pos = nx.spring_layout(G)  # positions for all nodes
    if 'pos' not in st.session_state:
        st.session_state.pos = nx.spring_layout(G)

    pos = st.session_state.pos
    nx.draw_networkx_nodes(G, pos, node_color="#CFCFCF", edgecolors="#AAAAAA", node_size=500)
    nx.draw_networkx_edges(G, pos, width=1, edge_color="#AAAAAA", arrows=False)

    checks = st.columns(3)

    with checks[0]:
        if st.checkbox("Link Bandwith", False):
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=nx.get_edge_attributes(G, 'bw'))

    nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")

    with checks[1]:
        if st.checkbox("Flows", False):
            df_flows.columns = df_flows.columns.str.lower()
            # Transform a column to a numerical value for colors
            df_flows['source']=pd.Categorical(df_flows['source'])
            G2 = nx.from_pandas_edgelist(df_flows, edge_attr=True)
            # nx.draw_networkx_edges(
            #     G2, pos, width=3, edge_color=df_flows['source'].cat.codes, 
            #     edge_cmap=plt.cm.Reds, edge_vmin=0.3, edge_vmax=0.7)
            nx.draw_networkx_edges(G2, pos, width=3, edge_color='r', alpha=0.6)
            nx.draw_networkx_edge_labels(
                G2, pos, edge_labels=nx.get_edge_attributes(G2, 'flow'))

    with checks[2]:
        if st.checkbox("Routes", False):
            df_flows.columns = df_flows.columns.str.lower()
            G2 = nx.from_pandas_edgelist(df_flows, edge_attr=True)
            for s, t in G2.edges:
                path = nx.shortest_path(G, source=s, target=t)
                path_edges = list(zip(path, path[1:]))
                nx.draw_networkx_nodes(
                    G, pos, nodelist=[s, t], node_color='#1f78b4', node_size=500, alpha=0.6)
                nx.draw_networkx_edges(
                    G, pos, edgelist=path_edges, arrows=False, edge_color='#1f78b4', width=3, alpha=0.6)

    st.pyplot(fig)

else:
    # Remove all keys
    for key in st.session_state.keys():
        del st.session_state[key]

    st.error(UPLOAD_FILE)
