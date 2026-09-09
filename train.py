import pandas as pd
import xgboost as xgb
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
import joblib

# Load data
df = pd.read_csv("GUIDE_Test.csv", low_memory=False, on_bad_lines='skip', nrows=50000, encoding='utf-8')

# Ensure columns exist for grouping
df['IncidentGrade'] = df['IncidentGrade'].fillna('Unknown')
detector_counts = df.groupby('DetectorId')['IncidentGrade'].value_counts().unstack(fill_value=0)

# Safety check: ensure TruePositive and FalsePositive columns exist
for col in ['TruePositive', 'FalsePositive']:
    if col not in detector_counts.columns:
        detector_counts[col] = 0

detector_counts['total'] = detector_counts.sum(axis=1)
detector_counts['historical_fp_rate'] = detector_counts['FalsePositive'] / detector_counts['total']
detector_counts['historical_tp_rate'] = detector_counts['TruePositive'] / detector_counts['total']
detector_counts.to_csv("detector_historical_stats.csv")

# Merge features
df = df.merge(detector_counts['historical_fp_rate'], on='DetectorId', how='left')
df['historical_fp_rate'] = df['historical_fp_rate'].fillna(0.0)

features = ['Category', 'MitreTechniques', 'historical_fp_rate']
X = df[features].copy()
y = df['IncidentGrade']

# Preprocessing
X['MitreTechniques'] = X['MitreTechniques'].fillna('None')
X['Category'] = X['Category'].fillna('Other')

le_cat = LabelEncoder()
le_mitre = LabelEncoder()
le_target = LabelEncoder()

X['Category'] = le_cat.fit_transform(X['Category'].astype(str))
X['MitreTechniques'] = le_mitre.fit_transform(X['MitreTechniques'].astype(str))
y_encoded = le_target.fit_transform(y.astype(str))

# Save Encoders
joblib.dump(le_cat, "le_cat.pkl")
joblib.dump(le_mitre, "le_mitre.pkl")
joblib.dump(le_target, "le_target.pkl")

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.3, stratify=y_encoded, random_state=42)

# Calculate sample weights to fix the "Benign only" bias
sample_weights = compute_sample_weight(class_weight='balanced', y=y_train)

# Train model
model = xgb.XGBClassifier(
    objective='multi:softprob', 
    num_class=len(np.unique(y_encoded)), 
    eval_metric='mlogloss'
)
model.fit(X_train, y_train, sample_weight=sample_weights)

# Save model
joblib.dump(model, "triage_xgboost_model.pkl")
print("Preprocessing complete. Balanced XGBoost model successfully trained and exported.")
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# After model.fit(), make predictions on the test set
y_pred = model.predict(X_test)

# 1. Print the detailed report
print(classification_report(y_test, y_pred, target_names=le_target.classes_))

# 2. Plot a Confusion Matrix (The best way to see where the model is failing)
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', xticklabels=le_target.classes_, yticklabels=le_target.classes_)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()