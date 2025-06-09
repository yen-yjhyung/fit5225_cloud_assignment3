import os
import boto3
import tempfile
import json
from birdnet_analyzer.analyze import utils as analyzer_utils
from birdnet_analyzer import config as cfg

# Global Variable and Conifguration for Model and related files
DEFAULT_S3_BUCKET = os.environ.get("S3_MODEL_BUCKET", "birdtag-inference-models-group9")
DEFAULT_MODEL_S3_KEY = os.environ.get("S3_MODEL_KEY", "audio/BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite")
DEFAULT_LABELS_S3_KEY = os.environ.get("S3_LABELS_KEY", "audio/labels/V2.4/BirdNET_GLOBAL_6K_V2.4_Labels.txt")
DEFAULT_TRANSLATED_LABELS_S3_KEY = os.environ.get("S3_TRANSLATED_LABELS_KEY", "audio/labels/V2.4/BirdNET_GLOBAL_6K_V2.4_Labels_en_uk.txt")
DEFAULT_CODES_S3_KEY = os.environ.get("S3_CODES_KEY", "audio/eBird_taxonomy_codes_2021E.json")
REGION = os.environ.get("REGION", "ap-southeast-2")

# Define local paths in /tmp/ where model and files will be downloaded
LOCAL_MODEL_BASE_DIR = os.path.join(tempfile.gettempdir(), "birdnet_model_data")
LOCAL_MODEL_PATH = os.path.join(LOCAL_MODEL_BASE_DIR, "BirdNET_GLOBAL_6K_V2.4_Model_FP32.tflite")
LOCAL_LABELS_PATH = os.path.join(LOCAL_MODEL_BASE_DIR, "BirdNET_GLOBAL_6K_V2.4_Labels.txt")
LOCAL_TRANSLATED_LABELS_DIR = os.path.join(LOCAL_MODEL_BASE_DIR, "labels", "V2.4")
LOCAL_TRANSLATED_LABELS_PATH = os.path.join(LOCAL_TRANSLATED_LABELS_DIR, "BirdNET_GLOBAL_6K_V2.4_Labels_en_uk.txt")
LOCAL_CODES_PATH = os.path.join(LOCAL_MODEL_BASE_DIR, "eBird_taxonomy_codes_2021E.json")

# Global flag to ensure model files are downloaded only once per Lambda execution environment
_AUDIO_MODEL_FILES_DOWNLOADED = False
_S3_CLIENT_AUDIO = None

def download_audio_model_files_from_s3():
    """
    Downloads all neccessary BirdNET model, label and codes files from S3 to /tmp/.
    """

    global _AUDIO_MODEL_FILES_DOWNLOADED
    global _S3_CLIENT_AUDIO

    if _AUDIO_MODEL_FILES_DOWNLOADED:
        print("[Audio] Model files already downloaded. Skipping")
        return
    
    print(f"[Audio] Attempting to download model files to {LOCAL_MODEL_BASE_DIR}")

    if _S3_CLIENT_AUDIO is None:
        _S3_CLIENT_AUDIO = boto3.client("s3", region_name=REGION)
    
    # Make sure the local directories exists
    os.makedirs(LOCAL_MODEL_BASE_DIR, exist_ok=True)
    os.makedirs(LOCAL_TRANSLATED_LABELS_DIR, exist_ok=True)

    files_to_download = [
        (DEFAULT_MODEL_S3_KEY, LOCAL_MODEL_PATH),
        (DEFAULT_LABELS_S3_KEY, LOCAL_LABELS_PATH),
        (DEFAULT_TRANSLATED_LABELS_S3_KEY, LOCAL_TRANSLATED_LABELS_PATH),
        (DEFAULT_CODES_S3_KEY, LOCAL_CODES_PATH)
    ]

    for s3_key, local_path in files_to_download:
        if not os.path.exists(local_path):
            try:
                print(f"[Audio] Downloading {s3_key} from s3://{DEFAULT_S3_BUCKET}/{s3_key} to {local_path}")
                _S3_CLIENT_AUDIO.download_file(DEFAULT_S3_BUCKET, s3_key, local_path)
                print(f"[Audio] Successfully downloaded {s3_key}")
            except Exception as e:
                print(f"[Audio] ERROR: Failed to download {s3_key} from S3: {e}")
                raise e
        else:
            print(f"[Audio] {s3_key} already exists at {local_path}. Skipping download.")
    _AUDIO_MODEL_FILES_DOWNLOADED = True
    print("[Audio] All model files downloaded successfully.")

def run_audio_prediction(file_path: str):

    # Ensure model files are downloaded and loaded once
    download_audio_model_files_from_s3()

    result_prediction = {"mediaType": "audio", "tags": []}

    # Configure BirdNET Analyzer with the local paths
    config_dict = {
        "INPUT_PATH": os.path.abspath(file_path),
        "OUTPUT_PATH": os.path.abspath(os.path.join(tempfile.gettempdir(), "audio_prediction_results")),
        "SCRIPT_DIR": LOCAL_MODEL_BASE_DIR,
        "MODEL_PATH": LOCAL_MODEL_PATH,
        "LABELS_FILE": LOCAL_LABELS_PATH,
        "TRANSLATED_LABELS_PATH": LOCAL_TRANSLATED_LABELS_PATH,
        "CODES_FILE": LOCAL_CODES_PATH,
        "RESULT_TYPES": {"csv"},
        "OUTPUT_CSV_FILENAME": os.path.join(os.path.abspath(os.path.join(tempfile.gettempdir(), "audio_prediction_results")), f"{os.path.splitext(os.path.basename(file_path))[0]}_detection.csv"),
    }

    # Set configuration
    cfg.set_config(config_dict)

    # load labels
    try:
        with open(cfg.LABELS_FILE, "r", encoding="utf-8") as f:
            cfg.LABELS = [line.strip() for line in f.readlines() if line.strip()]
        print(f"[Audio] Loaded {len(cfg.LABELS)} labels.")
    except Exception as e:
        print(f"[Audio] ERROR: Failed to load labels from {cfg.LABELS_FILE}: {e}")
        cfg.LABELS = []
    
    # load translated labels
    try:
        with open(cfg.TRANSLATED_LABELS_PATH, "r", encoding="utf-8") as f:
            cfg.TRANSLATED_LABELS = [line.strip() for line in f.readlines() if line.strip()]
        print(f"[Audio] Loaded {len(cfg.TRANSLATED_LABELS)} translated labels.")
    except Exception as e:
        print(f"[Audio] ERROR: Failed to load translated labels from {cfg.TRANSLATED_LABELS_PATH}: {e}")
        cfg.TRANSLATED_LABELS = []
    
    # Load eBird taxonomy codes
    try:
        with open(cfg.CODES_FILE, "r") as cfile:
            cfg.CODES = json.load(cfile)
        print(f"[Audio] Loaded {len(cfg.CODES)} eBird codes.")
    except Exception as e:
        print(f"[Audio] ERROR: Failed to load eBird codes from {cfg.CODES_FILE}: {e}")
        cfg.CODES = {}

    result_prediction["mediaType"] = "audio"

    # Run prediction
    predictions_dict = analyzer_utils.analyze_file((os.path.abspath(file_path), cfg.get_config()))

    result_prediction["tags"] = predictions_dict.get("tags", [])
    return result_prediction
