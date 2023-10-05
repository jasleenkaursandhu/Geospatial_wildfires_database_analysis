import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from sklearn.cluster import KMeans
import numpy as np

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Create a directory to store the images if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")

# Extract latitude and longitude
coordinates = data[['LATITUDE', 'LONGITUDE']]

# Perform K-Means clustering
num_clusters = 5  # You can adjust the number of clusters as needed
kmeans = KMeans(n_clusters=num_clusters, random_state=0)
data['Cluster'] = kmeans.fit_predict(coordinates)

# Visualization 1: Scatter Plot of Clusters on Map
cluster_centers = kmeans.cluster_centers_
m = folium.Map(location=[data['LATITUDE'].mean(), data['LONGITUDE'].mean()], zoom_start=5)

# Add markers for cluster centers
for i in range(num_clusters):
    folium.Marker(location=[cluster_centers[i][0], cluster_centers[i][1]], 
                  icon=folium.DivIcon(html=f'<div>Cluster {i}</div>')).add_to(m)

# Add markers for data points
for index, row in data.iterrows():
    folium.CircleMarker(location=[row['LATITUDE'], row['LONGITUDE']], 
                        radius=3, color=sns.color_palette("Set2")[row['Cluster']], fill=True).add_to(m)

# Save the map as an HTML file
m.save("images/kmeans_clusters_map.html")

# Visualization 2: Histogram of Cluster Sizes
cluster_sizes = data['Cluster'].value_counts()

plt.figure(figsize=(10, 6))
sns.barplot(x=cluster_sizes.index, y=cluster_sizes.values, palette="Set2")
plt.xlabel("Cluster")
plt.ylabel("Number of Incidents")
plt.title("Cluster Sizes")
plt.savefig("images/kmeans_cluster_sizes_histogram.png")

# Show the histograms
plt.show()
