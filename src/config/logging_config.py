import logging
import sys


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logging.getLogger("kubernetes").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
