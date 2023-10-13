import networkx as nx
import matplotlib.pyplot as plt

# maybe build a visualized representation of the file directory.
# here is some example graph code

def visualize_tree(tree_data):
    G = nx.DiGraph()

    for node_id, node_info in tree_data.items():
        G.add_node(node_id, label=node_info["name"])

        if node_info["pid"] is not None:
            G.add_edge(node_info["pid"], node_id)

    pos = nx.drawing.nx_agraph.graphviz_layout(G, prog="dot")

    labels = nx.get_node_attributes(G, 'label')
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=5000, node_color='lightblue')
    plt.axis('off')

    plt.savefig("tree_structure.png", format="PNG")
    plt.show()

if __name__ == "__main__":
    tree_data = {
        0: {"name": "Root", "pid": None},
        1: {"name": "Node A", "pid": 0},
        2: {"name": "Node B", "pid": 0},
        3: {"name": "Node C", "pid": 1},
        4: {"name": "Node D", "pid": 2},
    }


    visualize_tree(tree_data)




