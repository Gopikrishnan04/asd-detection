import customtkinter as ctk
import threading
from utils.survey_utils import predict_survey_risk
from emotion.emotion_engine import run_emotion_session

# -------------------------------------------------
# App Theme
# -------------------------------------------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# -------------------------------------------------
# Main Application Class
# -------------------------------------------------
class ASDScreeningApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("🧠 ASD Screening Application")
        self.geometry("900x850")
        self.resizable(True, True)

        # Store results
        self.survey_risk  = None
        self.survey_prob  = None
        self.emotion_score = None
        self.answer_vars  = []
        
        # Build UI
        self.build_ui()

    # -------------------------------------------------
    # Build Full UI
    # -------------------------------------------------
    def build_ui(self):

        # Scrollable main frame
        self.main_frame = ctk.CTkScrollableFrame(self, width=860, height=800)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # ---- Title ----
        ctk.CTkLabel(
            self.main_frame,
            text="🧠 Autism Spectrum Disorder (ASD) Screening Tool",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            self.main_frame,
            text="This application is a screening aid and not a medical diagnosis.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 15))

        # ---- Survey Header ----
        ctk.CTkLabel(
            self.main_frame,
            text="📝 Parent / Caregiver Questionnaire",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            self.main_frame,
            text="Q-CHAT-10: Quantitative Checklist for Autism in Toddlers (18–24 months)",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        # ---- Child Information ----
        self.build_demographics()

        # Divider
        ctk.CTkFrame(self.main_frame, height=2, fg_color="gray").pack(
            fill="x", padx=10, pady=15
        )

        # ---- Behavioural Questions ----
        self.build_questions()

        # ---- Q-CHAT Score Display ----
        self.qchat_label = ctk.CTkLabel(
            self.main_frame,
            text="📊 Q-CHAT-10 Score: 0/10 — ✅ Score ≤ 3: Low concern",
            font=ctk.CTkFont(size=12),
            fg_color="#e8f4f8",
            corner_radius=8,
            text_color="#1a6b8a"
        )
        self.qchat_label.pack(fill="x", padx=10, pady=10)

        # ---- Submit Survey Button ----
        ctk.CTkButton(
            self.main_frame,
            text="Submit Survey",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            command=self.submit_survey
        ).pack(fill="x", padx=10, pady=10)

        # ---- Survey Result Label ----
        self.survey_result_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=13)
        )
        self.survey_result_label.pack(pady=5)

        # Divider
        ctk.CTkFrame(self.main_frame, height=2, fg_color="gray").pack(
            fill="x", padx=10, pady=15
        )

        # ---- Emotion Section ----
        self.build_emotion_section()

        # Divider
        ctk.CTkFrame(self.main_frame, height=2, fg_color="gray").pack(
            fill="x", padx=10, pady=15
        )

        # ---- Final Result Section ----
        self.build_final_result()

    # -------------------------------------------------
    # Demographics Section
    # -------------------------------------------------
    def build_demographics(self):

        ctk.CTkLabel(
            self.main_frame,
            text="👶 Child Information",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 8))

        demo_frame = ctk.CTkFrame(self.main_frame)
        demo_frame.pack(fill="x", padx=10, pady=5)

        left  = ctk.CTkFrame(demo_frame)
        right = ctk.CTkFrame(demo_frame)
        left.pack(side="left",  fill="both", expand=True, padx=5, pady=5)
        right.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # -- LEFT COLUMN --

        # Age
        ctk.CTkLabel(left, text="Child's Age (in months):",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 2))
        self.age_var = ctk.StringVar(value="24")
        ctk.CTkEntry(left, textvariable=self.age_var,
                     placeholder_text="18-36").pack(fill="x", padx=10, pady=(0, 8))

        # Gender
        ctk.CTkLabel(left, text="Child's Gender:",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(0, 2))
        self.sex_var = ctk.StringVar(value="m")
        ctk.CTkOptionMenu(
            left,
            variable=self.sex_var,
            values=["m", "f"],
            command=lambda x: None
        ).pack(fill="x", padx=10, pady=(0, 8))

        # Ethnicity
        ctk.CTkLabel(left, text="Ethnicity:",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(0, 2))
        self.ethnicity_var = ctk.StringVar(value="White European")
        ctk.CTkOptionMenu(
            left,
            variable=self.ethnicity_var,
            values=[
                "White European", "middle eastern", "Hispanic",
                "black", "asian", "south asian", "Native Indian",
                "Latino", "mixed", "Pacifica", "Others"
            ]
        ).pack(fill="x", padx=10, pady=(0, 8))

        # -- RIGHT COLUMN --

        # Jaundice
        ctk.CTkLabel(right, text="Was child born with jaundice?",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 2))
        self.jaundice_var = ctk.StringVar(value="no")
        jaundice_frame = ctk.CTkFrame(right, fg_color="transparent")
        jaundice_frame.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkRadioButton(jaundice_frame, text="No",
                           variable=self.jaundice_var, value="no").pack(side="left", padx=5)
        ctk.CTkRadioButton(jaundice_frame, text="Yes",
                           variable=self.jaundice_var, value="yes").pack(side="left", padx=5)

        # Family ASD
        ctk.CTkLabel(right, text="Does any family member have ASD?",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(0, 2))
        self.family_var = ctk.StringVar(value="no")
        family_frame = ctk.CTkFrame(right, fg_color="transparent")
        family_frame.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkRadioButton(family_frame, text="No",
                           variable=self.family_var, value="no").pack(side="left", padx=5)
        ctk.CTkRadioButton(family_frame, text="Yes",
                           variable=self.family_var, value="yes").pack(side="left", padx=5)

        # Who completed
        ctk.CTkLabel(right, text="Who is completing this test?",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(0, 2))
        self.who_var = ctk.StringVar(value="family member")
        ctk.CTkOptionMenu(
            right,
            variable=self.who_var,
            values=[
                "family member",
                "Health Care Professional",
                "Health care professional",
                "Self",
                "Others"
            ]
        ).pack(fill="x", padx=10, pady=(0, 8))

    # -------------------------------------------------
    # Behavioural Questions Section
    # -------------------------------------------------
    def build_questions(self):

        ctk.CTkLabel(
            self.main_frame,
            text="📋 Behavioural Questions",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 2))

        ctk.CTkLabel(
            self.main_frame,
            text="For each question, please select Yes or No based on your child's behaviour.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=(0, 10))

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

        self.answer_vars = []

        for i, q in enumerate(questions, start=1):

            q_frame = ctk.CTkFrame(self.main_frame, fg_color="#f9f9f9", corner_radius=8)
            q_frame.pack(fill="x", padx=10, pady=4)

            ctk.CTkLabel(
                q_frame,
                text=f"Q{i}. {q}",
                font=ctk.CTkFont(size=12),
                wraplength=700,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(8, 4))

            var = ctk.StringVar(value="No")
            self.answer_vars.append(var)

            radio_frame = ctk.CTkFrame(q_frame, fg_color="transparent")
            radio_frame.pack(anchor="w", padx=12, pady=(0, 8))

            ctk.CTkRadioButton(
                radio_frame, text="No", variable=var, value="No",
                command=self.update_qchat_score
            ).pack(side="left", padx=(0, 20))

            ctk.CTkRadioButton(
                radio_frame, text="Yes", variable=var, value="Yes",
                command=self.update_qchat_score
            ).pack(side="left")

    # -------------------------------------------------
    # Emotion Section
    # -------------------------------------------------
    def build_emotion_section(self):

        ctk.CTkLabel(
            self.main_frame,
            text="😊 Emotion Recognition Assessment",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 5))

        ctk.CTkLabel(
            self.main_frame,
            text="The child will be shown a set of emotional stimuli while facial expressions\n"
                 "are analyzed to evaluate emotional responsiveness.",
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 10))

        ctk.CTkButton(
            self.main_frame,
            text="Run Emotion Analysis",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color="#e67e22",
            hover_color="#d35400",
            command=self.run_emotion
        ).pack(fill="x", padx=10, pady=5)

        self.emotion_status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=13)
        )
        self.emotion_status_label.pack(pady=5)

    # -------------------------------------------------
    # Final Result Section
    # -------------------------------------------------
    def build_final_result(self):

        ctk.CTkLabel(
            self.main_frame,
            text="🧩 Final ASD Screening Result",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=10, pady=(5, 10))

        self.final_result_label = ctk.CTkLabel(
            self.main_frame,
            text="Complete both Survey and Emotion Analysis to see the final result.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            fg_color="#f0f0f0",
            corner_radius=8
        )
        self.final_result_label.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            self.main_frame,
            text="This result is based on combined survey responses and emotion recognition.\n"
                 "It is intended only as a preliminary screening tool.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(padx=10, pady=(5, 15))

    # -------------------------------------------------
    # Update Q-CHAT Score (live)
    # -------------------------------------------------
    def update_qchat_score(self):
        score = sum(1 for v in self.answer_vars if v.get() == "Yes")
        if score > 3:
            self.qchat_label.configure(
                text=f"📊 Q-CHAT-10 Score: {score}/10 — ⚠️ Score > 3: Consider referral for further assessment",
                fg_color="#fff3cd",
                text_color="#856404"
            )
        else:
            self.qchat_label.configure(
                text=f"📊 Q-CHAT-10 Score: {score}/10 — ✅ Score ≤ 3: Low concern",
                fg_color="#d4edda",
                text_color="#155724"
            )

    # -------------------------------------------------
    # Submit Survey
    # -------------------------------------------------
    def submit_survey(self):
        answers = [1 if v.get() == "Yes" else 0 for v in self.answer_vars]

        try:
            age = int(self.age_var.get())
        except ValueError:
            self.survey_result_label.configure(
                text="⚠️ Please enter a valid age.", text_color="red"
            )
            return

        survey_risk, survey_prob = predict_survey_risk(
            answers,
            age_months=age,
            sex=self.sex_var.get(),
            ethnicity=self.ethnicity_var.get(),
            jaundice=self.jaundice_var.get(),
            family_asd=self.family_var.get(),
            who_completed=self.who_var.get()
        )

        self.survey_risk = survey_risk
        self.survey_prob = survey_prob

        color_map = {"High": "red", "Moderate": "orange", "Low": "green"}
        self.survey_result_label.configure(
            text=f"📝 Survey Risk Level: {survey_risk}   |   ASD Probability: {round(survey_prob, 2)}",
            text_color=color_map.get(survey_risk, "black")
        )

        self.compute_final_result()

    # -------------------------------------------------
    # Run Emotion Analysis (in separate thread)
    # -------------------------------------------------
    def run_emotion(self):
        self.emotion_status_label.configure(
            text="⏳ Running emotion analysis... Please wait",
            text_color="orange"
        )
        self.update()

        # Run in thread so UI doesn't freeze
        thread = threading.Thread(target=self._emotion_thread, daemon=True)
        thread.start()

    def _emotion_thread(self):
        emotion_score = run_emotion_session()
        self.emotion_score = emotion_score

        # Update UI from thread safely
        self.after(0, self._emotion_done)

    def _emotion_done(self):
        self.emotion_status_label.configure(
            text=f"✅ Emotion Analysis Completed (Score: {self.emotion_score})",
            text_color="green"
        )
        self.compute_final_result()

    # -------------------------------------------------
    # Compute Final Result (fusion logic)
    # -------------------------------------------------
    def compute_final_result(self):

        # Only compute if BOTH are available
        if self.survey_risk is None or self.emotion_score is None:
            return

        # Rule-based fusion (survey priority)
        if self.survey_risk == "High" or self.emotion_score == 2:
            final_risk = "High"
        elif self.survey_risk == "Moderate" or self.emotion_score == 1:
            final_risk = "Moderate"
        else:
            final_risk = "Low"

        # Update final result label
        if final_risk == "High":
            self.final_result_label.configure(
                text="⚠️  High ASD Risk Detected",
                fg_color="#f8d7da",
                text_color="#721c24",
                font=ctk.CTkFont(size=15, weight="bold")
            )
        elif final_risk == "Moderate":
            self.final_result_label.configure(
                text="⚠️  Moderate ASD Risk Detected",
                fg_color="#fff3cd",
                text_color="#856404",
                font=ctk.CTkFont(size=15, weight="bold")
            )
        else:
            self.final_result_label.configure(
                text="✅  Low ASD Risk Detected",
                fg_color="#d4edda",
                text_color="#155724",
                font=ctk.CTkFont(size=15, weight="bold")
            )

# -------------------------------------------------
# Run App
# -------------------------------------------------
if __name__ == "__main__":
    app = ASDScreeningApp()
    app.mainloop()