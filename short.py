# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 09:39:49 2023

@author: artim
"""

import streamlit as st
import networkx as nx
import io
from stp import get_stp
import pandas as pd
import matplotlib.pyplot as plt

# define a mapping between the 'speed' attribute and the 'weight' attribute
speed_to_weight = {"10": 100, "100": 19, "1000": 4, "10000": 2}


# Create a Streamlit file uploader
uploaded_file = st.file_uploader("Upload a DOT file", type="dot")

# If a file was uploaded
if uploaded_file is not None:
    # Read the uploaded file using nx_pydot.read_dot()
    dot_data = uploaded_file.read().decode("utf-8").replace('\r\n', '\n')
  
    # Convert the string to a file-like object
    file_obj = io.StringIO(dot_data)
    ORG = nx.Graph(nx.drawing.nx_pydot.read_dot(file_obj))

    st.write(ORG)
    st.write(ORG.edges)
    
    # Read the node's ID or create one based on its label
    for node in ORG.nodes:
        ORG.nodes[node]["ID"] = int(ORG.nodes[node].get(
            "ID",  ''.join(map(str, map(ord, node)))))

    # iterate through each edge in the pydot graph and add it to the networkx graph
    for edge in ORG.edges:
        # get the 'speed' attribute of the edge
        edge_speed = ORG.edges[edge].get('speed', '100')

        # map the 'speed' attribute to a 'weight' attribute using the speed_to_weight dictionary
        edge_weight = speed_to_weight[edge_speed]
        ORG.edges[edge]['weight'] = edge_weight
   
    st.write(ORG.edges)
    
    STP = get_stp(ORG)
    
    st.write(STP)
    st.write(STP.edges)
    
    G = ORG.edge_subgraph(STP.edges).copy()
    
    st.write(G)
    
     
    df = pd.DataFrame(G.edges(data=True), columns=['source', 'target', 'attributes'])

    # Split the attributes into separate columns
    df = pd.concat([df[['source', 'target']], df['attributes'].apply(pd.Series)], axis=1)
    
    # Print the DataFrame
    st.write(df)


    fig, _ = plt.subplots()
    # Draw the NetworkX graph G
    pos = nx.bipartite_layout(ORG, ['L1', 'L2', 'L3'], align='horizontal')
    nx.draw_networkx(ORG, pos=pos, with_labels=True)
    
    # Draw the STP over the NetworkX graph G
    nx.draw_networkx_edges(G, pos=pos, edgelist=STP.edges(),
                           edge_color='r', width=2.0)
    
    # Display the plot
    st.pyplot(fig)