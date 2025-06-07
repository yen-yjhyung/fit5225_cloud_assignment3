#!/usr/bin/env python
# coding: utf-8

# requirements
# !pip install ultralytics supervision

from ultralytics import YOLO
# import supervision as sv
import cv2 as cv
import os
from collections import defaultdict
import boto3
import tempfile

ENV = os.getenv("ENV", "prod") # default to prod if ENV is not set

# Only import supervision if in development environment
if ENV == "dev":
    import supervision as sv

DEFAULT_S3_BUCKET = "birdtag-inference-models"
DEFAULT_S3_KEY = "visual/model.pt"
DEFAULT_LOCAL_MODEL_PATH = os.path.join(tempfile.gettempdir(), "model.pt")

def download_model_from_s3():
    """
    Download the YOLO model from S3 to a local path.
    """
    bucket = os.environ.get("S3_MODEL_BUCKET", DEFAULT_S3_BUCKET)
    key = os.environ.get("S3_MODEL_KEY", DEFAULT_S3_KEY)
    local_path = DEFAULT_LOCAL_MODEL_PATH

    if not os.path.exists(local_path): # if model not already downloaded
        print(f"Downloading model from s3://{bucket}/{key} to {local_path}", flush=True)
        s3 = boto3.client('s3')
        try:
            s3.download_file(bucket, key, local_path)
            print(f"Model downloaded from s3://{bucket}/{key} to {local_path}")
        except Exception as e:
            # Log the error and raise an exception
            print(f"Error downloading model from S3: s3://{bucket}/{key} to {local_path} Error: {e}", flush=True)
            raise RuntimeError(f"Failed to download model from S3: {e}")

    return local_path

# ##### Global Initialization for Visual Detection Model Loading #### 
GLOBAL_MODEL = None # initialize global model to None
try:
    # Download the model to local path
    global_model_path = download_model_from_s3()

    # Local the YOLO model once into global variable
    GLOBAL_MODEL = YOLO(global_model_path)
    print("YOLO model loaded successsfully into global scope.", flush=True)
except Exception as e:
    # Print fatal error message and re-raise to inidicate a failed cold start
    print(f"FATAL ERROR: Could not initialize YOLO model in global scrope. Error: {e}", flush=True)
    # Re-raise the exception to prevent the Lambda handler from being invoked
    raise


def image_prediction(image_path, result_filename=None, save_dir="./image_prediction_results", confidence=0.5):
    """p
    Function to display predictions of a pre-trained YOLO model on a given image.

    Parameters:
        image_path (str): Path to the image file. Can be a local path or a URL.
        result_path (str): If not None, this is the output filename.
        confidence (float): 0-1, only results over this value are saved.
        model (str): path to the model.
    """

    # Load YOLO model
    # model = YOLO(model)
    model = GLOBAL_MODEL
    class_dict = model.names

    img = cv.imread(image_path)
    if img is None:
        print("Couldn't load the image! Check the image path.")
        return {}

    result = model(img)[0]
    tag_counter = defaultdict(int)

    if ENV == "dev":
        h, w = img.shape[:2]
        thickness = sv.calculate_optimal_line_thickness((w, h))
        text_scale = sv.calculate_optimal_text_scale((w, h))
        color_palette = sv.ColorPalette.from_matplotlib('magma', 10)
        box_annotator = sv.BoxAnnotator(thickness=thickness, color=color_palette)
        label_annotator = sv.LabelAnnotator(
            color=color_palette,
            text_scale=text_scale,
            text_thickness=thickness,
            text_position=sv.Position.TOP_LEFT
        )

        detections = sv.Detections.from_ultralytics(result)
        detections = detections[detections.confidence > confidence]

        if len(detections.class_id) > 0:
            labels = [
                f"{class_dict[cls_id]} {conf:.2f}"
                for cls_id, conf in zip(detections.class_id, detections.confidence)
            ]
            box_annotator.annotate(img, detections)
            label_annotator.annotate(img, detections, labels)

            if result_filename:
                try:
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, result_filename)
                    status = cv.imwrite(save_path, img)
                    print(f"Image save status = {status}.")
                except Exception as e:
                    print(f"Error saving image: {e}")

            for cls_id in detections.class_id:
                tag_counter[class_dict[cls_id]] += 1

    else:
        for box in result.boxes:
            conf = box.conf.cpu().item()
            cls = int(box.cls.cpu().item())
            if conf > confidence:
                tag_counter[class_dict[cls]] += 1

    return {
        "tags": [{"name": name, "count": count} for name, count in tag_counter.items()]
    }

# def image_prediction(image_path, result_filename=None, save_dir="./image_prediction_results", confidence=0.5, model="./model.pt"):
#     """
#     Function to display predictions of a pre-trained YOLO model on a given image.

