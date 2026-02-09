import joblib
import numpy as np

# -------------------------------
# Lazy load trained survey model
# -------------------------------
survey_bundle = None

def get_survey_model():
    global survey_bundle
    if survey_bundle is None:
        survey_bundle = joblib.load("models/asd_survey_model_colab.pkl")
    return survey_bundle

# -------------------------------
# Predict survey risk
# -------------------------------
def predict_survey_risk(answers):
    """
    answers: list of 10 values (A1–A10), each 0 or 1
    """

    bundle = get_survey_model()
    model = bundle["model"]
    threshold = bundle.get("threshold", 0.5)  # fallback safe

    X = np.array(answers).reshape(1, -1)

    if hasattr(model, "predict_proba"):
        prob = model.predict_proba(X)[0][1]

        if prob >= threshold:
            return "High", prob
        elif prob >= threshold * 0.7:
            return "Moderate", prob
        else:
            return "Low", prob

    # fallback (no probability support)
    pred = model.predict(X)[0]
    risk = "High" if pred == 1 else "Low"
    return risk, None
