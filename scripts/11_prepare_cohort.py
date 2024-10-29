# Date: 10-28-2024
# Author: Meghan Hutch
# Objective: This script follows the notebook from notebooks/11_prepare_cohort.ipynb which was used to solidify the included patient cohort after the manual review performed using code from notebook/10_tbi_cohort_inclusion.ipynb (scripts/10_tbi_cohort_inclusion.py). This notebook does additional data cleaning to prepare the main included cohort for modeling.

import os

import pandas as pd
import numpy as np
import random
import nibabel as nib
import csv
import openpyxl
import matplotlib.pyplot as plt
import seaborn as sns

os.chdir('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI')

## Load data
# load in csv file of our cohort with blast-ct predicted volumes
tbi_initial_cohort = pd.read_csv('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/tbi_cohort/0_initial_tbi_scans_volumes_v3.csv')

print('Unique number of included tbi patients', tbi_initial_cohort[['unique_study_id', 'report_num_temp']].nunique())

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

### Prepare Cohort for Review
### add reports from scans
tbi_initial_cohort = pd.merge(tbi_initial_cohort, 
                              reviewed_scans, 
                              on = 'unique_study_id',
                              how = 'left')

tbi_initial_cohort_include = pd.merge(tbi_initial_cohort,
                              suid_rad_reports[['unique_study_id', 'report_num_temp', 'report']])


print('Number of patients and scans:', tbi_initial_cohort_include[['unique_study_id', 'report_num_temp']].nunique())

#### Save list of trauma scans for included patients
#tbi_initial_cohort[['unique_study_id', 'id', 'scan_number', 'StudyDate_Time_format', 'report']].to_csv('data/processed/tbi_cohort/01_initial_tbi_cohort_reports_v3.csv', index = False)

### Keep scans within first 72 hours of the first scan
tbi_initial_cohort_include['StudyDate_Time_format'] = pd.to_datetime(tbi_initial_cohort_include['StudyDate_Time_format'])

# sort scans in chronological order
tbi_initial_cohort_include = tbi_initial_cohort_include.sort_values(['unique_study_id', 'StudyDate_Time_format'])

# create column for time of first scan
tbi_initial_cohort_include['first_scan_time'] = tbi_initial_cohort_include.groupby('unique_study_id')['StudyDate_Time_format'].transform('first')

# calculate time difference
tbi_initial_cohort_include['time_since_first_scan'] = (tbi_initial_cohort_include['StudyDate_Time_format'] - tbi_initial_cohort_include['first_scan_time']).dt.round('H') / pd.Timedelta('1 day')*24

# keep scans within 72 hours
print(len(tbi_initial_cohort_include))
tbi_cohort_clean = tbi_initial_cohort_include[tbi_initial_cohort_include['time_since_first_scan'] <= 72]

print('Number of patients with scans <= 72 hours:', tbi_cohort_clean[['unique_study_id', 'report']].nunique())

### Identify a patient's first scan
first_scan = tbi_cohort_clean.sort_values(['unique_study_id', 'StudyDate_Time_format']).groupby('unique_study_id').first().reset_index(drop=False)
first_scan['scan_number'].value_counts()

## Identify patients with 0 ml of hemorrhage
test_zero_ml = tbi_cohort_clean[(tbi_cohort_clean['iph_predicted_volume_ml'] == 0) & (tbi_cohort_clean['eah_predicted_volume_ml'] == 0) & (tbi_cohort_clean['ivh_predicted_volume_ml'] == 0) ]
print('Patients with 0mL of hemorrhage:', test_zero_ml[['unique_study_id']].nunique())

# Identify patients with >=2mL of hemorrhage on first scan
two_ml_first_include = first_scan[(first_scan['iph_predicted_volume_ml'] >= 2) | (first_scan['eah_predicted_volume_ml'] >= 2)]
print('Number of patients and scans with >= 2 mL of IPH or EAH:', two_ml_first_include[['unique_study_id', 'report']].nunique())

