# Flow Analyzer

This is a Python app built with Streamlit that analyzes traffic flow in a network. It uses the following libraries:

- Streamlit
- NetworkX
- Pydot
- Matplotlib
- Pandas


## Installation

Clone this repository to your local machine using this command:

```bash
$ git clone https://github.com/<USERNAME>/<REPOSITORY>.git
```

Once you have cloned the repository, navigate to the directory and install the necessary libraries with this command:

```bash
$ pip install -r requirements.txt
```

## Usage

To run the app, execute the following command in your terminal:

```bash
$ streamlit run app.py
```

The app will open in your default web browser.


To analyze a network, you can upload a text file containing the network in DOT format. The app will parse the file, create a network graph, and display information about the edges and nodes in the network.

Alternatively, you can use the built-in example network by checking the "Use example network" checkbox.

# Input

The App takes in the form of traffic requirements between an pair of nodes in the network.

 
# Output

The app generates the following output:

## Edge information

The app displays information about the capacity and traffic flow on each edge in the network in a table. The table includes the following columns:

Src: The source node of the edge.
Dst: The destination node of the edge.
Tx: The amount of traffic transmitted on the edge.
Rx: The amount of traffic received on the edge.

## Node information

The app displays information about the traffic flow at each node in the network in a table. The table includes the following columns:

Node: The name of the node.
Tx: The amount of traffic transmitted by the node.
Rx: The amount of traffic received by the node.


## Graph visualization

The app also displays a visualization of the network using Matplotlib. The nodes are positioned using the spring layout algorithm, and the edges are drawn as arrows with labels indicating the amount of traffic flow.
