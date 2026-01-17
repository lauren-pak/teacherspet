import cv2 as cv

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()


face_cascade = cv.CascadeClassifier("face.xml")
upper_body = cv.CascadeClassifier("upperbody.xml")

bg = cv.createBackgroundSubtractorMOG2(history=300, varThreshold=25, detectShadows=True)
kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))


while True:
    isTrue, frame = cap.read()
    if not isTrue:
        print("Can't receive frame. Exiting ...")
        break

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    

    faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=6,
    minSize=(30, 30)
    )

    for (x, y, w, h) in faces:
        cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # ---- Motion mask ----
    fg = bg.apply(frame)
    fg = cv.medianBlur(fg, 5)
    fg = cv.morphologyEx(fg, cv.MORPH_OPEN, kernel)

    contours, _ = cv.findContours(fg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    person_found = False

    for cnt in contours:
        area = cv.contourArea(cnt)
        if area < 2500:
            continue

        x, y, w, h = cv.boundingRect(cnt)

        # basic filters to skip tiny / weird boxes
        if h < 80 or w < 40:
            continue

        roi_gray = gray[y:y+h, x:x+w]
        if roi_gray.size == 0:
            continue

        # ---- Upper-body detection inside the moving ROI ----
        bodies = upper_body.detectMultiScale(
            roi_gray,
            scaleFactor=1.05,
            minNeighbors=4,
            minSize=(90, 90)
        )

        if len(bodies) > 0:
            person_found = True
            cv.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv.putText(frame, "Moving Person", (x, y-10),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


    cv.imshow("Live Camera Feed", frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()
