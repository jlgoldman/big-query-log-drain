# BigQuery Log Drain

A log drain for Heroku that syncs records to Google BigQuery.

## Why?

Being able to query logs for a service is essential for understanding usage,
finding bugs, and tracking abuse.

Most web frameworks output semi-structured plain text logs, which are certainly
helpful for grep-ing or tail-ing, but this is nowhere near as useful as being
able to write SQL queries on your logs.

Sending logs to a database or index should be done offline or asynchronously
to avoid blocking user requests and to ensure that transient errors don't
result in log records being dropped.

## Why BigQuery?

Both Google BigQuery and Amazon Redshift are highly scalable, column-oriented
big data stores well-suited to storing and querying log data. BigQuery is
simply just way cheaper for small projects, virtually free at trivial sizes
and with costs scaling at a reasonable rate vs Redshift which starts at
around $180/month no matter how small your scale.

## How it Works

Heroku allows any app to write to stdout and the results will be written to
temporary logs. Heroku also supports [log drains](https://devcenter.heroku.com/articles/log-drains)
which forward your plain text logs to another service for storage or indexing.

Launch this service on the host of your choice (including Heroku itself) and
register the url of that service as an http log drain for your Heroku app.
Set up a BigQuery dataset with a schema of your choice. Then print JSON
records matching that BigQuery schema to stdout on your Heroku app.
Heroku will send those log lines containing JSON to this log drain service,
which will parse them and make API requests to BigQuery to insert them.

## Setup

### Create a BigQuery Table

Create a Google Cloud project if you don't already have one.
Go to [https://bigquery.cloud.google.com](https://bigquery.cloud.google.com) and create a BigQuery dataset and
a table within that dataset.

It is highly recommended to leave all columns as `nullable`, otherwise
BigQuery will throw errors when those fields are absent on inserts.
In particular, if you add a new column to the schema later on, you must
add that column as `nullable` otherwise BigQuery will give errors
immediately until your app starts including that field in JSON records.

Get an access token with permissions to insert into BigQuery: TBD.

### Launch the Log Drain Service

Launch the code from this service using the hosting provider of your
choice. Heroku is likely the simplest, followed by Amazon Lambda.
Set the required environment variables as decribed in the
Configuration Reference below.

### Have Your App Print JSON Log Records

Change your application code to print JSON-serialized log data matching
your BigQuery schema, with a prefix that identifies that line as containing
JSON log records. Heroku will send all log lines to the log drain, including
lines for system services like the Heroku router, so the log drain will
ignore all lines that don't match a given prefix.

A sample log line would look like

```
json: {"url": "/foo", "response_code": 200}
```

If you're running a Python app, for example, at the end of a request you can
just do:

```python
print 'json: %s' % json.dumps({'url': 'foo', 'response_code': 200})
```

### Add an HTTP Log Drain to Your Existing Heroku App

Run this from the command line to register a log drain for your app:

```bash
heroku drains:add https://<username>:<password>@<log-drain-url>/log -a <heroku-app-name>
```

### Verify

Make a simple query at the BigQuery console to verify that records are being
inserted. Records added via streaming inserts should be available virtually
immediately.

Visit https://<your-log-drain-url>/ to see diagnostics about the number
of requests and log lines processed and their statuses. The diagnostic
page shows stats for the worker process that handled the request, since
the last restart time, and not all-time stats or combined stats from all
workers.

## Configuration Reference

Specify these environment variables when launching your service. If running,
the log drain on Heroku, these can be set via

```bash
heroku config:set VARIABLE=value
```

If you're modifying the source code here and want to run a log drain locally,
created a `.env` file in your project directory with these variables
one per line in the form `VARIABLE=value`.

Variable | Required? | Description
----------------------------------
| LOG_DRAIN_USERNAME | Required | An arbitrary username used to secure access to the /log endpoint from unauthorized sources. Use this same value when registering the drain using `heroku drains:add`. |
| LOG_DRAIN_PASSWORD | Required | An arbitrary password used to secure access to the /log endpoint from unauthorized sources. Use this same value when registering the drain using `heroku drains:add`. |
| LOG_RECORD_PREFIX  | Optional | An arbitrary prefix used to different log lines that contain json records from all other log records, which are plain text. If unspecified, defaults to `json:`. |
| GOOGLE_ACCESS_TOKEN | Required | An access token used for making insert requests to BigQuery, as described in https://cloud.google.com/bigquery/docs/reference/rest/v2/tabledata/insertAll. Must have at least one of these | | scoopes: `https://www.googleapis.com/auth/bigquery`, `https://www.googleapis.com/auth/cloud-platform`,  or `https://www.googleapis.com/auth/bigquery.insertdata`. For simplicity, you can just use `https://www.googleapis.com |/| auth/bigquery.insertdata`. |
| BIG_QUERY_PROJECT_ID | Required | The name of the Google Cloud project that contains your BigQuery dataset. This is typically a string of the form `my-project-19902`. |
| BIG_QUERY_DATASET_ID | Required | The name of dataset that you gave at creation time. This is an arbitrary string, typically a simple descriptive name like `weblog`. |
| BIG_QUERY_TABLE_ID | Required | The name of the table within the dataset that you'd like to insert into. This is an arbitrary string, it could be something like `all` if you have a single table for all logs, or perhaps a | | date if you partition logs in some qay. |
| BIG_QUERY_SKIP_INVALID_ROWS | Optional | Defaults to false. If true, BigQuery will simply skip any invalid rows on insert, otherwise it returns an error and all rows in that request will fail to insert. |
| BIG_QUERY_IGNORE_UNKNOWN_VALUES | Optional | Default to false. If true, BigQuery will ignore any unknown values it encounters within a record, otherwise it returns an error and all rows in that request will fail to insert. |
| DEBUG | Optional | Defaults to false. When running locally, sets the Flask/Werkzeug app server into debug mode, which enables automatic module reloading and debug logging. |

## Reliability

This is an extremely simple service that should work well in most cases but
isn't guaranteed to sync every single record when there are outages or
network issues. If running the log drain on Heroku, then if your app is
up and running on Heroku, the log drain should be up and running too.
If BigQuery is down or there is a network issue, records that are attempted
to sync during that time may be lost, there is not a recovery queue
at this time.

Duplicate records are unlikely. Heroku sends log records to the drain
exactly once in most cases, but in the case of a network-level retry
it's possible the drain can receive a record more than once. However,
Heroku sends a `Logplex-Frame-Id` header with each request. BigQuery
allows you to send an `insertId` string on each request, and if the same
`insertId` is seen more than once in a short period of time, it will
de-duplicate the insert request. The log drain derives an `insertId`
from the `Logplex-Frame-Id` and hence allows BigQuery to deduplicate
requests that were re-sent as a result of Heroku re-sending a log drain
request, provided that the re-send happens within BigQuery's deduplication
window.
