import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Group data by year and fire size class, count the number of fires
fires_by_year_size = data.groupby(['FIRE_YEAR', 'FIRE_SIZE_CLASS'])['OBJECTID'].count().unstack().fillna(0)

# Create a time series plot
plt.figure(figsize=(12, 6))
fires_by_year_size.plot(ax=plt.gca())
plt.xlabel("Year")
plt.ylabel("Number of Fires")
plt.title("Time Series of Fires Over the Years by Size Class")
plt.legend(title="Size Class")

# Save the image
plt.savefig("images/time_series_fires.png")

# Show the plot
plt.show()