#     Parameters:
#         image_path (str): Path to the image file. Can be a local path or a URL.
#         result_path (str): If not None, this is the output filename.
#         confidence (float): 0-1, only results over this value are saved.
#         model (str): path to the model.
#     """

#     # Load YOLO model
#     model = YOLO(model)
#     class_dict = model.names

#     # Load image from local path
#     img = cv.imread(image_path)

#     # Check if image was loaded successfully
#     if img is None:
#         print("Couldn't load the image! Please check the image path.")
#         return

#     # Get image dimensions
#     h, w = img.shape[:2]

#     # Calculate optimal thickness for boxes and text based on image resolution
#     thickness = sv.calculate_optimal_line_thickness(resolution_wh=(w, h))
#     text_scale = sv.calculate_optimal_text_scale(resolution_wh=(w, h))

#     # Set up color palette for annotations
#     color_palette = sv.ColorPalette.from_matplotlib('magma', 10)

#     # Create box and label annotators
#     box_annotator = sv.BoxAnnotator(thickness=thickness, color=color_palette)
#     label_annotator = sv.LabelAnnotator(color=color_palette, text_scale=text_scale, 
#                                         text_thickness=thickness, 
#                                         text_position=sv.Position.TOP_LEFT)

#     # Run the model on the image
#     result = model(img)[0]

#     # Convert YOLO result to Detections format
#     detections = sv.Detections.from_ultralytics(result)

#     save_annotated = os.getenv("ENV") == "dev"
    
#     # Filter based on confidence
#     detections = detections[detections.confidence > confidence]

#     if len(detections.class_id) > 0:
#         labels = [f"{class_dict[cls_id]} {conf:.2f}" for cls_id, conf in zip(detections.class_id, detections.confidence)]
#         box_annotator.annotate(img, detections)
#         label_annotator.annotate(img, detections, labels)

#         # Save annotated image if requested
#         if save_annotated and result_filename:
#             try:
#                 os.makedirs(save_dir, exist_ok=True)
#                 save_path = os.path.join(save_dir, result_filename)
#                 status = cv.imwrite(save_path, img)
#                 print(f"Image save status = {status}.")
#             except Exception as e:
#                 print(f"Error saving image: {e}")

#         # Count detected bird names
#         tag_counter = defaultdict(int)
#         for cls_id in detections.class_id:
#             name = class_dict[cls_id]
#             tag_counter[name] += 1


#         return {
#             "tags": [{"name": name, "count": count} for name, count in tag_counter.items()],
#         }

#     return {}  # No detections


# # ## Video Detection
def video_prediction(video_path, result_filename=None, save_dir = "./video_prediction_results", confidence=0.5, model="./model.pt", frame_skip=24):
    """
    Function to make predictions on video frames using a trained YOLO model and display the video with annotations.

    Parameters:
        video_path (str): Path to the video file.
        save_video (bool): If True, saves the video with annotations. Default is False.
        filename (str): The name of the output file where the video will be saved if save_video is True.
    """
    ENV = os.getenv("ENV", "prod").lower()
    save_annotated = ENV == "dev"
    # model = YOLO(model)
    model = GLOBAL_MODEL
    result = {"tags": []}
    cap = cv.VideoCapture(video_path)

    if not cap.isOpened():
        print("Failed to open video file.")
        return result

    fps = cap.get(cv.CAP_PROP_FPS)
    width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv.VideoWriter_fourcc(*'mp4v')

    out_writer = None
    box_annotator = None
    label_annotator = None

    if save_annotated:
        import supervision as sv
        thickness = sv.calculate_optimal_line_thickness((width, height))
        text_scale = sv.calculate_optimal_text_scale((width, height))
        color_palette = sv.ColorPalette.from_matplotlib('magma', 10)

        box_annotator = sv.BoxAnnotator(thickness=thickness, color=color_palette)
        label_annotator = sv.LabelAnnotator(
            color=color_palette,
            text_scale=text_scale,
            text_thickness=thickness,
            text_position=sv.Position.TOP_LEFT
        )

        if result_filename:
            os.makedirs(save_dir, exist_ok=True)
            output_path = os.path.join(save_dir, f"{result_filename}.mp4")
            out_writer = cv.VideoWriter(output_path, fourcc, fps, (width, height))

    tag_max_counts = {}
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_skip == 0:
            results = model(frame)[0]

            if save_annotated:
                detections = sv.Detections.from_ultralytics(results)
                labels = [model.names[class_id] for class_id in detections.class_id]

                # max count seen per frame
                for label in set(labels):
                    current_count = labels.count(label)
                    tag_max_counts[label] = max(tag_max_counts.get(label, 0), current_count)

                if out_writer:
                    annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
                    label_annotator.annotate(annotated_frame, detections, labels)
                    out_writer.write(annotated_frame)
            else:
                # Manual detection logic for prod (no supervision)
                frame_label_counter = {}
                for box in results.boxes:
                    conf = box.conf.cpu().item()
                    cls = int(box.cls.cpu().item())
                    if conf > confidence:
                        label = model.names[cls]
                        frame_label_counter[label] = frame_label_counter.get(label, 0) + 1

                for label, count in frame_label_counter.items():
                    tag_max_counts[label] = max(tag_max_counts.get(label, 0), count)

        elif save_annotated and out_writer:
            out_writer.write(frame)

        frame_count += 1

    cap.release()
    if out_writer:
        out_writer.release()

    result["tags"] = [{"name": name, "count": count} for name, count in tag_max_counts.items()]
    return result

