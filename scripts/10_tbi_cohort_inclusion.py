# Date: 10-28-2024
# Author: Meghan Hutch
# Objective: This script follows the notebook from notebooks/10_tbi_cohort.ipynb which was used for the following purposes:
## 1. Evaluate which patients should be included/excluded - this was performed by evaluating the radiology reports and scans of patients with a certain volume of hemorrhage
## 2. Quality control - identified patients with very high volumes of hemorrhage which often identified patients with artifact confounded scans and who were post-surgery
## 3. Selection of scans for Analyze Evaluation
## 4. Curate images for my dissertation (Note: this code wasn't working outside of the notebook for some reason; currently commented out)

import os

import pandas as pd
import numpy as np
import random
import nibabel as nib
import csv
import openpyxl
import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches

# Define your custom colormap with black as the first color
colors = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)]  # Black, Red, Green, Yellow, Blue
custom_cmap = ListedColormap(colors)

def window_function(nii_img, nii_array, window_center, window_width):
    
    img_header = nii_img.header
    scl_slope, scl_inter = img_header.get_slope_inter()

    if scl_slope is None:
        scl_slope = 1

    if scl_inter is None:
        scl_inter = 0
    
    #print('scl_slope=', scl_slope)
    #print('scl_inter=', scl_inter)
    
    hu_image = nii_array * scl_slope + scl_inter
    img_min = window_center - window_width // 2
    
    img_max = window_center + window_width // 2

    #window_image = nii_img.copy()

    hu_image[hu_image < img_min] = img_min

    hu_image[hu_image > img_max] = img_max

    return(hu_image)

os.chdir('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI')

## Load data
# load in csv file of our cohort with blast-ct predicted volumes
tbi_initial_cohort = pd.read_csv('data/processed/tbi_cohort/0_initial_tbi_scans_volumes_v3.csv')

print('Nunber of unique patients and reports:', tbi_initial_cohort[['unique_study_id', 'report_num_temp']].nunique())

# load in radiology reports
suid_rad_reports = pd.read_csv('data/processed/suid_rad_reports.csv')

# load in the xlsx file and sheet used for manual review of patients
reviewed_scans = pd.read_excel('data/processed/manual_review/02_initial_tbi_patient_list_inclusion.xlsx',
                               sheet_name = '02_initial_tbi_patient_list_inc',
                               engine='openpyxl')

# load in the xlsx file and sheet used for manual review of patients we want to exclude
scans_to_exclude = pd.read_excel('data/processed/manual_review/02_initial_tbi_patient_list_inclusion.xlsx',
                               sheet_name = 'scans_to_exclude',
                               engine='openpyxl')

# merge initial cohort with the reviewed scans
tbi_initial_cohort = pd.merge(tbi_initial_cohort,
                              reviewed_scans, 
                              on = 'unique_study_id',
                              how = 'left')

# merge cohort dataframe with radiology report info
tbi_initial_cohort = pd.merge(tbi_initial_cohort,
                              suid_rad_reports[['unique_study_id', 'report_num_temp', 'report']])

print('Nunber of unique patients and reports:', tbi_initial_cohort[['unique_study_id', 'report_num_temp']].nunique())

# create a separate dataframe for excluded patients
exclude = tbi_initial_cohort[tbi_initial_cohort['exclude']==1]
print('Number of excluded patients:', exclude[['unique_study_id', 'report_num_temp']].nunique())

# create a separate dataframe for included patients
include = tbi_initial_cohort[(tbi_initial_cohort['exclude']==0)]
print('Number of included patients:', include[['unique_study_id', 'report_num_temp']].nunique())

## Exclude patients
tbi_initial_cohort_include = tbi_initial_cohort[~(tbi_initial_cohort['exclude'] == 1)]

print('Number of included patients in `tbi_initial_cohort_include` df:', tbi_initial_cohort_include[['unique_study_id', 'report_num_temp']].nunique())

