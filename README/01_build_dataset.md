# Protocol for building NU-TBI dataset
---

This protocol details the order or scripts and programs needed to curate our TBI cohort, starting from radiology reports.

---

### Main Directory

Directory: `NU_TBI/`
```

├── data/
|   ├── HemorrhageProject/
|   ├── processed/  
|   ├────├ blast_ct_batches/
|   ├────├ blast_ct_predictions/
|
├── nifti_images/  
|
├── notebooks/  
|
├── README/
|   ├── 01_build_dataset.md 
|   ├── 02_process_nifti.md
|   ├── 03_run_blast_ct.md
|
├── scripts/  
|   ├── 01_prepare_radiology_reports.py
|   ├── 02_run_traumaScanner.py
|   ├── 03_identifyTBI_patients.py
|   ├── 04_prepare_cohort_scans_.py
|   ├── 05_abstract_dicom_header.py
|   ├── 06_prepare_axial_brain_windows.py
|   ├── 07_prepare_blast_ct.py
|   ├── 08_prepare_blast_predictions.py
|   ├── 07_eval_blast_predictions.py
|
├── README.md                        
|
├── .gitignore
```
---

### To Prepare Dataset

---

Follow the order of scripts below to create initial TBI dataset:

1. `scripts/01_prepare_radiology_reports.py`
2. `scripts/02_run_traumaScanner.py` - *Note: currently wrapping this into a package so that I can create a dedicated script for calling this*
3. `scripts/03_identifyTBI_patients.py` - *Note: need to create a dedicated script from my notebook – can refer to the notebook for the notes/decisions re: cleaning, but can simplify the script for cleaning and upload to GitHub*
4. `scripts/04_prepare_cohort_scans.py`
5. `scripts/05_abstract_dicom_header.py`
6. `scripts/06_prepare_axial_brain_windows.py`

Included scans for analysis have been prepared and are ready to be processed as NIFTI files

7. Follow `README/02_process_nifti.md`
    - `scripts/process_nifti.sh`

8. `scripts/07_prepare_blast_ct.py`

Run blast-ct to segement hematomas and quantify lesion volumes

9. Follow `README/03_run_blast_ct.md`

10. `scripts/08_prepare_blast_predictions.py`
11. `scripts/09_eval_blast_predictions.py`

---