two_ml_first_all = tbi_cohort_clean[tbi_cohort_clean['unique_study_id'].isin(two_ml_first_include['unique_study_id'])]
print('Number of patients with >= 2mL of IPH or EAH', len(two_ml_first_all))

# Identify patients with >= 6L of hemorrhage on a follow-up scan
two_ml_first_all[((two_ml_first_all['change_iph_volume_first_scan'] >= 6) | (two_ml_first_all['change_eah_volume_first_scan'] >= 6))].nunique()

## Save cleaned up cohort to review
#two_ml_chart_review = two_ml_first_all[['unique_study_id', '041224_review_5ml', 'injury', 'exclude', 'surgery', 'surgery_type', 'artifact', 'reason_excluded', 'notes']].drop_duplicates().sort_values(['041224_review_5ml', 'exclude'])

# saved to csv April 25, 2024 - MH resaved as an excel notebook to work on to further review/annotated included/excluded patients
#two_ml_chart_review.to_csv('data/processed/manual_review/02_initial_tbi_patient_list_inclusion_2ml.csv', index = False)

### Upload and clean reviewed patients with >= 2mL of hemorrhage
# reload updated annotations
two_ml_annotated = pd.read_excel('data/processed/manual_review/02_initial_tbi_patient_list_inclusion_2ml.xlsx',
                                 sheet_name = 'chart_review',
                                 engine='openpyxl')

exclude_reasons = pd.DataFrame(two_ml_annotated[two_ml_annotated['exclude']==1]['reason_excluded'].str.lower())
exclude_reasons = exclude_reasons['reason_excluded'].str.strip().value_counts().reset_index(drop=False)
exclude_reasons.columns = ['Reason Excluded', 'Patient Count']
exclude_n = exclude_reasons['Patient Count'].sum()
print('Number of excluded patients:', exclude_n)
exclude_reasons['percent_of_excluded'] = round(exclude_reasons['Patient Count'] / exclude_n * 100, 1)
#exclude_reasons.iloc[:60]#[exclude_reasons['Patient Count'] > 1]['Patient Count'

# keep only the included patients (e.g. `exclude == 0`)
two_ml_annotated_include = two_ml_annotated[two_ml_annotated['exclude'] == 0]

# retrieve the first scan to facilitate text-matching to identify potential reports to exclude
two_ml_include_first = pd.merge(two_ml_annotated_include, 
                                first_scan[['unique_study_id', 'report', 'id', 'quality_control_metric']],
                                on = ['unique_study_id'],
                                how = 'inner')

### Create QC Plots for evaluating image QC
print('Preparing plots for evaluating image QC')
#I will create these plots on the 457 patients, as this is the cohort I used to decide whether or not to include
print('Unique number of patients in `tbi_cohort_clean`:', tbi_cohort_clean[['unique_study_id']].nunique())

tbi_cohort_qc = pd.merge(tbi_cohort_clean,
                         two_ml_annotated[['unique_study_id']],
                         how = 'inner')

print('Unique number of patients for QC:', tbi_cohort_qc[['unique_study_id']].nunique())

excluded_scans = scans_to_exclude.copy()
excluded_scans = excluded_scans.rename(columns  = {'id_to_remove':'id'})
excluded_scans['exclude_id'] = 1

tbi_cohort_qc = pd.merge(tbi_cohort_qc,
                         excluded_scans,
                         on = ['unique_study_id', 'id'],
                         how = 'left')

# we need to indicate if the patient and/or the scan were excluded
two_ml_annotated_exclude = two_ml_annotated[two_ml_annotated['exclude'] == 1]
two_ml_annotated_exclude['patient_excluded'] = 1

tbi_cohort_qc = pd.merge(tbi_cohort_qc, 
                         two_ml_annotated_exclude[['unique_study_id', 'patient_excluded']],
                         on = 'unique_study_id', 
                         how = 'left')

