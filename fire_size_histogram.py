import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Create a histogram of fire sizes
plt.figure(figsize=(10, 6))
plt.hist(data["FIRE_SIZE"], bins=50, edgecolor='k')
plt.xlabel("Fire Size")
plt.ylabel("Frequency")
plt.title("Distribution of Fire Sizes")

# Save the image
plt.savefig("images/fire_size_histogram.png")

# Show the plot
plt.show()
