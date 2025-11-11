import logging

def setup_logger(name="logs", log_file="log_data.log", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add both
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
