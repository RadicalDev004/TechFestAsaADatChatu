import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'techfestproj.firebasestorage.app'
})

bucket = storage.bucket()

def upload_to_firebase(id, file):
    blob = bucket.blob(f"{id}/{file.filename}")
    blob.upload_from_file(file.file, content_type=file.content_type)

def download_from_firebase(id, file_name):
    blob = bucket.blob(f"{id}/{file_name}")
    blob.download_to_filename(file_name)

def download_all_from_firebase(id, local_dir):
    blobs = bucket.list_blobs(prefix=f"{id}/")
    for blob in blobs:
        file_name = blob.name.split('/')[-1]
        blob.download_to_filename(f"{local_dir}/{file_name}")

def list_files_from_firebase(id):
    blobs_iter = bucket.list_blobs(prefix=f"{id}/")
    out = []
    for blob in blobs_iter:
        out.append(blob.name)   # e.g. "<id>/filename.pdf"
    return out