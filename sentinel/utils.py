import subprocess
import sys
import logging

logger = logging.getLogger("sentinel_utils")

def download_spacy_model(model_name: str = "en_core_web_lg") -> None:
    """
    Downloads the specified Spacy model using the current python executable.
    
    Args:
        model_name: Name of the Spacy model to download (default: en_core_web_lg)
    """
    logger.info(f"Attempting to download Spacy model: {model_name}...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "spacy", "download", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"Successfully downloaded {model_name}.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download model {model_name}. Error: {e}")
        logger.error("Try running: python -m spacy download en_core_web_lg manually.")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error downloading model: {e}")
        raise e
