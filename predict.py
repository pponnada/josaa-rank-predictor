import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

# Load the feature engineered data
data = pd.read_csv('feature_engineered_data.csv')

# Convert the 'year' column to integer type
data['year'] = data['year'].astype(int)

# Load the trained model from file
filename_model = 'josaa_model.pkl'
model = pickle.load(open(filename_model, 'rb'))

# Load the scaler from file
filename_scaler = 'scaler.pkl'
scaler = pickle.load(open(filename_scaler, 'rb'))

# Load the OneHotEncoder from file (ensure this was saved during preprocessing)
filename_encoder = 'encoder.pkl'
encoder = pickle.load(open(filename_encoder, 'rb'))

# Identify one-hot encoded college and branch columns
college_branch_cols = [col for col in data.columns if col.startswith('college_name_') or col.startswith('academic_program_name_')]

# Group by college and branch and get the last row
last_rows = data.groupby(college_branch_cols, as_index=False).last()

# Create data for 2025, round 6
year = 2025
round_num = 6

# Create a new dataframe for 2025 round 6 predictions based on the last known data
data_2025 = last_rows.copy()
data_2025['year'] = year
data_2025['round'] = round_num

# The 'closing_rank' column in data_2025 at this point is the SCALED closing rank
# from the last historical record for each college/branch combination.
# We'll save it to inverse_transform later for comparison.
historical_scaled_closing_rank = data_2025['closing_rank'].copy()


# Get the column names from the training data
X_train_columns = model.feature_names_in_

# Prepare the feature matrix X_2025 for prediction.
# data_2025 contains all columns, including the historical 'closing_rank'.
# X_train_columns contains the feature names the model was trained on (and does not include 'closing_rank').
# Selecting columns from data_2025 using X_train_columns ensures:
#   1. Only the required features are selected.
#   2. The historical 'closing_rank' from data_2025 is excluded.
#   3. The columns are in the correct order as expected by the model.
X_2025 = data_2025[X_train_columns]

y_pred_2025_scaled = model.predict(X_2025)

# Create a dummy dataframe to inverse transform the scaled predictions
numerical_cols = ['opening_rank', 'closing_rank', 'prev_year_closing_rank', 'delta_closing_rank_1yr', 'delta_closing_rank_2yr_avg', 'round_relative_rank_diff', 'closing_rank_percent_change_from_round1', 'mean_closing_rank_last_2yrs', 'weighted_moving_avg']
dummy_df = pd.DataFrame(np.zeros((len(y_pred_2025_scaled), len(numerical_cols))), columns=numerical_cols)

# The model predicts 'closing_rank'. So, place the scaled predictions in the 'closing_rank' column.
dummy_df['closing_rank'] = y_pred_2025_scaled

# Inverse transform the scaled predictions
# 'closing_rank' is the second column (index 1) in numerical_cols as defined in preprocess.py
try:
    closing_rank_col_index = numerical_cols.index('closing_rank')
except ValueError:
    # This should not happen if preprocess.py and predict.py are consistent
    print("Error: 'closing_rank' not found in numerical_cols. Defaulting to index 1.")
    closing_rank_col_index = 1
y_pred_2025 = scaler.inverse_transform(dummy_df)[:, closing_rank_col_index]

# Inverse transform the historical scaled closing ranks
dummy_df_historical = pd.DataFrame(np.zeros((len(historical_scaled_closing_rank), len(numerical_cols))), columns=numerical_cols)
dummy_df_historical['closing_rank'] = historical_scaled_closing_rank.values
historical_unscaled_final_rank = scaler.inverse_transform(dummy_df_historical)[:, closing_rank_col_index]

# Print the predicted closing ranks for 2025
print("Predicted closing ranks for 2025:")

# Inverse transform one-hot encoded college and branch names
ohe_columns_for_decode = data_2025[college_branch_cols]
actual_names_array = encoder.inverse_transform(ohe_columns_for_decode)

# Create a DataFrame for more readable results
output_df = pd.DataFrame({
    'college_name': actual_names_array[:, 0],
    'academic_program_name': actual_names_array[:, 1],
    'year': data_2025['year'].values,
    'round': data_2025['round'].values,
    'historical_final_closing_rank': historical_unscaled_final_rank,
    'predicted_closing_rank': y_pred_2025
})

# Ensure ranks are integers for display if appropriate, or round them
output_df['historical_final_closing_rank'] = output_df['historical_final_closing_rank'].round().astype(int)
output_df['predicted_closing_rank'] = output_df['predicted_closing_rank'].round().astype(int)

# Sort the DataFrame by predicted closing rank in ascending order
output_df_sorted = output_df.sort_values(by='predicted_closing_rank', ascending=True)

# Save the sorted DataFrame to a CSV file
csv_report_filename = "prediction_report.csv"
output_df_sorted.to_csv(csv_report_filename, index=False)

print(f"\nSorted prediction report saved to {csv_report_filename}")

# The previous text report code is now replaced by CSV saving.
# If you still want the text report, you can uncomment the lines below
# and adjust the `report_string` to use `output_df_sorted.to_string()` if needed.
# pd.set_option('display.max_rows', 100)
# pd.set_option('display.max_columns', None)
# pd.set_option('display.width', 1000)
# pd.set_option('display.max_colwidth', None)
# report_string = output_df_sorted.to_string() # Or output_df.to_string() if you want unsorted for text
# report_filename_txt = "prediction_report.txt"
# with open(report_filename_txt, "w") as f:
#     f.write("Predicted Closing Ranks for 2025:\n\n") # Removed "First 50 Entries"
#     f.write(report_string)
# print(f"Text report saved to {report_filename_txt}")
