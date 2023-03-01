### M2 Customer Code Store

This app contains:

1. Redis client
2. Lightweight API for getting customer codes
3. A script for uploading customer codes to the Redis Elasticache

## Config

all this app requires is the kms-encrypted Redis endpoint.

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
“data”: [
{
“barcode”: “1234”,
“m2CustomerCode”: “NX”
}
]
}}
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
## Loading data to the store

### Creating CSV to upload

This script expects a csv generated following the procedure discussed here:

The “Barcodes by CUS/DATE” report is the best way to extract customer codes and barcodes from LAS. This is the report we should use to populate the M2 Customer Code Store.

From Phill Mui:
For the complete list of all the item barcodes and customer codes, I would suggest to try Reports --> Export Item Barcodes --> Export Item Barcodes --> Export Barcodes by CUS/DATE

For that report, you should be able to gather the entire list of item barcodes according to which customer codes they belong to. If you do not want to work with files that are too massive though, I would suggest to run yearly report instead. As for incremental updates as my team accession more materials, we should definitely have a conversation about that to see if I can assist you with that considering I mainly deal with newly accessioned materials every night.

That should produce a file with the complete set of barcodes and customer codes for items in M2, including columns:
Item barcode
Accession date
Customer code
Delete date

## Script to upload

`python write_csv_to_redis {csvfilename} {batchsize}`
Batch size defaults to 100. The initial load of >2,000,000 records, using a batch size of 10,000, took around 30 seconds.
