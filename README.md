# mightee-hi

This scripts are for flagging, self-calibration, continuum subtraction and broadband spectral line imaging of MeerKAT L-band data. They were made for the MIGHTEE HI project, but are generic. It is assumed the data are in 32k mode and are already reference-calibrated. A FITS image that contains a deconvolution mask (10240 x 10240, 1" pixels) is also assumed to be available (e.g. from the MIGHTEE continuum imaging). Make a scratch folder, clone this repo into it, and symlink the parent Measurement Set (with `.ms` suffix) to that path. The scripts below generate shell scripts that will submit batch jobs for each stage to the ilifu cluster slurm queue. The `oxkat-0.42.sif` container is required, and should be picked up automatically.

* **00_split_ms.py:** This will split the master MS into a MMS with a sub-MS for each scan to aid parallelisation. Three relatively clean sub-bands are split out, labeled LOW, MID and HIGH, with Doppler correction applied to the resulting MMS. The split data is placed into a sub-folder corresponding to the sub-band name. The LOW band will have a factor 4 frequency averaging applied, MID and HIGH will have their native frequency resolution retained.

* **01_process_mms.py:** This script should be symlinked into the LOW, MID or HIGH folders, so `cd` to that and run it there. The clean mask should have a suffix `mask.fits` and be placed in the sub-folder also. This script will perform flagging, imaging, continuum model frequency interpolation, self-calibration, continuum subtraction, and an additional round of flagging. Flagging and self-calibration are parallelised by scan. Band-integrated images before and after self-cal and continuum subtraction are produced to verify these processes before proceeding to the spectral line imaging.

* **02_image_channels.py:** Running this script (which is also symlinked into the sub-band folder) should make per-channel images from the results of the above two scripts. It must be run separately for each of the LOW, MID and HIGH sub-bands. In the case of MID the imaging will be parallelised using four instances of wsclean due to the large number of channels. Primary beam correction will be performed. There will be a per-channel image with and without this correction, as well as images of the PSF and primary beam model.

There are some auxiliary scripts for creating actual cube FITS images and quick-look movies, but those steps are somewhat manual for now. 
