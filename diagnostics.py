import collections

import jinja2

class Diagnostics(object):
    def __init__(self, launched_at):
        self.launched_at = launched_at
        self.request_count = 0
        self.authorized_count = 0
        self.unauthorized_count = 0
        self.log_lines_processed = 0
        self.big_query_response_codes = collections.defaultdict(int)
        self.big_query_rows_inserted = 0
        self.big_query_rows_failed = 0
        self.sample_big_query_insert_errors = collections.deque(maxlen=10)

    def render(self):
        return template.render(d=self)

template = jinja2.Template('''BigQuery Log Drain Stats for Current Worker

Launched at: {{d.launched_at}} UTC
Requests: {{d.request_count}} (Authorized: {{d.authorized_count}}, Unauthorized: {{d.unauthorized_count}})
Log Lines Processed: {{d.log_lines_processed}}
BigQuery Insert Response Codes: {% for code, count in d.big_query_response_codes | dictsort %}{{code}}: {{count}}{% if not loop.last %}, {% endif %}{% endfor %}
BigQuery Rows Inserted: {{d.big_query_rows_inserted}}
BigQuery Rows Failed: {{d.big_query_rows_failed}}
{% if d.sample_big_query_insert_errors %}
Sampling of BigQuery insert responses:
{% for error in d.sample_big_query_insert_errors %}
{{error}}
{% endfor %}
{% endif %}
''')
