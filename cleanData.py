import pandas as pd

# Load CSV file
df = pd.read_csv("C:\\Users\\HP\\Downloads\\aieLeads.csv")

# Sort by a specific column (replace 'ColumnName' with actual column)
df_sorted = df.sort_values(by="CollegeName", ascending=True)

# Save the sorted file
df_sorted.to_csv("ai_sorted.csv", index=False)
