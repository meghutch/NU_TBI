# Date: 04-03-2024
# Author: Meghan Hutch
# Objective: Filter predictions from blast-ct. 
# This script will select tilt corrected images (if available), remove scans with few or extremely large number of slices, 
# and calculate change in volume overtime. 

import os

import re
from datetime import datetime
import pandas as pd
import numpy as np
import nibabel as nib
import csv
import openpyxl

# set working directory
os.chdir('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI')

# set options (this is neccessary for correct file imports/processing)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 200)

## load data
predictions = pd.read_csv('data/processed/prepped_predictions.csv')
predictions = predictions.drop_duplicates()

# manually remove problematic scan
print('manually removing problematic scan')
print(len(predictions))
predictions = predictions[~(predictions['id']=='scan_5338')]
print(len(predictions))

print('print unique number of patients and images', predictions[['unique_study_id', 'id', 'image']].nunique())

# format the quality_control_metric
# for scans with a missing metric (nan), we will replace with a 0 which is outside of the range (quality_control_metric < 0)
predictions['quality_control_metric'] = predictions['quality_control_metric'].fillna(0) 

## Evaluate differences in patients who have repeated images per session
## patients may have multiple images under the same folder that have different image 'names'
## from review, it looks as though sometimes repeats were taken due to patient motion, artifact, or because radiologist wanted a closer look at some area of the brain

# create new column for image name - this will help us distinguish images from within the same folder
predictions['image_name'] = [s.split('/random/') for s in predictions['image']]
predictions['image_name'] = [item[1] for item in predictions['image_name']]
predictions['image_name'] =  [s.split('/') for s in  predictions['image_name']]
predictions['image_name'] = [item[0] for item in predictions['image_name']]

# remove scans that contain the words 'bone' or 'petro'
predictions = predictions[~predictions['image'].str.contains('bone', case = False)]
predictions = predictions[~predictions['image'].str.contains('petro', case = False)]

# remove h60s images
# h60s look blurry and there is always a corresponding h41 that is more crisp
predictions = predictions[~(predictions['image'].str.contains('h60s', case = False))]

print('print unique number of patients and images', predictions[['unique_study_id', 'id', 'image']].nunique())

# remove scans with < 30 or > 100 slices
predictions = predictions[~((predictions['slice_num'] < 30) | (predictions['slice_num'] >= 100))]

# determine max number of slices for each unique combination
predictions['max_slice'] = predictions.groupby(['unique_study_id', 'scan_number', 'image_name'])['slice_num'].transform('max')

# remove cases where the max_slice number less than 30 for all the images of a specific image type (e.g. 'image_name')
predictions_filtered = predictions[~(predictions['max_slice'] < 30)].copy()

print('print unique number of patients and images', predictions[['unique_study_id', 'id', 'image']].nunique())

# separate by tilt/eq separated to facilitate further pre-processing and evaluation of scans to include
print('separating by tilt/eq corrected vs non-tilt corrected')
tilt_predictions = predictions_filtered[predictions_filtered['image'].str.contains('|'.join(['tilt', '_Eq']), case = False)].drop_duplicates()
non_tilt_predictions = predictions_filtered[~(predictions_filtered['image'].str.contains('|'.join(['tilt', '_Eq']), case = False))].drop_duplicates()

### Evaluate cases when there are multiple images per unique_study_id, image_name, and scan_number
# count number of unique scans per unique_study_id and image
tilt_scan_counts = tilt_predictions.groupby(['unique_study_id', 'image_name', 'scan_number'])['image_name'].count().reset_index(name = 'count').sort_values('count', ascending = False)
non_tilt_scan_counts = non_tilt_predictions.groupby(['unique_study_id', 'image_name', 'scan_number'])['image_name'].count().reset_index(name = 'count').sort_values('count', ascending = False)

### create new dataframe with images that have multiple scans during the same imaging session

## tilt scans
multiple_scans = tilt_scan_counts[tilt_scan_counts['count'] > 1]
one_scan = tilt_scan_counts[tilt_scan_counts['count'] == 1]

tilt_predictions_multiple = pd.merge(tilt_predictions, multiple_scans,
                                     how = 'inner')
tilt_predictions_one = pd.merge(tilt_predictions, one_scan,
                                     how = 'inner')

