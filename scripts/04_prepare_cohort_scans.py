# Date: 03-25-2024
# Author: Meghan Hutch
# Objective: To create a clean list of folder locations for the scans to run blast-ct on

import pandas as pd

# import scans to include 
tbi_scans = pd.read_csv('data/processed/20240325_1136_tbi_patients_scans_to_include.csv')

# remove whitespace that exists before and after strings to aid in pre-processing
def remove_whitespace(string): 
    processed_string = string.rstrip()
    processed_string = processed_string.lstrip()
    return processed_string

## add scan identifiers

## identifier lists
# Batch1 are the first set of scans that were pulled
batch1 = pd.read_csv('data/HemorrhageProject/Transfer20211010/LocalIdentifierList.txt',
                    header = None, delimiter = '|', names = ['patient_id', 'accession', 'folder'])

# Batch2 are the updated list of scans we requested 
batch2 = batch2 = pd.read_csv('data/HemorrhageProject/HemorrhageTransfer20231128/LocalIdentifierList.txt',
                    header = None, delimiter = '|', names = ['patient_id', 'accession', 'folder'])

# add file paths for scans
batch1['file_path'] = '/share/hemorrhage_project/Transfer20211010/images/' + batch1['folder']
batch2['file_path'] = '/share/hemorrhage_project/HemorrhageTransfer20231128/images/' + batch2['folder']

# combine batches 
batch_all = pd.concat([batch1, batch2])

# remove empty spaces from the joining of strings for `file_path`
batch_all['file_path'] = batch_all['file_path'].str.replace(" ", "")

# pre-process accession text to remove '*CT20' prefix
tbi_scans['accession_temp'] = tbi_scans['report_num_temp'].str.replace("*","")
tbi_scans['accession_temp'] = tbi_scans['accession_temp'].str.replace(r'^.*?CT20', '', regex=True).astype('str')
tbi_scans['accession_temp'] = tbi_scans['accession_temp'].str.replace("CT","")
# remove white spaces
tbi_scans['accession_temp'] = tbi_scans['accession_temp'].apply(lambda x:remove_whitespace(x))

# pre-process accession text to remove '*CT20' prefix
batch_all['accession_temp'] = batch_all['accession'].str.replace("*","")
batch_all['accession_temp'] = batch_all['accession_temp'].str.replace(r'^.*?CT20', '', regex=True).astype('str')
batch_all['accession_temp'] = batch_all['accession_temp'].str.replace(r"^.*?CT","")
# remove white spaces
batch_all['accession_temp'] = batch_all['accession_temp'].apply(lambda x:remove_whitespace(x))

# merge our list of tbi_scans for our identified cohort and merge with the file paths
tbi_scans_id = pd.merge(tbi_scans,
                        batch_all, 
                        on = 'accession_temp',
                        how = 'inner').drop_duplicates()

# print total number of scans
print('print total number of scans to match', tbi_scans['report_num_temp'].nunique())
print('print number of scans that matched', tbi_scans_id['report_num_temp'].nunique())

# identify whether any missing images
tbi_scans_review = pd.merge(tbi_scans, 
                            batch_all, 
                            on = 'accession_temp',
                            how = 'outer',
                            indicator = True)

# create new data frame of images that we did not find a matching accession number for
tbi_scans_missing = tbi_scans_review[tbi_scans_review['_merge']=='left_only'].drop_duplicates()

# print number of 'missing' scans
print('print number of mising scans', tbi_scans_missing.nunique())

# merge with VNA number instead of accession number
# create a new dataframe to match onto VNAAccession
vna_suid_df = tbi_scans_missing[['report_num_temp', 'unique_study_id', 'SearchAccession', 'VNAAccession', 'EDWAccession', 'StudyID', 'SearchAccession', 'accession_temp']].drop_duplicates()

# pre-process accession text to remove '*CT20' prefix
vna_suid_df['VNAAccession_temp'] = vna_suid_df['VNAAccession'].str.replace("*","")
vna_suid_df['VNAAccession_temp'] = vna_suid_df['VNAAccession_temp'].str.replace(r'^.*?CT20', '', regex=True).astype('str')
vna_suid_df['VNAAccession_temp'] = vna_suid_df['VNAAccession_temp'].str.replace("CT|1CT","")
# remove white spaces
vna_suid_df['VNAAccession_temp'] = vna_suid_df['VNAAccession_temp'].apply(lambda x:remove_whitespace(x))

# perform the merge with VNAAccession
tbi_scans_vna = pd.merge(batch_all,
                        vna_suid_df,
                        left_on = 'accession_temp',
                        right_on = 'VNAAccession_temp',
                        how = 'right')

# check if any columns are missing
print('checking if any columns have missing values', tbi_scans_vna.isnull().sum())

# merge the list of 'found' scans (tbi_scans_vna) with the initial tbi_scans dataframe 
# merge by `unique_study_id` and `report_num_temp`
tbi_scans_id2 = pd.merge(tbi_scans,
                         tbi_scans_vna[['unique_study_id', 'report_num_temp', 'VNAAccession_temp', 'folder', 'file_path', 'patient_id']], 
                         on = ['unique_study_id', 'report_num_temp'],
                         how = 'inner')

# check if any columns are missing
print('checking if any columns have missing values', tbi_scans_id2.isnull().sum())

# merge all scans with associated file paths together
tbi_scans_all = pd.concat([tbi_scans_id, tbi_scans_id2]).drop_duplicates()

# print total number of scans
print('print total number of scans', tbi_scans_all['report_num_temp'].nunique())

# check if we found file paths for all scans
if(tbi_scans_all['report_num_temp'].nunique() == tbi_scans['report_num_temp'].nunique()):
    print('all scans and file paths found. saving list of scans')
    tbi_scans_all.to_csv('data/processed/tbi_scan_file_paths.csv', index = False) 
else:
    print('missing scans were identified. please review!')

