# Detects people, ignores "me", highlights closest other person
import cv2 as cv
from ultralytics import YOLO
from collections import deque

class Camera:
    def __init__(self,
                 camera_index: int = 0,
                 model_name: str = "yolov8n.pt",
                 conf: float = 0.45,
                 imgsz: int = 640,
                 lock_frames: int = 35,
                 me_iou_thresh: float = 0.25,
                 smooth_alpha: float = 0.6,
                 other_history: int = 7,
                 other_trigger: int = 4):

        self.model = YOLO(model_name)
        self.cap = cv.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise SystemExit("Cannot open camera")

        # Config
        self.conf = conf
        self.imgsz = imgsz
        self.lock_frames = lock_frames
        self.me_iou_thresh = me_iou_thresh
        self.smooth_alpha = smooth_alpha
        self.other_trigger = other_trigger
        self.other_people = []

        # State
        self.me_box = None                  # (x1,y1,x2,y2)
        self.me_candidates = []             # list of (x1,y1,x2,y2)
        self.frame_count = 0
        self.other_hits = deque(maxlen=other_history)
        self.last_closest_box = None        # (x1,y1,x2,y2)


    @staticmethod
    def detect_me(a, b) -> float:
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

    @staticmethod
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

    def _get_person_boxes(self, frame):
        """Returns [(x1,y1,x2,y2,conf), ...] for 'person' class only."""
        res = self.model.predict(frame, conf=self.conf, imgsz=self.imgsz, verbose=False)[0]

        person_boxes = []
        if res.boxes is None:
            return person_boxes

        for b in res.boxes:
            cls_id = int(b.cls[0].item())
            if cls_id != 0:  # COCO 'person'
                continue
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            conf = float(b.conf[0].item())
            person_boxes.append((x1, y1, x2, y2, conf))

        return person_boxes

    def _init_me(self, person_boxes, cx, cy):
        """Lock onto 'me' during the first lock_frames frames."""
        if self.me_box is not None or self.frame_count >= self.lock_frames:
            return

        best = None
        best_score = -1e9

        for (x1, y1, x2, y2, conf) in person_boxes:
            area = (x2 - x1) * (y2 - y1)
            bx = (x1 + x2) / 2.0
            by = (y1 + y2) / 2.0
            dist = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
            score = area - 2.0 * dist  # big + centered => likely you

            if score > best_score:
                best_score = score
                best = (x1, y1, x2, y2)

        if best is not None:
            self.me_candidates.append(best)

        # finalize on last lock frame
        if self.frame_count == self.lock_frames - 1 and len(self.me_candidates) > 0:
            xs1 = sorted([b[0] for b in self.me_candidates])
            ys1 = sorted([b[1] for b in self.me_candidates])
            xs2 = sorted([b[2] for b in self.me_candidates])
            ys2 = sorted([b[3] for b in self.me_candidates])
            mid = len(self.me_candidates) // 2
            self.me_box = (xs1[mid], ys1[mid], xs2[mid], ys2[mid])

    def _update_me(self, person_boxes):
        """Track 'me' using IoU match."""
        if self.me_box is None:
            return

        best_match = None
        best_iou = 0.0

        for (x1, y1, x2, y2, conf) in person_boxes:
            box = (x1, y1, x2, y2)
            v = self.detect_me(self.me_box, box)
            if v > best_iou:
                best_iou = v
                best_match = box

        if best_match is not None and best_iou > self.me_iou_thresh:
            self.me_box = best_match

    def _find_others(self, person_boxes):
        """Return (other_people_list, closest_box, closest_conf, found_other)."""
        self.other_people = []
        closest_box = None
        closest_conf = 0.0
        closest_area = -1

        for (x1, y1, x2, y2, conf) in person_boxes:
            box = (x1, y1, x2, y2)

            # ignore "me"
            if self.me_box is not None and self.detect_me(self.me_box, box) > self.me_iou_thresh:
                continue

            self.other_people.append((x1, y1, x2, y2, conf))

            area = (x2 - x1) * (y2 - y1)
            print(area)
        if area > closest_area:
            closest_area = area
            closest_box = (x1, y1, x2, y2)
            closest_conf = conf

        found_other = len(self.other_people) > 0
        return self.other_people, closest_box, closest_conf, found_other

    def _draw(self, frame, other_people, closest_box, closest_conf):
        # Draw "me"
        if self.me_box is not None:
            mx1, my1, mx2, my2 = self.me_box
            cv.rectangle(frame, (mx1, my1), (mx2, my2), (255, 0, 0), 2)
            cv.putText(frame, "ME (ignored)", (mx1, my1 - 10),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

        # Draw OTHER people (skip closest)
        for (x1, y1, x2, y2, conf) in other_people:
            if closest_box is not None and (x1, y1, x2, y2) == closest_box:
                continue
            cv.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)
            cv.putText(frame, f"OTHER {conf:.2f}", (x1, y1 - 10),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 0), 2)

        # Highlight CLOSEST
        if closest_box is not None:
            closest_box = self.smooth_box(self.last_closest_box, closest_box, alpha=self.smooth_alpha)
            self.last_closest_box = closest_box

            x1, y1, x2, y2 = closest_box
            cv.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 6)
            cv.putText(frame, f"Teacher {closest_conf:.2f}", (x1, y1 - 12),
                       cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # Status text during locking
        if self.me_box is None:
            cv.putText(frame, f"Locking onto YOU... {self.frame_count+1}/{self.lock_frames}", (20, 30),
                       cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    