## non-tilt scans
multiple_scans_non_tilt = non_tilt_scan_counts[non_tilt_scan_counts['count'] > 1]
one_scan_non_tilt = non_tilt_scan_counts[non_tilt_scan_counts['count'] == 1]

non_tilt_predictions_multiple = pd.merge(non_tilt_predictions, multiple_scans_non_tilt,
                                     how = 'inner')
non_tilt_predictions_one = pd.merge(non_tilt_predictions, one_scan_non_tilt,
                                     how = 'inner')

# if multiple scans, we select the one with the lowest (best) quality_control_metric
tilt_predictions_multiple_filtered = tilt_predictions_multiple.loc[tilt_predictions_multiple.groupby(['unique_study_id', 'image_name', 'scan_number'])['quality_control_metric'].idxmin()]
non_tilt_predictions_multiple_filtered = non_tilt_predictions_multiple.loc[non_tilt_predictions_multiple.groupby(['unique_study_id', 'image_name', 'scan_number'])['quality_control_metric'].idxmin()]

## merge back with the single scans
tilt_predictions_filtered = pd.concat([tilt_predictions_one, tilt_predictions_multiple_filtered])
non_tilt_predictions_filtered = pd.concat([non_tilt_predictions_one, non_tilt_predictions_multiple_filtered])

# if there is a tilted version, we will remove from the `non_tilt_predictions_filtered`
non_tilt_predictions_to_filter = pd.merge(non_tilt_predictions_filtered[['unique_study_id', 'report_num_temp', 'scan_number', 'folder', 'image_name']],
                                          tilt_predictions_filtered[['unique_study_id', 'report_num_temp', 'scan_number', 'folder', 'image_name']],
                                          how = 'outer',
                                          indicator = True)

# if a unique_study_id and report_num only appear in the left df (non_tilt_predictions), then we will keep those - these do not have a corrected counter part
non_tilt_predictions_filtered_keep = non_tilt_predictions_to_filter[(non_tilt_predictions_to_filter['_merge'] == "left_only")]
print('printing length of non_tilt_predictions_filtered', len(non_tilt_predictions_filtered_keep))

del non_tilt_predictions_filtered_keep['_merge']

# merge in order to retrieve full data frame
non_tilt_predictions_filtered2 = pd.merge(non_tilt_predictions_filtered_keep,
                                         non_tilt_predictions_filtered,
                                         how = 'inner')

print('printing length of the filtered non_tilt_predictions_filtered2', len(non_tilt_predictions_filtered2))

print('combing tilt/eq and non-tilt/eq predictions back together')
tbi_predictions = pd.concat([tilt_predictions_filtered, non_tilt_predictions_filtered2])

print('printing unique number of patients and images', tbi_predictions[['unique_study_id', 'id', 'image']].nunique())

# further evaluate folders with multiple images
## evaluate if images within each folder are now unique
counts = tbi_predictions.groupby(['unique_study_id', 'report_num_temp', 'folder', 'image_name', 'scan_number'])['image_name'].count().reset_index(name = 'count').sort_values('count', ascending = False)
print('eval if images are unique', counts['count'].max()==1)

# evaluate whether there is one scan per folder
counts = tbi_predictions.groupby(['unique_study_id', 'folder', 'scan_number'])['folder'].count().reset_index(name = 'count').sort_values('count', ascending = False)

# identify folders with > 1 scan
counts_2 = counts[counts['count']>=2]

# prepare a dataframe contianing the image information for folders with more than one scan
# we will further evaluate these cases
to_eval = pd.merge(tbi_predictions, 
                   counts_2, 
                   on = ['unique_study_id', 'folder', 'scan_number'],
                   how = 'inner')

# keep columns of interest
to_eval = to_eval[['unique_study_id', 'report_num_temp', 'scan_number', 'folder', 'image_name', 'id', 'slice_num', 'max_slice', 'image', 'iph_predicted_volume_ml', 'eah_predicted_volume_ml', 'quality_control_metric']]

#### For subset of patients we reviewed, we will manually choose which image to select. Otherwise, we will select image with min(quality_control_metric)

reviewed_scans = pd.read_excel('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/manual_review/02_initial_tbi_patient_list_inclusion.xlsx',
                               sheet_name = 'multiple_image_filter',
                               engine='openpyxl')