## Excluded listed scans
# remove scans that we decided to move due to extensive artifacts

tbi_initial_cohort_include = tbi_initial_cohort_include[~(tbi_initial_cohort_include['id'].isin(scans_to_exclude['id_to_remove']))]
print('Number of included patients in `tbi_initial_cohort_include` df after excluding poor quality scans:', tbi_initial_cohort_include[['unique_study_id', 'report_num_temp']].nunique())

# review scans where 'quality_control_metric'==0
tbi_initial_cohort_include[tbi_initial_cohort_include['quality_control_metric']==0][['unique_study_id', 'id', 'quality_control_metric', 'slice_num']]

# look at cases where I marked 'potential_hematoma_expansion_case' as 999
cases = tbi_initial_cohort_include[(tbi_initial_cohort_include['potential_hematoma_expansion_case']==1) | (tbi_initial_cohort_include['potential_hematoma_expansion_case']==999)]
print('Number of potential hematoma expansion cases', cases[['unique_study_id', 'report_num_temp']].nunique())

### Randomly select scans for Analyze Evaluation

#We will randomly select from patients who have >= 5 ml of hemorrhage (IPH, EAH, or both)

five_ml_include = tbi_initial_cohort_include[(tbi_initial_cohort_include['iph_predicted_volume_ml'] >= 5) | (cases['eah_predicted_volume_ml'] >= 5)]

print('Unique patients and scans with IPH or EAH >= 5mL', five_ml_include[['unique_study_id', 'report_num_temp']].nunique())

five_ml_include[['unique_study_id', 'id', 'iph_predicted_volume_ml', 'eah_predicted_volume_ml']].sample(n = 20, random_state = 1148)

#five_ml_include[five_ml_include['notes'].isnull()][['unique_study_id', 'notes']].drop_duplicates()

five_ml_change = five_ml_include[(five_ml_include['change_iph_volume_first_scan'] >= 8) | (five_ml_include['change_eah_volume_first_scan'] >= 9)]
print('Number of unique patients and scans >=8 ml of IPH or 9mL of EAH', five_ml_change[['unique_study_id', 'report_num_temp']].nunique())

### Review potential cases by varying predicted volume thresholds
five_ml = cases[(cases['iph_predicted_volume_ml'] >= 5) | (cases['eah_predicted_volume_ml'] >= 5)]
print('Unique cases (patinets and scans) with IPH or EAH >= 5mL', five_ml[['unique_study_id', 'report_num_temp']].nunique())

five_ml_iph = five_ml[five_ml['change_iph_volume_first_scan'] >= 8]

five_ml_eah = five_ml[five_ml['change_eah_volume_first_scan'] >= 9]
print('Number of patients and scans with >= 9 EAH', five_ml_eah[['unique_study_id', 'report_num_temp']].nunique())

five_ml_all = five_ml[(five_ml['change_iph_volume_first_scan'] >= 8) | (five_ml['change_eah_volume_first_scan'] >= 9)]
print('Number of patients and scans with >= 9 IPH',five_ml_all[['unique_study_id', 'report_num_temp']].nunique())

