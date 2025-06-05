import os
import uuid
import datetime
from birdnet_analyzer.analyze import utils as analyzer_utils
from birdnet_analyzer import config as cfg

def run_audio_prediction(file_path: str):

    # Resolve paths
    abs_file_path = os.path.abspath(file_path)
    file_basename = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.abspath("audio_prediction_results")

    output_file_path = os.path.join(output_dir, f"{file_basename}_detection.csv")

    # path where .tflite and label files are located
    model_base_dir = os.path.dirname(__file__)


    config_dict = {
        "INPUT_PATH": abs_file_path,
        "OUTPUT_PATH": output_dir,
        "SCRIPT_DIR": model_base_dir,
        "MODEL_PATH": os.path.join(model_base_dir, "BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite"),
        "LABELS_FILE": os.path.join(model_base_dir, "BirdNET_GLOBAL_6K_V2.4_Labels.txt"),
        "TRANSLATED_LABELS_PATH": os.path.join(f"{model_base_dir}/labels/V2.4","BirdNET_GLOBAL_6K_V2.4_Labels_en_uk.txt"),
        "CODES_FILE": os.path.join(model_base_dir, "eBird_taxonomy_codes_2021E.json"),
        "RESULT_TYPES": {"csv"},
        "OUTPUT_CSV_FILENAME": output_file_path,
    }

    # Set configuration
    cfg.set_config(config_dict)

    # load labels
    try:
        with open(config_dict["LABELS_FILE"], "r", encoding="utf-8") as f:
            cfg.LABELS = [line.strip() for line in f.readlines() if line.strip()]
        print(f"[Audio] Loaded {len(cfg.LABELS)} labels.")
    except Exception as e:
        print(f"[Audio] ERROR: Failed to load labels: {e}")
        cfg.LABELS = []
    
    # load translated labels
    try:
        with open(config_dict["TRANSLATED_LABELS_PATH"], "r", encoding="utf-8") as f:
            cfg.TRANSLATED_LABELS = [line.strip() for line in f.readlines() if line.strip()]
        print(f"[Audio] Loaded {len(cfg.TRANSLATED_LABELS)} translated labels.")
    except Exception as e:
        print(f"[Audio] ERROR: Failed to load translated labels: {e}")
        cfg.TRANSLATED_LABELS = []


    # Run prediction
    print(f"[Audio] Analyzing audio: {abs_file_path}")
    predictions_dict = analyzer_utils.analyze_file((abs_file_path, cfg.get_config()))

    # Return JSON response
    return {
        "tags": predictions_dict.get("tags", []),
    }
