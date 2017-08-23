import os

import dotenv

dotenv_filename = dotenv.find_dotenv()
if dotenv_filename:
    dotenv.load_dotenv(dotenv_filename)

def parse_bool(env_value):
    return env_value is not None and env_value.lower() not in ('0', 'false')

DEBUG = parse_bool(os.environ.get('DEBUG'))
LOG_DRAIN_USERNAME = os.environ.get('LOG_DRAIN_USERNAME')
LOG_DRAIN_PASSWORD = os.environ.get('LOG_DRAIN_PASSWORD')
LOG_RECORD_PREFIX = os.environ.get('LOG_RECORD_PREFIX', 'json:')

GOOGLE_ACCESS_TOKEN = os.environ.get('GOOGLE_ACCESS_TOKEN')
BIG_QUERY_PROJECT_ID = os.environ.get('BIG_QUERY_PROJECT_ID')
BIG_QUERY_DATASET_ID = os.environ.get('BIG_QUERY_DATASET_ID')
BIG_QUERY_TABLE_ID = os.environ.get('BIG_QUERY_TABLE_ID')
BIG_QUERY_SKIP_INVALID_ROWS = parse_bool(os.environ.get('BIG_QUERY_SKIP_INVALID_ROWS'))
BIG_QUERY_IGNORE_UNKNOWN_VALUES = parse_bool(os.environ.get('BIG_QUERY_IGNORE_UNKNOWN_VALUES'))