# create a dataframe containing the scan info of the patients we've manually reviewed
reviewed_ids = pd.merge(to_eval, 
                        reviewed_scans[['unique_study_id', 'id_to_keep']],
                        left_on = ['unique_study_id', 'id'],
                        right_on = ['unique_study_id', 'id_to_keep'],
                        how = 'inner')

# create a list of report numbers
reviewed_ids_list = reviewed_ids['report_num_temp']

# remove report numbers that we identified from the `to_eval` dataframe
to_eval_filtered = to_eval[~to_eval['report_num_temp'].isin(reviewed_ids_list)]

# for the rest of the images, we will select the report with min(quality_control_metric)
to_eval_filtered = to_eval_filtered.loc[to_eval_filtered.groupby(['unique_study_id', 'report_num_temp'])['quality_control_metric'].idxmin()]

# remove unneeded column
del reviewed_ids['id_to_keep']

# combine the updated `to_eval_filtered`` and `reviewed_ids` dataframe
# there should only be one scan per folder now 
to_eval_filtered_combined = pd.concat([to_eval_filtered, reviewed_ids])

print('evaluating whether there is 1 report_num_temp per folder')
counts_check = to_eval_filtered_combined.groupby(['unique_study_id', 'folder'])['report_num_temp'].count().reset_index(name = 'count').sort_values('count', ascending = False)

print('length of counts_check should be 0:', len(counts_check[counts_check['count']>1])==0)

# combine with the rest of the predictions
print('combining updated predictions together')
tbi_predictions_outer = pd.merge(tbi_predictions, 
                                to_eval_filtered_combined[['unique_study_id', 'report_num_temp', 'folder']], 
                                how = 'outer', 
                                indicator = True)

# create a separate dataframe with the images we have not-updated (the ones that only had one image per folder)
print('creating tbi_prediction_outer')
tbi_predictions_outer = tbi_predictions_outer[tbi_predictions_outer['_merge']=="left_only"]
print('printing unique numbre of patients and scans', tbi_predictions_outer[['unique_study_id', 'id', 'report_num_temp', 'folder']].nunique())

# create a new dataframe with the predictions we just pre-processed (those that had multiple images per folder)
print('creating tbi_predictions_right')
tbi_predictions_right = pd.merge(tbi_predictions, 
                                to_eval_filtered_combined[['unique_study_id', 'report_num_temp', 'folder', 'id']], 
                                how = 'right', 
                                indicator = True)
print('printing unique numbre of patients and scans', tbi_predictions_right[['unique_study_id', 'id', 'report_num_temp', 'folder']].nunique())

# combine predictions
print('combing predictions')
tbi_predictions_clean = pd.concat([tbi_predictions_outer, tbi_predictions_right])
del tbi_predictions_clean['_merge']

print('printing unique patient and report numbers', tbi_predictions_clean[['unique_study_id', 'id', 'report_num_temp', 'folder']].nunique())

### one patient appears to have two separate report numbres for the same scan. They look essentially the same so we will just take the first 
print('removing duplicate folder')
tbi_predictions_clean = tbi_predictions_clean.sort_values(['unique_study_id', 'scan_number'], ascending = True)
tbi_predictions_clean = tbi_predictions_clean.groupby(['unique_study_id', 'folder']).first().reset_index(drop=False)

print('printing updated patient and report numbers', tbi_predictions_clean[['unique_study_id', 'id', 'report_num_temp', 'folder']].nunique())

### Identify whether all patients have >= 2 scans
print('evaluating whether patients have at least 2 scans')
scan_counts = tbi_predictions_clean.groupby(['unique_study_id'])['report_num_temp'].count().reset_index(name = 'scan_count').sort_values('scan_count', ascending = False)

print('printing number of patients with < 2 scans', len(scan_counts[scan_counts['scan_count'] < 2]))

# create new dataframe of patients with < 2 scans
one_scan = scan_counts[scan_counts['scan_count'] < 2]
ids_to_remove = one_scan['unique_study_id']

# remove patients with < 2 scans
print('removing patients with < 2 scans')
tbi_predictions_clean = tbi_predictions_clean[~tbi_predictions_clean['unique_study_id'].isin(ids_to_remove)]

print('printing updated patient and report numbers', tbi_predictions_clean[['unique_study_id', 'id', 'report_num_temp', 'folder']].nunique())

### Determining Changes in Volume
print('calculate changes in volume of hemorrhage')

