import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
import pickle

# Load the data
data = pd.read_csv('historical_data.csv')

# Handle missing values
# Impute missing values in 'prev_year_closing_rank' with the mean closing rank for that college and branch
data['prev_year_closing_rank'] = data['prev_year_closing_rank'].fillna(data.groupby(['college_name', 'academic_program_name'])['closing_rank'].transform('mean'))

# For 2020, impute with a global mean
data['prev_year_closing_rank'] = data['prev_year_closing_rank'].fillna(data['closing_rank'].mean())

# One-hot encode 'college_name' and 'academic_program_name'
encoder = OneHotEncoder(handle_unknown='ignore')
encoder.fit(data[['college_name', 'academic_program_name']])

filename_encoder = 'encoder.pkl'
pickle.dump(encoder, open(filename_encoder, 'wb'))
print(f"Encoder saved to {filename_encoder}")

encoded_data = encoder.transform(data[['college_name', 'academic_program_name']]).toarray()
encoded_df = pd.DataFrame(encoded_data, columns=encoder.get_feature_names_out(['college_name', 'academic_program_name']))

# Concatenate encoded features with the original data
data = pd.concat([data, encoded_df], axis=1)

# Remove original categorical columns
data = data.drop(['college_name', 'academic_program_name'], axis=1)

# Scale the numerical features, excluding 'year', 'round', and 'is_final_round'
numerical_cols = ['opening_rank', 'closing_rank', 'prev_year_closing_rank', 'delta_closing_rank_1yr', 'delta_closing_rank_2yr_avg', 'round_relative_rank_diff', 'closing_rank_percent_change_from_round1', 'mean_closing_rank_last_2yrs', 'weighted_moving_avg']
scaler = StandardScaler()
data[numerical_cols] = scaler.fit_transform(data[numerical_cols])

# Save the preprocessed data
data.to_csv('preprocessed_data.csv', index=False)

# Save the scaler to a file
filename = 'scaler.pkl'
pickle.dump(scaler, open(filename, 'wb'))
print(f"Scaler saved to {filename}")

print("Data preprocessing complete. Preprocessed data saved to preprocessed_data.csv")
