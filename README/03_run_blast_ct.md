# Protocol for blast-ct
---

This details the entire pipeline for performing hematoma segementation and volume quantification using [blast-ct](https://github.com/biomedia-mira/blast-ct). 

### Run blast-ct

**1. Create new virtual env**

`conda create -n blast-ct2 python=3.7.13`

`conda activate blast-c2`

`pip install git+https://github.com/biomedia-mira/blast-ct.git`

**2. Check gpu usage**

`nvidia-smi`

Check GPU usage to determine which GPU to call device. As explained by Will Thompson, the following GPUs are paired together on the Naidech lab server:

- 0,1
- 2,3
- 4,5
- 6,7

**3. Run inference on images:**

**Make sure to be in directory NU_TBI/**

```python 
blast-ct-inference --job-dir /share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/blast_ct_predictions/batch_1/ --test-csv-path /share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/blast_ct_batches/blast_ct_batch_1.csv --device 0 --overwrite true
```

**Localize hematoma:**

**March 27, 2024:**
device 0 - batch1, batch8
device 1 - batch2, batch9
device 2 - batch3, batch10
device 3 - batch4, batch11
device 4 - batch5 
device 5 - batch6, 
device 6 - batch13, batch12
device 7 - batch7


```python
blast-ct-inference --job-dir /share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/blast_ct_predictions/batch_1/ --test-csv-path /share/nubar/Neurotrauma/hematoma_expansion/NU_TBI/data/processed/blast_ct_batches/blast_ct_batch_1.csv --device 0 --do-localisation True --save-atlas-and-brain-mask-native-space True --overwrite True
```
