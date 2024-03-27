# Date: 03-26-2024
# Author: Meghan Hutch
# Objective: Abstract dicom header from scans

import os

import pandas as pd
from glob import glob
import time
import pydicom
import csv

# import list of scans for TBI cohort
tbi_scan_list = pd.read_csv('data/processed/tbi_scan_file_paths.csv')

# list out all ct scans from the folders identified in tbi_scan_list
file_paths = tbi_scan_list['file_path'].tolist()

# abstract all CT scans from each directory indicated in file_path
print('creating list of CT scans')
start = time.time()

# create empty list to store indiviudal CT scans
image_list = []

# for each directory in file_paths
for i in file_paths:
    # create a list of CT scans from the main folder we want to process
    ct_list = [y for x in os.walk(i) for y in glob(os.path.join(x[0], 'CT.*'))]
    image_list.append(ct_list)

end = time.time()
print('list of CT scans completed in', (end - start)/60, 'minutes')

# the previous for loop created a list of lists
# to collapse we can perform the following nested list comprehension
image_list_collapse = [i for sublist in image_list for i in sublist] 

# separate file paths
data = [s.split('/CT.') for s in image_list_collapse]
data = [item[0] for item in data]
data = list(set(data))

# **Abstract dicom header info**

# The below code will abstract all of the meta-data from the header of each dicom image in our `image_list`. 
# Our code will also save the file_path from `image_list`. 
# Of note, we do not save the pixel data in order to save memory and speed of computational abstraction.
print('abstracting dicom header. this process takes time.')

# https://stackoverflow.com/questions/66640997/write-dicom-header-to-csv
start = time.time()

# initialize counter to create new index for each file processed - this will facilitate the pivot step
counter = 0

with open('data/processed/dicom_header_table.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # define column names
    writer.writerow("file_path Group Elem Description VR value".split())
    
    for i in data:
        #counter = counter + 1
        #print(counter)
        file_dir = i
        first_file = os.listdir(file_dir)[0]
        ds = pydicom.dcmread(file_dir+'/'+first_file)
        
        for elem in ds:
            if elem.description() != 'Pixel Data':
                writer.writerow([
                    # specify values for each column
                    file_dir,
                    f"{elem.tag.group:04X}", f"{elem.tag.element:04X}",
                    elem.description(), elem.VR, str(elem.value)
            ])

end = time.time()
print('dicom header abstracted in', (end - start)/60, 'minutes')

# read in dicom_header_table
dicom_table =  pd.read_csv('data/processed/dicom_header_table.csv')

# pivot table
dicom_table_pivot = dicom_table.pivot(index='file_path', columns='Description', values='value').reset_index()

# save pivoted table
dicom_table_pivot.to_csv('data/processed/dicom_header_table_processed.csv')

print('dicom header abstracted and save is now completed.')