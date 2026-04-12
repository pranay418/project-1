import cv2
import time
import os
from datetime import datetime

# ==========================
# CONFIGURATION
# ==========================
RESTRICTED_ZONE = (50, 50, 250, 250)   # x1,y1,x2,y2
LOITER_TIME = 10                       # seconds
MIN_AREA = 1200                        # motion contour area
SAVE_FOLDER = 'evidence'

os.makedirs(SAVE_FOLDER, exist_ok=True)

# ==========================
# HELPER FUNCTIONS
# ==========================
def inside_zone(cx, cy, zone):
    x1, y1, x2, y2 = zone
    return x1 <= cx <= x2 and y1 <= cy <= y2


def save_evidence(frame, reason):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    path = os.path.join(SAVE_FOLDER, f'{reason}_{ts}.jpg')
    cv2.imwrite(path, frame)
    print(f'[ALERT] {reason} -> Saved: {path}')

# ==========================
# MAIN
# ==========================
cap = cv2.VideoCapture(0)  # webcam / CCTV stream
ret, frame1 = cap.read()
ret, frame2 = cap.read()

entered_time = None
alert_sent = False

while cap.isOpened():
    diff = cv2.absdiff(frame1, frame2)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(thresh, None, iterations=3)

    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cv2.rectangle(frame1, (RESTRICTED_ZONE[0], RESTRICTED_ZONE[1]),
                  (RESTRICTED_ZONE[2], RESTRICTED_ZONE[3]), (0, 0, 255), 2)
    cv2.putText(frame1, 'Restricted Area', (RESTRICTED_ZONE[0], RESTRICTED_ZONE[1]-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

    person_detected = False

    for contour in contours:
        if cv2.contourArea(contour) < MIN_AREA:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        cx, cy = x + w//2, y + h//2
        person_detected = True

        cv2.rectangle(frame1, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.circle(frame1, (cx, cy), 4, (255, 0, 0), -1)
        cv2.putText(frame1, 'Motion Detected', (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

        if inside_zone(cx, cy, RESTRICTED_ZONE):
            cv2.putText(frame1, 'INTRUSION ALERT!', (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
            if not alert_sent:
                save_evidence(frame1, 'intrusion')
                alert_sent = True

            if entered_time is None:
                entered_time = time.time()
            else:
                stay = int(time.time() - entered_time)
                cv2.putText(frame1, f'Loitering: {stay}s', (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
                if stay >= LOITER_TIME:
                    cv2.putText(frame1, 'LOITERING ALERT!', (20, 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
        else:
            entered_time = None
            alert_sent = False

    if not person_detected:
        entered_time = None
        alert_sent = False

    cv2.imshow('Smart CCTV Surveillance', frame1)

    frame1 = frame2
    ret, frame2 = cap.read()

    if not ret:
        break

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
