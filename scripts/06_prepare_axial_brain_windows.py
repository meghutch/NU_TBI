# Date: 03-26-2024
# Author: Meghan Hutch
# Objective: Identify axial brain scans and brain tissue windows

import ast
import time
import pandas as pd

# load list of TBI scan file paths
tbi_scan_list = pd.read_csv('data/processed/tbi_scan_file_paths.csv')

start = time.time()

dicom_table =  pd.read_csv('data/processed/dicom_header_table_processed.csv')

end = time.time()
print((end - start)/60)

# create a separate list of the main scan folder name
data = [s.split('/images/') for s in dicom_table['file_path']]
data = [item[1] for item in data]
data = [s.split('/') for s in data]
data = [item[0] for item in data]

# print total number of unique scans 
print('printing number of unique scan folders', len(set(data)))

# keep axial scans
print('filtering axial scans')
dicom_table_axial = dicom_table[dicom_table['Image Type'].str.contains('AXIAL', case = False)]

# count unique accession numbers
print('printing number of unique accession numbers after filtering axial images', len(dicom_table_axial['Accession Number'].drop_duplicates()))

# create separate list of axial folder paths
print('creating separate list of axial folders')
start = time.time()

axial_folder_list = []

for line in dicom_table_axial['file_path']:
    line2 = line.split('CT.')[0] 
    axial_folder_list.append(line2)

end = time.time()
print((end - start)/60)

# remove duplicates
print('printing length of axial_folder_list', len(axial_folder_list))
print('removing duplicates')
axial_folder_list = list(set(axial_folder_list))
print('printing length of axial_folder_list after duplicate removal', len(axial_folder_list))

# remove non-brain images
axial_brain_folder_list = [s.lower() for s in axial_folder_list if not "coronal" in s.lower()]
axial_brain_folder_list = [s.lower() for s in axial_brain_folder_list if not "sag" in s.lower()]
axial_brain_folder_list = [s.lower() for s in axial_brain_folder_list if not "chest" in s.lower()]
axial_brain_folder_list = [s.lower() for s in axial_brain_folder_list if not "abdomen" in s.lower()]
axial_brain_folder_list = [s.lower() for s in axial_brain_folder_list if not "spine" in s.lower()]
axial_brain_folder_list = [s.lower() for s in axial_brain_folder_list if not "facial_bones" in s.lower()]
axial_brain_folder_list = [s.lower() for s in axial_brain_folder_list if not "lung" in s.lower()]

print('printing number of axial brain images', len(axial_brain_folder_list))

# Resave dicom-header table to only include these cleaned up brain scans
print('removing non-axial brain scans from the dicom_table')
img_accessions = '|'.join(axial_brain_folder_list)

dicom_table_axial_brain = dicom_table_axial[dicom_table_axial['file_path'].str.contains(img_accessions, case = False)]

print('printing length of dicom_table_axial_brain',len(dicom_table_axial_brain))

# add folder name to help us sort by window level/center and width
dicom_table_axial_brain['image_type_temp'] = [s.split('/random/') for s in dicom_table_axial_brain['file_path']]
dicom_table_axial_brain['image_type_temp'] = [item[1] for item in dicom_table_axial_brain['image_type_temp']]
dicom_table_axial_brain['image_type_temp'] = [s.split('/CT') for s in dicom_table_axial_brain['image_type_temp']]
dicom_table_axial_brain['image_type_temp'] = [item[0] for item in dicom_table_axial_brain['image_type_temp']]

## abstract Window Center and Window Width
print('pre-processing of Window Center and Window Width')
# Convert strings to lists, leave integers as they are
dicom_table_axial_brain['numbers_center'] = [ast.literal_eval(str(s)) if isinstance(s, str) else [s] for s in dicom_table_axial_brain['Window Center']]
dicom_table_axial_brain['numbers_width'] = [ast.literal_eval(str(s)) if isinstance(s, str) else [s] for s in dicom_table_axial_brain['Window Width']]

# Extract first element of each list or take the integer value directly
dicom_table_axial_brain['first_center_number'] = [lst[0] if isinstance(lst, list) else lst for lst in dicom_table_axial_brain['numbers_center']]
dicom_table_axial_brain['first_width_number'] = [lst[0] if isinstance(lst, list) else lst for lst in dicom_table_axial_brain['numbers_width']]

print('filtering window and center to keep brain windowed images')
dicom_table_axial_brain_window = dicom_table_axial_brain[(dicom_table_axial_brain['first_center_number'] <= 100) & (dicom_table_axial_brain['first_width_number'] <= 400)]

print('printing length of dicom_table_axial_brain', len(dicom_table_axial_brain))
print('printing length of dicom_table_axial_brain_window', len(dicom_table_axial_brain_window))
print('printing count of unique accession numbers', len(dicom_table_axial_brain_window[['Accession Number']].drop_duplicates()))

# create list of folder paths
axial_brain_window_folder_list = dicom_table_axial_brain_window['file_path'].to_list()
print('printing length of unique folder paths', len(set(axial_brain_window_folder_list)))

# save list of folder paths to identify images for nifti processing
print('saving list to axial_brain_folders.txt')
with open(r'data/processed/axial_brain_folders.txt', 'w') as fp:
    for folder in axial_brain_window_folder_list:
        # write each item on a new line
        fp.write("%s\n" % folder)
    print('Done')

# save updated dicom header
print('saving updated dicom header')
dicom_table_axial_brain_window.to_csv('data/processed/dicom_header_table_axial_brain_window_processed.csv', index = False)

print('preparation of axial brain window scans complete')