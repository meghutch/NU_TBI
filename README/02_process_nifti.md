# Protocol for nifti processing
---

This details the process of converting dicom issues to nifti file format.

### Installations and setup

**Convert .dcm images to .nii**
	
Install and run `dcm2niix` to convert dicom images to NIfTI (Neuroimaging Informatics Technology Initiative) file format (.nii)

* [Install dcm2niix](https://github.com/rordenlab/dcm2niix/blob/master/README.md#install):
	     
```linux
curl -fLO https://github.com/rordenlab/dcm2niix/releases/latest/download/dcm2niix_lnx.zip
```

*Notes: I installed in my home directory: `/home/mrh1996`. Thus, to use, I should be in my home directory*

To use `dcm2niix`, we also need to install [FSL](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation/Linux):

- I copied over the source code `/home/mrh1996/fslinstaller.py` (*not sure if I am remembering correctly, but I believe I optained this by registering [here](https://fsl.fmrib.ox.ac.uk/fsldownloads_registration)*
- To install `FSL`:

```linux
conda activate tbi-env

python fslinstaller
```

*This will prompt you to where you want FSL to install. I chose my own directory (`/home/mrh1996/fsl`) since the default requires sudo rights:*

*Note: do not create an fsl folder in the chosen directory. The install will do this for us.*

To [run](https://github.com/rordenlab/dcm2niix#running) `dcm2niix`:

- Review the [Userguide](https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage#General_Usage) for details on running the program and specifying the named output of the processed-file.
- I prepared and ran the following bash script in my home directory:

```linux
#start new screen session
screen 

#go to home directory (or whereever fsl/dcm2nii is saved)
cd home/mrh1996

sh /share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/scripts/process_nifti.sh > output_process_nifti.txt
```

This scrpt saves the nifti files to the indicated output script in the `process_nifti.sh` file. In our case: `NU_TBI/nifti_images`

*Note: This step takes about 10 hours to complete for ~6,000 imaging studies*

