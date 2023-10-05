import pandas as pd

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Get basic statistics about the dataset
summary_stats = data.describe()

# Display the summary statistics
print(summary_stats)

# Get information about the columns, data types, and missing values
info = data.info()