# plot histograms of changes in hemorrhage volumes
print('Printing histograms of hemorrhage volumes')
five_ml[['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'change_iph_volume_first_scan', 'change_eah_volume_first_scan']]['change_iph_volume_first_scan'].hist()

five_ml[['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'change_iph_volume_first_scan', 'change_eah_volume_first_scan']]['change_eah_volume_first_scan'].hist()


### Patients with likely hematoma expansion
iph_high = tbi_initial_cohort_include[tbi_initial_cohort_include['change_iph_volume_first_scan'] >= 10][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'iph_predicted_volume_ml', 'change_iph_volume_first_scan']]
#iph_high[iph_high['exclude'].isnull()].sort_values('change_iph_volume_first_scan', ascending = False)

eah_high = tbi_initial_cohort_include[tbi_initial_cohort_include['change_eah_volume_first_scan'] >= 10][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'eah_predicted_volume_ml', 'change_eah_volume_first_scan']]
#eah_high[eah_high['exclude'].isnull()].sort_values('change_eah_volume_first_scan', ascending = False)


### Patients with high hemorrhage volumes
iph_vol_high = tbi_initial_cohort_include[tbi_initial_cohort_include['iph_predicted_volume_ml'] >= 10][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'iph_predicted_volume_ml', 'change_iph_volume_first_scan']]
#iph_vol_high[iph_vol_high['exclude'].isnull()].sort_values('iph_predicted_volume_ml', ascending = False)

eah_vol_high = tbi_initial_cohort_include[tbi_initial_cohort_include['eah_predicted_volume_ml'] >= 10][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'eah_predicted_volume_ml']]
#eah_vol_high[eah_vol_high['exclude'].isnull()].sort_values('eah_predicted_volume_ml', ascending = False)

tbi_initial_cohort_include[tbi_initial_cohort_include['exclude'].isnull()][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'ivh_predicted_volume_ml']].sort_values('ivh_predicted_volume_ml', ascending = False)

### Identify patients with likely surgery between scans
large_dec = tbi_initial_cohort_include[tbi_initial_cohort_include['change_eah_volume_first_scan'] <= -10][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'eah_predicted_volume_ml', 'change_eah_volume_first_scan']]
#large_dec[large_dec['exclude'].isnull()][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'eah_predicted_volume_ml', 'change_eah_volume_first_scan']].sort_values('change_eah_volume_first_scan', ascending = True) 

large_dec = tbi_initial_cohort_include[tbi_initial_cohort_include['change_iph_volume_first_scan'] <= -10][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'iph_predicted_volume_ml', 'change_iph_volume_first_scan']]
#large_dec[large_dec['exclude'].isnull()][['unique_study_id',  'exclude', 'id', 'report_num_temp', 'folder', 'iph_predicted_volume_ml', 'change_iph_volume_first_scan']].sort_values('change_iph_volume_first_scan', ascending = True)

### Patients without hemorrhage
max_iph = tbi_initial_cohort_include.groupby(['unique_study_id'])['iph_predicted_volume_ml'].max().reset_index(name = 'max_iph')
max_eah = tbi_initial_cohort_include.groupby(['unique_study_id'])['eah_predicted_volume_ml'].max().reset_index(name = 'max_eah')
max_ivh = tbi_initial_cohort_include.groupby(['unique_study_id'])['ivh_predicted_volume_ml'].max().reset_index(name = 'max_ivh')

max_vols = pd.merge(max_iph, max_eah,
                     how = 'left')

max_vols = pd.merge(max_vols, max_ivh,
                     how = 'left')

#max_vols[['unique_study_id']].nunique()

max_vols['total_hemorrhage'] = max_vols.loc[:,['max_iph', 'max_eah', 'max_ivh']].sum(axis=1)
len(max_vols[max_vols['total_hemorrhage'] == 0])#.sort_values('total_hemorrhage', ascending = True).iloc[5:10]

max_vols[max_vols['total_hemorrhage'] == 0].sort_values('total_hemorrhage', ascending = True)#.iloc[5:10]

### Images for dissertation
# Update: 10/28/2024 - for some reason, Python won't read in the file from orig_path
# print('Preparing images for dissertation')
# ## Example 1
# slice_number=8

# img_path = tbi_initial_cohort[tbi_initial_cohort['id'] == 'scan_6194']
# orig_path = img_path['image'].to_string(index=False).lstrip()
# pred_path = img_path['prediction'].to_string(index=False).lstrip()

# orig_img = nib.load(orig_path)
# orig_array = orig_img.get_fdata()

# # print(orig_array.max())
# # print(orig_array.min())

# pred_img = nib.load(pred_path)
# pred_array = pred_img.get_fdata()

# orig_img_windowed = window_function(orig_img, orig_array, 40, 80)
# pred_img_windowed = window_function(pred_img, pred_array, 40, 80)

