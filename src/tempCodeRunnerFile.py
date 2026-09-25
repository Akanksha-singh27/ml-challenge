"""
Central config for data locations. Nobody should hardcode a path like
Usage:
    from config import DATA_DIR, TRAIN_DIR, TEST_DIR

Override without editing code, in order of priority:
  1. --data-dir CLI flag (each script that needs it exposes this)
  2. ENTITY_RES_DATA_DIR environment variable
  3. Default below (relative "dataset" folder next to student_resource/)
"""

import os
from typing import Optional

# Default assumes you run scripts from inside student_resource/ with the
# provided folder structure: student_resource/dataset/train, dataset/test
DEFAULT_DATA_DIR = os.environ.get("ENTITY_RES_DATA_DIR", "dataset")


def get_data_dir(cli_arg: Optional[str] = None) -> str:
    """Resolve the dataset root: CLI arg > env var > default."""
    data_dir = cli_arg or DEFAULT_DATA_DIR
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(
            f"Data dir '{data_dir}' not found. Set it with --data-dir, or the "
            f"ENTITY_RES_DATA_DIR environment variable, or place a 'dataset' "
            f"folder next to this script."
        )
    return data_dir


def train_paths(data_dir: str) -> dict:
    train_dir = os.path.join(data_dir, "train")
    return {
        "source1": os.path.join(train_dir, "train_source1.tsv"),
        "source2": os.path.join(train_dir, "train_source2.tsv"),
        "source3": os.path.join(train_dir, "train_source3.tsv"),
        "ground_truth": os.path.join(train_dir, "train_ground_truth.tsv"),
    }


def test_paths(data_dir: str) -> dict:
    test_dir = os.path.join(data_dir, "test")
    return {
        "source1": os.path.join(test_dir, "test_source1.tsv"),
        "source2": os.path.join(test_dir, "test_source2.tsv"),
        "source3": os.path.join(test_dir, "test_source3.tsv"),
    }