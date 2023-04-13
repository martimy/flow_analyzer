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
from io import StringIO
from stp import get_stp

# Inject CSS with Markdown to hide the index column in pandas frames
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
st.markdown(hide_table_row_index, unsafe_allow_html=True)


TITLE = "Flow Analyzer"
ABOUT = "This app analyzes traffic flows in the network and displays the \
    results in tabular and graphical format."
UPLOAD_TOPO_HELP = "Upload a network topology in DOT format."
UPLOAD_FLOW_HELP = "Upload traffic flow information in csv format."
UPLOAD_FILE = "Upload a file or use demo network."
EDIT_FLOWS = r"""Edit the table below to enter traffic information.
To delete a row, select it from the left side then hit DEL. Use CTRL to select multiple rows.
"""

DEMO_TOPOLOGY = "graph {1 -- 2;2 -- 3;3 -- 4;4 -- 1;A -- 1;B -- 2;C -- 3;D -- 4;}"
DEMO_FLOWS = """Source,Target,Flow
A,B,1
C,D,2
"""

# define a mapping between the 'speed' attribute and the 'weight' attribute
speed_to_weight = {"10": 100, "100": 19, "1000": 4, "10000": 2}


def remove_session_keys():
    # Remove all keys
    for key in st.session_state.keys():
        del st.session_state[key]

def add_capacity(G, s, d, b):
    """Adds amount of traffic to edges and nodes along the shortest path"""

    nodes_list = nx.shortest_path(G, source=s, target=d)
    edges = list(zip(nodes_list, nodes_list[1:]))

    # Add traffic to edges in both directions
    for x, y in edges:
        G[x][y]['fwd'] += b
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


# The following will appear in a sidebar
with st.sidebar:
    topo_file = st.file_uploader(
        "Upload Network", type="dot", help=UPLOAD_TOPO_HELP)
    flow_file = st.file_uploader(
        "Upload Flow Information", type="csv", help=UPLOAD_FLOW_HELP)



# This will be the main page
st.title(TITLE)
st.markdown(ABOUT)

