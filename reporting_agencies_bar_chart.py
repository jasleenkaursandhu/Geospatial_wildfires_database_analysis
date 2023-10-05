import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
data = pd.read_csv("data/Fires_pruned.csv")

# Get the top 10 reporting agencies by frequency
top_reporting_agencies = data["NWCG_REPORTING_AGENCY"].value_counts().head(10)

# Create a bar chart
plt.figure(figsize=(12, 6))
top_reporting_agencies.plot(kind='bar', color='skyblue')
plt.xlabel("Reporting Agency")
plt.ylabel("Count")
plt.title("Top 10 Reporting Agencies")
plt.xticks(rotation=45)

# Save the image
plt.savefig("images/top_reporting_agencies_bar_chart.png")

# Show the plot
plt.show()