# format `StudyDate_Time_format`
tbi_predictions_clean['StudyDate_Time_format'] = pd.to_datetime(tbi_predictions_clean['StudyDate_Time_format'])

# sort by `unique_study_id` and `StudyDate_Time_format`
tbi_predictions_clean = tbi_predictions_clean.sort_values(['unique_study_id', 'StudyDate_Time_format'])

# every patient should have at least 2 scans 
print('evaluate whether each patient has 2 scans')
print(tbi_predictions_clean.groupby(['unique_study_id'])['scan_number'].count().min() == 2)

# calculate total scan volume
print('calculate total volume of hemorrhage for each scan')
tbi_predictions_clean['total_volume_scan'] = tbi_predictions_clean[['iph_predicted_volume_ml', 'eah_predicted_volume_ml', 'ivh_predicted_volume_ml']].sum(axis=1)

# create new column for total first scan
# subtract this from each subsequent row. This will allow us to more easily identify changes in volume that may not have occured right away
tbi_predictions_clean['total_volume_first_scan'] = tbi_predictions_clean.groupby(['unique_study_id'])['total_volume_scan'].transform('first')
tbi_predictions_clean['change_total_volume_scan'] = tbi_predictions_clean['total_volume_scan'] - tbi_predictions_clean['total_volume_first_scan']       

# calculate change by compartment
print('calculating change in volume by compartment')
tbi_predictions_clean['iph_volume_first'] = tbi_predictions_clean.groupby(['unique_study_id'])['iph_predicted_volume_ml'].transform('first')
tbi_predictions_clean['eah_volume_first'] = tbi_predictions_clean.groupby(['unique_study_id'])['eah_predicted_volume_ml'].transform('first')
tbi_predictions_clean['ivh_volume_first'] = tbi_predictions_clean.groupby(['unique_study_id'])['ivh_predicted_volume_ml'].transform('first')

tbi_predictions_clean['change_iph_volume_first_scan'] = tbi_predictions_clean['iph_predicted_volume_ml'] - tbi_predictions_clean['iph_volume_first']         
tbi_predictions_clean['change_eah_volume_first_scan'] = tbi_predictions_clean['eah_predicted_volume_ml'] - tbi_predictions_clean['eah_volume_first']         
tbi_predictions_clean['change_ivh_volume_first_scan'] = tbi_predictions_clean['ivh_predicted_volume_ml'] - tbi_predictions_clean['ivh_volume_first']         

