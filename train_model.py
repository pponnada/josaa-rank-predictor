import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import pickle

# Load the feature engineered data
data = pd.read_csv('feature_engineered_data.csv')

# Convert the 'year' column to integer type
data['year'] = data['year'].astype(int)

# Define features and target
features = data.drop(['closing_rank'], axis=1)
target = data['closing_rank']

# Split the data into training and testing sets based on year
train_data = data[data['year'].isin([2020, 2021, 2022, 2023])]
test_data = data[data['year'] == 2024]

X_train = train_data.drop(['closing_rank'], axis=1)
y_train = train_data['closing_rank']
X_test = test_data.drop(['closing_rank'], axis=1)
y_test = test_data['closing_rank']

# Train the Random Forest Regression model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

print(f"Mean Absolute Error: {mae}")
print(f"Mean Squared Error: {mse}")
print(f"Root Mean Squared Error: {rmse}")
print(f"R-squared: {r2}")

print("Model training complete.")

# Save the trained model to a file
filename = 'josaa_model.pkl'
pickle.dump(model, open(filename, 'wb'))
print(f"Trained model saved to {filename}")
