# Date: 03-22-2024
# Author: Meghan Hutch
# Objective: Merge the suidDFFound.csv (brain image metadata) with post_traumatic_hemorrhage_search.xlsx (annotated for trauma and hemorrhage)
# Output: data/processed/suid_rad_reports.csv

import os
import pandas as pd

# remove whitespace that exists before and after strings
def remove_whitespace(string): 
    processed_string = string.rstrip()
    processed_string = processed_string.lstrip()
    return processed_string

# load in the image meta-data ; these images look to have been a large extraction for brain CTs between a range of dates
print('loading in suidDFFound.csv')
suid = pd.read_csv('data/suidDFFound.csv', index_col = 0)
print('length of suid dataframe', len(suid))

# evaluate whether each row is a unique accession number
# if so, the unique `SearchAccession` ids should equal the length of the dataframe
print('evaluating whether each row is a unique accession number - TRUE if so')
print(len(suid[['SearchAccession']].drop_duplicates()) == len(suid))

print('pre-processing suid dataframe')

# convert `StudyDate_format` into a datatime variable
suid['StudyDate_format'] = pd.to_datetime(suid['StudyDate'], format='%Y%m%d')

# pre-process accession text to remove '*CT' prefix
suid['SearchAccession_temp'] = suid['SearchAccession'].str.replace("*","")
suid['SearchAccession_temp'] = suid['SearchAccession_temp'].str.replace("CT","")

# remove whitespace
suid['SearchAccession_temp'] = suid['SearchAccession_temp'].apply(lambda x:remove_whitespace(x))

# import annotated radiology reports; these reports have been annotated by 
# the key-word matching and NLP detection method described by data/post_traumatic_hemorrhage/search_criteria.txt
print('importing radiology reports')
rad_reports = pd.read_excel('data/post_traumatic_hemorrhage_search.xlsx',
                             engine = 'openpyxl')

print('length of radiology reports', len(rad_reports))

# pre-process rad_reports `accession` numbers similarly to suid
# pre-process accession text to remove '*CT' prefix
print('pre-processing radiology reports')
rad_reports['accession_temp'] = rad_reports['accession'].str.replace("*","")
rad_reports['accession_temp'] = rad_reports['accession_temp'].str.replace("CT","")

# remove whitespace
rad_reports['accession_temp'] = rad_reports['accession_temp'].apply(lambda x:remove_whitespace(x))

# combine rad_reports with the suid dataframe
print('merging rad_reports with suid dataframe')
suid_rad_reports = pd.merge(suid,
                            rad_reports, 
                            left_on = 'EDWAccession', 
                            right_on = 'accession',
                            how = 'inner')  

# add report_num_temp which is used throughout other scripts
suid_rad_reports['report_num_temp'] = suid_rad_reports['EDWAccession'].str.replace(r'.*CT', 'CT', regex=True)

print('length of merged dataset', len(suid_rad_reports))

# delete identifying information
del suid_rad_reports['Name']
del suid_rad_reports['DOB']

# add previously generated unique ids as initially assigned via notebooks/03_process_image_data.ipynb 

# load data
print('loading data')
unique_ids = pd.read_csv('data/suid_reports_identifiers_master_list.csv')

# merge dataframes
print('merging dataframes by accession numbers')
suid_rad_reports = pd.merge(suid_rad_reports, 
                            unique_ids[['unique_study_id', 'SearchAccession', 'VNAAccession', 'EDWAccession']],
                            on = ['SearchAccession', 'VNAAccession', 'EDWAccession'],
                            how = 'inner')

print('length of merged dataset with identifiers', len(suid_rad_reports))

# rearrange column order
print('rearranging column order')
suid_rad_reports = suid_rad_reports[['unique_study_id',  'report_num_temp', 'SearchAccession', 'VNAAccession', 'StudyID', 'EDWAccession',
                                     'StudyDescription', 'StudyDate', 'StudyTime', 'SUIDs',
                                     'StudyDate_format', 'SearchAccession_temp', 'order_reason', 'accession',
                                     'trauma', 'fall', 'injury', 'assault', 'auto', 'any trauma',
                                     ' hemorrhage ', 'posttraumatic hemorrhage', 'report', 'accession_temp']]

# save merged dataset 
print('saving merged dataset to data/processed/suid_rad_reports.csv')
suid_rad_reports.to_csv('data/processed/suid_rad_reports.csv', index = False)


