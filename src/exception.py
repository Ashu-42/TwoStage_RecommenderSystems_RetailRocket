# common for every project

import sys
from src.logger import logging

def error_message_details(error, error_detail:sys):

    _,_, exc_tb = error_detail.exc_info() # gives all the info related to error, not interested in the first 2 values, the 3rd value gives data like file in which exception occured, line of error, error type etc 
    
    err_file, err_line,  err_msg = exc_tb.tb_frame.f_code.co_filename, exc_tb.tb_lineno, str(error)
    
    error_message = f"error occured in python script name : {err_file}, line num : {err_line}, error message : {err_msg}"

    return error_message

class CustomException(Exception):

    def __init__(self, error_message, error_detail:sys):
        super().__init__(error_message)
        self.error_message = error_message_details(error=error_message, error_detail=error_detail)

    def __str__(self):
        return self.error_message
    
# if __name__=="__main__":

#     try:
#         a=1/0
#     except Exception as e:
#         logging.info("division by zero")
#         raise CustomException(e, sys)