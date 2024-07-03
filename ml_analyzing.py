"""
This script demonstrates a machine learning approach to predict the feasibility of
routes using a RandomForestClassifier model. It begins by loading route data from a
CSV file into a pandas DataFrame, where preprocessing steps include filling missing
values to ensure data integrity. Categorical variables such as city names and road
types are then encoded using OneHotEncoder to transform them into a numerical format
suitable for machine learning models. The dataset is further processed by selecting
relevant features and the target variable, which indicates whether a route is feasible.
The data is split into training and testing sets to evaluate the model's performance
on unseen data. A RandomForestClassifier is trained on the training set, and its
accuracy is assessed on the test set, providing insights into the model's ability to
predict route feasibility accurately. This script encapsulates the end-to-end process
of preparing data, training a model, and evaluating its performance, serving as a
foundational example of applying machine learning techniques to real-world problems.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import OneHotEncoder

# Data loading
df = pd.read_csv('/Users/pahomovskij/PycharmProjects/road-helper/routes.csv')

# Preprocessing
df.fillna(0, inplace=True)

# Encoding categorical variables
encoder = OneHotEncoder()
encoded_features = encoder.fit_transform(df[['city1', 'city2', 'road']]).toarray()

# Adding encoded features back to DataFrame
df_encoded = pd.concat([df, pd.DataFrame(encoded_features)], axis=1)

# Feature selection and target variable
X = df_encoded.drop(['id', 'is_possible', 'city1', 'city2', 'road', 'problem_point1', 'problem_point2', 'created_at'], axis=1)
y = df['is_possible']

# Data splitting
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model training
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Model evaluation
predictions = model.predict(X_test)
print("Accuracy:", round(accuracy_score(y_test, predictions),2))
