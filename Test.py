import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
from shapely.geometry import MultiLineString, LineString
from matplotlib.widgets import Button, TextBox

# Load the India map shapefile
india_shapefile_path = "D:\\ALL DATA\\9JAN\\SIMPLIFUED_POLYGON\\INPUT\\RoadPolygon.shp"
india_gdf = gpd.read_file(india_shapefile_path)

# Create an empty graph
G = nx.Graph()

# Function to add edges from a LineString
def add_edges_from_linestring(G, line):
    for start, end in zip(line.coords[:-1], line.coords[1:]):
        G.add_edge(start, end, weight=line.length)

# Add edges to the graph based on the India map shapefile
for idx, row in india_gdf.iterrows():
    geometry = row['geometry']
    if isinstance(geometry, LineString):
        add_edges_from_linestring(G, geometry)
    elif isinstance(geometry, MultiLineString):
        for line in geometry.geoms:
            add_edges_from_linestring(G, line)

# Define the start and end points (will be set by the user)
start_point = None
end_point = None

# Function to handle click event
def onclick(event):
    global start_point, end_point
    if event.button == 1:  # Left click
        if start_point is None:
            start_point = (event.xdata, event.ydata)
            print(f"Start point: {start_point}")
            plt.scatter(start_point[0], start_point[1], color='g', s=100)
        else:
            end_point = (event.xdata, event.ydata)
            print(f"End point: {end_point}")
            plt.scatter(end_point[0], end_point[1], color='r', s=100)
            find_shortest_path()
    plt.draw()

# Function to find and plot the shortest path
def find_shortest_path():
    global start_point, end_point
    
    if start_point is not None and end_point is not None:
        if not G.has_node(start_point):
            G.add_node(start_point)
        if not G.has_node(end_point):
            G.add_node(end_point)
        
        try:
            shortest_path = nx.shortest_path(G, source=start_point, target=end_point, weight='weight')
            print("Shortest path:", shortest_path)

            pos = {node: node for node in G.nodes()}
            india_gdf.plot(ax=plt.gca(), color='lightgray')
            nx.draw(G, pos, with_labels=False, node_size=5)

            path_edges = list(zip(shortest_path, shortest_path[1:]))
            path_lines = [LineString([start, end]) for start, end in path_edges]
            path_gdf = gpd.GeoDataFrame(geometry=path_lines, crs=india_gdf.crs)
            path_gdf.plot(ax=plt.gca(), color='r', linewidth=3)

            plt.show()
        except nx.NetworkXNoPath:
            print("No path found between the specified points.")
        except nx.NodeNotFound as e:
            print(f"Node not found in the graph: {e}")
    else:
        print("Please select start and end points before finding the shortest path.")

# Create the figure and connect the click event
fig, ax = plt.subplots(figsize=(10, 10))
cid = fig.canvas.mpl_connect('button_press_event', onclick)

# Plot the India map
india_gdf.plot(ax=ax, color='lightgray')

plt.title('Click to select start and end points')
plt.show()