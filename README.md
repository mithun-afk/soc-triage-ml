# Security Incident Triage System

## Abstract

Security Operations Centers (SOC) are frequently overwhelmed by a high volume of alerts, many of which are false positives. This project introduces a machine learning-based security incident triage system designed to predict and analyze cybersecurity alerts, thereby reducing alert fatigue. By leveraging historical telemetry data, the system calculates detector-specific false positive rates and trains an XGBoost classifier to automatically grade incoming alerts (e.g., True Positive, False Positive). The solution encompasses a complete pipeline: an automated model training script, a RESTful Flask API for real-time inference and integration, and an interactive Streamlit dashboard for SOC analysts to visualize trends and monitor alert distributions. This approach significantly streamlines the incident response workflow, enabling analysts to focus on genuine threats.


## Overview

The repository consists of three main components:
1. **Model Training (`train.py`)**: An automated script to preprocess telemetry data, calculate historical False Positive (FP) rates per detector, and train an XGBoost classifier with balanced class weights to predict the incident grade.
2. **Flask API (`app.py`)**: A backend web service exposing endpoints for real-time predictions and analytics summaries. It evaluates incoming alerts based on the trained XGBoost model.
3. **Streamlit Dashboard (`dashboard.py`)**: An interactive analytics dashboard for security operations center (SOC) analysts to visualize alert trends, filter telemetry records, and download summary reports.

## Features

- **Automated Triage**: Classifies alerts based on Category, MITRE ATT&CK techniques, and historical detector behavior.
- **RESTful Endpoints**:
  - `POST /predict`: Predicts the status of an alert (e.g., "Auto-Archived", "THREAT DETECTED", "Manual Review") along with a confidence score.
  - `GET /api/analytics/summary`: Serves historical detector metrics.
- **Interactive Analytics**: Rich visualizations including Daily Alert Trends, Incident Grade Distributions, and Alerts by Category, built with Streamlit and Plotly.
- **Data Export**: Capability to download filtered summary reports directly from the dashboard.

## Requirements

Ensure you have Python 3.x installed along with the following packages:

```bash
pip install flask pandas numpy xgboost scikit-learn joblib streamlit plotly
```

## The Project Structure

- `train.py`: The machine learning pipeline script to train the XGBoost model and save encoders.
- `app.py`: The main Flask application for serving model inferences.
- `dashboard.py`: The Streamlit application for the interactive dashboard.
- `triage_xgboost_model.pkl`: The trained XGBoost model (generated after running `train.py`).
- `le_*.pkl`: Saved LabelEncoders for categorical features.
- `detector_historical_stats.csv`: Precomputed historical FP rates for detectors.
- `GUIDE_Test.csv`: Sample historical telemetry dataset (required for training and the dashboard).
- `/templates` & `/static`: Frontend assets for the Flask application.

## Usage

### 1. Model Training
Before running the API, ensure the model and encoders are generated. Place your historical telemetry data (`GUIDE_Test.csv`) in the root directory and run:
```bash
python train.py
```
This will output `triage_xgboost_model.pkl`, the encoder `.pkl` files, and evaluate the model on a test split.

### 2. Start the API Server
Run the Flask application to start the inference API:
```bash
python app.py
```
The server will start on `http://localhost:5000`. You can send a `POST` request to `/predict` or `/api/predict` with JSON data representing an alert.

### 3. Launch the Dashboard
To visualize the telemetry data and metrics, start the Streamlit dashboard in a separate terminal:
```bash
streamlit run dashboard.py
```
This will launch the dashboard in your default web browser.

## API Documentation

### `POST /predict`
Predicts the severity and action required for a given alert.

**Request Body:**
```json
{
  "category": "Credential Access",
  "mitre": "T1003",
  "fp_rate": 0.4
}
```

**Response:**
```json
{
  "status": "THREAT DETECTED",
  "color": "red"
}
```
