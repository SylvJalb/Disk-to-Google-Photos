import os
import pickle
import requests
import pandas as pd
from Google import Create_Service

directory = "Photos"
output_dir = "Photos_traitees"
output_bad_date_file = "./outputs/output_bad_date.txt"
output_bad_format_file = "./outputs/output_bad_format.txt"
output_video_file = "./outputs/output_video.txt"
output_csv_file = "./outputs/output.csv"
output_error_file = "./outputs/output_error.txt"
# extensions compatibles google photos
extensions_photo = ["BMP", "GIF", "HEIC", "ICO", "JPG", "PNG", "TIFF", "WEBP", "RAW"]
extensions_video = ["3GP", "3G2", "ASF", "AVI", "DIVX", "M2T", "M2TS", "M4V", "MKV", "MMV", "MOD", "MOV", "MP4", "MPG", "MTS", "TOD", "WMV"]


CLIENT_SECRET_FILE = 'code_secret_client.json'
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES =['https://www.googleapis.com/auth/photoslibrary']


service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)
print(dir(service))

# Récupération des données
df = pd.read_csv("./outputs/datas.csv")
df["description"] = df["description"].fillna("")

# step 1: Upload byte data to Google Server

image_dir = os.path.join(os.getcwd(), output_dir)
upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
token = pickle.load(open('token_photoslibrary_v1.pickle', 'rb'))

headers = {
    'Authorization': 'Bearer ' + token.token,
    'Content-type': 'application/octet-stream',
    'X-Goog-Upload-Protocol': 'raw'
}

df["response"] = ""
# if type(df["description"]) != string, convert it to string ""
df["description"] = df["description"].astype(str)


# parcour df 40 rows by 40 rows in dataframes names ddf
ddf = pd.DataFrame()
for i in range(0, len(df), 40):
    ddf = df.iloc[i:i+40]
    for index, row in ddf.iterrows():
        image_file = "./" + row["url"]
        image_name = image_file.split("/")[-1]

        headers['X-Goog-Upload-File-Name'] = image_name

        with open(image_file, 'rb') as f:
            img = f.read()
            f.close()
        row["response"] = requests.post(upload_url, data=img, headers=headers)

    print(ddf)

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
