# Detects moving people & closest person => teacher!
import cv2 as cv
from ultralytics import YOLO
from collections import deque

model = YOLO("yolov8n.pt")  # fast

cap = cv.VideoCapture(0)
if not cap.isOpened():
    raise SystemExit("Cannot open camera")

def detect_me(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0, inter_x2 - inter_x1)
    inter_h = max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter_area
    return inter_area / union if union > 0 else 0.0

me_box = None
lock_frames = 35
me_candidates = []
frame_count = 0

# Stability for "someone else"
other_hits = deque(maxlen=7)

# Optional: smoothing so the closest highlight doesn't jitter
last_closest_box = None
def smooth_box(prev_box, new_box, alpha=0.6):
    if prev_box is None:
        return new_box
    px1, py1, px2, py2 = prev_box
    x1, y1, x2, y2 = new_box
    sx1 = int(px1 * (1 - alpha) + x1 * alpha)
    sy1 = int(py1 * (1 - alpha) + y1 * alpha)
    sx2 = int(px2 * (1 - alpha) + x2 * alpha)
    sy2 = int(py2 * (1 - alpha) + y2 * alpha)
    return (sx1, sy1, sx2, sy2)

while True:
    ok, frame = cap.read()
    if not ok:
        break

    H, W = frame.shape[:2]
    cx, cy = W / 2.0, H / 2.0

    # YOLO on full frame
    res = model.predict(frame, conf=0.45, imgsz=640, verbose=False)[0]

    person_boxes = []
    if res.boxes is not None:
        for b in res.boxes:
            cls_id = int(b.cls[0].item())
            if cls_id != 0:  # COCO person
                continue
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            conf = float(b.conf[0].item())
            person_boxes.append((x1, y1, x2, y2, conf))

    # initialise me
    if me_box is None and frame_count < lock_frames:
        best = None
        best_score = -1e9

        for (x1, y1, x2, y2, conf) in person_boxes:
            area = (x2 - x1) * (y2 - y1)
            bx = (x1 + x2) / 2.0
            by = (y1 + y2) / 2.0
            dist = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5

            score = area - 2.0 * dist
            if score > best_score:
                best_score = score
                best = (x1, y1, x2, y2)

        if best is not None:
            me_candidates.append(best)

        if frame_count == lock_frames - 1 and len(me_candidates) > 0:
            xs1 = sorted([b[0] for b in me_candidates])
            ys1 = sorted([b[1] for b in me_candidates])
            xs2 = sorted([b[2] for b in me_candidates])
            ys2 = sorted([b[3] for b in me_candidates])
            mid = len(me_candidates) // 2
            me_box = (xs1[mid], ys1[mid], xs2[mid], ys2[mid])

    # update me
    if me_box is not None:
        best_match = None
        best_iou = 0.0

        for (x1, y1, x2, y2, conf) in person_boxes:
            box = (x1, y1, x2, y2)
            v = detect_me(me_box, box)
            if v > best_iou:
                best_iou = v
                best_match = box

        if best_match is not None and best_iou > 0.25:
            me_box = best_match

        mx1, my1, mx2, my2 = me_box
        cv.rectangle(frame, (mx1, my1), (mx2, my2), (255, 0, 0), 2)
        cv.putText(frame, "ME (ignored)", (mx1, my1 - 10),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    
    found_other = False
    closest_other_box = None
    closest_other_conf = 0.0
    closest_area = -1

    other_people = []  # store background people

    for (x1, y1, x2, y2, conf) in person_boxes:
        box = (x1, y1, x2, y2)

        # ignore "me"
        if me_box is not None and detect_me(me_box, box) > 0.25:
            continue


        found_other = True
        other_people.append((x1, y1, x2, y2, conf))

        area = (x2 - x1) * (y2 - y1)
        if area > closest_area:
            closest_area = area
            closest_other_box = (x1, y1, x2, y2)
            closest_other_conf = conf


    # Draw OTHER people 
    for (x1, y1, x2, y2, conf) in other_people:
        # skip closest instead of removing it
        if closest_other_box and (x1, y1, x2, y2) == closest_other_box:
            continue

        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)
        cv.putText(frame, f"OTHER {conf:.2f}", (x1, y1 - 10),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 0), 2)

    # Highlight CLOSEST other person
    if closest_other_box is not None:
        closest_other_box = smooth_box(last_closest_box, closest_other_box, alpha=0.6)
        last_closest_box = closest_other_box

        x1, y1, x2, y2 = closest_other_box
        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 6)
        cv.putText(frame, f"CLOSEST {closest_other_conf:.2f}", (x1, y1 - 12),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Alert background
    other_hits.append(found_other)
    if sum(other_hits) >= 4:
        cv.putText(frame, "BACKGROUND PERSON DETECTED!", (20, 50),
                   cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

    # Status text during locking
    if me_box is None:
        cv.putText(frame, f"Locking onto YOU... {frame_count+1}/{lock_frames}", (20, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    cv.imshow("TeachersPet's vision", frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

    frame_count += 1

cap.release()
cv.destroyAllWindows()
