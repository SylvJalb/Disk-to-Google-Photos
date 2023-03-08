import os
import sys
import time
from PIL import Image
import piexif
import shutil

# Get the files directory, given in parameter
INPUT_DIR = "./input/" + sys.argv[1]
OUTPUT_DIR = "./outputs/Photos_processed/"
OUTPUT_BAD_DATE_FILE = "./outputs/output_bad_date.csv"
OUTPUT_BAD_FORMAT_FILE = "./outputs/output_bad_format.csv"
OUTPUT_CSV_FILE = "./outputs/output.csv"
OUTPUT_VIDEO_FILE = "./outputs/output_video.csv"
OUTPUT_ERROR_FILE = "./outputs/output_error.csv"
# extensions compatibles google photos
EXTENSIONS_PHOTO = ["BMP", "GIF", "HEIC", "ICO", "JPG", "PNG", "TIFF", "WEBP", "RAW", "JPEG"]
EXTENSIONS_VIDEO = ["3GP", "3G2", "ASF", "AVI", "DIVX", "M2T", "M2TS", "M4V", "MKV", "MMV", "MOD", "MOV", "MP4", "MPG", "MTS", "TOD", "WMV"]

def check_format(url_file):
    extension = url_file.split(".")[-1].upper()
    if extension in EXTENSIONS_PHOTO:
        return "photo"
    elif extension in EXTENSIONS_VIDEO:
        return "video"
    else:
        return "other"

def set_date_photo(url_file, url_new_file, last_date):
    annee = url_file.split(" - ")[0][-4:]
    date_creation = None

    # open file
    img = Image.open(url_file)
    
    # get date creation
    date_creation = img.info.get("date_original")
    if date_creation is None or date_creation == "0000:00:00 00:00:00":
        date_creation = img.info.get("date_digitized")
        if date_creation is None or date_creation == "0000:00:00 00:00:00":
            date_creation = img.info.get("date_created")
            if date_creation == "0000:00:00 00:00:00":
                date_creation = None
    if date_creation is None and os.path.getmtime(url_file) is not None:
        date_creation = os.path.getmtime(url_file)
        if date_creation is None and os.path.getctime(url_file) is not None:
            date_creation = os.path.getctime(url_file)
            if date_creation is None and os.path.getatime(url_file) is not None:
                date_creation = os.path.getatime(url_file)
        if date_creation is not None:
            date_creation = time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(date_creation))
    # get year of date_creation
    year = date_creation.split(":")[0]
    # CHECK YEAR
    if year != annee:
        print("\t\t\t/!\ BAD YEAR -> " + year + " != " + annee)
        # set date at the last date if it is set
        if last_date.split(":")[0] == annee:
            date_creation = last_date
            print("\t\t\t\tSET TO LAST DATE")
        else:
            date_creation = annee + ":01:01 12:01:01"
            print("\t\t\t\t/!\ NO LAST DATE")

        # write in output_bad_date file
        with open(OUTPUT_BAD_DATE_FILE, 'a') as f:
            f.write(url_new_file + "  ->  " + date_creation + "\n")
    
    print("\t\t\tdate_creation: " + date_creation)

    exif_dict = piexif.load(url_file)
    # set date_creation
    exif_dict["0th"][piexif.ImageIFD.DateTime] = date_creation
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_creation
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_creation

    return date_creation

set_date_photo("./inputs/photos/.../name.jpg", OUTPUT_DIR, "")

def save_file(path, album, description = ""):
    # check format
    # check date
    # save file
    # write in output_csv file

albums = []
# parcour du dossier Photos
for elt in os.listdir(INPUT_DIR):
    albums.append(elt)
# order folder by number asc
albums.sort(key=lambda x: int(x[:4]))

for album in albums:
    print("Album : " + album)
    # parcour du dossier album
    for elt in os.listdir(INPUT_DIR + "/" + album):
        # si c'est un fichier
        if os.path.isfile(INPUT_DIR + "/" + album + "/" + elt):
            # save file
            save_file(INPUT_DIR + "/" + album + "/" + elt, album)
        # si c'est un dossier
        else:
            for elt_elt in os.listdir(INPUT_DIR + "/" + album + "/" + elt):
                # si c'est un fichier
                if os.path.isfile(INPUT_DIR + "/" + album + "/" + elt + "/" + elt_elt):
                    # save file
                    save_file(INPUT_DIR + "/" + album + "/" + elt + "/" + elt_elt, album, elt)