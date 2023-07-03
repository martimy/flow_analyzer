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
import pandas as pd
import time
from stp import get_stp
from plotting import plot_graph
import graph_data as gd

# Inject CSS with Markdown to hide the index column in tables and dataframes
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
hide_dataframe_row_index = """
            <style>
            .row_heading.level0 {display:none}
            .blank {display:none}
            </style>
            """
# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)
st.markdown(hide_dataframe_row_index, unsafe_allow_html=True)


TITLE = "Flow Analyzer"
ABOUT = "This app analyzes traffic flows in the network and displays the \
    results in tabular and graphical format."
UPLOAD_TOPO_HELP = "Upload a network topology in DOT format."
UPLOAD_FLOW_HELP = "Upload traffic flow information in csv format."
UPLOAD_FILE = "Upload a file or use demo network."
EDIT_FLOWS = r"""Edit the table below to enter traffic information.
To delete a row, select it from the left side then hit DEL. Use CTRL to select multiple rows.
"""
STP_HELP = "Use in switched networks."


def clear_session_state():
    """
    Remove all keys from the session state.

    Returns:
        None.
    """
    for key in st.session_state.keys():
        del st.session_state[key]


def create_flows_frame():
    """
    Create an empty pandas DataFrame with the columns 'Source', 'Target', and 'Flow'.

    Returns:
        A pandas DataFrame with the columns 'Source', 'Target', and 'Flow'.
    """
    df = pd.DataFrame({"Source": [], "Target": [], "Flow": []})
    convert_dict = {"Source": str, "Target": str}
    return df.astype(convert_dict)


def analyze_flows(topo_file, flow_file):
    """
    Analyze the flows in the given topology and flow information files.

    Args:
        topo_file (FileUploader): A file uploader widget for the network topology file.
        flow_file (FileUploader): A file uploader widget for the flow information file.

    Returns:
        None.
    """

    # Load the graph from a DOT file
    # Read the uploaded file using nx_pydot.read_dot()
    dot_data = topo_file.read().decode("utf-8").replace("\r\n", "\n")

    # Convert the Pydot graph to a NetworkX graph
    ORG = gd.get_dot_graph(dot_data)

    switching = st.sidebar.checkbox("Apply Spanning Tree", False, help=STP_HELP)
    if switching:
        gd.assign_stp_attributes(ORG)
        G = get_stp(ORG)
    else:
        G = ORG

    # Assign remaining attributes
    gd.assign_flow_attributes(G)
    gd.assign_bipartite_attributes(G)

    st.header("Traffic Flows")
    # Allow user to edit dataframe
    st.markdown(EDIT_FLOWS)

    # Creat a editable dataframe representing traffic flows by
    # reading a csv file or start with an empty frame
    if flow_file is None:
        df = create_flows_frame()
    else:
        df = pd.read_csv(flow_file)

    df_flows = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # The user must enter the source and target nodes correctly
    # followed by +ve flow value
    # TODO: Find a way to restrict input to nodes that exit in the graph
    for index, row in df_flows.iterrows():
        try:
            source = row.get("Source", "")
            target = row.get("Target", "")
            flow = row.get("Flow", 0)

            if (source in G.nodes) and (target in G.nodes) and (flow > 0):
                gd.add_capacity(G, row["Source"], row["Target"], row["Flow"])
            else:
                st.error(f"Unknown node or invalid flow at line {index}.")
                continue
        except Exception as e:
            st.error(e)

    # Add a button to save the DataFrame
    if st.button("Save Flows"):
        df_flows.to_csv("flows.csv", index=False)
        placeholder = st.empty()
        placeholder.success("Flows saved to CSV file!")
        time.sleep(1)  # Wait for 3 seconds
        placeholder.empty()

    st.header("Link Traffic")
    # Display the edge flows
    edge_data = [
        G[x][y]["dr"].split(",") + [G[x][y]["fw"], G[x][y]["bk"]] for x, y in G.edges
    ]
    df_edge = pd.DataFrame(edge_data, columns=("Source", "Target", "FW", "BK"))
    df_edge_selected = df_edge[(df_edge["FW"] > 0) | (df_edge["BK"] > 0)]
    st.dataframe(df_edge_selected, use_container_width=True)

    st.header("Node Traffic")
    # Display the node attributes
    node_data = [[n, G.nodes[n]["tx"], G.nodes[n]["rx"]] for n in G.nodes]
    df_node = pd.DataFrame(node_data, columns=("Node", "Outbound", "Inbound"))

    st.dataframe(
        df_node[(df_node["Outbound"] > 0) | (df_node["Inbound"] > 0)],
        use_container_width=True,
    )

    # Plotting the network graph
    plot_graph(ORG, G, df_flows, switching)

    if st.button("Redraw"):
        # Needed to re-draw graph
        if "pos" in st.session_state:
            del st.session_state["pos"]
            st.experimental_rerun()


def app():
    """
    The main application function that displays the user interface and handles
    the file uploads.

    Returns:
        None.
    """

    # The following will appear in a sidebar
    with st.sidebar:
        topo_file = st.file_uploader(
            "Upload Network", type="dot", help=UPLOAD_TOPO_HELP
        )
        flow_file = st.file_uploader(
            "Upload Flow Information", type="csv", help=UPLOAD_FLOW_HELP
        )

    # This will be the main page
    st.title(TITLE)
    st.markdown(ABOUT)

    # Display an error message if there is no input topology or
    if topo_file is not None:
        analyze_flows(topo_file, flow_file)
    else:
        clear_session_state()
        st.warning(UPLOAD_FILE)


if __name__ == "__main__":
    app()