tbi_cohort_qc['exclude_id'] = np.where(tbi_cohort_qc['exclude_id'].isnull(), 0, 1) 
tbi_cohort_qc['patient_excluded'] = np.where(tbi_cohort_qc['patient_excluded'].isnull(), 0, 1) 
tbi_cohort_qc['exclude_id'] = np.where((tbi_cohort_qc['exclude_id']==1) | (tbi_cohort_qc['patient_excluded'] == 1), 1, tbi_cohort_qc['exclude_id'])

# Convert data to long format
vols_long = pd.melt(tbi_cohort_qc, id_vars = ['unique_study_id', 'id', 'scan_number', 'quality_control_metric', 'exclude_id', 'patient_excluded',  'reason_excluded', 'notes'], value_vars = [ 'iph_predicted_volume_ml', 'eah_predicted_volume_ml'])

# Define conditions
conditions = [
    (vols_long['exclude_id'] == 1) & (vols_long['variable'] == 'iph_predicted_volume_ml'),
    (vols_long['exclude_id'] == 1) & (vols_long['variable'] == 'eah_predicted_volume_ml'),
    (vols_long['exclude_id'] == 0) & (vols_long['variable'] == 'iph_predicted_volume_ml'),
    (vols_long['exclude_id'] == 0) & (vols_long['variable'] == 'eah_predicted_volume_ml'),
]

# Define corresponding choices
choices = ['IPH-Exclude', 'EAH-Exclude', 'IPH', 'EAH']

# Apply np.select
vols_long['scan_status'] = np.select(conditions, choices, default='Unknown')

# Box Plot + Strip Plot
plt.figure(figsize=(8, 5))

# Define a custom palette
custom_palette = {
    'IPH-Exclude': 'black',
    'EAH-Exclude': 'black',  
    'IPH': 'tomato',
    'EAH': '#17C717'
}

palette_box = {
    'iph_predicted_volume_ml': 'tomato', 
    'eah_predicted_volume_ml': '#17C717'
}

#palette = sns.color_palette("Set2", n_colors=2)

# sns.boxplot(x='variable', y=np.log(vols_long['value']+1), data=vols_long, hue = 'variable', dodge = False, whis=[0, 100], palette=palette_box)
# ax = sns.stripplot(x='variable', y=np.log(vols_long['value']+1), data=vols_long, jitter=True, hue = 'variable', dodge = False, alpha=0.7, palette = palette_box)

sns.boxplot(x='variable', y='value', data=vols_long, hue = 'variable', dodge = False, whis=[0, 100], palette=palette_box)
ax = sns.stripplot(x='variable', y='value', data=vols_long, jitter=True, hue = 'scan_status', dodge = False, alpha=0.7, palette = custom_palette)

plt.legend().remove()
# Change x-axis labels
new_labels = ['Intraparenchymal\n(IPH)', 'Extra-axial\n(EAH)']
# Remove the x-axis title
ax.set_xlabel('')
ax.set_ylabel('Volume in mL', fontsize = 14)
ax.set_xticklabels(new_labels)

# Rotate labels and change font size
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
#plt.savefig('results/blast-ct_qc/large_absolute_hemorrhage_values.png')

high_volumes = vols_long[vols_long['value'] > 100]
print(len(high_volumes))
high_volumes.groupby(['variable'])['patient_excluded'].value_counts()

# remove the first scan
# find minimum scan_number for each patient (1 patient's first scan was excluded so it starts at 2)
first_scan_id = tbi_cohort_qc.groupby(['unique_study_id'])['scan_number'].idxmin()
first_scan = tbi_cohort_qc.loc[first_scan_id].reset_index(drop=True).sort_values(['scan_number'], ascending = False)

follow_up_scan = tbi_cohort_qc[~(tbi_cohort_qc['report_num_temp'].isin(first_scan['report_num_temp']))]

print('Number of patients with follow-up scans:', follow_up_scan[['unique_study_id']].nunique())

# Convert data to long format
vols_change_long = pd.melt(follow_up_scan, 
                           id_vars = ['unique_study_id', 'id', 'scan_number', 'quality_control_metric', 'exclude_id', 'patient_excluded',  'reason_excluded'], 
                           value_vars = [ 'change_iph_volume_first_scan', 'change_eah_volume_first_scan'])

