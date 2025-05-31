import os

# === MODEL CONFIGURATION ===
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../model/BirdNET_GLOBAL_6K_V2.3_Model_FP32.tflite")
LABELS_FILE = os.path.join(os.path.dirname(__file__), "../model/BirdNET_GLOBAL_6K_V2.4_Labels.txt")
CODES_FILE = os.path.join(os.path.dirname(__file__), "../model/eBird_taxonomy_codes_2021E.json")

# === AUDIO SETTINGS ===
SAMPLE_RATE = 48000
SIG_LENGTH = 3.0
SIG_OVERLAP = 0.0
SIG_MINLEN = 1.0
BANDPASS_FMIN = 150.0
BANDPASS_FMAX = 15000.0
AUDIO_SPEED = 1.0
BATCH_SIZE = 1
APPLY_SIGMOID = True
SIGMOID_SENSITIVITY = 1.0

# === PREDICTION FILTERS ===
TOP_N = 5
MIN_CONFIDENCE = 0.1
SPECIES_LIST = []  # Optional: filter specific species

# === COORDINATES (Optional) ===
LATITUDE = 0.0
LONGITUDE = 0.0
WEEK = 20

# === RESULT CONFIGURATION ===
RESULT_TYPES = ["csv"]
OUTPUT_PATH = "/tmp/results"
SKIP_EXISTING_RESULTS = False
MERGE_CONSECUTIVE = 3
OUTPUT_CSV_FILENAME = "BirdNET_combined.csv"
OUTPUT_RAVEN_FILENAME = "BirdNET_combined.table.txt"
OUTPUT_KALEIDOSCOPE_FILENAME = "BirdNET_combined.kaleidoscope.csv"

# === DYNAMIC VARIABLES ===
LABELS = []
TRANSLATED_LABELS = []
CODES = {}
INPUT_PATH = ""

def set_config(args):
    global LATITUDE, LONGITUDE, WEEK, SPECIES_LIST, OUTPUT_PATH, INPUT_PATH

    LATITUDE = args.get("lat", LATITUDE)
    LONGITUDE = args.get("lon", LONGITUDE)
    WEEK = args.get("week", WEEK)
    SPECIES_LIST = args.get("species_list", SPECIES_LIST)
    OUTPUT_PATH = args.get("output_path", OUTPUT_PATH)
    INPUT_PATH = args.get("input_path", INPUT_PATH)
