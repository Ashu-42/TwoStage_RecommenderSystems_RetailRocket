# common for every project

import logging
import os
from datetime import datetime

LOG_FILE = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log" #names the log file with the timestamp  of execution

# LOG PATH
logs_dir=os.path.join(os.getcwd(), "logs")
os.makedirs(logs_dir, exist_ok=True) # exist_ok=True -> even if file exists in the directory just go and append the new file

# LOG FILE PATH
LOG_FILE_PATH = os.path.join(logs_dir, LOG_FILE)

# to overwrite the functionality of normal logging, we have to update this in the basic config

logging.basicConfig(
    filename=LOG_FILE_PATH,
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# if __name__=="__main__":
#     logging.info("logging has started")