import os
import sys
import time
from PIL import Image
import piexif

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

# create output directory if not exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# clear output files if exist
if os.path.exists(OUTPUT_BAD_DATE_LOG):
    os.remove(OUTPUT_BAD_DATE_LOG)
if os.path.exists(OUTPUT_BAD_FORMAT_LOG):
    os.remove(OUTPUT_BAD_FORMAT_LOG)
if os.path.exists(OUTPUT_DATAS):
    os.remove(OUTPUT_DATAS)
if os.path.exists(OUTPUT_VIDEO_LOG):
    os.remove(OUTPUT_VIDEO_LOG)
if os.path.exists(PROCESS_LOG):
    os.remove(PROCESS_LOG)

# Write header in OUTPUT_DATAS file
with open(OUTPUT_DATAS, "a") as f:
    f.write("path;album;description;date\n")

#--------------------------------------------------------------#
#---------------------------- FUNC ----------------------------#
#--------------------------------------------------------------#

def check_format(path):
    extension = path.split(".")[-1].upper()
    if extension in EXTENSIONS_PHOTO:
        return "photo"
    elif extension in EXTENSIONS_VIDEO:
        return "video"
    else:
        return "other"

def set_date(path, last_date, album, isPhoto):
    annee = album[:4]
    date_creation = None

    if isPhoto:
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
        if last_date and last_date.split(":")[0] == annee:
            date_creation = last_date
            log_msg = year + " != " + annee + "\t|\tSET TO LAST DATE"
        else:
            date_creation = annee + ":01:01 12:01:01"
            log_msg = year + " != " + annee + "\t|\tSET TO " + date_creation
        # write log
        with open(OUTPUT_BAD_DATE_LOG, 'a') as f:
            f.write(path + "\n\t" + log_msg + "\n\n")

    if isPhoto:
        exif_dict = piexif.load(path)
        # set date_creation
        exif_dict["0th"][piexif.ImageIFD.DateTime] = date_creation
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_creation
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_creation

    return date_creation

def save_file(path, album, last_date, description = ""):
    date = None
    # check format
    format = check_format(path)
    if format == "photo":
        # check date
        date = set_date(path, last_date, album, True)
    elif format == "video":
        # check date
        date = set_date(path, last_date, album, False)
        # write log
        with open(OUTPUT_VIDEO_LOG, 'a') as f:
            f.write(path + "\n\t" + album + "\n\t" + description + "\n\n")
    if format == "other":
        # write log
        with open(OUTPUT_BAD_FORMAT_LOG, 'a') as f:
            f.write(path + "\n\t" + album + "\n\t" + description + "\n\n")
    else :
        # write infos in the data file
        with open(OUTPUT_DATAS, 'a') as f:
            f.write(path + ";" + album + ";" + description + ";" + date + "\n")
    return date


#--------------------------------------------------------------#
#---------------------------- MAIN ----------------------------#
#--------------------------------------------------------------#

# get albums in the input directory
albums = []
for elt in os.listdir(INPUT_DIR):
    albums.append(elt)

# order folder by number asc
albums.sort(key=lambda x: int(x[:4]))

last_date = "0000:00:00 00:00:00"

for index, album in enumerate(albums):
    with open(PROCESS_LOG, 'a') as log:
        log.write("Processing \"" + album + "\" -> " + str(index + 1) + "/" + str(len(albums)) + " ...\n")
        album_path = os.path.join(INPUT_DIR, album)
        number_of_files = sum([len(files) for r, d, files in os.walk(album_path)])
        counter = 1
        # parcour du dossier album
        for elt in os.listdir(album_path):
            elt_path = os.path.join(album_path, elt)
            # si c'est un fichier
            if os.path.isfile(elt_path):
                log.write("\tProcessing \"" + album + "\" -> " + str(index + 1) + "/" + str(len(albums)) + " ... " + str(counter) + "/" + str(number_of_files) + "\n")
                # save file
                last_date = save_file(elt_path, album, last_date)
                counter += 1
            # si c'est un dossier
            else:
                for elt_elt in os.listdir(elt_path):
                    elt_elt_path = os.path.join(elt_path, elt_elt)
                    # si c'est un fichier
                    if os.path.isfile(elt_elt_path):
                        log.write("\tProcessing \"" + album + "\" -> " + str(index + 1) + "/" + str(len(albums)) + " ... " + str(counter) + "/" + str(number_of_files) + "\n")
                        # save file
                        last_date = save_file(elt_elt_path, album, last_date, elt)
                        counter += 1