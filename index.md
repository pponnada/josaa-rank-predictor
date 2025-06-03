---
layout: default
title: Building a JOSAA Rank Prediction Engine - A Technical Overview
---

# Building a JOSAA Rank Prediction Engine: A Technical Overview

This post outlines the development of a system designed to predict college admission closing ranks for the Joint Seat Allocation Authority (JoSAA) counselling process. The primary objective is to leverage historical data and machine learning techniques to forecast these ranks, providing a data-informed perspective on potential admission scenarios.

**Disclaimer:**
The JOSAA Rank Predictor is an experimental project developed for educational and illustrative purposes. The predictions generated are based on statistical models and historical data, and are not guaranteed to be accurate. Users should exercise their own due diligence and consult official JoSAA resources or professional advisors before making any decisions related to the JoSAA application process.

**The Core Technical Goal:**
To develop a predictive model capable of estimating the closing rank for a given college, academic program, year, and counselling round tuple.

**Access the Code:**
The complete codebase for this project is open-source and available on GitHub: [https://github.com/pponnada/josaa-rank-predictor](https://github.com/pponnada/josaa-rank-predictor)

## System Architecture and Pipeline

The system architecture follows a standard machine learning pipeline, transforming raw data into actionable predictions through several key stages:

### 1. Data Acquisition
The foundational dataset comprises historical opening and closing ranks obtained from the official JoSAA admissions portal: [JoSAA Opening Closing Rank Archive](https://josaa.admissions.nic.in/applicant/seatmatrix/openingclosingrankarchieve.aspx). Data extraction was facilitated by the `josaa-scrapper` Chrome extension, which automates the retrieval of rank details across various parameters (years, rounds, institutes, programs).

### 2. Data Storage and Structuring (`build_db.py`)
The scraped data, initially in CSV-like formats, is consolidated into a SQLite database using the `build_db.py` script. This relational database provides a structured and queryable repository for the historical data, as defined by the `schema.sql` file. This structured approach enables efficient data retrieval and manipulation in subsequent stages of the pipeline.

### 3. Initial Feature Engineering (`query.sql`)
A comprehensive SQL query, `query.sql`, is executed against the SQLite database to extract relevant data and engineer initial features. This query focuses on specific seat types ('OPEN'), gender categories ('Gender-Neutral'), and quotas ('AI', 'OS') for non-IIT institutes. Key engineered features, designed to capture temporal trends and relative rank positioning, include:

*   `prev_year_closing_rank`: The closing rank for the same college/branch combination from the previous year.
*   `delta_closing_rank_1yr`: Year-over-year change in closing rank.
*   `delta_closing_rank_2yr_avg`: Change in closing rank compared to the average of the last two years.
*   `is_final_round`: A binary indicator (0 or 1) to denote if a particular entry is from the final counselling round for that year.
*   `round_relative_rank_diff`: Difference in closing rank compared to the previous round in the same year.
*   `closing_rank_percent_change_from_round1`: Percentage change in closing rank from Round 1 for a given year.
*   `mean_closing_rank_last_2yrs`: Simple moving average of closing ranks over the past two years.
*   `weighted_moving_avg`: A weighted average of past years' closing ranks, giving more importance to recent years.

The resulting dataset, enriched with these features, is exported to `historical_data.csv`.

### 4. Data Preprocessing (`preprocess.py`)
The `historical_data.csv` undergoes several preprocessing steps critical for machine learning model efficacy:

*   **Missing Value Imputation**: Null values, particularly for historical rank features (e.g., `prev_year_closing_rank` for the earliest year in the dataset), are handled using appropriate imputation strategies.
*   **Categorical Encoding**: Textual features such as `college_name` and `academic_program_name` are transformed into a numerical representation using One-Hot Encoding. The fitted `OneHotEncoder` object is persisted as `encoder.pkl` for later use in decoding predictions.
*   **Feature Scaling**: Numerical features (e.g., `opening_rank`, `closing_rank`, and engineered rank-based features) are standardized using `StandardScaler`. This process scales features to have zero mean and unit variance, which benefits many learning algorithms by preventing features with larger magnitudes from dominating the learning process. The fitted `scaler` object is also saved as `scaler.pkl`.

The preprocessed dataset is then saved as `preprocessed_data.csv`.

### 5. Advanced Feature Engineering (`feature_engineering.py`)
The `feature_engineering.py` script ingests `preprocessed_data.csv` to perform further feature transformations or selection. This stage is intended to derive more sophisticated features that might capture more complex relationships in the data, potentially improving model performance. The final feature set for model training is exported as `feature_engineered_data.csv`.

### 6. Model Training and Evaluation (`train_model.py`)
The `feature_engineered_data.csv` serves as input to the `train_model.py` script for model development:

*   **Data Splitting**: The dataset is partitioned into training and testing subsets. This allows the model to be trained on one portion of the data and evaluated on unseen data (the test set) to provide an unbiased assessment of its generalization capabilities.
*   **Model Selection & Training**: A `RandomForestRegressor` is employed for this regression task. Random Forests are ensemble learning methods that construct multiple decision trees during training and output the mean prediction of the individual trees, which generally improves predictive accuracy and controls over-fitting. The model is trained on the training subset to learn the mapping from input features to the target variable (`closing_rank`).
*   **Persistence**: The trained model object is serialized using `pickle` and saved to `josaa_model.pkl`. This allows the trained model to be reloaded and used for predictions without retraining.

### 7. Prediction Pipeline (`predict.py`)
The `predict.py` script orchestrates the generation of closing rank predictions for a target year (e.g., 2025, Round 6):

*   **Artifact Loading**: It loads the persisted model (`josaa_model.pkl`), scaler (`scaler.pkl`), and one-hot encoder (`encoder.pkl`) that were saved during the preprocessing and training phases.
*   **Input Data Preparation**: To predict for a future year, the script takes the latest available historical data for each unique college-branch combination as a template. It then updates time-dependent features (like 'year' and 'round') to reflect the target prediction period. Other features are derived or carried over based on the logic established in the feature engineering steps.
*   **Prediction**: The prepared feature matrix for the target year is fed into the loaded `RandomForestRegressor` model, which outputs scaled predictions for the `closing_rank`.
*   **Inverse Transformation**: The model's predictions are initially in a scaled format, and categorical identifiers are one-hot encoded. To make them human-readable:
    *   The `scaler` object's `inverse_transform` method is used to convert the scaled `closing_rank` predictions back to their original rank values. This requires constructing a dummy DataFrame with the same structure as the data used to fit the scaler, placing the predicted scaled values in the correct column, and then applying the inverse transformation.
    *   The `encoder` object's `inverse_transform` method is used to convert the one-hot encoded college and program features back to their original string representations.
*   **Reporting**: The final, human-readable predictions, along with the last known historical final ranks for comparative analysis, are compiled into a pandas DataFrame. This DataFrame is then sorted by the `predicted_closing_rank` in ascending order and saved to a CSV file named `prediction_report.csv`.

## Conclusion

This project demonstrates a systematic, data-driven approach to building a predictive model for JoSAA closing ranks. It covers key stages of a typical machine learning workflow, from data acquisition and preprocessing to feature engineering, model training, and prediction.

While this system serves as an educational tool and a practical example of applying ML to real-world data, the accuracy of its predictions is subject to the quality and representativeness of the historical data and the inherent complexities of the admissions process.

The codebase is available on GitHub for review, further development, and contributions. Potential future enhancements could include exploring alternative modeling techniques (e.g., Gradient Boosting, Neural Networks), incorporating more diverse data sources, or refining feature engineering strategies to capture more nuanced trends.
