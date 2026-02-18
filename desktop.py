import customtkinter as ctk
import threading

# ── Lazy-import your real modules ──────────────────────────────────────────────
try:
    from utils.survey_utils import predict_survey_risk
    from emotion.emotion_engine import run_emotion_session
except ImportError:
    # Fallback stubs so the UI runs standalone for development
    def predict_survey_risk(answers, age_months, sex, family_asd):
        score = sum(answers)
        prob  = score / 10
        risk  = "High" if score > 6 else "Moderate" if score > 3 else "Low"
        return risk, prob

    def run_emotion_session():
        import time; time.sleep(2)
        return 1


# ══════════════════════════════════════════════════════════════════════════════
# THEME ENGINE
# ══════════════════════════════════════════════════════════════════════════════

LIGHT = dict(
    bg          = "#F7F5F2",
    surface     = "#FDFCFA",
    surface_alt = "#F0EDE8",
    border      = "#E2DDD8",
    border_dark = "#C8C2BB",
    text        = "#1C1917",
    text_mid    = "#57534E",
    text_light  = "#A8A29E",
    accent      = "#6B5E52",
    accent_hov  = "#57504A",
    gold        = "#B5975A",
    low_fg      = "#3D6B4F",
    low_bg      = "#EEF4F1",
    mod_fg      = "#7A5C1E",
    mod_bg      = "#F9F3E8",
    high_fg     = "#7A2E2E",
    high_bg     = "#F7EEEE",
    toggle_bg   = "#E2DDD8",
    toggle_icon = "☀",
)

DARK = dict(
    bg          = "#18181B",
    surface     = "#27272A",
    surface_alt = "#3F3F46",
    border      = "#3F3F46",
    border_dark = "#52525B",
    text        = "#FAFAFA",
    text_mid    = "#D4D4D8",
    text_light  = "#71717A",
    accent      = "#A89880",
    accent_hov  = "#C4B09A",
    gold        = "#D4A853",
    low_fg      = "#6EE7A0",
    low_bg      = "#14532D",
    mod_fg      = "#FCD34D",
    mod_bg      = "#78350F",
    high_fg     = "#FCA5A5",
    high_bg     = "#7F1D1D",
    toggle_bg   = "#3F3F46",
    toggle_icon = "☾",
)

T = LIGHT.copy()   # mutable global theme dict


def apply_theme(mode: str):
    T.clear()
    T.update(LIGHT if mode == "light" else DARK)
    ctk.set_appearance_mode(mode)


# ══════════════════════════════════════════════════════════════════════════════
# ANIMATION HELPER
# ══════════════════════════════════════════════════════════════════════════════

class FadeSlide:
    """Slide a widget in from the right using place()."""
    FPS      = 60
    DURATION = 320

    def __init__(self, widget, container_w: int, on_done=None):
        self._w       = widget
        self._cw      = container_w
        self._done_cb = on_done
        self._steps   = max(1, int(self.DURATION / (1000 / self.FPS)))
        self._step    = 0
        self._start_x = container_w * 0.09
        widget.place(x=self._start_x, y=0, relwidth=1.0, relheight=1.0)
        self._tick()

    def _tick(self):
        if self._step > self._steps:
            self._w.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            if self._done_cb:
                self._done_cb()
            return
        t   = self._step / self._steps
        t_e = 1 - (1 - t) ** 3          # ease-out cubic
        x   = self._start_x * (1 - t_e)
        self._w.place(x=x, y=0, relwidth=1.0, relheight=1.0)
        self._step += 1
        self._w.after(int(1000 / self.FPS), self._tick)


# ══════════════════════════════════════════════════════════════════════════════
# REUSABLE WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

