import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from statsmodels.tsa.arima.model import ARIMA  # Import ARIMA from the new location
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import plotly.express as px
import plotly.graph_objects as go

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Convert the date column to datetime format
data['DISCOVERY_DATE'] = pd.to_datetime(data['DISCOVERY_DATE'], unit='D', origin='julian')

# Set the datetime column as the index
data.set_index('DISCOVERY_DATE', inplace=True)

# Create a directory to store the images if it doesn't exist
if not os.path.exists("images"):
    os.makedirs("images")

# Visualization 1: Time Series Forecasting of Fire Incidents using ARIMA
time_series = data.resample('M')['OBJECTID'].count()

# Fit an ARIMA model
model = ARIMA(time_series, order=(5, 1, 0))
model_fit = model.fit()

# Make forecasts
forecast_steps = 12  # Number of steps to forecast
forecast, stderr, conf_int = model_fit.forecast(steps=forecast_steps)

# Create forecasted date range
forecast_dates = pd.date_range(start=time_series.index[-1] + pd.DateOffset(months=1), periods=forecast_steps, freq='M')

# Plot time series with forecasts
plt.figure(figsize=(12, 6))
plt.plot(time_series, label='Observed')
plt.plot(forecast_dates, forecast, color='red', label='Forecast')
plt.fill_between(forecast_dates,
                 forecast - 1.96 * stderr, forecast + 1.96 * stderr,
                 color='pink', alpha=0.3, label='95% Confidence Interval')
plt.xlabel('Date')
plt.ylabel('Number of Fires')
plt.title('Time Series Forecasting of Fire Incidents using ARIMA')
plt.legend()
plt.savefig("images/time_series_forecast.png")

# Visualization 2: Spatial Clustering of Fire Incidents using DBSCAN
X = data[['LATITUDE', 'LONGITUDE']]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Apply DBSCAN clustering
dbscan = DBSCAN(eps=0.1, min_samples=10)
data['Cluster'] = dbscan.fit_predict(X_scaled)

# Visualization 3: Principal Component Analysis (PCA) for Dimensionality Reduction
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
data['PCA1'] = X_pca[:, 0]
data['PCA2'] = X_pca[:, 1]

# Advanced Visualization 4: Interactive Dashboard using Plotly
app = px.scatter(data, x='PCA1', y='PCA2', color='Cluster',
                 title='Interactive Dashboard - Spatial Clustering of Fire Incidents',
                 labels={'PCA1': 'Principal Component 1', 'PCA2': 'Principal Component 2'},
                 width=800, height=600,
                 hover_name=data.index.strftime('%Y-%m-%d'), hover_data=['OBJECTID', 'Cluster'])

# Add map with geospatial data
m = folium.Map(location=[data['LATITUDE'].mean(), data['LONGITUDE'].mean()], zoom_start=5)
heat_data = [[row['LATITUDE'], row['LONGITUDE']] for index, row in data.iterrows()]
folium.plugins.HeatMap(heat_data).add_to(m)

app.add_trace(go.Scattermapbox(
    lat=data['LATITUDE'],
    lon=data['LONGITUDE'],
    mode='markers',
    marker=dict(size=4, color='black'),
    showlegend=False
))

app.update_geos(projection_type="mercator")
app.show()
