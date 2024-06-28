import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import MultiLineString, LineString
from scipy.spatial import KDTree
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox

# Initialize global variables
start_point = None
end_point = None
india_shapefile_path = None
output_shapefile = None
india_gdf = None
G = None
kdtree = None
nodes = None

# Function to add edges from a LineString
def add_edges_from_linestring(G, line):
    for start, end in zip(line.coords[:-1], line.coords[1:]):
        G.add_edge(start, end, weight=LineString([start, end]).length)

# Function to find the nearest node in the graph
def find_nearest_node(point):
    _, idx = kdtree.query(point)
    nearest_node = tuple(nodes[idx])
    return nearest_node

# Function to handle click event
def onclick(event):
    global start_point, end_point
    if event.button == 1:  # Left click
        if start_point is None:
            start_point = (event.xdata, event.ydata)
            start_point = find_nearest_node(start_point)
            print(f"Start point: {start_point}")
            plt.scatter(start_point[0], start_point[1], color='g', s=100)
        else:
            end_point = (event.xdata, event.ydata)
            end_point = find_nearest_node(end_point)
            print(f"End point: {end_point}")
            plt.scatter(end_point[0], end_point[1], color='r', s=100)
            find_shortest_path()
            # Reset start_point and end_point for next path calculation
            start_point = None
            end_point = None
    plt.draw()

# Function to find the shortest path
def find_shortest_path():
    global start_point, end_point
    
    # Ensure start and end points exist in the graph
    if not G.has_node(start_point):
        G.add_node(start_point)
    if not G.has_node(end_point):
        G.add_node(end_point)
    
    # Find the shortest path
    try:
        shortest_path = nx.shortest_path(G, source=start_point, target=end_point, weight='weight')
        print("Shortest path:", shortest_path)
        
        # Prepare the shortest path as a GeoDataFrame
        path_edges = list(zip(shortest_path, shortest_path[1:]))
        path_lines = [LineString([start, end]) for start, end in path_edges]
        path_gdf = gpd.GeoDataFrame(geometry=path_lines, crs=india_gdf.crs)
        
        # Save the GeoDataFrame to a shapefile
        path_gdf.to_file(output_shapefile)
        
        # Plot the graph and the shortest path
        pos = {node: node for node in G.nodes()}
        india_gdf.plot(ax=plt.gca(), color='lightgray')
        nx.draw(G, pos, with_labels=False, node_size=5)

        # Highlight the entire road
        path_gdf.plot(ax=plt.gca(), color='r', linewidth=3)

        plt.show()
        
        print(f"Saved shortest path to {output_shapefile}")
        
    except nx.NetworkXNoPath:
        print("No path found between the specified points.")
    except nx.NodeNotFound as e:
        print(f"Node not found in the graph: {e}")

# Function to select input shapefile
def select_input_shapefile():
    global india_shapefile_path, india_gdf, G, kdtree, nodes
    india_shapefile_path = filedialog.askopenfilename(filetypes=[("Shapefiles", "*.shp")])
    if india_shapefile_path:
        india_gdf = gpd.read_file(india_shapefile_path)
        
        # Create an empty graph
        G = nx.Graph()
        
        # Add edges to the graph based on the shapefile
        for idx, row in india_gdf.iterrows():
            geometry = row['geometry']
            if isinstance(geometry, LineString):
                add_edges_from_linestring(G, geometry)
            elif isinstance(geometry, MultiLineString):
                for line in geometry.geoms:
                    add_edges_from_linestring(G, line)

        # Create KDTree for fast nearest node lookup
        nodes = np.array(G.nodes)
        kdtree = KDTree(nodes)

        messagebox.showinfo("Input Shapefile", f"Loaded input shapefile: {india_shapefile_path}")

# Function to select output shapefile
def select_output_shapefile():
    global output_shapefile
    output_shapefile = filedialog.asksaveasfilename(defaultextension=".shp", filetypes=[("Shapefiles", "*.shp")])
    if output_shapefile:
        messagebox.showinfo("Output Shapefile", f"Selected output shapefile: {output_shapefile}")

# Create Tkinter window
root = tk.Tk()
root.title("Shapefile Selector")

input_button = tk.Button(root, text="Select Input Shapefile", command=select_input_shapefile)
input_button.pack(pady=10)

output_button = tk.Button(root, text="Select Output Shapefile", command=select_output_shapefile)
output_button.pack(pady=10)

start_button = tk.Button(root, text="Start", command=root.quit)
start_button.pack(pady=10)

root.mainloop()

# After the Tkinter window is closed, proceed with the plotting
if india_shapefile_path and output_shapefile:
    # Create the figure and connect the click event
    fig, ax = plt.subplots(figsize=(10, 10))
    cid = fig.canvas.mpl_connect('button_press_event', onclick)
    
    # Plot the India map
    india_gdf.plot(ax=plt.gca(), color='lightgray')
    plt.show()
else:
    print("Input or output shapefile not selected. Exiting.")
