import pickle
import numpy as np

# Load trained model
with open("models/survey_model_2.pkl", "rb") as f:
    survey_model = pickle.load(f)

# Load encoders
with open("models/survey_encoders_2.pkl", "rb") as f:
    encoders = pickle.load(f)

def predict_survey_risk(answers, age_months, sex, family_asd):
    """
    Predicts ASD risk from survey responses.
    
    Parameters:
    - answers: list of 10 binary values (A1-A10)
    - age_months: int (18-36)
    - sex: str ("m" or "f")
    - family_asd: str ("yes" or "no")
    
    Returns:
    - risk: str ("High", "Moderate", or "Low")
    - probability: float (0.0 to 1.0)
    """
    
    # Encode categorical features
    sex_enc    = encoders['sex'].transform([sex])[0]
    family_enc = encoders['family_asd'].transform([family_asd])[0]
    
    # Combine features: A1-A10 (10) + Age (1) + Sex (1) + Family (1) = 13
    features = answers + [age_months, sex_enc, family_enc]
    
    # Reshape for model
    features_array = np.array(features).reshape(1, -1)
    
    # Predict
    probability = survey_model.predict_proba(features_array)[0][1]
    
    # Map to risk levels
    if probability >= 0.7:
        risk = "High"
    elif probability >= 0.4:
        risk = "Moderate"
    else:
        risk = "Low"
    
    return risk, probability