import cv2
import numpy as np
import time
from tensorflow.keras.models import load_model

# -------------------------------
# Load emotion model (FER+)
# -------------------------------
emotion_model = load_model(
    "models/best_emotion_model_ferplus_colab_2.h5",
    compile=False
)

emotion_labels = [
    "Neutral", "Happy", "Surprise", "Sad",
    "Angry", "Disgust", "Fear", "Contempt"
]

face_cascade = cv2.CascadeClassifier(
    "emotion/haarcascade_frontalface_default.xml"
)

# -------------------------------
# Emotion score logic (UNCHANGED)
# -------------------------------
def compute_emotion_score(neutral_ratio):
    if neutral_ratio < 0.4:
        return 0
    elif neutral_ratio < 0.7:
        return 1
    else:
        return 2

# -------------------------------
# Run emotion session
# -------------------------------
def run_emotion_session():

    # ✅ Neutral stimulus REMOVED
    stimuli = {
        "Happy": "emotion/stimuli/happy.jpg",
        "Sad": "emotion/stimuli/sad.jpg",
        "Surprise": "emotion/stimuli/surprise.jpg"
    }

    cap = cv2.VideoCapture(0)
    session_scores = []
    total_faces_detected = 0

    for name, img_path in stimuli.items():

        stimulus = cv2.imread(img_path)

        # Blank baseline screen
        blank = np.ones_like(stimulus) * 255
        cv2.namedWindow("Stimulus", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty("Stimulus", cv2.WND_PROP_TOPMOST, 1)
        cv2.setWindowProperty("Stimulus", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow("Stimulus", blank)
        time.sleep(1)

        # Show stimulus
        cv2.imshow("Stimulus", stimulus)
        time.sleep(0.5)

        start_time = time.time()
        emotion_log = []

        while time.time() - start_time < 5:
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(30, 30)
            )

            for (x, y, w, h) in faces:
                total_faces_detected += 1

                face = gray[y:y+h, x:x+w]
                face = cv2.resize(face, (48, 48))
                face = face / 255.0
                face = face.reshape(1, 48, 48, 1)

                prediction = emotion_model.predict(face, verbose=0)
                emotion = emotion_labels[np.argmax(prediction)]
                emotion_log.append(emotion)

            cv2.waitKey(1)

        cv2.destroyWindow("Stimulus")

        # Neutral ratio (still used, but no neutral stimulus bias)
        if emotion_log:
            neutral_ratio = emotion_log.count("Neutral") / len(emotion_log)
        else:
            neutral_ratio = 1.0

        session_scores.append(compute_emotion_score(neutral_ratio))

    cap.release()
    cv2.destroyAllWindows()

    if total_faces_detected == 0:
        return "No face detected"

    # ✅ Improvement 2: MEAN instead of MAX
    final_score = round(np.mean(session_scores))
    return final_score
