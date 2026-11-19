# M2 Customer Code Store

This app contains:

1. Redis client
2. Lightweight API for getting customer codes
3. A script for uploading customer codes to the Redis Elasticache

## API

The interface for this API looks like this:
`GET /api/v0.1/m2-customer-code?barcodes=[barcode, …]`

The app will return a 400 if the barcodes param is missing or invalid.
The app should respond with a structure resembling this in general:

Successful response:

```json
{
  "statusCode": 200,
  "body": {
    "status": 200,
    "data": [
      {
        "barcode": "1234",
        "m2CustomerCode": "NX"
      }
    ]
  }
}
```

Failure response (returned with no response from elasticache):
```json
{
"statusCode": 400,
  "body": {
    "status": 400,
    "message": "Failure message"
  }
}
```

## Running locally

To install:

```
python -m venv localenv
source localenv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r dev-requirements.txt
```

To process API Gateway event:

```
python handle-local-event.py ./events/event.json
```

Or, to run against production config (note that the production Redis is only available to the SASB internal network at writing):

```
ENVIRONMENT=production python handle-local-event.py ./events/event.json
```

### Using sam (for best emulation)

Use `sam` to run the code in a container that best emulates the deployment environment.

Set up:

```
./provisioning/package.sh
```

Invoke on arbitrary event:

```
sam local invoke --profile nypl-digital-dev -t sam.local.yml -e ./events/event.json
```

## Testing

`make test`

## Loading data to the store

This app is invoked via a custom EventBridge event to retrieve the latest accession CSVs from S3, download them, and ingest them into Redis. Historically this was a manual process, documented below.

To invoke the ingest manually:

```
ENVIRONMENT=qa python handle-local-event.py ./events/event-scheduled-ingest.json
```

### Manually Data Load

If you need to manually retrieve accessions reports to load the data into the store, this section is for you. Note that this process is now automated, but we're keeping the manual version documented in case the automation fails.

#### Creating CSV to load

Consult the [TAD for fuller instructions with sensitive information included](https://docs.google.com/document/d/1Tl7TLIxE6uS5fPV-955F90TivfzINegCX8vmamEgkAw/edit?pli=1#heading=h.sv5u9sslauox). The basic procedure is:

 - Connect to VPN
 - Connect to LAS server
 - Load LAS client (`TERM=xterm /las/prod/scripts/lasuser`)
 - Navigate to “Barcodes by CUS/DATE” report via 3 REPORTS > 8 EXPORT ITEM BARCODES > 12 EXPORT ITEM BARCoDES
 - Select "By Customer", CUS: \*, and relevant "Beg Date" and "End Date" range
 - Note the exported file path
 - Log out and SCP the report to your local machine.

That should produce a file with barcodes and customer codes for items in M2, including columns:
- Item barcode
- Accession date
- Customer code
- Delete date

#### Update store from CSV

`ENVIRONMENT=(qa|production) python ingest_csv_report.py {csvfilename}`

Batch size defaults to 1000. The initial load of >2,000,000 records, using a batch size of 10,000, took around 30 seconds.

For all the options, run:

`python ingest_csv_report.py -h`

Note that access to the shared prod Redis appears restricted to SASB internal network at writing.

## Troubleshooting

Troubleshooting psycopg "ImportError: no pq wrapper available."

In OSX, if you have a /usr/local/opt/libpq/lib and xcode installed, but get above error when running the app locally, you may need to install the psycopg this way:

```
pip uninstall psycopg
pip install "psycopg[c]"
``
