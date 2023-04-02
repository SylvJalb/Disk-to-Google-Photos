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
OUTPUT_UPLOAD_LOG = os.path.join(OUTPUT_DIR, "output_upload.log")
PROCESS_LOG = os.path.join(OUTPUT_DIR, "processing.log")
# extensions compatibles google photos
EXTENSIONS_PHOTO = ["BMP", "GIF", "HEIC", "ICO", "JPG", "PNG", "TIFF", "WEBP", "RAW", "JPEG"]
EXTENSIONS_VIDEO = ["3GP", "3G2", "ASF", "AVI", "DIVX", "M2T", "M2TS", "M4V", "MKV", "MMV", "MOD", "MOV", "MP4", "MPG", "MTS", "TOD", "WMV"]


CLIENT_SECRET_FILE = 'client_secret.json'
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES =['https://www.googleapis.com/auth/photoslibrary']

MAX_FILES_PER_STEP = 40


# READ DATAS
df = pd.read_csv(OUTPUT_DATAS, sep=";")


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
    image_file = "./" + row["path"]
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
albums_titles = df["album"].unique()
# get all albums in google photos
albums = service.albums().list().execute()
albums = [{'title': album["title"], 'id': album["id"]} for album in albums["albums"]]
# remove albums who not exists in albums_titles
albums = [album for album in albums if album["title"] in albums_titles]
for album_title in albums_titles:
    # check if album exists
    if album_title in [a["title"] for a in albums]:
        print("Album already exists: " + album_title)
        continue
    print("Creating album: " + album_title)
    request_body = {
        'album': {
            'title': album_title
        }
    }
    new_album = service.albums().create(body=request_body).execute()
    # save the new album locally
    albums.append({'title': album_title, 'id': new_album["id"]})


# UPLOAD FILES AND ADD TO ALBUMS
album_df = pd.DataFrame()
for album in albums:
    print("Uploading files for album: " + album["title"])
    # get all files for this album
    album_df = df[df["album"] == album["title"]]
    step_df = pd.DataFrame()
    for i in range(0, len(album_df), MAX_FILES_PER_STEP):
        step_df = album_df.iloc[i:i+MAX_FILES_PER_STEP]
        # upload files
        upload_files(step_df)
        # add files to album
        request_body  = {
            "albumId": album["id"],
            'newMediaItems': [
                {
                    'description': row["description"],
                    'simpleMediaItem': {
                        'uploadToken': row["response"].content.decode('utf-8')
                    }
                } for index, row in step_df.iterrows()
            ]
        }

        response = service.mediaItems().batchCreate(body=request_body).execute()
        print(response)
        for result in response["newMediaItemResults"]:
            if result['status']['message'] != "Success":
                print("Error while uploading file: " + result['mediaItem']['filename'])
                print("\t" + result['status']['message'])
                # Write log in OUTPUT_UPLOAD_LOG file
                with open(OUTPUT_UPLOAD_LOG, "a") as f:
                    f.write("Error while uploading file: " + album + "/" + result['mediaItem']['filename'] + "\n")

