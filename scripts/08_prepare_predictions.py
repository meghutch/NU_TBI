# Date: 03-30-2024
# Author: Meghan Hutch
# Objective: Clean-up predictions from blast-ct. 
# This script will combine predictions from each batch into one dataframe, combine additional scan information, 
# and calculate number of slices for each image.

import os

import re
from datetime import datetime
import pandas as pd
import numpy as np
import nibabel as nib
import csv
import matplotlib.pyplot as plt
import seaborn as sns

# set working directory
os.chdir('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI')

# set options (this is neccessary for correct file imports/processing)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 200)

# remove whitespace that exists before and after strings to aid in pre-processing
def remove_whitespace(string): 
    processed_string = string.rstrip()
    processed_string = processed_string.lstrip()
    return processed_string

### load in data
print('loading in data')
## list of TBI scans
tbi_scan_list = pd.read_csv('data/processed/tbi_scan_file_paths.csv')

## blast-ct predictions
batch_1 = pd.read_csv('data/processed/blast_ct_predictions/batch_1/predictions/prediction.csv')
batch_2 = pd.read_csv('data/processed/blast_ct_predictions/batch_2/predictions/prediction.csv')
batch_3 = pd.read_csv('data/processed/blast_ct_predictions/batch_3/predictions/prediction.csv')
batch_4 = pd.read_csv('data/processed/blast_ct_predictions/batch_4/predictions/prediction.csv')
batch_5 = pd.read_csv('data/processed/blast_ct_predictions/batch_5/predictions/prediction.csv')
batch_6 = pd.read_csv('data/processed/blast_ct_predictions/batch_6/predictions/prediction.csv')
batch_7 = pd.read_csv('data/processed/blast_ct_predictions/batch_7/predictions/prediction.csv')
batch_8 = pd.read_csv('data/processed/blast_ct_predictions/batch_8/predictions/prediction.csv')
batch_9 = pd.read_csv('data/processed/blast_ct_predictions/batch_9/predictions/prediction.csv')
batch_10 = pd.read_csv('data/processed/blast_ct_predictions/batch_10/predictions/prediction.csv')
batch_11 = pd.read_csv('data/processed/blast_ct_predictions/batch_11/predictions/prediction.csv')
batch_12 = pd.read_csv('data/processed/blast_ct_predictions/batch_12/predictions/prediction.csv')
batch_13 = pd.read_csv('data/processed/blast_ct_predictions/batch_13/predictions/prediction.csv')

# combine prediction batches into one dataframe
print('joining predictions')
predictions = pd.concat([batch_1, batch_2, batch_3, batch_4, batch_5, batch_6, batch_7, batch_8, 
                         batch_9, batch_10, batch_11, batch_12, batch_13])

# delete unneeded dataframes
del batch_1, batch_2, batch_3, batch_4, batch_5, batch_6, batch_7, batch_8, batch_9, batch_10, batch_11, batch_12, batch_13

# abstract folder name from predictions
# this will facilitate joining the unique_study_id to the predictions dataframe
predictions['folder'] = [s.split('/') for s in predictions['image']]
predictions['folder'] = [item[1] for item in predictions['folder']]

# remove white space which causes problems merging
tbi_scan_list['folder'] = tbi_scan_list['folder'].apply(lambda x:remove_whitespace(x))
predictions['image'] = predictions['image'].apply(lambda x:remove_whitespace(x))
predictions['prediction'] = predictions['prediction'].apply(lambda x:remove_whitespace(x))

# merge predictions and tbi_scan_list together to join unique_study_id and folder (scan identifier)
print('merging predictions and tbi_scan_list to join `unique_study_id`')
predictions_ids = pd.merge(predictions, 
                           tbi_scan_list[['unique_study_id', 'folder']].drop_duplicates(),
                           on = ['folder'],
                           how = 'inner')
print(len(predictions_ids))

### add additional scan information
tbi_scans = pd.read_csv('data/processed/20240325_1136_tbi_patients_scans_to_include_all.csv')

### add back report_num_temp
tbi_scans_all_preds = pd.merge(predictions_ids, 
                                tbi_scan_list[['unique_study_id', 'report_num_temp', 'folder']].drop_duplicates(),
                                on = ['unique_study_id', 'folder'],
                                how = 'inner')

## add back additional scan data
tbi_scans_all_preds = pd.merge(tbi_scans_all_preds, 
                                tbi_scans,
                                on = ['unique_study_id', 'report_num_temp'],
                                how = 'inner')

# convert StudyDate_Time_format
tbi_scans_all_preds['StudyDate_Time_format'] = pd.to_datetime(tbi_scans_all_preds['StudyDate_Time_format'])

# Iterate over unique_study_id
for unique_id in tbi_scans_all_preds['unique_study_id'].unique():
    # Filter DataFrame for the current unique_study_id
    subset = tbi_scans_all_preds[tbi_scans_all_preds['unique_study_id'] == unique_id]
    # Apply group numbering within each unique_study_id
    tbi_scans_all_preds.loc[subset.index, 'scan_number'] = subset.sort_values(['StudyDate_Time_format', 'folder']).groupby(['StudyDate_Time_format', 'folder']).ngroup(ascending = True) + 1

# create a function that will allow me to count number of slices easily for all images
# note: a few ids repeat due to what looks like duplicates vna accession numbers.
def slice_number(dataframe, i):
    scan = dataframe.iloc[[i]]
    prediction_path = scan['prediction'].to_string(index=False).lstrip()
    image = nib.load(prediction_path)
    slice_num = image.shape[2]
    df = pd.DataFrame({'unique_study_id': scan['unique_study_id'], 
                    'slice_num': slice_num, 
                    'image': scan['image'], 
                    'prediction': scan['prediction']})
    return(df)

# create empty dataframe to collect slice_num 
slice_df = pd.DataFrame({'unique_study_id': [], 'slice_num': [], 'image': []})

for i in range(0, len(tbi_scans_all_preds)):
    df = slice_number(tbi_scans_all_preds, i)
    slice_df = slice_df.append(df)

print('check that length of tbi_scans_all_preds is equal to slice_df', len(tbi_scans_all_preds) == len(slice_df))

# merge slice_num with the rest of the scan information
tbi_scans_all_preds = pd.merge(tbi_scans_all_preds,
                               slice_df,
                               how = 'inner')

# save prepared_predictions for further processing
tbi_scans_all_preds.to_csv('data/processed/prepped_predictions_v2.csv', index = False)