# Define conditions
conditions = [
    (vols_change_long['exclude_id'] == 1) & (vols_change_long['variable'] == 'change_iph_volume_first_scan'),
    (vols_change_long['exclude_id'] == 1) & (vols_change_long['variable'] == 'change_eah_volume_first_scan'),
    (vols_change_long['exclude_id'] == 0) & (vols_change_long['variable'] == 'change_iph_volume_first_scan'),
    (vols_change_long['exclude_id'] == 0) & (vols_change_long['variable'] == 'change_eah_volume_first_scan'),
]

# Define corresponding choices
choices = ['IPH-Exclude', 'EAH-Exclude', 'IPH', 'EAH']

# Apply np.select
vols_change_long['scan_status'] = np.select(conditions, choices, default='Unknown')

# Box Plot + Strip Plot
plt.figure(figsize=(8, 5))

# Define a custom palette
custom_palette = {
    'IPH-Exclude': 'black',
    'EAH-Exclude': 'black',  
    'IPH': 'tomato',
    'EAH': '#17C717'
}

palette_box = {
    'change_iph_volume_first_scan': 'tomato', 
    'change_eah_volume_first_scan': '#17C717'
}

sns.boxplot(x='variable', y='value', data=vols_change_long, hue = 'variable', dodge = False, whis=[0, 100], width = 0.6, palette=palette_box)
ax = sns.stripplot(x='variable', y='value', data=vols_change_long, jitter=True, hue = 'scan_status', dodge = False, alpha=0.7, palette = custom_palette)
plt.legend().remove()
# Change x-axis labels
new_labels = ['Intraparenchymal\n(IPH)', 'Extra-axial\n(EAH)']
# Remove the x-axis title
ax.set_xlabel('')
ax.set_ylabel('Change of Volume in mL', fontsize = 14)
ax.set_xticklabels(new_labels)

# Rotate labels and change font size
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
#plt.savefig('results/blast-ct_qc/large_changes_hemorrhage_values.png')

vols_change_long['value_abs'] = vols_change_long['value'].abs()

### Prepare censored cohort
# keep only the included patients OR patients who had surgery by the second scan - we will try to censor these patients
two_ml_annotated_censored = two_ml_annotated[(two_ml_annotated['exclude'] == 0) | (two_ml_annotated['second_scan_post_surgery_trauma'] == 1)]

print('Number of patients', two_ml_annotated_censored[['unique_study_id']].nunique())

#### Review list of excluded scans for the `two_ml_annotated_censored` cohort
two_ml_annotated_censored_scan_review = pd.merge(two_ml_annotated_censored[['unique_study_id', 'surgery', 'surgery_type', 'first_scan_after_surgery', 'exclude', 'notes']],
                                                 scans_to_exclude,
                                                 on = ['unique_study_id'],
                                                 how = 'inner')

#two_ml_annotated_censored_scan_review[['unique_study_id']].nunique()

#### Add all scans to the `two_ml_annotated_censored` cohort

# drop unneeded columns to prepare merging with 2ml cohort
tbi_cohort_clean = tbi_cohort_clean.drop(columns = ['injury', '041224_review_5ml', '04102024_review', '04092024_5ml_review', '04072024_review','radiology_report_exercepts', 
                                 'update_cohorted', 'potential_hematoma_expansion_case', 'exclude', 'potential_hematoma_expansion_case_v2', 
                                 'surgery','surgery_type', 'artifact', 'reason_excluded', 'notes'])

# merge new censored dataframe with our tbi_cohort_clean dataframe in order to add back all scans
two_ml_annotated_censored_scans = pd.merge(two_ml_annotated_censored[['unique_study_id', 'injury', 'exclude', 'surgery', 'surgery_type', 'first_scan_after_surgery', 
                                                                      'second_scan_post_surgery_trauma', 'artifact', 'prior_neurological_surgery', 
                                                                      'reason_excluded', 'notes']],
                                           tbi_cohort_clean,
                                           on = ['unique_study_id'])