# orig_ct = np.rot90(orig_img_windowed[:,:,slice_number], 1)
# pred_ct = np.rot90(pred_img_windowed[:,:,slice_number], 1)

# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 4), gridspec_kw={'width_ratios': [1, 1]})  # Adjusting width ratio for the second subplot

# # Displaying original image on the first subplot (ax1)
# ax1.imshow(orig_ct, cmap='gray', interpolation='none')
# ax1.set_title('Motion/Streak Artifact')
# ax1.axis('off')  # Remove axis ticks

# # Displaying predicted image on the second subplot (ax2)
# ax2.imshow(orig_ct, cmap='gray', interpolation='none')  # Displaying original image again
# ax2.imshow(pred_ct, cmap=custom_cmap, alpha=0.5, interpolation='none', vmin=0, vmax=4)
# ax2.set_title('Hemorrhage Quantification')
# ax2.axis('off')  # Remove axis ticks

# # Adding legend to the second subplot (ax2)
# red_patch = mpatches.Patch(color='red', label='IPH')
# green_patch = mpatches.Patch(color='green', label='EAH')
# yellow_patch = mpatches.Patch(color='yellow', label='Edema')
# blue_patch = mpatches.Patch(color='blue', label='IVH')
# #ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch])
# #legend = ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch], bbox_to_anchor=(1.05, 1), loc='upper left')

# # Save the figure
# #plt.savefig('results/blast-ct_qc/motion_streak_artifact_scan_6194.png')

# ## Example 2
# slice_number=24

# img_path = tbi_initial_cohort[tbi_initial_cohort['id'] == 'scan_5994']
# orig_path = img_path['image'].to_string(index=False).lstrip()
# pred_path = img_path['prediction'].to_string(index=False).lstrip()

# orig_img = nib.load(orig_path)
# orig_array = orig_img.get_fdata()

# pred_img = nib.load(pred_path)
# pred_array = pred_img.get_fdata()

# orig_img_windowed = window_function(orig_img, orig_array, 40, 80)
# pred_img_windowed = window_function(pred_img, pred_array, 40, 80)


# orig_ct = np.rot90(orig_img_windowed[:,:,slice_number], 1)
# pred_ct = np.rot90(pred_img_windowed[:,:,slice_number], 1)

# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 4), gridspec_kw={'width_ratios': [1, 1]})  # Adjusting width ratio for the second subplot

# # Displaying original image on the first subplot (ax1)
# ax1.imshow(orig_ct, cmap='gray', interpolation='none')
# ax1.set_title('Streak Artifact')
# ax1.axis('off')  # Remove axis ticks

# # Displaying predicted image on the second subplot (ax2)
# ax2.imshow(orig_ct, cmap='gray', interpolation='none')  # Displaying original image again
# ax2.imshow(pred_ct, cmap=custom_cmap, alpha=0.5, interpolation='none', vmin=0, vmax=4)
# ax2.set_title('Hemorrhage Quantification')
# ax2.axis('off')  # Remove axis ticks

# # Adding legend to the second subplot (ax2)
# red_patch = mpatches.Patch(color='red', label='IPH')
# green_patch = mpatches.Patch(color='green', label='EAH')
# yellow_patch = mpatches.Patch(color='yellow', label='Edema')
# blue_patch = mpatches.Patch(color='blue', label='IVH')
# #ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch])
# #legend = ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch], bbox_to_anchor=(1.05, 1), loc='upper left')

# # Save the figure
# #plt.savefig('results/blast-ct_qc/streak_artifact_bullet_scan_5994.png')

# ## Example 3
# slice_number=14

# img_path = tbi_initial_cohort[tbi_initial_cohort['id'] == 'scan_9504']
# orig_path = img_path['image'].to_string(index=False).lstrip()
# pred_path = img_path['prediction'].to_string(index=False).lstrip()