class ThemeToggle(ctk.CTkButton):
    def __init__(self, parent, on_toggle, **kw):
        super().__init__(
            parent,
            text=T["toggle_icon"],
            width=42, height=28, corner_radius=14,
            font=ctk.CTkFont(size=14),
            fg_color=T["toggle_bg"],
            hover_color=T["border_dark"],
            text_color=T["text_mid"],
            command=self._click,
            **kw
        )
        self._on_toggle = on_toggle
        self._mode = "light"

    def _click(self):
        self._mode = "dark" if self._mode == "light" else "light"
        apply_theme(self._mode)
        self._on_toggle(self._mode)

    def refresh(self):
        self.configure(
            text=T["toggle_icon"],
            fg_color=T["toggle_bg"],
            hover_color=T["border_dark"],
            text_color=T["text_mid"],
        )


class PillButton(ctk.CTkButton):
    def __init__(self, parent, label, selected=False, **kw):
        super().__init__(
            parent, text=label,
            width=160, height=58, corner_radius=29,
            font=ctk.CTkFont(family="Georgia", size=20),
            **kw
        )
        self.refresh_style(selected)

    def refresh_style(self, selected: bool):
        if selected:
            self.configure(
                fg_color=T["accent"], hover_color=T["accent_hov"],
                text_color="#FFFFFF", border_width=0,
            )
        else:
            self.configure(
                fg_color="transparent", hover_color=T["surface_alt"],
                text_color=T["text_mid"], border_width=2,
                border_color=T["border_dark"],
            )