### Remove excluded scans
two_ml_annotated_censored_scans_initial = two_ml_annotated_censored_scans.copy()

# exclude reports indicated
two_ml_annotated_censored_scans = two_ml_annotated_censored_scans[~(two_ml_annotated_censored_scans['id'].isin(scans_to_exclude['id_to_remove']))]

#### Review blast-ct QC metric for remaining scans

### Review for portable scanner
#two_ml_annotated_censored_scans[(two_ml_annotated_censored_scans['report'].str.contains('8-slice', case = False))][['unique_study_id', 'id', 'report']]
#two_ml_annotated_censored_scans[(two_ml_annotated_censored_scans['report'].str.contains('portable', case = False))][['unique_study_id', 'id', 'report']]

print('Unique number of censored patients and scans:', two_ml_annotated_censored_scans[['unique_study_id', 'id']].nunique())

### Ensure all included patients have their first scan
first = two_ml_annotated_censored_scans[two_ml_annotated_censored_scans['scan_number']==1]
first_ids = first['unique_study_id']
tbi_2ml_cohort_ids = two_ml_annotated_censored_scans['unique_study_id']
first['unique_study_id'].nunique()

# this will reveal whether any patients do not have a scan_number==1
print('Checking if any patients do not have a scan_number==1')
list(set(tbi_2ml_cohort_ids) - set(first_ids))

### Do all first scans still have > 2ml of hemorrhage
first[(first['iph_predicted_volume_ml']>=2) | (first['eah_predicted_volume_ml']>=2)]['unique_study_id'].nunique()

### Recalculate change from first scan
# We will recalculated the change from the first scan after having excluded some patient's first scan

# ensure data is arranged by patient and scan number
two_ml_annotated_censored_scans = two_ml_annotated_censored_scans.sort_values(['unique_study_id', 'scan_number'])

# calculate change by compartment
two_ml_annotated_censored_scans['iph_volume_first'] = two_ml_annotated_censored_scans.groupby(['unique_study_id'])['iph_predicted_volume_ml'].transform('first')
two_ml_annotated_censored_scans['eah_volume_first'] = two_ml_annotated_censored_scans.groupby(['unique_study_id'])['eah_predicted_volume_ml'].transform('first')
two_ml_annotated_censored_scans['ivh_volume_first'] = two_ml_annotated_censored_scans.groupby(['unique_study_id'])['ivh_predicted_volume_ml'].transform('first')

two_ml_annotated_censored_scans['change_iph_volume_first_scan'] = two_ml_annotated_censored_scans['iph_predicted_volume_ml'] - two_ml_annotated_censored_scans['iph_volume_first']         
two_ml_annotated_censored_scans['change_eah_volume_first_scan'] = two_ml_annotated_censored_scans['eah_predicted_volume_ml'] - two_ml_annotated_censored_scans['eah_volume_first']         
two_ml_annotated_censored_scans['change_ivh_volume_first_scan'] = two_ml_annotated_censored_scans['ivh_predicted_volume_ml'] - two_ml_annotated_censored_scans['ivh_volume_first']   

### Identify potential HE Cases
## identify max change for each patient
two_ml_annotated_censored_scans['max_change_iph_volume_first_scan'] = two_ml_annotated_censored_scans.groupby('unique_study_id')['change_iph_volume_first_scan'].transform('max')
two_ml_annotated_censored_scans['max_change_eah_volume_first_scan'] = two_ml_annotated_censored_scans.groupby('unique_study_id')['change_eah_volume_first_scan'].transform('max')
two_ml_annotated_censored_scans['max_change_ivh_volume_first_scan'] = two_ml_annotated_censored_scans.groupby('unique_study_id')['change_ivh_volume_first_scan'].transform('max')

#### Create columns for outcomes
#two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'].value_counts()

