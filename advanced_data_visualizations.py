import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from statsmodels.tsa.seasonal import seasonal_decompose

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Convert the date column to datetime format
data['DISCOVERY_DATE'] = pd.to_datetime(data['DISCOVERY_DATE'], unit='D', origin='julian')

# Set the datetime column as the index
data.set_index('DISCOVERY_DATE', inplace=True)

# Create a directory to store the images if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")

# Visualization 1: Geospatial Heatmap of Fire Incidents
m = folium.Map(location=[data['LATITUDE'].mean(), data['LONGITUDE'].mean()], zoom_start=5)
heat_data = [[row['LATITUDE'], row['LONGITUDE']] for index, row in data.iterrows()]

# Create a heatmap with time
from folium.plugins import HeatMapWithTime
HeatMapWithTime(heat_data).add_to(m)

# Save the interactive map as an HTML file
m.save("images/geospatial_heatmap.html")

# Visualization 2: Time Series Decomposition of Fire Incidents
time_series = data.resample('Y')['OBJECTID'].count()
decomposition = seasonal_decompose(time_series, model='additive', period=1)  # Assuming annual data, period=1

plt.figure(figsize=(12, 8))
plt.subplot(411)
plt.plot(time_series, label='Original')
plt.legend(loc='upper left')
plt.subplot(412)
plt.plot(decomposition.trend, label='Trend')
plt.legend(loc='upper left')
plt.subplot(413)
plt.plot(decomposition.seasonal, label='Seasonal')
plt.legend(loc='upper left')
plt.subplot(414)
plt.plot(decomposition.resid, label='Residual')
plt.legend(loc='upper left')
plt.tight_layout()
plt.savefig("images/time_series_decomposition.png")

# Visualization 3: Heatmap of Correlation Matrix
numeric_columns = data.select_dtypes(include='number')
correlation_matrix = numeric_columns.corr()

plt.figure(figsize=(12, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
plt.title("Correlation Heatmap")
plt.savefig("images/correlation_heatmap.png")

# Visualization 4: Time Series of Fires Over the Years by Size Class
fires_by_year_size = data.groupby([data.index.year, 'FIRE_SIZE_CLASS'])['OBJECTID'].count().unstack().fillna(0)

plt.figure(figsize=(12, 6))
fires_by_year_size.plot(ax=plt.gca())
plt.xlabel("Year")
plt.ylabel("Number of Fires")
plt.title("Time Series of Fires Over the Years by Size Class")
plt.legend(title="Size Class")
plt.savefig("images/time_series_fires.png")

# Save the images to the "images" folder
plt.show()
