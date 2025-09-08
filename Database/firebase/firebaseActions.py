import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'techfestproj.appspot.com'
})

bucket = storage.bucket()

def upload_to_firebase(id, file_name):
    blob = bucket.blob(f"{id}/{file_name}")
    blob.upload_from_filename(file_name)

def download_from_firebase(id, file_name):
    blob = bucket.blob(f"{id}/{file_name}")
    blob.download_to_filename(file_name)

def download_all_from_firebase(id, local_dir):
    blobs = bucket.list_blobs(prefix=f"{id}/")
    for blob in blobs:
        file_name = blob.name.split('/')[-1]
        blob.download_to_filename(f"{local_dir}/{file_name}")