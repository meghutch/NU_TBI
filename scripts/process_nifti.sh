#!/bin/bash

for i in $(cat /share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/axial_brain_folders.txt); do
   echo $i
   output_dir=/share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/nifti_images/
   # modify output to remove everything before actual patient specific image folder 
   output_folder=${i##*/images/}
   mkdir -p $output_dir$output_folder
   echo $output_dir$output_folder
   ./dcm2niix -f %i_%s -o $output_dir$output_folder $i
done

