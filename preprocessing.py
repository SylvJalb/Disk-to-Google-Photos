import os
import sys
import time
from PIL import Image
import piexif
import shutil

# Get the files directory, given in parameter
INPUT_DIR = "./input/" + sys.argv[1]
OUTPUT_DIR = "./outputs/"
OUTPUT_FILES_DIR = os.path.join(OUTPUT_DIR, "preprocessed_files")
OUTPUT_BAD_DATE_LOG = os.path.join(OUTPUT_DIR, "output_bad_date.csv")
OUTPUT_BAD_FORMAT_LOG = os.path.join(OUTPUT_DIR, "output_bad_format.csv")
OUTPUT_DATAS = os.path.join(OUTPUT_DIR, "output.csv")
OUTPUT_VIDEO_LOG = os.path.join(OUTPUT_DIR, "output_video.csv")
OUTPUT_ERROR_LOG = os.path.join(OUTPUT_DIR, "output_error.csv")
# extensions compatibles google photos
EXTENSIONS_PHOTO = ["BMP", "GIF", "HEIC", "ICO", "JPG", "PNG", "TIFF", "WEBP", "RAW", "JPEG"]
EXTENSIONS_VIDEO = ["3GP", "3G2", "ASF", "AVI", "DIVX", "M2T", "M2TS", "M4V", "MKV", "MMV", "MOD", "MOV", "MP4", "MPG", "MTS", "TOD", "WMV"]

# create output directory if not exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
if not os.path.exists(OUTPUT_FILES_DIR):
    os.makedirs(OUTPUT_FILES_DIR)

def check_format(path):
    extension = path.split(".")[-1].upper()
    if extension in EXTENSIONS_PHOTO:
        return "photo"
    elif extension in EXTENSIONS_VIDEO:
        return "video"
    else:
        return "other"

def set_date_photo(path, new_path, last_date):
    annee = path.split(" - ")[0][-4:]
    date_creation = None

    # open file
    img = Image.open(path)
    
    # get date creation
    date_creation = img.info.get("date_original")
    if date_creation is None or date_creation == "0000:00:00 00:00:00":
        date_creation = img.info.get("date_digitized")
        if date_creation is None or date_creation == "0000:00:00 00:00:00":
            date_creation = img.info.get("date_created")
            if date_creation == "0000:00:00 00:00:00":
                date_creation = None
    if date_creation is None and os.path.getmtime(path) is not None:
        date_creation = os.path.getmtime(path)
        if date_creation is None and os.path.getctime(path) is not None:
            date_creation = os.path.getctime(path)
            if date_creation is None and os.path.getatime(path) is not None:
                date_creation = os.path.getatime(path)
        if date_creation is not None:
            date_creation = time.strftime("%Y:%m:%d %H:%M:%S", time.gmtime(date_creation))
    # get year of date_creation
    year = date_creation.split(":")[0]
    # CHECK YEAR
    if year != annee:
        log_msg = ""
        # set date at the last date if it is set
        if last_date.split(":")[0] == annee:
            date_creation = last_date
            log_msg = year + " != " + annee + "\t|\tSET TO LAST DATE"
        else:
            date_creation = annee + ":01:01 12:01:01"
            log_msg = year + " != " + annee + "\t|\tSET TO " + date_creation
        # write log
        with open(OUTPUT_BAD_DATE_LOG, 'a') as f:
            f.write(path + "\n" + new_path + "\n\t" + log_msg + "\n\n")

    exif_dict = piexif.load(path)
    # set date_creation
    exif_dict["0th"][piexif.ImageIFD.DateTime] = date_creation
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_creation
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_creation

    return date_creation

def save_file(path, album, id, last_date, description = ""):
    date = None
    new_file_name = str(id) + "." + path.split(".")[-1]
    new_path = OUTPUT_FILES_DIR + "/" + new_file_name
    # check format
    format = check_format(path)
    if format == "photo":
        # check date
        date = set_date_photo(path, new_path, last_date)
    elif format == "video":
        # write log
        with open(OUTPUT_VIDEO_LOG, 'a') as f:
            f.write(path + "\n\t" + album + "\n\t" + description + "\n\n")
    if format == "other":
        # write log
        with open(OUTPUT_BAD_FORMAT_LOG, 'a') as f:
            f.write(path + "\n\t" + album + "\n\t" + description + "\n\n")
    else :
        # copy file
        try:
            shutil.copy2(path, new_path)
        except:
            # write log
            with open(OUTPUT_ERROR_LOG, 'a') as f:
                f.write(path + "\n\t" + album + "\n\t" + description + "\n\n")
        # write in OUTPUT_DATAS csv file
        with open(OUTPUT_DATAS, 'a') as f:
            f.write(str(id) + ";" + album + ";" + new_file_name + ";" + path + ";" + new_path + ";" + description + ";" + date)
    return date

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