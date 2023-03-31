import os
import sys
import pickle
import requests
import pandas as pd
from Google import Create_Service

#--------------------------------------------------------------#
#---------------------------- INIT ----------------------------#
#--------------------------------------------------------------#

# Get the files directory, given in parameter
INPUT_DIR = "./inputs/" + sys.argv[1]
OUTPUT_DIR = "./outputs/"
OUTPUT_BAD_DATE_LOG = os.path.join(OUTPUT_DIR, "output_bad_date.log")
OUTPUT_BAD_FORMAT_LOG = os.path.join(OUTPUT_DIR, "output_bad_format.log")
OUTPUT_DATAS = os.path.join(OUTPUT_DIR, "output.csv")
OUTPUT_VIDEO_LOG = os.path.join(OUTPUT_DIR, "output_video.log")
PROCESS_LOG = os.path.join(OUTPUT_DIR, "processing.log")
# extensions compatibles google photos
EXTENSIONS_PHOTO = ["BMP", "GIF", "HEIC", "ICO", "JPG", "PNG", "TIFF", "WEBP", "RAW", "JPEG"]
EXTENSIONS_VIDEO = ["3GP", "3G2", "ASF", "AVI", "DIVX", "M2T", "M2TS", "M4V", "MKV", "MMV", "MOD", "MOV", "MP4", "MPG", "MTS", "TOD", "WMV"]


CLIENT_SECRET_FILE = 'client_secret.json'
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES =['https://www.googleapis.com/auth/photoslibrary']

NBR_FILES_PER_REQUEST = 40


# READ DATAS
df = pd.read_csv(OUTPUT_DATAS)


# PREPARE DATAS
if "response" in df.columns:
    # remove rows with response
    df = df[df["response"] == ""]
else:
    df["response"] = ""
df["description"] = df["description"].fillna("")
df["description"] = df["description"].astype(str)


# PREPARE UPLOAD
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
print(dir(service))

upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
token = pickle.load(open('token_photoslibrary_v1.pickle', 'rb'))

headers = {
    'Authorization': 'Bearer ' + token.token,
    'Content-type': 'application/octet-stream',
    'X-Goog-Upload-Protocol': 'raw'
}

#--------------------------------------------------------------#
#---------------------------- FUNC ----------------------------#
#--------------------------------------------------------------#


def upload_file(row):
    image_file = "./" + row["url"]
    image_name = image_file.split("/")[-1]

    headers['X-Goog-Upload-File-Name'] = image_name

    with open(image_file, 'rb') as f:
        data = f.read()
        f.close()
    row["response"] = requests.post(upload_url, data=data, headers=headers)
    if row["response"].status_code != 200:
        print("Error uploading file: " + image_name)
        print(row["response"].content)
        sys.exit(1)


def upload_files(df):
    for index, row in df.iterrows():
        upload_file(row)

#--------------------------------------------------------------#
#---------------------------- MAIN ----------------------------#
#--------------------------------------------------------------#


# CREATE ALL ALBUMS
# get all albums in df (only once)
albums = df["album"].unique()
# get all albums in google photos
existing_albums = service.albums().list().execute()
for album in albums:
    # check if album exists
    if album in existing_albums:
        continue
    request_body = {
        'album': {
            'title': album
        }
    }
    response = service.albums().create(body=request_body).execute()
    print(response)
    # TODO: save album id

ddf = pd.DataFrame()
for i in range(0, len(df), NBR_FILES_PER_REQUEST):
    ddf = df.iloc[i:i+NBR_FILES_PER_REQUEST]
    upload_files(ddf)
    request_body  = {
        "albumId": "**********************",
        'newMediaItems': [
            {
                'description': row["description"],
                'simpleMediaItem': {
                    'uploadToken': row["response"].content.decode('utf-8')
                }
            } for index, row in ddf.iterrows()
        ]
    }

    upload_response = service.mediaItems().batchCreate(body=request_body).execute()
    print(upload_response)
