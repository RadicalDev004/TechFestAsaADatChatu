from datetime import timedelta
import firebase_admin
from firebase_admin import credentials, storage
from datetime import timezone
from zoneinfo import ZoneInfo


cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'techfestproj.firebasestorage.app'
})

bucket = storage.bucket()

def upload_to_firebase(id, file):
    blob = bucket.blob(f"{id}/{file.filename}")
    blob.upload_from_file(file.file, content_type=file.content_type)
    from Database.firebaseIngest import ingest_clinic_from_firebase
    ingest_clinic_from_firebase(id)

def download_from_firebase(id, file_name):
    blob = bucket.blob(f"{id}/{file_name}")
    blob.download_to_filename(file_name)

def get_download_url(id, file_name):
    blob = bucket.blob(f"{id}/{file_name}")
    return blob.generate_signed_url(version="v4", expiration=timedelta(minutes=15), method="GET")

def download_all_from_firebase(id, local_dir):
    blobs = bucket.list_blobs(prefix=f"{id}/")
    for blob in blobs:
        file_name = blob.name.split('/')[-1]
        blob.download_to_filename(f"{local_dir}/{file_name}")

def list_files_from_firebase(id):
    blobs_iter = bucket.list_blobs(prefix=f"{id}/")
    out = []
    for blob in blobs_iter:
        dt = blob.updated
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        out.append({
            "name": blob.name,
            "size": blob.size,
            "updated": dt.astimezone(ZoneInfo("Europe/Bucharest")) if dt else None 
        })
    #print(id)
    #print(out)
    return out
  
def delete_from_firebase(id: str, file_name: str) -> bool:
    if not file_name or "/" in file_name or "\\" in file_name:
        raise ValueError("Invalid file name")

    blob = bucket.blob(f"{id}/{file_name}")
    if not blob.exists():
        return False
    blob.delete()
    return True

