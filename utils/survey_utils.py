import pickle
import numpy as np

# Load BOTH files
with open("models/survey_model.pkl", "rb") as f:
    survey_model = pickle.load(f)

with open("models/survey_encoders.pkl", "rb") as f:
    encoders = pickle.load(f)

def predict_survey_risk(answers, age_months, sex,
                         ethnicity, jaundice,
                         family_asd, who_completed):

    # Step 1: Use encoders to convert text → numbers
    sex_enc       = encoders['sex'].transform([sex])[0]
    ethnicity_enc = encoders['ethnicity'].transform([ethnicity])[0]
    jaundice_enc  = encoders['jaundice'].transform([jaundice])[0]
    family_enc    = encoders['family_asd'].transform([family_asd])[0]
    who_enc       = encoders['who'].transform([who_completed])[0]

    # Step 2: Combine all features
    features = answers + [
        age_months,
        sex_enc,
        ethnicity_enc,
        jaundice_enc,
        family_enc,
        who_enc
    ]

    # Step 3: Use model to predict
    features_array = np.array(features).reshape(1, -1)
    probability = survey_model.predict_proba(features_array)[0][1]

    if probability >= 0.7:
        risk = "High"
    elif probability >= 0.4:
        risk = "Moderate"
    else:
        risk = "Low"

    return risk, probability