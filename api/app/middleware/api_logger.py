import logging
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent.parent / "chapflix-api.log"

logger = logging.getLogger("chapflix-api")
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
