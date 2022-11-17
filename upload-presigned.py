from urllib.parse import urlparse
from server import config
from server.util.file import s3
import requests

bucket_name = urlparse(config.FILE_UPLOAD_STORAGE_PATH).netloc
print(bucket_name)
base_storage_path = "audits/33ed5bdf-2646-4004-b53a-3327d4b55f53/jurisdictions/01b93dc6-831a-44cd-bad5-f6b7da52b7f7"
upload_url = s3().generate_presigned_post(
    bucket_name,
    f"{base_storage_path}/${{filename}}",
    Conditions=[["starts-with", "$key", base_storage_path]],
    ExpiresIn=60 * 10,  # 10 minutes
)
print(upload_url)

with open("test-file.txt", "rb") as file:
    response = requests.post(
        upload_url["url"],
        data=upload_url["fields"],
        files={"file": ("test-file.txt", file)},
    )
print(response.status_code)
print(response.text)

with open("test-file.txt", "rb") as file:
    response = requests.post(
        upload_url["url"],
        data=upload_url["fields"],
        files={"file": ("test-file-2.txt", file)},
    )
print(response.status_code)
print(response.text)