# # # ## Video Detection
# def video_prediction(video_path, result_filename=None, save_dir = "./video_prediction_results", confidence=0.5, model="./model.pt", frame_skip=24):
#     """
#     Function to make predictions on video frames using a trained YOLO model and display the video with annotations.

#     Parameters:
#         video_path (str): Path to the video file.
#         save_video (bool): If True, saves the video with annotations. Default is False.
#         filename (str): The name of the output file where the video will be saved if save_video is True.
#     """
#     model = YOLO(model)

#     result = {
#         "tags": [],
#     }
#     cap = cv.VideoCapture(video_path)
#     if not cap.isOpened():
#         print("Failed to open video file.")
#         return result

#     fps = cap.get(cv.CAP_PROP_FPS)
#     width  = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
#     height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
#     fourcc = cv.VideoWriter_fourcc(*'mp4v')

#     save_annotated = os.getenv("ENV") == "dev"
#     output_path = None
#     out_writer = None

#     # Calculate optimal thickness for boxes and text based on image resolution
#     thickness = sv.calculate_optimal_line_thickness(resolution_wh=(width, height))
#     text_scale = sv.calculate_optimal_text_scale(resolution_wh=(width, height))

#     # Set up color palette for annotations
#     color_palette = sv.ColorPalette.from_matplotlib('magma', 10)

#     # Create box and label annotators
#     box_annotator = sv.BoxAnnotator(thickness=thickness, color=color_palette)
#     label_annotator = sv.LabelAnnotator(color=color_palette, text_scale=text_scale, 
#                                         text_thickness=thickness, 
#                                         text_position=sv.Position.TOP_LEFT)

#     if save_annotated and result_filename:
#         os.makedirs(save_dir, exist_ok=True)
#         output_path = os.path.join(save_dir, f"{result_filename}.mp4")
#         out_writer = cv.VideoWriter(output_path, fourcc, fps, (width, height))

#     tag_max_counts = {}
#     frame_count = 0

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         if frame_count % frame_skip == 0:
#             results = model(frame)[0]
#             detections = sv.Detections.from_ultralytics(results)

#             labels = [model.names[class_id] for class_id in detections.class_id]

#             # Track max counts
#             for label in labels:
#                 current_count = labels.count(label)
#                 tag_max_counts[label] = max(tag_max_counts.get(label, 0), current_count)

#             if save_annotated and out_writer:
#                 if frame_count % frame_skip == 0:
#                     annotated_frame = box_annotator.annotate(
#                         scene=frame.copy(),
#                         detections=detections
#                     )
#                     label_annotator.annotate(annotated_frame, detections, labels)
#                     out_writer.write(annotated_frame)
#                 else:
#                     out_writer.write(frame)

#         frame_count += 1

#     cap.release()
#     if out_writer:
#         out_writer.release()

#     result["tags"] = [{"name": name, "count": count} for name, count in tag_max_counts.items()]
#     return result


if __name__ == '__main__':
    print("predicting...")
    image_prediction("./test_images/crows_1.jpg", result_filename="crows_result1.jpg")
    image_prediction("./test_images/crows_3.jpg", result_filename='crows_detected_2.jpg')
    image_prediction("./test_images/kingfisher_2.jpg",result_filename='kingfishers_detected.jpg' )
    image_prediction("./test_images/myna_1.jpg",result_filename='myna_detected.jpg')
    image_prediction("./test_images/owl_2.jpg",result_filename='owls_detected.jpg')
    image_prediction("./test_images/peacocks_3.jpg",result_filename='peacocks_detected_1.jpg')
    image_prediction('./test_images/sparrow_3.jpg',result_filename='sparrow_detected_1.jpg')
    image_prediction('./test_images/sparrow_1.jpg',result_filename='sparrow_detected_2.jpg')

    # uncomment to test video prediction
    # video_prediction("./test_videos/crows.mp4",result_filename='crows_detected.mp4')
    # video_prediction("./test_videos/kingfisher.mp4",result_filename='kingfisher_detected.mp4')