# orig_img = nib.load(orig_path)
# orig_array = orig_img.get_fdata()

# pred_img = nib.load(pred_path)
# pred_array = pred_img.get_fdata()

# orig_img_windowed = window_function(orig_img, orig_array, 40, 80)
# pred_img_windowed = window_function(pred_img, pred_array, 40, 80)


# orig_ct = np.rot90(orig_img_windowed[:,:,slice_number], 1)
# pred_ct = np.rot90(pred_img_windowed[:,:,slice_number], 1)

# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 4), gridspec_kw={'width_ratios': [1, 1]})  # Adjusting width ratio for the second subplot

# # Displaying original image on the first subplot (ax1)
# ax1.imshow(orig_ct, cmap='gray', interpolation='none')
# ax1.set_title('Portable Scanner')
# ax1.axis('off')  # Remove axis ticks

# # Displaying predicted image on the second subplot (ax2)
# ax2.imshow(orig_ct, cmap='gray', interpolation='none')  # Displaying original image again
# ax2.imshow(pred_ct, cmap=custom_cmap, alpha=0.5, interpolation='none', vmin=0, vmax=4)
# ax2.set_title('Hemorrhage Quantification')
# ax2.axis('off')  # Remove axis ticks

# # Adding legend to the second subplot (ax2)
# red_patch = mpatches.Patch(color='red', label='IPH')
# green_patch = mpatches.Patch(color='green', label='EAH')
# yellow_patch = mpatches.Patch(color='yellow', label='Edema')
# blue_patch = mpatches.Patch(color='blue', label='IVH')
# #ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch])
# #legend = ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch], bbox_to_anchor=(1.05, 1), loc='upper left')

# # Save the figure
# #plt.savefig('results/blast-ct_qc/streak_artifact_bullet_scan_9504.png')

# ## Example 4
# slice_number=10

# img_path = tbi_initial_cohort[tbi_initial_cohort['id'] == 'scan_11838']
# orig_path = img_path['image'].to_string(index=False).lstrip()
# pred_path = img_path['prediction'].to_string(index=False).lstrip()

# orig_img = nib.load(orig_path)
# orig_array = orig_img.get_fdata()

# pred_img = nib.load(pred_path)
# pred_array = pred_img.get_fdata()

# orig_img_windowed = window_function(orig_img, orig_array, 40, 80)
# pred_img_windowed = window_function(pred_img, pred_array, 40, 80)


# orig_ct = np.rot90(orig_img_windowed[:,:,slice_number], 1)
# pred_ct = np.rot90(pred_img_windowed[:,:,slice_number], 1)

# fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 4), gridspec_kw={'width_ratios': [1, 1]})  # Adjusting width ratio for the second subplot

# # Displaying original image on the first subplot (ax1)
# ax1.imshow(orig_ct, cmap='gray', interpolation='none')
# ax1.set_title('Motion Artifact')
# ax1.axis('off')  # Remove axis ticks

# # Displaying predicted image on the second subplot (ax2)
# ax2.imshow(orig_ct, cmap='gray', interpolation='none')  # Displaying original image again
# ax2.imshow(pred_ct, cmap=custom_cmap, alpha=0.5, interpolation='none', vmin=0, vmax=4)
# ax2.set_title('Hemorrhage Quantification')
# ax2.axis('off')  # Remove axis ticks

# # Adding legend to the second subplot (ax2)
# red_patch = mpatches.Patch(color='red', label='IPH')
# green_patch = mpatches.Patch(color='green', label='EAH')
# yellow_patch = mpatches.Patch(color='yellow', label='Edema')
# blue_patch = mpatches.Patch(color='blue', label='IVH')
# #ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch])
# #legend = ax2.legend(handles=[red_patch, green_patch, blue_patch, yellow_patch], bbox_to_anchor=(1.05, 1), loc='upper left')

# # Save the figure
# #plt.savefig('results/blast-ct_qc/motion_artifact_scan_11838.png')