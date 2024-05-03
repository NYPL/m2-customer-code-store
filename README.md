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

Set up:

```
./provisioning/package.sh
```

Invoke on arbitrary event:

```
sam local invoke --profile nypl-digital-dev -t sam.local.yml -e event.json
```

## Testing

`make test`

## Loading data to the store

Periodically, we need to generate a CSV of recent M2 accessions and load them into the QA and Prod Redis stores.

### Creating CSV to load

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

### Update store from CSV

`ENVIRONMENT=(qa|production) python write_csv_to_redis.py {csvfilename}`

Batch size defaults to 1000. The initial load of >2,000,000 records, using a batch size of 10,000, took around 30 seconds.

For all the options, run:

`python write_csv_to_redis.py -h`

Note that access to the shared prod Redis appears restricted to SASB internal network at writing.

## Troubleshooting

Troubleshooting psycopg "ImportError: no pq wrapper available."

In OSX, if you have a /usr/local/opt/libpq/lib and xcode installed, but get above error when running the app locally, you may need to install the psycopg this way:

```
pip uninstall psycopg
pip install "psycopg[c]"
``
