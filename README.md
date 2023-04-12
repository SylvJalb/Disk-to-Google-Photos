# Disk-to-Google-Photos
Import photos from your Disk to your Google Photos, retaining/creating as much Metadata as possible.

## Why?
I have a lot of photos on my Disk, and I want to upload them to Google Photos. I want to retain as much metadata as possible, and I want to be able to search for photos by location, date, etc.    
I also want to categorize my photos into albums.

## How?
I use the Google Photos API to : 
- upload the photos to Google Photos.
- create albums.
- add photos to albums.

## How to use?
- Create a Google Cloud Platform project.
- Enable the Google Photos Library API.
- Create an OAuth 2.0 Client ID.
- Download the OAuth 2.0 Client ID as a JSON file.
- Rename the JSON file to `client_secret.json` and put it in the root of the project.
- Run `pip install -r requirements.txt` to install the dependencies.
- Put your photos in a folder, and put the folder in the `inputs/` directory (look at the `inputs/example` folder for an example and follow the rules section below).
- Run `python preprocessing.py exemple` to start the script (change `exemple` by the name of your folder).
- You can check output logs if yout want to see errors.
- Run `python upload.py exemple` to start the upload in Google Photos (change `exemple` by the name of your folder).

## Tools
- You can remove uploaded photos running `python clean.py exemple` (change `exemple` by the name of your folder).
- You can look at all your albums in Google Photos running `python list_albums.py` it generate the file `./output/album_list.csv`.

## Rules
- The main folder name (in the `inputs/` directory) have no importance.
- The folders inside the main folder are the albums names. The name have to be unique, and follow the sheme : `YYYY-MM Album name`.  
    (the month `-MM` is optional).
- The photos inside the albums folders will be uploaded to the corresponding album.
- You can put subfolders inside the albums folders. The subfolders names will be the description of the photos inside.

## Warning !
- The script `preprocessing.py` can update metadata of your photos. It can also remove files if the format is not supported by Google Photos.
- The script `clean.py` can remove files and folders from your given folder.