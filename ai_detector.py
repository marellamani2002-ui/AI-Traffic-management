"""
AI Computer Vision Vehicle Detection Module
Utilizes OpenCV and YOLOv8 for vehicle classification (cars, motorcycles/bikes, buses, trucks),
traffic density estimation, and dynamic signal timing calculation.
"""

import os
import time
import cv2
import numpy as np

# Vehicle Class ID mappings in COCO dataset
# 2: car, 3: motorcycle, 5: bus, 7: truck
COCO_VEHICLE_CLASSES = {
    2: 'car',
    3: 'motorcycle',
    5: 'bus',
    7: 'truck'
}

# Color palette for vehicle bounding boxes (BGR format for OpenCV)
CLASS_COLORS = {
    'car': (246, 130, 37),       # Blue / Cyan accent
    'motorcycle': (110, 231, 16), # Vibrant Green
    'bus': (11, 158, 245),        # Amber / Orange
    'truck': (214, 50, 180)       # Purple
}

# Lazy loading of YOLO model
_YOLO_MODEL = None
_YOLO_AVAILABLE = None


def is_yolo_available():
    """Check if ultralytics YOLO is importable and available"""
    global _YOLO_AVAILABLE
    if _YOLO_AVAILABLE is None:
        try:
            from ultralytics import YOLO
            _YOLO_AVAILABLE = True
        except ImportError:
            _YOLO_AVAILABLE = False
    return _YOLO_AVAILABLE


def get_yolo_model():
    """Load or retrieve the cached YOLOv8 nano model"""
    global _YOLO_MODEL
    if _YOLO_MODEL is None and is_yolo_available():
        try:
            from ultralytics import YOLO
            print("[*] Loading YOLOv8 nano neural model...")
            _YOLO_MODEL = YOLO('yolov8n.pt')
            print("[OK] YOLOv8 model loaded successfully.")
        except Exception as e:
            print(f"[!] Warning: Could not load YOLO model: {e}")
            _YOLO_MODEL = None
    return _YOLO_MODEL


def calculate_metrics(cars, bikes, buses, trucks):
    """
    Calculate traffic density level and recommended green-light duration
    based on weighted Passenger Car Units (PCU).
    """
    total = cars + bikes + buses + trucks

    # Determine Density
    if total <= 15:
        density = "Low"
    elif total <= 35:
        density = "Medium"
    else:
        density = "High"

    # Dynamic Green-light timing formula
    base_time = 15
    weighted_pcu = (cars * 1.5) + (bikes * 0.8) + (buses * 4.0) + (trucks * 5.0)
    recommended_green = int(min(max(base_time + (weighted_pcu * 0.6), 15), 75))

    return {
        "total_vehicles": total,
        "cars": cars,
        "bikes": bikes,
        "buses": buses,
        "trucks": trucks,
        "density": density,
        "recommended_green": recommended_green
    }


def detect_frame_yolo(frame, model, conf_threshold=0.35):
    """
    Run YOLOv8 inference on a single video frame.
    Draws stylized bounding boxes and counts vehicle categories.
    """
    results = model(frame, conf=conf_threshold, verbose=False)[0]
    
    counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
    annotated = frame.copy()

    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        if cls_id in COCO_VEHICLE_CLASSES:
            class_name = COCO_VEHICLE_CLASSES[cls_id]
            counts[class_name] += 1
            color = CLASS_COLORS.get(class_name, (0, 240, 255))

            # Bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Draw rectangle with glowing corners
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Label banner
            label = f"{class_name.upper()} {int(conf * 100)}%"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - 20), (x1 + w + 6, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (10, 15, 29), 1, cv2.LINE_AA)

    return annotated, counts


