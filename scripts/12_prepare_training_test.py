# Date: 10-29-2024
# Author: Meghan Hutch
# Objective: To prepare the training and test set for modeling.

import os

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

os.chdir('/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI')

## load data
# April 30, 2024
# tbi_data = pd.read_csv('data/modeling/tbi_data_first_scan_v2.csv')
# tbi_data_all = pd.read_csv('data/modeling/tbi_data_all_scans_v2.csv')

# October 29, 2024: used v3 for splitting - this is the same as '_v2' results, except with additional cleaning on columns: 'Injury', 'surgery_type', and floating point precession (rounded to three decimal places) of blast-ct predictions
tbi_data = pd.read_csv('data/modeling/tbi_data_first_scan_v3.csv')
tbi_data_all = pd.read_csv('data/modeling/tbi_data_all_scans_v3.csv')

print('Number of patients:', len(tbi_data))

print('Unique number of patients and scans:', tbi_data_all[['unique_study_id', 'report_num_temp']].nunique())

print('Unique number of Included Patients (patients who are not post-surgery):', tbi_data_all[tbi_data_all['second_scan_post_surgery_trauma']==0][['unique_study_id', 'report_num_temp']].nunique())

print('Unique number of Included Patients with 6ml increase:', tbi_data[tbi_data['second_scan_post_surgery_trauma']==0]['outcome_6ml'].value_counts())

print('Unique number of Included Patients with 8ml increase:',tbi_data[tbi_data['second_scan_post_surgery_trauma']==0]['outcome_8ml'].value_counts())

print('Unique number of Included Patients with 10ml increase:',tbi_data[tbi_data['second_scan_post_surgery_trauma']==0]['outcome_10ml'].value_counts())

### Prepare X and y sets
X = tbi_data.drop(['outcome_6ml', 'outcome_8ml', 'outcome_10ml'], axis=1)[['unique_study_id', 'surgery', 'surgery_type', 'second_scan_post_surgery_trauma', 'iph_predicted_volume_ml', 'eah_predicted_volume_ml', 'oedema_predicted_volume_ml', 'ivh_predicted_volume_ml']]
       
y = tbi_data[['unique_study_id', 'second_scan_post_surgery_trauma', 'outcome_6ml', 'outcome_8ml', 'outcome_10ml']]

# split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1300, shuffle=True)

print('Print len(X_train):', len(X_train))
print('Print len(y_train):', len(y_train))
print('Print len(X_test):', len(X_test))
print('Print len(y_test):', len(y_test))

### Save data for modeling
# May 2nd, 2024 -- data with identifier - no stratifcation by any outcome
#X_train.to_csv('data/modeling/model1_structured_radiographic/X_train_id_v3.csv')
#y_train.to_csv('data/modeling/model1_structured_radiographic/y_train_id_v3.csv')

#X_test.to_csv('data/modeling/model1_structured_radiographic/X_test_id_v3.csv')
#y_test.to_csv('data/modeling/model1_structured_radiographic/y_test_id_v3.csv')

# October 29, 2024 - resaving for modeling with correct input file version (see note above)
X_train.to_csv('data/modeling/model1_structured_radiographic/X_train_id_v4.csv')
y_train.to_csv('data/modeling/model1_structured_radiographic/y_train_id_v4.csv')

X_test.to_csv('data/modeling/model1_structured_radiographic/X_test_id_v4.csv')
y_test.to_csv('data/modeling/model1_structured_radiographic/y_test_id_v4.csv')


# save without id
del X_train['unique_study_id']
del y_train['unique_study_id']
del X_test['unique_study_id']
del y_test['unique_study_id']

# May 2nd, 2024 -- data without identifier - no stratifcation by any outcome
#X_train.to_csv('data/modeling/model1_structured_radiographic/X_train_v3.csv')
#y_train.to_csv('data/modeling/model1_structured_radiographic/y_train_v3.csv')

#X_test.to_csv('data/modeling/model1_structured_radiographic/X_test_v3.csv')
#y_test.to_csv('data/modeling/model1_structured_radiographic/y_test_v3.csv')

# October 29, 2024 resaving for modeling with correct input file version (see note above)
X_train.to_csv('data/modeling/model1_structured_radiographic/X_train_v4.csv')
y_train.to_csv('data/modeling/model1_structured_radiographic/y_train_v4.csv')

X_test.to_csv('data/modeling/model1_structured_radiographic/X_test_v4.csv')
y_test.to_csv('data/modeling/model1_structured_radiographic/y_test_v4.csv')