## first fill NaN with `second_scan_post_surgery_trauma`
two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'] = np.where(two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'].isnull(), 0, two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'])

#two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'].value_counts()

two_ml_annotated_censored_scans['outcome_6ml'] = np.where((two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'] == 0) & 
((two_ml_annotated_censored_scans['max_change_iph_volume_first_scan'] >= 6) | (two_ml_annotated_censored_scans['max_change_eah_volume_first_scan'] >= 6)), 1, 0) 

two_ml_annotated_censored_scans['outcome_8ml'] = np.where((two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'] == 0) & 
((two_ml_annotated_censored_scans['max_change_iph_volume_first_scan'] >= 8) | (two_ml_annotated_censored_scans['max_change_eah_volume_first_scan'] >= 8)), 1, 0) 

two_ml_annotated_censored_scans['outcome_10ml'] = np.where((two_ml_annotated_censored_scans['second_scan_post_surgery_trauma'] == 0) & 
((two_ml_annotated_censored_scans['max_change_iph_volume_first_scan'] >= 10) | (two_ml_annotated_censored_scans['max_change_eah_volume_first_scan'] >= 10)), 1, 0)

### Prepare data for modeling
tbi_cohort_clean_to_model = two_ml_annotated_censored_scans[[
    'unique_study_id', 
    'report_num_temp', 
    'scan_number',
    'StudyDate_Time_format', 
    'quality_control_metric', 
    'injury',
    'second_scan_post_surgery_trauma',
    'surgery',
    'surgery_type',
    'first_scan_after_surgery',
    'artifact',
    'outcome_6ml',
    'outcome_8ml',
    'outcome_10ml',
    'notes',
    'iph_predicted_volume_ml',
    'eah_predicted_volume_ml',
    'ivh_predicted_volume_ml',
    'oedema_predicted_volume_ml',
    'change_iph_volume_first_scan',	
    'change_eah_volume_first_scan', 
    'change_ivh_volume_first_scan',
    'max_change_iph_volume_first_scan',	
    'max_change_eah_volume_first_scan', 
    'max_change_ivh_volume_first_scan',
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
    'prediction_ivh_Ventricle_ml']]

print('Number of unique patients for modeling:', tbi_cohort_clean_to_model[['unique_study_id']].nunique())

#### Select the first scan of each patient
tbi_cohort_clean_to_model = tbi_cohort_clean_to_model.sort_values(['unique_study_id', 'StudyDate_Time_format'])
tbi_cohort_clean_to_model_first = tbi_cohort_clean_to_model.groupby('unique_study_id').first().reset_index(drop=False)

print('Total number of unique patients and scans:', tbi_cohort_clean_to_model_first[['unique_study_id']].nunique())

### Clean Dataset
tbi_cohort_clean_to_model_first.drop(['notes'], axis=1, inplace=True)

print('Number of unique patients for modeling (first scan for modeling):', tbi_cohort_clean_to_model[['unique_study_id']].nunique())

#### Save copy of dataset before transformation
# save full dataset
# v2 saved on 04.30.2024
# tbi_cohort_clean_to_model.to_csv('data/modeling/tbi_data_all_scans_v2.csv', index = False)
# tbi_cohort_clean_to_model_first.to_csv('data/modeling/tbi_data_first_scan_v2.csv', index = False)

# v3 saved on 6.05.2024 with cleaned up injury labels
# saved on 6.14.2024 with cleaned up surgery labels
tbi_cohort_clean_to_model_first.to_csv('data/modeling/tbi_data_first_scan_v3.csv', index = False)
tbi_cohort_clean_to_model.to_csv('data/modeling/tbi_data_all_scans_v3.csv', index = False)

# to check outputs are the same
# ran on 10/28/2024
# tbi_cohort_clean_to_model_first.to_csv('data/modeling/TO_CHECK_tbi_data_first_scan_v3.csv', index = False)
# tbi_cohort_clean_to_model.to_csv('data/modeling/TO_CHECK_tbi_data_all_scans_v3.csv', index = False)