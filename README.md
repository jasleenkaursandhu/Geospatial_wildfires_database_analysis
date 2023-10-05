# Geospatial Fires Database Analysis

![Wildfire](images/wildfire.jpg)

## Overview

Wildfires are a growing concern worldwide, posing significant threats to ecosystems, communities, and the environment. Understanding their patterns, causes, and impact is crucial for effective management and mitigation. This project focuses on the analysis of geospatial data related to wildfire incidents, aiming to gain insights into their behavior and trends.

## Dataset

We utilize a comprehensive dataset containing information about wildfire incidents. The dataset includes attributes such as:

- **Location**: Latitude and longitude coordinates of each fire incident.
- **Date and Time**: Timestamps of when each incident was discovered.
- **Size and Intensity**: Data on the size and intensity of the fires.
- **Cause**: Information about the potential causes of each fire.

The dataset provides a rich source of information that allows us to explore various aspects of wildfires, from their spatial distribution to temporal trends.

## Complex Visualizations

In this project, we have performed advanced data visualizations and analysis to uncover valuable insights:

### 1. Time Series Forecasting with ARIMA

We have employed the Autoregressive Integrated Moving Average (ARIMA) model to perform time series forecasting of fire incidents. This analysis helps us predict future trends in wildfire occurrences based on historical data.

### 2. Spatial Clustering with DBSCAN

Using the Density-Based Spatial Clustering of Applications with Noise (DBSCAN) algorithm, we have clustered fire incidents based on their geographic proximity. This enables us to identify high-density fire regions and potential hotspots.

### 3. Dimensionality Reduction with PCA

Principal Component Analysis (PCA) is applied to reduce the dimensionality of the dataset while preserving essential information. This aids in visualizing complex spatial data in a more manageable format.

### 4. Interactive Dashboard with Plotly

We have created an interactive dashboard using Plotly, allowing users to explore the spatial clustering of fire incidents dynamically. The dashboard provides insights into fire patterns, locations, and clusters.

## Requirements

To run this project, please install the required Python libraries and dependencies listed in the `requirements.txt` file. You can install them using pip:

```bash
pip install -r requirements.txt
