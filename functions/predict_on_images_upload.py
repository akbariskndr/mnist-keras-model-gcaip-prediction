import json
import os
from google.cloud import storage
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery

GOOGLE_CLOUD_PROJECT = 'your-google-cloud-project-name'
BUCKET = "your-storage-bucket-name"
MODEL_NAME = 'MNIST'
MODEL_VERSION = 'v1'
MODEL_PATH = f"projects/{GOOGLE_CLOUD_PROJECT}/models/{MODEL_NAME}"

def predict(imgfiles):
    credentials = GoogleCredentials.get_application_default()
    service = discovery.build(
        'ml', MODEL_VERSION, credentials=credentials, cache_discovery=False
    )

    response = service.projects().predict(
        name=MODEL_PATH,
        body={'instances': imgfiles}
    ).execute()

    return response

def save_to_bucket(filename, prediction_result):
    client = storage.Client()
    jsonfilename = f"{filename}-result.json"
    json.dump(prediction_result, open(f"/tmp/{jsonfilename}", 'w'))

    bucket = client.bucket(BUCKET)
    blob = bucket.blob(f"json/{jsonfilename}")

    blob.upload_from_filename(f"/tmp/{jsonfilename}")

def listener(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    file = event
    is_image = "images" in file["name"] and (".jpg" in file["name"] or ".png" in file["name"])
    if not is_image:
        return

    imgfiles = [f"gs://{BUCKET}/{file['name']}"]
    result = predict(imgfiles)

    filename = file['name'].split('/')[-1].split('.')[0]
    save_to_bucket(filename, result)