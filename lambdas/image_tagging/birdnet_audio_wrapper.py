import os
import uuid
import json
from datetime import datetime

from model.birdnet_analyzer import config as cfg
from model.birdnet_analyzer import utils as analyzer_utils

def run_audio_prediction(file_path):
    # Set up config paths
    input_path = os.path.dirname(file_path)
    cfg.set_config({
        "input_path": input_path,
        "output_path": "/tmp/results"
    })

    # Run analysis
    analyzer_utils.analyze_file(file_path)

    result_path = os.path.join(cfg.OUTPUT_PATH, cfg.OUTPUT_CSV_FILENAME)
    tag_counts = {}

    if not os.path.exists(result_path):
        raise FileNotFoundError(f"No prediction output found at {result_path}")

    # Parse the result file
    with open(result_path, "r") as f:
        for line in f:
            if line.strip().startswith("Start (s)"):
                continue  # Skip header
            parts = line.strip().split("\t")
            if len(parts) < 7:
                continue
            species_name = parts[6]
            tag_counts[species_name] = tag_counts.get(species_name, 0) + 1

    tags = [{"name": name, "count": count} for name, count in tag_counts.items()]

    result = {
        "id": str(uuid.uuid4()),
        "tags": tags,
        "mediaType": "audio",
        "uploadedAt": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    return result