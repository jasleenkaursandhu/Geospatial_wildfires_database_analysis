import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Select numeric columns for correlation analysis
numeric_columns = data.select_dtypes(include='number')

# Compute the correlation matrix
correlation_matrix = numeric_columns.corr()

# Create a heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
plt.title("Correlation Heatmap")

# Save the image
plt.savefig("images/correlation_heatmap.png")

# Show the plot
plt.show()
