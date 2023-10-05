import pandas as pd

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Display the first few rows of the dataset to get an overview
print(data.head())
