# Date: 03-26-2024
# Author: Meghan Hutch
# Objective: Prepare images for blast-ct. 
# Specifically, this dataset will add columns for a unique 'id' and  'image' path 
# and will save all scans in batches to facilitate processing by blast-ct

import os

import re
import pandas as pd
import time
from glob import glob
import nibabel as nib

# **Create list of scans to process for blast-ct**
# This function loops through all of the nifti processed images in the
#  specified folder (`nifti_images/`) and appends the full file path. 
print('creating a list of nifti_images/')
start = time.time()

ct_list = []

for root, dirs, files in os.walk("nifti_images"):
    for file in files:
        if file.endswith(".nii"):
             ct_list.append(os.path.join(root, file))

end = time.time()
print((end - start)/60)

# create dataframe
print('converting ct_list to dataframe')
ct_df = pd.DataFrame({'image': ct_list})
print(len(ct_df))

# add unique identifier
print('adding unique identifier `id`')
ct_df['id'] = ct_df.index + 1

ct_df['id'] = ct_df['id'].astype('str')

ct_df['id'] = 'scan_' + ct_df['id'] 

col = ct_df.pop('id')
ct_df.insert(0, 'id', col)

# identify images with a fourth dimension - these will be removed as they causes an error when running blast-ct
# note: this takes a while to run.


print('identifying images with a fourth dimension to remove')
# initiate empty list
to_remove = [] 

for i in ct_df['image']:
    img = nib.load(i)
    img_array = img.get_fdata()
    img_shape = img_array.shape
    if len(img_shape)==4:
        to_remove.append(i)
        print(i)

# remove specified images
print('printing initial number of file paths', len(ct_df))

print('removing images')
ct_df = ct_df[~ct_df['image'].str.contains('|'.join(to_remove))]

print('printing number of images after removing problematic images', len(ct_df))

# save list of files
print('saving list of files')
ct_df.to_csv('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/nifti_file_paths.csv', index = False)

## save datasets in batches -thanks chatgpt :) 
# Create a list to store DataFrames
print('saving scans into batches for blast-ct processing')
dfs = []
# define rows per batch
batch_rows = 1000
# initiate counter
counter = 0

# Loop through every defined batch
for i in range(0, len(ct_df), batch_rows):
    counter = counter + 1
    # Slice the DataFrame to get number of specified rows per batch
    temp_df = ct_df.iloc[i:i+batch_rows]
    temp_df.to_csv(f'data/processed/blast_ct_batches/blast_ct_batch_{counter}.csv', index=False)

print('blast-ct preparation complete')