class ProgressDots(ctk.CTkFrame):
    def __init__(self, parent, total: int, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._dots  = []
        self._active = 0
        for _ in range(total):
            d = ctk.CTkFrame(self, width=8, height=8, corner_radius=4,
                             fg_color=T["border_dark"])
            d.pack(side="left", padx=4)
            self._dots.append(d)

    def set_index(self, idx: int, answered: list):
        self._active = idx
        for i, d in enumerate(self._dots):
            if i == idx:
                d.configure(width=22, fg_color=T["gold"])
            elif answered[i] is not None:
                d.configure(width=8, fg_color=T["accent"])
            else:
                d.configure(width=8, fg_color=T["border_dark"])


# ══════════════════════════════════════════════════════════════════════════════
# BASE PAGE
# ══════════════════════════════════════════════════════════════════════════════

class BasePage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=T["bg"], **kw)

    def refresh_theme(self):
        self.configure(fg_color=T["bg"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 0 — Welcome / Demographics
# ══════════════════════════════════════════════════════════════════════════════

class WelcomePage(BasePage):
    def __init__(self, master, on_continue, **kw):
        super().__init__(master, **kw)
        self._on_continue = on_continue
        self._build()

    def _build(self):
        col = ctk.CTkFrame(self, fg_color="transparent")
        col.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72)

        self._rule = ctk.CTkFrame(col, height=2, fg_color=T["gold"])
        self._rule.pack(fill="x", pady=(0, 24))

        self._t1 = ctk.CTkLabel(col, text="Autism Spectrum Disorder",
            font=ctk.CTkFont(family="Georgia", size=30, weight="bold"),
            text_color=T["text"], anchor="w")
        self._t1.pack(anchor="w")

        self._t2 = ctk.CTkLabel(col, text="Screening Application",
            font=ctk.CTkFont(family="Georgia", size=30),
            text_color=T["accent"], anchor="w")
        self._t2.pack(anchor="w")

        self._sub = ctk.CTkLabel(col,
            text="A preliminary multi-modal assessment tool  ·  Not for diagnostic use",
            font=ctk.CTkFont(size=12), text_color=T["text_light"], anchor="w")
        self._sub.pack(anchor="w", pady=(8, 30))

        # demographics card
        self._card = ctk.CTkFrame(col, fg_color=T["surface"], corner_radius=14,
                                   border_width=1, border_color=T["border"])
        self._card.pack(fill="x")
        inner = ctk.CTkFrame(self._card, fg_color="transparent")
        inner.pack(fill="x", padx=26, pady=22)

        self._cap = ctk.CTkLabel(inner, text="CHILD INFORMATION",
            font=ctk.CTkFont(size=9), text_color=T["text_light"])
        self._cap.pack(anchor="w", pady=(0, 14))

        g = ctk.CTkFrame(inner, fg_color="transparent")
        g.pack(fill="x")
        g.columnconfigure((0, 1, 2), weight=1, uniform="g")

        # Age
        ac = ctk.CTkFrame(g, fg_color="transparent")
        ac.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._la = ctk.CTkLabel(ac, text="Age (months)",
            font=ctk.CTkFont(size=10), text_color=T["text_light"])
        self._la.pack(anchor="w")
        self._age_var = ctk.StringVar(value="24")
        self._age_e = ctk.CTkEntry(ac, textvariable=self._age_var,
            placeholder_text="18–36", font=ctk.CTkFont(size=14),
            height=42, corner_radius=8, border_color=T["border"],
            fg_color=T["surface"], text_color=T["text"])
        self._age_e.pack(fill="x", pady=(5, 0))

        # Gender
        sc = ctk.CTkFrame(g, fg_color="transparent")
        sc.grid(row=0, column=1, sticky="nsew", padx=5)
        self._ls = ctk.CTkLabel(sc, text="Gender",
            font=ctk.CTkFont(size=10), text_color=T["text_light"])
        self._ls.pack(anchor="w")
        self._sex_var = ctk.StringVar(value="Male")
        self._sex_m = ctk.CTkOptionMenu(sc, variable=self._sex_var,
            values=["Male", "Female"], font=ctk.CTkFont(size=14),
            height=42, corner_radius=8,
            fg_color=T["surface"], text_color=T["text"],
            button_color=T["surface_alt"], button_hover_color=T["border"],
            dropdown_fg_color=T["surface"], dropdown_hover_color=T["surface_alt"],
            dropdown_text_color=T["text"])
        self._sex_m.pack(fill="x", pady=(5, 0))

        # Family
        fc = ctk.CTkFrame(g, fg_color="transparent")
        fc.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        self._lf = ctk.CTkLabel(fc, text="Family history of ASD",
            font=ctk.CTkFont(size=10), text_color=T["text_light"])
        self._lf.pack(anchor="w")
        self._family_var = ctk.StringVar(value="no")
        rf = ctk.CTkFrame(fc, fg_color="transparent")
        rf.pack(anchor="w", pady=(11, 0))
        self._rb_no  = ctk.CTkRadioButton(rf, text="No",  variable=self._family_var, value="no",
            font=ctk.CTkFont(size=13), text_color=T["text_mid"],
            fg_color=T["accent"], hover_color=T["accent_hov"])
        self._rb_yes = ctk.CTkRadioButton(rf, text="Yes", variable=self._family_var, value="yes",
            font=ctk.CTkFont(size=13), text_color=T["text_mid"],
            fg_color=T["accent"], hover_color=T["accent_hov"])
        self._rb_no.pack(side="left", padx=(0, 16))
        self._rb_yes.pack(side="left")

        self._btn = ctk.CTkButton(col, text="Begin Assessment  →",
            font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
            height=52, corner_radius=10,
            fg_color=T["accent"], hover_color=T["accent_hov"], text_color="#FFF",
            command=self._go)
        self._btn.pack(fill="x", pady=(18, 0))

        self._err = ctk.CTkLabel(col, text="", font=ctk.CTkFont(size=11),
                                  text_color=T["high_fg"])
        self._err.pack(pady=(6, 0))

    def _go(self):
        try:
            age = int(self._age_var.get())
            assert 10 <= age <= 60
        except Exception:
            self._err.configure(text="Please enter a valid age between 10 and 60 months.")
            return
        self._err.configure(text="")
        self._on_continue(age,
                          "m" if self._sex_var.get() == "Male" else "f",
                          self._family_var.get())

    def refresh_theme(self):
        super().refresh_theme()
        self._rule.configure(fg_color=T["gold"])
        self._t1.configure(text_color=T["text"])
        self._t2.configure(text_color=T["accent"])
        self._sub.configure(text_color=T["text_light"])
        self._card.configure(fg_color=T["surface"], border_color=T["border"])
        self._cap.configure(text_color=T["text_light"])
        for w in [self._la, self._ls, self._lf]:
            w.configure(text_color=T["text_light"])
        self._age_e.configure(border_color=T["border"], fg_color=T["surface"], text_color=T["text"])
        self._sex_m.configure(fg_color=T["surface"], text_color=T["text"],
            button_color=T["surface_alt"], button_hover_color=T["border"],
            dropdown_fg_color=T["surface"], dropdown_hover_color=T["surface_alt"],
            dropdown_text_color=T["text"])
        for rb in [self._rb_no, self._rb_yes]:
            rb.configure(text_color=T["text_mid"], fg_color=T["accent"], hover_color=T["accent_hov"])
        self._btn.configure(fg_color=T["accent"], hover_color=T["accent_hov"])
        self._err.configure(text_color=T["high_fg"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — One Question Per Page
# ══════════════════════════════════════════════════════════════════════════════

class QuestionPage(BasePage):
    QUESTIONS = [
        "Does your child look at you when you\ncall their name?",
        "How easy is it for you to get\neye contact with your child?",
        "Does your child point to indicate\nthat they want something?\n(e.g. a toy out of reach)",
        "Does your child point to share\ninterest with you?\n(e.g. pointing at an interesting sight)",
        "Does your child engage in\npretend play?\n(e.g. caring for dolls, talking on a toy phone)",
        "Does your child follow\nwhere you are looking?",
        "Does your child show signs of wanting\nto comfort a distressed family member?",
        "Would you describe your child's\nfirst words as typical?",
        "Does your child use\nsimple gestures?\n(e.g. waving goodbye)",
        "Does your child stare at nothing\nwith no apparent purpose?",
    ]

    def __init__(self, master, on_complete, **kw):
        super().__init__(master, **kw)
        self._on_complete = on_complete
        self._answers     = [None] * len(self.QUESTIONS)
        self._current     = 0
        self._animating   = False
        self._card        = None

        self._build_chrome()
        self._render(animate=False)

    # ── static chrome ─────────────────────────────────────────────────────────
    def _build_chrome(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=48, pady=(28, 0))

        self._section_lbl = ctk.CTkLabel(top,
            text="BEHAVIOURAL QUESTIONNAIRE  ·  Q-CHAT-10",
            font=ctk.CTkFont(size=9), text_color=T["text_light"])
        self._section_lbl.pack(anchor="w")

        self._prog = ctk.CTkProgressBar(top, height=3, corner_radius=2,
            fg_color=T["border"], progress_color=T["gold"])
        self._prog.set(0)
        self._prog.pack(fill="x", pady=(8, 0))

        dr = ctk.CTkFrame(top, fg_color="transparent")
        dr.pack(fill="x", pady=(10, 0))

        self._dots = ProgressDots(dr, len(self.QUESTIONS))
        self._dots.pack(side="left")

        self._counter = ctk.CTkLabel(dr,
            text=f"1 / {len(self.QUESTIONS)}",
            font=ctk.CTkFont(size=11), text_color=T["text_light"])
        self._counter.pack(side="right")

        # score chip
        self._sf = ctk.CTkFrame(top, fg_color=T["surface_alt"], corner_radius=8)
        self._sf.pack(anchor="w", pady=(12, 0))
        sf_i = ctk.CTkFrame(self._sf, fg_color="transparent")
        sf_i.pack(padx=14, pady=8)
        ctk.CTkLabel(sf_i, text="SCORE", font=ctk.CTkFont(size=8),
                     text_color=T["text_light"]).pack(side="left", padx=(0, 8))
        self._score_lbl = ctk.CTkLabel(sf_i, text="0 / 10",
            font=ctk.CTkFont(family="Georgia", size=15, weight="bold"),
            text_color=T["text"])
        self._score_lbl.pack(side="left")
        self._score_bar = ctk.CTkProgressBar(sf_i, width=100, height=4,
            corner_radius=2, fg_color=T["border"], progress_color=T["low_fg"])
        self._score_bar.set(0)
        self._score_bar.pack(side="left", padx=(12, 0))

    # ── animated question card ────────────────────────────────────────────────
    def _render(self, animate=True):
        if self._card:
            self._card.destroy()

        idx = self._current
        q   = self.QUESTIONS[idx]

        card = ctk.CTkFrame(self, fg_color=T["surface"], corner_radius=20,
                             border_width=1, border_color=T["border"])
        self._card = card

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.78)

        # item number + gold rule
        ctk.CTkLabel(inner, text=f"ITEM  {idx + 1:02d}",
            font=ctk.CTkFont(size=10), text_color=T["gold"]).pack(anchor="w")
        ctk.CTkFrame(inner, height=1, fg_color=T["gold"]).pack(fill="x", pady=(5, 26))

        # question — big serif
        ctk.CTkLabel(inner, text=q,
            font=ctk.CTkFont(family="Georgia", size=28),
            text_color=T["text"], justify="left", anchor="w",
            wraplength=580).pack(anchor="w", fill="x")

        # answer pills
        pr = ctk.CTkFrame(inner, fg_color="transparent")
        pr.pack(anchor="w", pady=(40, 0))

        cur = self._answers[idx]
        self._no_pill  = PillButton(pr, "No",  selected=(cur == "No"))
        self._yes_pill = PillButton(pr, "Yes", selected=(cur == "Yes"))
        self._no_pill.configure( command=lambda: self._answer("No"))
        self._yes_pill.configure(command=lambda: self._answer("Yes"))
        self._no_pill.pack(side="left", padx=(0, 16))
        self._yes_pill.pack(side="left")

        # back button
        if idx > 0:
            ctk.CTkButton(inner, text="← Back", width=90, height=34,
                corner_radius=8, font=ctk.CTkFont(size=12),
                fg_color="transparent", hover_color=T["surface_alt"],
                text_color=T["text_light"], border_width=1, border_color=T["border"],
                command=self._go_back).pack(anchor="w", pady=(18, 0))

        self._update_chrome()

        host_w = self.winfo_width() or 860
        if animate:
            card.pack(fill="both", expand=True, padx=48, pady=(16, 40))
            card.update_idletasks()
            FadeSlide(card, host_w, on_done=lambda: None)
        else:
            card.pack(fill="both", expand=True, padx=48, pady=(16, 40))

    def _answer(self, value):
        if self._animating:
            return
        self._animating = True
        self._answers[self._current] = value

        if value == "Yes":
            self._yes_pill.refresh_style(True)
            self._no_pill.refresh_style(False)
        else:
            self._no_pill.refresh_style(True)
            self._yes_pill.refresh_style(False)

        self._update_chrome()

        if self._current < len(self.QUESTIONS) - 1:
            self._current += 1
            self.after(200, self._delayed_render)
        else:
            self.after(260, self._finish)

    def _delayed_render(self):
        self._render(animate=True)
        self._animating = False

    def _go_back(self):
        if self._current > 0 and not self._animating:
            self._current -= 1
            self._render(animate=False)

    def _finish(self):
        self._animating = False
        self._on_complete(self._answers)

    def _update_chrome(self):
        idx    = self._current
        total  = len(self.QUESTIONS)
        yes_ct = sum(1 for a in self._answers if a == "Yes")
        self._prog.set((idx + 1) / total)
        self._counter.configure(text=f"{idx + 1} / {total}")
        self._dots.set_index(idx, self._answers)
        self._score_lbl.configure(text=f"{yes_ct} / {total}")
        self._score_bar.set(yes_ct / total)
        self._score_bar.configure(
            progress_color=T["mod_fg"] if yes_ct > 3 else T["low_fg"])

    def refresh_theme(self):
        super().refresh_theme()
        self._section_lbl.configure(text_color=T["text_light"])
        self._prog.configure(fg_color=T["border"], progress_color=T["gold"])
        self._counter.configure(text_color=T["text_light"])
        self._sf.configure(fg_color=T["surface_alt"])
        self._score_lbl.configure(text_color=T["text"])
        self._score_bar.configure(fg_color=T["border"])
        self._render(animate=False)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Emotion Analysis
# ══════════════════════════════════════════════════════════════════════════════

class EmotionPage(BasePage):
    def __init__(self, master, on_complete, **kw):
        super().__init__(master, **kw)
        self._on_complete = on_complete
        self._build()

    def _build(self):
        col = ctk.CTkFrame(self, fg_color="transparent")
        col.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.65)

        self._cap = ctk.CTkLabel(col, text="EMOTION RECOGNITION ASSESSMENT",
            font=ctk.CTkFont(size=9), text_color=T["text_light"])
        self._cap.pack(anchor="w")

        self._rule = ctk.CTkFrame(col, height=1, fg_color=T["gold"])
        self._rule.pack(fill="x", pady=(6, 26))

        self._title = ctk.CTkLabel(col, text="Facial Expression\nAnalysis",
            font=ctk.CTkFont(family="Georgia", size=30, weight="bold"),
            text_color=T["text"], justify="left", anchor="w")
        self._title.pack(anchor="w")

        self._desc = ctk.CTkLabel(col,
            text=(
                "The child will be presented with a set of emotional stimuli.\n"
                "Facial expressions are captured and analysed in real-time\n"
                "to evaluate emotional responsiveness and recognition."
            ),
            font=ctk.CTkFont(family="Georgia", size=15),
            text_color=T["text_mid"], justify="left", anchor="w")
        self._desc.pack(anchor="w", pady=(16, 34))

        self._btn = ctk.CTkButton(col, text="Run Emotion Analysis",
            font=ctk.CTkFont(family="Georgia", size=16, weight="bold"),
            height=52, corner_radius=10,
            fg_color=T["accent"], hover_color=T["accent_hov"], text_color="#FFF",
            command=self._run)
        self._btn.pack(fill="x")

        self._status = ctk.CTkLabel(col, text="",
            font=ctk.CTkFont(size=12), text_color=T["text_light"])
        self._status.pack(pady=(12, 0))

    def _run(self):
        self._btn.configure(state="disabled")
        self._status.configure(text="Initialising — please wait…", text_color=T["gold"])
        threading.Thread(target=self._thread, daemon=True).start()

    def _thread(self):
        score = run_emotion_session()
        self.after(0, lambda: self._done(score))

    def _done(self, score):
        self._status.configure(
            text=f"Analysis complete  ·  Responsiveness score: {score}",
            text_color=T["low_fg"])
        self.after(800, lambda: self._on_complete(score))

    def refresh_theme(self):
        super().refresh_theme()
        self._cap.configure(text_color=T["text_light"])
        self._rule.configure(fg_color=T["gold"])
        self._title.configure(text_color=T["text"])
        self._desc.configure(text_color=T["text_mid"])
        self._btn.configure(fg_color=T["accent"], hover_color=T["accent_hov"])
        self._status.configure(text_color=T["text_light"])


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Final Result
# ══════════════════════════════════════════════════════════════════════════════

class ResultPage(BasePage):
    CFG = {
        "High":     ("High Risk Detected",      "Clinical referral is strongly recommended.",        "high_fg", "high_bg"),
        "Moderate": ("Moderate Risk Detected",   "Further evaluation by a specialist is advisable.", "mod_fg",  "mod_bg"),
        "Low":      ("Low Risk Detected",        "No significant indicators detected at this time.", "low_fg",  "low_bg"),
    }

    def __init__(self, master, on_restart, **kw):
        super().__init__(master, **kw)
        self._on_restart = on_restart
        self._risk = None
        self._build()

    def _build(self):
        col = ctk.CTkFrame(self, fg_color="transparent")
        col.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.66)

        self._cap = ctk.CTkLabel(col, text="FINAL SCREENING RESULT",
            font=ctk.CTkFont(size=9), text_color=T["text_light"])
        self._cap.pack(anchor="w")

        self._rule = ctk.CTkFrame(col, height=1, fg_color=T["gold"])
        self._rule.pack(fill="x", pady=(6, 26))

        self._rc = ctk.CTkFrame(col, fg_color=T["surface"], corner_radius=16,
                                 border_width=1, border_color=T["border"])
        self._rc.pack(fill="x")

        rc_i = ctk.CTkFrame(self._rc, fg_color="transparent")
        rc_i.pack(fill="x", padx=30, pady=26)

        self._risk_lbl = ctk.CTkLabel(rc_i, text="—",
            font=ctk.CTkFont(family="Georgia", size=26, weight="bold"),
            text_color=T["text_light"])
        self._risk_lbl.pack(anchor="w")

        self._note_lbl = ctk.CTkLabel(rc_i, text="",
            font=ctk.CTkFont(size=13), text_color=T["text_mid"])
        self._note_lbl.pack(anchor="w", pady=(8, 0))

        dr = ctk.CTkFrame(rc_i, fg_color="transparent")
        dr.pack(fill="x", pady=(20, 0))

        self._c1 = self._chip(dr, "Survey Risk", "—")
        self._c1.pack(side="left", padx=(0, 12))
        self._c2 = self._chip(dr, "Emotion Score", "—")
        self._c2.pack(side="left")

        self._disc = ctk.CTkLabel(col,
            text=(
                "This result is a preliminary screening output only and does\n"
                "not constitute a clinical diagnosis. Please consult a qualified\n"
                "professional for a formal evaluation."
            ),
            font=ctk.CTkFont(size=11), text_color=T["text_light"], justify="center")
        self._disc.pack(pady=(20, 22))

        self._restart = ctk.CTkButton(col, text="Start New Assessment",
            font=ctk.CTkFont(size=13, weight="bold"), height=44, corner_radius=8,
            fg_color="transparent", hover_color=T["surface_alt"],
            text_color=T["accent"], border_width=1, border_color=T["accent"],
            command=self._on_restart)
        self._restart.pack(fill="x")

    def _chip(self, parent, label, value):
        f = ctk.CTkFrame(parent, fg_color=T["surface_alt"], corner_radius=8)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=9),
                     text_color=T["text_light"]).pack(padx=14, pady=(8, 2))
        v = ctk.CTkLabel(f, text=value,
            font=ctk.CTkFont(family="Georgia", size=15, weight="bold"),
            text_color=T["text"])
        v.pack(padx=14, pady=(0, 8))
        f._vlbl = v
        return f

    def show_result(self, survey_risk, survey_prob, emotion_score):
        if survey_risk == "High":
            final = "High"
        elif survey_risk == "Moderate":
            final = "High" if emotion_score == 2 else "Moderate"
        else:
            final = "Moderate" if emotion_score == 2 else "Low"

        self._risk = final
        title, note, fg_k, bg_k = self.CFG[final]
        self._rc.configure(fg_color=T[bg_k], border_color=T[fg_k])
        self._risk_lbl.configure(text=title, text_color=T[fg_k])
        self._note_lbl.configure(text=note,  text_color=T[fg_k])
        self._c1._vlbl.configure(text=f"{survey_risk}  ({round(survey_prob, 2)})")
        self._c2._vlbl.configure(text=str(emotion_score))

    def refresh_theme(self):
        super().refresh_theme()
        self._cap.configure(text_color=T["text_light"])
        self._rule.configure(fg_color=T["gold"])
        self._disc.configure(text_color=T["text_light"])
        self._restart.configure(hover_color=T["surface_alt"], text_color=T["accent"],
                                 border_color=T["accent"])
        for c in [self._c1, self._c2]:
            c.configure(fg_color=T["surface_alt"])
        if self._risk:
            _, _, fg_k, bg_k = self.CFG[self._risk]
            self._rc.configure(fg_color=T[bg_k], border_color=T[fg_k])
            self._risk_lbl.configure(text_color=T[fg_k])
            self._note_lbl.configure(text_color=T[fg_k])


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class ASDScreeningApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        apply_theme("light")
        self.title("ASD Screening Application")
        self.geometry("960x780")
        self.minsize(820, 660)
        self.configure(fg_color=T["bg"])

        self._age    = 24
        self._sex    = "m"
        self._family = "no"
        self._sur    = None
        self._prob   = None
        self._em     = None
        self._pages  = []

        self._build_shell()
        self._show(self._p_welcome)

    def _build_shell(self):
        # nav bar
        self._nav = ctk.CTkFrame(self, fg_color=T["surface"], height=52, corner_radius=0)
        self._nav.pack(fill="x", side="top")
        self._nav.pack_propagate(False)
        ni = ctk.CTkFrame(self._nav, fg_color="transparent")
        ni.pack(fill="both", expand=True, padx=24)
        self._nav_lbl = ctk.CTkLabel(ni, text="ASD  Screening",
            font=ctk.CTkFont(family="Georgia", size=14, weight="bold"),
            text_color=T["text"])
        self._nav_lbl.pack(side="left", pady=12)
        self._toggle = ThemeToggle(ni, on_toggle=self._theme_switch)
        self._toggle.pack(side="right", pady=12)

        self._nav_rule = ctk.CTkFrame(self, height=2, fg_color=T["gold"])
        self._nav_rule.pack(fill="x", side="top")

        # host
        self._host = ctk.CTkFrame(self, fg_color=T["bg"])
        self._host.pack(fill="both", expand=True)

        self._p_welcome  = WelcomePage(self._host,  on_continue=self._after_demo)
        self._p_question = QuestionPage(self._host, on_complete=self._after_q)
        self._p_emotion  = EmotionPage(self._host,  on_complete=self._after_em)
        self._p_result   = ResultPage(self._host,   on_restart=self._restart)

        self._pages = [self._p_welcome, self._p_question, self._p_emotion, self._p_result]
        self._active = None

    def _show(self, page):
        if self._active:
            self._active.place_forget()
        page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._active = page

    def _after_demo(self, age, sex, family):
        self._age, self._sex, self._family = age, sex, family
        self._show(self._p_question)

    def _after_q(self, answers):
        ans_int = [1 if a == "Yes" else 0 for a in answers]
        risk, prob = predict_survey_risk(
            ans_int, age_months=self._age,
            sex=self._sex, family_asd=self._family)
        self._sur, self._prob = risk, prob
        self._show(self._p_emotion)

    def _after_em(self, score):
        self._em = score
        self._p_result.show_result(self._sur, self._prob, score)
        self._show(self._p_result)

    def _restart(self):
        self._p_question.destroy()
        self._p_question = QuestionPage(self._host, on_complete=self._after_q)
        self._pages[1] = self._p_question

        self._p_emotion.destroy()
        self._p_emotion = EmotionPage(self._host, on_complete=self._after_em)
        self._pages[2] = self._p_emotion

        self._show(self._p_welcome)

    def _theme_switch(self, mode):
        self._host.configure(fg_color=T["bg"])
        self._nav.configure(fg_color=T["surface"])
        self._nav_rule.configure(fg_color=T["gold"])
        self._nav_lbl.configure(text_color=T["text"])
        self._toggle.refresh()
        self.configure(fg_color=T["bg"])
        for p in self._pages:
            try:
                p.refresh_theme()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ctk.set_default_color_theme("blue")
    app = ASDScreeningApp()
    app.mainloop()