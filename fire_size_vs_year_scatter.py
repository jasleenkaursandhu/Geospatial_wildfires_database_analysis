import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Create a scatter plot of fire size vs. fire year
plt.figure(figsize=(10, 6))
plt.scatter(data["FIRE_YEAR"], data["FIRE_SIZE"], alpha=0.5, color='red')
plt.xlabel("Fire Year")
plt.ylabel("Fire Size")
plt.title("Fire Size vs. Fire Year")

# Save the image
plt.savefig("images/fire_size_vs_year_scatter.png")

# Show the plot
plt.show()
