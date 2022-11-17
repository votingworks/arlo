import os
import random
import shutil
import tempfile
from typing import BinaryIO, Dict, Iterable
import uuid

# Input data from the client

chunks = [
    dict(fileName="fileA", chunkNumber=1, chunkContents=b"chunkA1\n",),
    dict(fileName="fileA", chunkNumber=2, chunkContents=b"chunkA2\n",),
    dict(fileName="fileB", chunkNumber=1, chunkContents=b"chunkB1\n",),
    dict(fileName="fileB", chunkNumber=2, chunkContents=b"chunkB2\n",),
    dict(fileName="fileB", chunkNumber=3, chunkContents=b"chunkB3\n",),
]
random.shuffle(chunks)

chunked_upload_id = str(uuid.uuid4())


# Overall approach:
# For each file we want to upload:
# 1. Upload each chunk to a separate file
# 2. When we're done uploading all the chunks, concatenate the chunks into a single file
# 3. Open the concatenated file as a file stream
#
# Note that this allows the chunks to be uploaded in any order (or even in parallel).


def chunked_upload_dir_path(chunked_upload_id: str):
    tempdir_path = tempfile.gettempdir()
    return os.path.join(tempdir_path, chunked_upload_id)


# Handle one chunk upload (this would be one API endpoint)
def upload_chunk(chunked_upload_id: str, chunk):
    # Store each chunk in a separate file
    # /tmp/<chunked_upload_id>/<file_name>/<chunk_number>
    file_dir_path = os.path.join(
        chunked_upload_dir_path(chunked_upload_id), chunk["fileName"]
    )
    os.makedirs(file_dir_path, exist_ok=True)
    chunk_path = os.path.join(file_dir_path, str(chunk["chunkNumber"]))
    print("Uploading", chunk_path)
    with open(chunk_path, "wb") as chunk_file:
        chunk_file.write(chunk["chunkContents"])


# Concatenate a list of files into a single file on disk
def concatenate_files(file_names: Iterable[str], output_path: str):
    with open(output_path, "wb") as output_file:
        for file_name in file_names:
            with open(file_name, "rb") as input_file:
                output_file.write(input_file.read())


# Open the files from a chunked upload as a dict of file_name -> file_stream
# This matches the format of how we load files from Flask's request.files
def open_chunked_upload_files(chunked_upload_id: str) -> Dict[str, BinaryIO]:
    upload_dir_path = chunked_upload_dir_path(chunked_upload_id)
    files = {}
    for file_dir in os.scandir(upload_dir_path):
        # Sort the chunks by name *as numbers*
        chunk_file_names = sorted(os.listdir(file_dir.path), key=int)
        chunk_file_paths = [
            os.path.join(file_dir.path, chunk_file_name)
            for chunk_file_name in chunk_file_names
        ]
        concatenated_file_path = os.path.join(file_dir.path, "concatenated")
        concatenate_files(chunk_file_paths, concatenated_file_path)
        files[file_dir.name] = open(concatenated_file_path, "rb")
    return files


def read_uploaded_files(chunked_upload_id: str):
    for file_name, file_stream in open_chunked_upload_files(chunked_upload_id).items():
        print(f"Reading file {file_name}")
        print(file_stream.read())
    shutil.rmtree(chunked_upload_dir_path(chunked_upload_id))


# Simulate uploading the chunks
for chunk in chunks:
    upload_chunk(chunked_upload_id, chunk)

# After all the chunks are uploaded, the client would make a separate request to
# say that it's done, at which point we'd read the uploaded chunks, zip them,
# and proceed with our existing file processing pipeline
read_uploaded_files(chunked_upload_id)