def detect_frame_opencv_fallback(frame):
    """
    Fallback Computer Vision detector using adaptive contour thresholding
    when YOLO/PyTorch is still preparing or on systems without PyTorch.
    """
    annotated = frame.copy()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect_ratio = float(w) / h if h > 0 else 0

        # Heuristic classification based on bounding box geometry
        if 2000 < area < 15000:
            if aspect_ratio < 0.8:
                class_name = 'motorcycle'
            else:
                class_name = 'car'
        elif 15000 <= area < 35000:
            class_name = 'bus'
        elif area >= 35000:
            class_name = 'truck'
        else:
            continue

        counts[class_name] += 1
        color = CLASS_COLORS.get(class_name, (0, 240, 255))
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
        label = f"{class_name.upper()} [CV]"
        cv2.putText(annotated, label, (x, y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

    return annotated, counts


def process_video_or_image(input_path, output_dir):
    """
    Main processing pipeline for uploaded videos and images.
    Returns structured detection metrics and relative web paths for annotated visuals.
    """
    start_time = time.time()
    ext = os.path.splitext(input_path)[1].lower()
    is_video = ext in ['.mp4', '.avi', '.mov', '.mkv']

    model = get_yolo_model()
    model_name = "YOLOv8 Nano (Neural Vision)" if model is not None else "OpenCV Classical Vision Engine"

    filename = os.path.basename(input_path)
    annotated_filename = f"detected_{os.path.splitext(filename)[0]}.jpg"
    annotated_output_path = os.path.join(output_dir, annotated_filename)

    aggregated_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
    total_frames_processed = 0

    if is_video:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {input_path}")

        frame_count = 0
        best_frame = None
        max_detected_in_frame = -1

        # Process keyframes (1 frame every 10 frames to optimize CPU inference)
        while True:
            ret, frame = cap.read()
            if not ret or frame_count > 150:
                break

            if frame_count % 10 == 0:
                total_frames_processed += 1
                if model:
                    ann_frame, frame_counts = detect_frame_yolo(frame, model)
                    if sum(frame_counts.values()) == 0:
                        ann_frame, frame_counts = detect_frame_opencv_fallback(frame)
                else:
                    ann_frame, frame_counts = detect_frame_opencv_fallback(frame)

                frame_total = sum(frame_counts.values())
                if frame_total > max_detected_in_frame:
                    max_detected_in_frame = frame_total
                    best_frame = ann_frame

                for k in aggregated_counts:
                    aggregated_counts[k] = max(aggregated_counts[k], frame_counts[k])

            frame_count += 1

        cap.release()

        # If no frame could be analyzed, make a fallback thumbnail
        if best_frame is None:
            best_frame = np.zeros((400, 600, 3), dtype=np.uint8)
            cv2.putText(best_frame, "Traffic Video Processed", (50, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 240, 255), 2)

        cv2.imwrite(annotated_output_path, best_frame)

    else:
        # Processing a still image
        frame = cv2.imread(input_path)
        if frame is None:
            raise ValueError(f"Could not open image file: {input_path}")

        if model:
            ann_frame, aggregated_counts = detect_frame_yolo(frame, model)
            # If photographic YOLO detector finds 0 objects (e.g. on synthetic shapes or sketches),
            # combine with OpenCV structural contour detector
            if sum(aggregated_counts.values()) == 0:
                ann_frame, aggregated_counts = detect_frame_opencv_fallback(frame)
        else:
            ann_frame, aggregated_counts = detect_frame_opencv_fallback(frame)

        cv2.imwrite(annotated_output_path, ann_frame)
        total_frames_processed = 1

    proc_time = round(time.time() - start_time, 2)

    cars = aggregated_counts['car']
    bikes = aggregated_counts['motorcycle']
    buses = aggregated_counts['bus']
    trucks = aggregated_counts['truck']

    metrics = calculate_metrics(cars, bikes, buses, trucks)
    metrics["processing_time"] = proc_time
    metrics["model_used"] = model_name
    metrics["annotated_image"] = f"uploads/{annotated_filename}"
    metrics["is_video"] = is_video
    metrics["frames_analyzed"] = total_frames_processed

    return metrics