# Display an erroe message if there is no input topology or
if topo_file is not None:
    # Load the graph from a DOT file
    # Read the uploaded file using nx_pydot.read_dot()
    dot_data = topo_file.read().decode("utf-8")
    # Replace all occurrences of '\r\n' with '\n'
    dot_data = dot_data.replace('\r\n', '')
    graph_pydot = nx.drawing.nx_pydot.read_dot(dot_data)
    
    # Convert the Pydot graph to a NetworkX graph
    ORG = nx.Graph(graph_pydot)
    
    # Set node and edge attributes
    for node in ORG.nodes:
        # Assign tx and rx attributes
        ORG.nodes[node]["ttx"] = 0
        ORG.nodes[node]["trx"] = 0
    
    for edge in ORG.edges:
        st.write(edge)
        ORG.edges[edge]["fwd"] = 0
        ORG.edges[edge]["bck"] = 0


    switching = st.sidebar.checkbox("Switching", False)
    if switching:
        # Read the node's ID or create one based on its label
        for node in ORG.nodes:
            ORG.nodes[node]["ID"] = int(ORG.nodes[node].get(
                "ID",  ''.join(map(str, map(ord, node)))))

        # iterate through each edge in the pydot graph and add it to the networkx graph
        for edge in ORG.edges:
            # get the 'speed' attribute of the edge
            edge_speed = ORG.edges[edge].get('speed', 100)

            # map the 'speed' attribute to a 'weight' attribute using the speed_to_weight dictionary
            edge_weight = speed_to_weight.get(edge_speed, 100)
            ORG.edges[edge]['weight'] = edge_weight
        
        G = get_stp(ORG)
    else:
        G = ORG
    
    st.header("Traffic Flows")
    # Allow user to edit dataframe
    st.markdown(EDIT_FLOWS)

    # Creat a editable dataframe representing traffic flows by
    # reading a csv file or start with an empty frame
    if flow_file is None:
        # Make sure that all node names are of type string
        df = pd.DataFrame({'Source': [], 'Target': [], 'Flow': []})
        convert_dict = {'Source': str, 'Target': str}
        df = df.astype(convert_dict)
    else:
        df = pd.read_csv(flow_file)

    df_flows = st.experimental_data_editor(
        df, num_rows="dynamic", use_container_width=True)

    # The user must enter the source and target nodes correctly
    # followed by +ve flow value
    # TODO: Find a way to restrict input to nodes that exit in the graph
    for index, row in df_flows.iterrows():
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


    st.header("Link Traffic")
    # Display the edge capacities
    edge_data = [[x, y, G[x][y]['fwd']] for x, y in G.edges]
    df_edge = pd.DataFrame(edge_data, columns=("Source", "Target", "Tx"))

    st.table(df_edge[(df_edge['Tx'] > 0)])

    st.header("Node Traffic")
    # Display the node attributes
    node_data = [[n, G.nodes[n]['ttx'], G.nodes[n]['trx']] for n in G.nodes]
    df_node = pd.DataFrame(node_data, columns=("Node", "Outbound", "Inbound"))

    st.table(df_node[(df_node['Outbound'] > 0) | (df_node['Inbound'] > 0)])

    # Plotting the network graph
    st.header("Network Topology")
    fig, _ = plt.subplots()
    # fig = plt.figure()

    # Get positions for all nodes and save in a session state
    if 'pos' not in st.session_state:
        st.session_state.pos = nx.spring_layout(G)

    # Plot the original plain graph
    pos = st.session_state.pos
    nx.draw_networkx_edges(
        ORG, pos, width=1, edge_color="#AAAAAA", arrows=False).zorder = 0
    nx.draw_networkx_nodes(ORG, pos, node_color="#CFCFCF",
                           edgecolors="#AAAAAA", node_size=500).zorder = 2
    # labels have have a zorder pf >3
    nx.draw_networkx_labels(ORG, pos, font_size=10, font_family="sans-serif")

    # Disoplay filtering options in three columns
    checks = st.columns(4)
    with checks[0]:
        if st.checkbox("Spanning Tree", switching):
            # Draw the STP over the NetworkX graph G
            nx.draw_networkx_edges(ORG, pos=pos, edgelist=G.edges(),
                                   edge_color='r', width=2.0)        

    with checks[1]:
        # If selected draw bandwidth labels
        if not df_flows.empty and st.checkbox("Link Bandwith", False):
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=nx.get_edge_attributes(G, 'bw'))

    with checks[2]:
        # If selected draw flows
        if not df_flows.empty and st.checkbox("Flows", False):
            df_flows.columns = df_flows.columns.str.lower()

            # Select filter type and value
            filter_type = st.sidebar.selectbox(
                'Filter by', ['none', 'source', 'target'])
            if filter_type != 'none':
                # Filter dataframe based on user selection
                filter_values = df_flows[filter_type].unique()
                # Select filter value from dropdown list
                filter_value = st.sidebar.selectbox('Value', filter_values)
                # Filter dataframe based on user selection
                df_flows = df_flows.loc[df_flows[filter_type] == filter_value]

            G2 = nx.from_pandas_edgelist(df_flows, edge_attr=True)
            nx.draw_networkx_edges(
                G2, pos, width=3, edge_color='r', alpha=0.6).zorder = 1
            nx.draw_networkx_edge_labels(
                G2, pos, edge_labels=nx.get_edge_attributes(G2, 'flow'), rotate=False)

    with checks[3]:
        # If selected draw all routes used by traffic flows
        # if the df_flows are filterd from above, the routes shown are belong
        # to selected flows.
        if not df_flows.empty and st.checkbox("Routes", False):
            df_flows.columns = df_flows.columns.str.lower()
            G2 = nx.from_pandas_edgelist(df_flows, edge_attr=True)
            for s, t in G2.edges:
                path = nx.shortest_path(G, source=s, target=t)
                path_edges = list(zip(path, path[1:]))
                nx.draw_networkx_edges(
                    G, pos, edgelist=path_edges, arrows=False, edge_color='#1f78b4', width=3, alpha=0.6).zorder = 0.5
                nx.draw_networkx_nodes(
                    G, pos, nodelist=[s, t], node_color='#1f78b4', node_size=500, alpha=0.6).zorder = 2.5

    st.pyplot(fig)

    if st.button('Redraw'):
        # Needed to re-draw graph
        if 'pos' in st.session_state:
            del st.session_state["pos"]
            st.experimental_rerun()
else:
    remove_session_keys()
    st.warning(UPLOAD_FILE)
