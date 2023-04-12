import os
import sys
import pickle
import requests
import pandas as pd
import time
from Google import Create_Service

#--------------------------------------------------------------#
#---------------------------- INIT ----------------------------#
#--------------------------------------------------------------#

# Get the files directory, given in parameter
OUTPUT_DIR = "./outputs/"
OUTPUT_ALBUM_CSV = os.path.join(OUTPUT_DIR, "album_list.csv")


NUMBER_OF_REQUESTS_PER_MINUTE = 28

CLIENT_SECRET_FILE = 'client_secret.json'
API_NAME = 'photoslibrary'
API_VERSION = 'v1'
SCOPES =['https://www.googleapis.com/auth/photoslibrary']

# PREPARE REQUESTS
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

starting_time = time.time()
request_count = 0

#--------------------------------------------------------------#
#---------------------------- FUNC ----------------------------#
#--------------------------------------------------------------#

def check_quota():
    global request_count
    global starting_time
    request_count += 1
    if request_count >= NUMBER_OF_REQUESTS_PER_MINUTE:
        if time.time() - starting_time < 45:
            print("Waiting 70 seconds to avoid quota limit...")
            time.sleep(70)
            print("Continue !")
        starting_time = time.time()
        request_count = 0


#--------------------------------------------------------------#
#---------------------------- MAIN ----------------------------#
#--------------------------------------------------------------#

albums_next = service.albums().list().execute()
albums = albums_next["albums"].copy()
while True:
    if "nextPageToken" in albums_next:
        albums_next = service.albums().list(pageToken=albums_next["nextPageToken"]).execute()
        albums += albums_next["albums"]
    else:
        break
    check_quota()
albums = [{'title': album["title"], 'id': album["id"], 'number_of_media_items': (int(album["mediaItemsCount"]) if album.get("mediaItemsCount") else 0)} for album in albums]

# Order by title
albums = sorted(albums, key=lambda k: k['title'])
albums = pd.DataFrame(albums)
non_empty_albums = albums[albums["number_of_media_items"] > 0]
print("Number of albums: {}".format(len(albums)))
print("Number of non-empty albums: {}".format(len(non_empty_albums)))
# get non-empty albums with same title
same_title_albums = non_empty_albums[non_empty_albums.duplicated(subset=["title"], keep=False)]
if len(same_title_albums) > 0:
    print("\n/!\ WARNING: You have non-empty albums with same title :")
    print("Number of non-empty albums with same title: {}".format(len(same_title_albums)))
    print("\nList of non-empty albums with same title :\n")
    for album in same_title_albums.to_dict("records"):
        print(album["title"] + " (" + str(album["number_of_media_items"]) + " items)")


# create output directory if not exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
# Save to csv
albums.to_csv(OUTPUT_ALBUM_CSV, index=False)

print("Done !")
