import datetime
import json

from flask import Flask
from flask import request
import requests

from diagnostics import Diagnostics
import settings

app = Flask(__name__)

diagnostics = Diagnostics(launched_at=datetime.datetime.utcnow())

@app.route('/log', methods=['POST'])
def log():
    diagnostics.request_count += 1
    auth = request.authorization
    if not auth or auth.username != settings.LOG_DRAIN_USERNAME or auth.password != settings.LOG_DRAIN_PASSWORD:
        diagnostics.unauthorized_count += 1
        return '', 403
    diagnostics.authorized_count += 1

    log_records = []
    for log_line in _parse_log_lines(request.data):
        if log_line.startswith(settings.LOG_RECORD_PREFIX):
            json_string = log_line.replace(settings.LOG_RECORD_PREFIX, '', 1).strip()
            log_record = json.loads(json_string)
            log_records.append(log_record)
            diagnostics.log_lines_processed += 1

    logplex_frame_id = request.headers.get('Logplex-Frame-Id')

    if log_records:
        _post_to_bigquery(log_records, logplex_frame_id)

    return ''

@app.route('/')
def index():
    return diagnostics.render(), 200, {'Content-Type': 'text/plain'}

def _parse_log_lines(body):
    lines = []
    current = body
    while current:
        space_index = current.find(' ')
        if space_index == -1:
            return lines
        try:
            length = int(current[:space_index])
        except ValueError:
            return lines
        # +1 is for the space after the length
        full_line = current[space_index + 1:space_index + length]
        line = full_line[full_line.find(' - ') + 3:]
        lines.append(line)
        current = current[space_index + length + 1:]
    return lines

def _post_to_bigquery(log_records, logplex_frame_id):
    rows = []
    for i, record in enumerate(log_records):
        row = {
            'insertId': '%s-%d' % (logplex_frame_id, i),
            'json': record,
        }
        rows.append(row)
    insert_req = {
      'kind': 'bigquery#tableDataInsertAllRequest',
      'skipInvalidRows': settings.BIG_QUERY_SKIP_INVALID_ROWS,
      'ignoreUnknownValues': settings.BIG_QUERY_IGNORE_UNKNOWN_VALUES,
      'rows': rows,
    }
    url = 'https://www.googleapis.com/bigquery/v2/projects/%s/datasets/%s/tables/%s/insertAll' % (
        settings.BIG_QUERY_PROJECT_ID, settings.BIG_QUERY_DATASET_ID, settings.BIG_QUERY_TABLE_ID)
    response = requests.post(url,
        data=json.dumps(insert_req),
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % settings.GOOGLE_ACCESS_TOKEN,
            })
    diagnostics.big_query_response_codes[response.status_code] += 1
    if response.status_code == 200 and not response.json().get('error'):
        diagnostics.big_query_rows_inserted += len(log_records)
    else:
        diagnostics.big_query_rows_failed += len(log_records)
        diagnostics.sample_big_query_insert_errors.append(response.text)

if __name__ == '__main__':
    app.debug = settings.DEBUG
    app.run()
