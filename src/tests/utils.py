import os
from dotenv import load_dotenv


def patch_path(func):
    class_name = str(func).replace('<function ', '').replace('<bound method ', '').split('.')[0]
    if class_name.startswith(func.__name__):
        return func.__module__ + '.' + func.__name__
    return func.__module__ + '.' + class_name + '.' + func.__name__


def load_test_env():
    dotenv_path = os.path.dirname(__file__) + os.path.sep + '.testenv'
    # Load file from the path.
    load_dotenv(dotenv_path)
