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
st.caption("Q-CHAT-10: Quantitative Checklist for Autism in Toddlers (18–24 months)")

# ---- Child Demographics ----
st.subheader("👶 Child Information")

col1, col2 = st.columns(2)

with col1:
    age_months = st.number_input(
        "Child's Age (in months)",
        min_value=18,
        max_value=36,
        value=24,
        step=1
    )
    sex = st.selectbox(
        "Child's Gender",
        ["m", "f"],
        format_func=lambda x: "Male" if x == "m" else "Female"
    )
    ethnicity = st.selectbox(
        "Ethnicity",
        [
            "White European", "middle eastern", "Hispanic",
            "black", "asian", "south asian", "Native Indian",
            "Latino", "mixed", "Pacifica", "Others"
        ]
    )

with col2:
    jaundice = st.radio(
        "Was the child born with jaundice?",
        ["no", "yes"],
        horizontal=True
    )
    family_asd = st.radio(
        "Does any family member have ASD?",
        ["no", "yes"],
        horizontal=True
    )
    who_completed = st.selectbox(
        "Who is completing this test?",
        [
            "family member",
            "Health Care Professional",
            "Health care professional",
            "Self",
            "Others"
        ]
    )

st.divider()

# -------------------------------------------------
# Q-CHAT-10 Questions (Yes/No - matches dataset)
# -------------------------------------------------
st.subheader("📋 Behavioural Questions")
st.caption("For each question, please select Yes or No based on your child's behaviour.")

questions = [
    "Does your child look at you when you call his/her name?",
    "How easy is it for you to get eye contact with your child?",
    "Does your child point to indicate that s/he wants something? (e.g. a toy that is out of reach)",
    "Does your child point to share interest with you? (e.g. pointing at an interesting sight)",
    "Does your child pretend? (e.g. care for dolls, talk on a toy phone)",
    "Does your child follow where you're looking?",
    "If you or someone else in the family is visibly upset, does your child show signs of wanting to comfort them? (e.g. stroking hair, hugging them)",
    "Would you describe your child's first words as typical?",
    "Does your child use simple gestures? (e.g. wave goodbye)",
    "Does your child stare at nothing with no apparent purpose?"
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

# Show live Q-CHAT score
qchat_score = sum(answers)
st.info(
    f"📊 Q-CHAT-10 Score: **{qchat_score}/10** — "
    f"{'⚠️ Score > 3: Consider referral for further assessment' if qchat_score > 3 else '✅ Score ≤ 3: Low concern'}"
)

if st.button("Submit Survey"):
    survey_risk, survey_prob = predict_survey_risk(
        answers,
        age_months=age_months,
        sex=sex,
        ethnicity=ethnicity,
        jaundice=jaundice,
        family_asd=family_asd,
        who_completed=who_completed
    )
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

    survey_risk   = st.session_state["survey_risk"]
    emotion_score = st.session_state["emotion_score"]

    # Rule-based fusion (survey priority)
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