# reorder columns
print('reordering columns')
tbi_predictions_clean_final = tbi_predictions_clean[[
'unique_study_id',
 'report_num_temp',
 'flag_post_trauma_hem',
 'id',
 'scan_number',
 'StudyDate_Time_format',
 'iph_predicted_volume_ml',
 'eah_predicted_volume_ml',
 'oedema_predicted_volume_ml',
 'ivh_predicted_volume_ml',
 'quality_control_metric',
 'folder',
 'image_name',
 'slice_num',
 'total_volume_scan',
 'total_volume_first_scan',
 'change_total_volume_scan',
 'iph_volume_first',
 'eah_volume_first',
 'ivh_volume_first',
 'change_iph_volume_first_scan',
 'change_eah_volume_first_scan',
 'change_ivh_volume_first_scan',
 'prediction_iph_BrainStem_ml',
 'prediction_iph_Cerebellum_ml',
 'prediction_iph_LeftBasalForebrain_ml',
 'prediction_iph_LeftBasalGanglia_ml',
 'prediction_iph_LeftBasalganglia-lentiform-nucleus_ml',
 'prediction_iph_LeftCaudate_ml',
 'prediction_iph_LeftCerebellum_ml',
 'prediction_iph_LeftFrontalLobe-inferior-orbital_ml',
 'prediction_iph_LeftFrontalLobe-lateral_ml',
 'prediction_iph_LeftFrontalLobe-medial_ml',
 'prediction_iph_LeftHippocampus_ml',
 'prediction_iph_LeftInsula_ml',
 'prediction_iph_LeftOccipitalLobe_ml',
 'prediction_iph_LeftParietalLobe_ml',
 'prediction_iph_LeftTemporalLobe_ml',
 'prediction_iph_LeftThalamusProper_ml',
 'prediction_iph_RightBasalForebrain_ml',
 'prediction_iph_RightBasalGanglia_ml',
 'prediction_iph_RightBasalGanglia-lentiform-nucleus_ml',
 'prediction_iph_RightCaudate_ml',
 'prediction_iph_RightCerebellum_ml',
 'prediction_iph_RightFrontalLobe-inferior-orbital_ml',
 'prediction_iph_RightFrontalLobe-lateral_ml',
 'prediction_iph_RightFrontalLobe-medial_ml',
 'prediction_iph_RightHippocampus_ml',
 'prediction_iph_RightInsula_ml',
 'prediction_iph_RightOccipitalLobe_ml',
 'prediction_iph_RightParietalLobe_ml',
 'prediction_iph_RightTemporalLobe_ml',
 'prediction_iph_RightThalamusProper_ml',
 'prediction_iph_Ventricle_ml',
 'prediction_eah_BrainStem_ml',
 'prediction_eah_Cerebellum_ml',
 'prediction_eah_LeftBasalForebrain_ml',
 'prediction_eah_LeftBasalGanglia_ml',
 'prediction_eah_LeftBasalganglia-lentiform-nucleus_ml',
 'prediction_eah_LeftCaudate_ml',
 'prediction_eah_LeftCerebellum_ml',
 'prediction_eah_LeftFrontalLobe-inferior-orbital_ml',
 'prediction_eah_LeftFrontalLobe-lateral_ml',
 'prediction_eah_LeftFrontalLobe-medial_ml',
 'prediction_eah_LeftHippocampus_ml',
 'prediction_eah_LeftInsula_ml',
 'prediction_eah_LeftOccipitalLobe_ml',
 'prediction_eah_LeftParietalLobe_ml',
 'prediction_eah_LeftTemporalLobe_ml',
 'prediction_eah_LeftThalamusProper_ml',
 'prediction_eah_RightBasalForebrain_ml',
 'prediction_eah_RightBasalGanglia_ml',
 'prediction_eah_RightBasalGanglia-lentiform-nucleus_ml',
 'prediction_eah_RightCaudate_ml',
 'prediction_eah_RightCerebellum_ml',
 'prediction_eah_RightFrontalLobe-inferior-orbital_ml',
 'prediction_eah_RightFrontalLobe-lateral_ml',
 'prediction_eah_RightFrontalLobe-medial_ml',
 'prediction_eah_RightHippocampus_ml',
 'prediction_eah_RightInsula_ml',
 'prediction_eah_RightOccipitalLobe_ml',
 'prediction_eah_RightParietalLobe_ml',
 'prediction_eah_RightTemporalLobe_ml',
 'prediction_eah_RightThalamusProper_ml',
 'prediction_eah_Ventricle_ml',
 'prediction_oedema_BrainStem_ml',
 'prediction_oedema_Cerebellum_ml',
 'prediction_oedema_LeftBasalForebrain_ml',
 'prediction_oedema_LeftBasalGanglia_ml',
 'prediction_oedema_LeftBasalganglia-lentiform-nucleus_ml',
 'prediction_oedema_LeftCaudate_ml',
 'prediction_oedema_LeftCerebellum_ml',
 'prediction_oedema_LeftFrontalLobe-inferior-orbital_ml',
 'prediction_oedema_LeftFrontalLobe-lateral_ml',
 'prediction_oedema_LeftFrontalLobe-medial_ml',
 'prediction_oedema_LeftHippocampus_ml',
 'prediction_oedema_LeftInsula_ml',
 'prediction_oedema_LeftOccipitalLobe_ml',
 'prediction_oedema_LeftParietalLobe_ml',
 'prediction_oedema_LeftTemporalLobe_ml',
 'prediction_oedema_LeftThalamusProper_ml',
 'prediction_oedema_RightBasalForebrain_ml',
 'prediction_oedema_RightBasalGanglia_ml',
 'prediction_oedema_RightBasalGanglia-lentiform-nucleus_ml',
 'prediction_oedema_RightCaudate_ml',
 'prediction_oedema_RightCerebellum_ml',
 'prediction_oedema_RightFrontalLobe-inferior-orbital_ml',
 'prediction_oedema_RightFrontalLobe-lateral_ml',
 'prediction_oedema_RightFrontalLobe-medial_ml',
 'prediction_oedema_RightHippocampus_ml',
 'prediction_oedema_RightInsula_ml',
 'prediction_oedema_RightOccipitalLobe_ml',
 'prediction_oedema_RightParietalLobe_ml',
 'prediction_oedema_RightTemporalLobe_ml',
 'prediction_oedema_RightThalamusProper_ml',
 'prediction_oedema_Ventricle_ml',
 'prediction_ivh_BrainStem_ml',
 'prediction_ivh_Cerebellum_ml',
 'prediction_ivh_LeftBasalForebrain_ml',
 'prediction_ivh_LeftBasalGanglia_ml',
 'prediction_ivh_LeftBasalganglia-lentiform-nucleus_ml',
 'prediction_ivh_LeftCaudate_ml',
 'prediction_ivh_LeftCerebellum_ml',
 'prediction_ivh_LeftFrontalLobe-inferior-orbital_ml',
 'prediction_ivh_LeftFrontalLobe-lateral_ml',
 'prediction_ivh_LeftFrontalLobe-medial_ml',
 'prediction_ivh_LeftHippocampus_ml',
 'prediction_ivh_LeftInsula_ml',
 'prediction_ivh_LeftOccipitalLobe_ml',
 'prediction_ivh_LeftParietalLobe_ml',
 'prediction_ivh_LeftTemporalLobe_ml',
 'prediction_ivh_LeftThalamusProper_ml',
 'prediction_ivh_RightBasalForebrain_ml',
 'prediction_ivh_RightBasalGanglia_ml',
 'prediction_ivh_RightBasalGanglia-lentiform-nucleus_ml',
 'prediction_ivh_RightCaudate_ml',
 'prediction_ivh_RightCerebellum_ml',
 'prediction_ivh_RightFrontalLobe-inferior-orbital_ml',
 'prediction_ivh_RightFrontalLobe-lateral_ml',
 'prediction_ivh_RightFrontalLobe-medial_ml',
 'prediction_ivh_RightHippocampus_ml',
 'prediction_ivh_RightInsula_ml',
 'prediction_ivh_RightOccipitalLobe_ml',
 'prediction_ivh_RightParietalLobe_ml',
 'prediction_ivh_RightTemporalLobe_ml',
 'prediction_ivh_RightThalamusProper_ml',
 'prediction_ivh_Ventricle_ml',
 'Brain_volume_ml',
 'BrainStem_volume_ml',
 'Cerebellum_volume_ml',
 'LeftBasalForebrain_volume_ml',
 'LeftBasalGanglia_volume_ml',
 'LeftBasalganglia-lentiform-nucleus_volume_ml',
 'LeftCaudate_volume_ml',
 'LeftCerebellum_volume_ml',
 'LeftFrontalLobe-inferior-orbital_volume_ml',
 'LeftFrontalLobe-lateral_volume_ml',
 'LeftFrontalLobe-medial_volume_ml',
 'LeftHippocampus_volume_ml',
 'LeftInsula_volume_ml',
 'LeftOccipitalLobe_volume_ml',
 'LeftParietalLobe_volume_ml',
 'LeftTemporalLobe_volume_ml',
 'LeftThalamusProper_volume_ml',
 'RightBasalForebrain_volume_ml',
 'RightBasalGanglia_volume_ml',
 'RightBasalGanglia-lentiform-nucleus_volume_ml',
 'RightCaudate_volume_ml',
 'RightCerebellum_volume_ml',
 'RightFrontalLobe-inferior-orbital_volume_ml',
 'RightFrontalLobe-lateral_volume_ml',
 'RightFrontalLobe-medial_volume_ml',
 'RightHippocampus_volume_ml',
 'RightInsula_volume_ml',
 'RightOccipitalLobe_volume_ml',
 'RightParietalLobe_volume_ml',
 'RightTemporalLobe_volume_ml',
 'RightThalamusProper_volume_ml',
 'Ventricle_volume_ml',
 'image',
 'prediction',
 'atlas_in_native_space',
 'brain_mask_native_space']]

### final numbers
print('printing final prediction numbers', tbi_predictions_clean_final[['unique_study_id', 'id', 'report_num_temp', 'folder']].nunique())

### Save predictions
print('saving cleaned up predictions')
tbi_predictions_clean_final.to_csv('data/processed/tbi_cohort/0_initial_tbi_scans_volumes_v3.csv', index = False)