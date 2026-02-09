import streamlit as st
from utils.survey_utils import predict_survey_risk
from emotion.emotion_engine import run_emotion_session

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="ASD Screening Application",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Autism Spectrum Disorder (ASD) Screening Tool")
st.caption("This application is a screening aid and not a medical diagnosis.")

# -------------------------------------------------
# Survey Section
# -------------------------------------------------
st.header("📝 Parent / Caregiver Questionnaire")

questions = [
    "Does your child struggle to understand how others are feeling by looking at their facial expressions?",
    
    "Does your child find it hard to keep a conversation going back-and-forth, or do they tend to talk mostly about their own interests?",
    
    "When playing with other children, does your child have difficulty understanding the unwritten social rules (like taking turns or sharing)?",
    
    "Does your child become very upset or anxious when their daily routine changes, even in small ways?",
    
    "Does your child find it difficult to imagine what things might be like from another person's point of view?",
    
    "In social gatherings (like birthday parties or family events), does your child seem confused about what to do or how to join in?",
    
    "Does your child avoid making eye contact, or does eye contact seem uncomfortable or unnatural for them?",
    
    "Does your child have very strong, focused interests in specific topics (like trains, numbers, or certain TV shows) that they talk about repeatedly?",
    
    "Does your child notice small details that others might miss, but sometimes miss the bigger picture or main point?",
    
    "Does your child find noisy, crowded, or bright environments (like supermarkets or playgrounds) overwhelming or distressing?"
]

answers = []

for i, q in enumerate(questions, start=1):
    response = st.radio(
        f"Q{i}. {q}",
        ["No", "Yes"],
        horizontal=True,
        key=f"q{i}"
    )
    answers.append(1 if response == "Yes" else 0)

if st.button("Submit Survey"):
    survey_risk, survey_prob = predict_survey_risk(answers)
    st.session_state["survey_risk"] = survey_risk
    st.session_state["survey_prob"] = survey_prob

    st.success(f"📝 Survey Risk Level: **{survey_risk}**")
    if survey_prob is not None:
        st.caption(f"Predicted ASD Probability: {round(survey_prob, 2)}")

# -------------------------------------------------
# Emotion Detection Section
# -------------------------------------------------
st.header("😊 Emotion Recognition Assessment")

st.write(
    "The child will be shown a set of emotional stimuli while facial expressions "
    "are analyzed to evaluate emotional responsiveness."
)

if st.button("Run Emotion Analysis"):
    with st.spinner("Running emotion analysis... Please wait"):
        emotion_score = run_emotion_session()
        st.session_state["emotion_score"] = emotion_score

    st.success(f"Emotion Analysis Completed (Score: {emotion_score})")

# -------------------------------------------------
# Final ASD Risk Assessment
# -------------------------------------------------
if "survey_risk" in st.session_state and "emotion_score" in st.session_state:

    st.header("🧩 Final ASD Screening Result")

    survey_risk = st.session_state["survey_risk"]
    emotion_score = st.session_state["emotion_score"]

    # IMPROVED FUSION LOGIC
    if survey_risk == "High" or emotion_score == 2:
        final_risk = "High"
    elif survey_risk == "Moderate" or emotion_score == 1:
        final_risk = "Moderate"
    else:
        final_risk = "Low"

    if final_risk == "High":
        st.error("⚠️ **High ASD Risk Detected**")
    elif final_risk == "Moderate":
        st.warning("⚠️ **Moderate ASD Risk Detected**")
    else:
        st.success("✅ **Low ASD Risk Detected**")

    st.caption(
        "This result is based on combined survey responses and emotion recognition. "
        "It is intended only as a preliminary screening tool."
    )

