# app.py
from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib
import numpy as np

app = Flask(__name__)

model = joblib.load("triage_xgboost_model.pkl")
detector_stats = pd.read_csv("detector_historical_stats.csv").set_index("DetectorId")
le_cat = joblib.load("le_cat.pkl")
le_mitre = joblib.load("le_mitre.pkl")
le_target = joblib.load("le_target.pkl")

@app.route('/')
def live_queue_page():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def run_triage_inference():
    data = request.json
    detector_id = int(data.get("DetectorId", 0))
    category_str = str(data.get("Category", "Other"))
    mitre_str = str(data.get("MitreTechniques", "None"))

    hist_fp_rate = 0.5
    if detector_id in detector_stats.index:
        hist_fp_rate = float(detector_stats.loc[detector_id, 'historical_fp_rate'])

    try:
        cat_encoded = le_cat.transform([category_str])[0]
    except ValueError:
        cat_encoded = 0
        
    try:
        mitre_encoded = le_mitre.transform([mitre_str])[0]
    except ValueError:
        mitre_encoded = 0

    features = np.array([[cat_encoded, mitre_encoded, hist_fp_rate]])
    pred_code = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    
    predicted_grade = le_target.inverse_transform([pred_code])[0]
    confidence = float(max(probabilities))

    return jsonify({
        "Predicted_Grade": predicted_grade,
        "Confidence_Score": confidence,
        "Historical_FP_Rate": hist_fp_rate
    })

@app.route('/api/analytics/summary', methods=['GET'])
def serve_dashboard_data():
    return jsonify(detector_stats.reset_index().to_dict(orient="records"))
import numpy as np

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    # 1. Transform input (Ensure these match your training encoders)
    cat = le_cat.transform([data['category']])[0]
    mitre = le_mitre.transform([data['mitre']])[0]
    fp_rate = float(data['fp_rate'])
    
    # 2. Get prediction
    features = np.array([[cat, mitre, fp_rate]])
    probs = model.predict_proba(features)[0]
    pred_idx = np.argmax(probs)
    confidence = probs[pred_idx]
    label = le_target.inverse_transform([pred_idx])[0]
    
    # 3. Decision Logic for the UI
    if label == 'FalsePositive' and confidence > 0.70:
        status = "Auto-Archived"
        color = "green"
    elif label == 'TruePositive' and confidence > 0.60:
        status = "THREAT DETECTED"
        color = "red"
    else:
        status = f"Manual Review ({confidence:.1%})"
        color = "orange"
        
    return jsonify({'status': status, 'color': color})

if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)