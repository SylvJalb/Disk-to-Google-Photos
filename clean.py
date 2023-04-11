import os
import sys
import pandas as pd

#--------------------------------------------------------------#
#---------------------------- INIT ----------------------------#
#--------------------------------------------------------------#

# Get the files directory, given in parameter
INPUT_DIR = "./inputs/" + sys.argv[1]
OUTPUT_DIR = "./outputs/"
OUTPUT_UPLOAD_CSV = os.path.join(OUTPUT_DIR, "output_upload.csv")



#--------------------------------------------------------------#
#---------------------------- MAIN ----------------------------#
#--------------------------------------------------------------#

if os.path.exists(OUTPUT_UPLOAD_CSV):
    # Read the csv file
    df = pd.read_csv(OUTPUT_UPLOAD_CSV, sep=";")

    # Get the list of files to remove
    files_to_remove = df["path"].tolist()

    # Remove the files
    for path in files_to_remove:
        if path != "" and os.path.exists(path):
            os.remove(path)

# Remove empty folders
for root, dirs, files in os.walk(INPUT_DIR, topdown=False):
    for name in dirs:
        if len(os.listdir(os.path.join(root, name))) == 0:
            os.rmdir(os.path.join(root, name))

print("Done")