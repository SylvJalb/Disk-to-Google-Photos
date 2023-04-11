import os
import sys
import time
import filedate
import datetime
import piexif

#--------------------------------------------------------------#
#---------------------------- INIT ----------------------------#
#--------------------------------------------------------------#

# Get the files directory, given in parameter
INPUT_DIR = "./inputs/" + sys.argv[1]
OUTPUT_DIR = "./outputs/"
OUTPUT_BAD_DATE_LOG = os.path.join(OUTPUT_DIR, "output_bad_date.log")
OUTPUT_BAD_DATE_DATAS = os.path.join(OUTPUT_DIR, "output_bad_date.csv")
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
if os.path.exists(OUTPUT_BAD_DATE_DATAS):
    os.remove(OUTPUT_BAD_DATE_DATAS)
if os.path.exists(OUTPUT_BAD_FORMAT_LOG):
    os.remove(OUTPUT_BAD_FORMAT_LOG)
if os.path.exists(OUTPUT_DATAS):
    os.remove(OUTPUT_DATAS)
if os.path.exists(OUTPUT_VIDEO_LOG):
    os.remove(OUTPUT_VIDEO_LOG)
if os.path.exists(PROCESS_LOG):
    os.remove(PROCESS_LOG)

# Write headers
with open(OUTPUT_DATAS, "a") as f:
    f.write("path;album;description;date\n")
with open(OUTPUT_BAD_DATE_DATAS, "a") as f:
    f.write("path;album;bad_date;new_date\n")

#--------------------------------------------------------------#
#---------------------------- FUNC ----------------------------#
#--------------------------------------------------------------#

def get_date(path, last_date, album):
    annee = album[:4]
    date_creation = os.path.getmtime(path)

    if date_creation is not None:
        date_creation = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(date_creation))

    # get year of date_creation
    year = date_creation.split("-")[0]
    # CHECK YEAR
    if year != annee:
        bad_date_creation = date_creation
        log_msg = ""
        # set date at the last date if it is set
        if last_date and last_date.split("-")[0] == annee:
            date_creation = last_date
            log_msg = year + " != " + annee + "\t|\tSET TO " + date_creation + "(LAST DATE)"
        else:
            if album[4] == " ":
                date_creation = annee + "-01-01 23:01:01"
            elif album[4] == "-":
                date_creation = album[:6] + "-01 23:01:01"
            else:
                print("ERROR: album name not valid -> " + album)
                sys.exit(1)
            log_msg = year + " != " + annee + "\t|\tSET TO " + date_creation
        # write log
        with open(OUTPUT_BAD_DATE_LOG, 'a') as f:
            f.write(path + "\n\t" + log_msg + "\n\n")
        # write csv bad date
        with open(OUTPUT_BAD_DATE_DATAS, 'a') as f:
            f.write(path + ";" + album + ";" + bad_date_creation + ";" + date_creation + "\n")

    return date_creation

def set_date(path, date):
    date_creation = os.path.getmtime(path)
    if date_creation is not None:
        date_creation = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(date_creation))
    
    if date_creation != date:
        new_date = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        # set date
        if path.split(".")[-1].upper() in EXTENSIONS_PHOTO:
            exif_dict = piexif.load(path)
            # set date_creation
            exif_dict["0th"][piexif.ImageIFD.DateTime] = new_date.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = new_date.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = new_date.strftime("%Y:%m:%d %H:%M:%S")
            # save exif
            piexif.insert(piexif.dump(exif_dict), path)
        file_date = filedate.File(path)
        file_date.set(
            created = new_date.strftime("%Y.%m.%d %H:%M:%S"),
            modified = new_date.strftime("%Y.%m.%d %H:%M:%S"),
            accessed = new_date.strftime("%Y.%m.%d %H:%M:%S")
        )


def save_file(path, album, last_date, description = ""):
    date = None
    extension = path.split(".")[-1].upper()
    if extension in EXTENSIONS_PHOTO or extension in EXTENSIONS_VIDEO:
        # check date
        date = get_date(path, last_date, album)
        set_date(path, date)
        # write infos in the data file
        with open(OUTPUT_DATAS, 'a') as f:
            f.write(path + ";" + album + ";" + description + ";" + date + "\n")
        return date
    else:
        # remove file
        os.remove(path)
        # write log
        with open(OUTPUT_BAD_FORMAT_LOG, 'a') as f:
            f.write(path + "\n\t" + album + "\n\t" + description + "\n\n")
        return last_date


#--------------------------------------------------------------#
#---------------------------- MAIN ----------------------------#
#--------------------------------------------------------------#

# get albums in the input directory
albums = []
for elt in os.listdir(INPUT_DIR):
    albums.append(elt)

# order folder by number asc
albums.sort(key=lambda x: int(x[:4]))

last_date = "0000-00-00 00:00:00"

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