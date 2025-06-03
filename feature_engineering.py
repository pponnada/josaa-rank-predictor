import pandas as pd

# Load the preprocessed data
data = pd.read_csv('preprocessed_data.csv')

# Feature engineering
# Rank difference between opening and closing rank for each round
data['rank_diff'] = data['closing_rank'] - data['opening_rank']

# Save the feature engineered data
data.to_csv('feature_engineered_data.csv', index=False)

print("Feature engineering complete. Feature engineered data saved to feature_engineered_data.csv")
