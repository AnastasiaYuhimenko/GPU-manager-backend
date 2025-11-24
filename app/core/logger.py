import logging

logging.basicConfig(level=logging.INFO, filename="logs.log", filemode="w")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
