<p align="center">
  <img src="seqseg/Resources/Icons/seqseg_logo.png" alt="SeqSeg logo" width="96">
</p>

# SeqSeg

![Example coronary segmentation in 3D Slicer](seqseg/Resources/screenshot/coronary.png)

**SeqSeg** is a [3D Slicer](https://www.slicer.org/) extension for clinicians and researchers who want to segment tubular structures (for example coronary or other vessels) from CT or MR without drawing full contours. You place two seed points and a radius hint; the module runs the [SeqSeg](https://github.com/numisveinsson/SeqSeg) workflow with nnUNet models and loads the result back into Slicer.

## Modules

- **seqseg** — Scripted module in the Segmentation category: selects a volume, two fiducial markups, nnUNet paths and options, runs SeqSeg, then loads segmentation (.mha) and optional surface (.vtp) outputs.

## Publication

If you use SeqSeg or this extension in research, please cite:

Sveinsson Cepero, N., Shadden, S.C. SeqSeg: Learning Local Segments for Automatic Vascular Model Construction. *Ann Biomed Eng* **53**, 158–179 (2025). [https://doi.org/10.1007/s10439-024-03611-z](https://doi.org/10.1007/s10439-024-03611-z)

**Known patents:** None known to the extension authors; if that changes, update this section and the extension description in `CMakeLists.txt`.

## Prerequisites

The SeqSeg Python package is automatically installed when you first use the extension. However, you can also install it manually if preferred:

```bash
pip install seqseg
```

Or use the provided setup script:

```bash
python setup_dependencies.py
```

## Usage

1. **Load your volume**: Use the Data module or File menu to load your medical imaging volume.

2. **Create seed points**: 
   - Go to the Markups module
   - Create two fiducial points by clicking "Add" and then placing points in your volume
   - These will serve as seed points for the SeqSeg algorithm

3. **Use the SeqSeg module**:
   - Navigate to the SeqSeg module (found in the Segmentation category)
   - Select your input volume
   - Select your two seed point markups nodes
   - Set the radius estimate (approximate size of the structure you want to segment)
   - Configure nnUNet settings:
     - **Download pretrained weights**: Click "Download Pretrained Weights" button to automatically download model weights from [Zenodo](https://zenodo.org/records/15020477) (236.3 MB). The weights will be saved to `~/SeqSeg_Weights/nnUNet_results` by default, and the path will be set automatically.
     - Or manually set nnUNet results path to your trained models directory
     - Choose nnUNet type (3d_fullres or 2d)
     - Set train dataset name (default: Dataset005_SEQAORTANDFEMOMR for CT, or Dataset006_SEQAORTANDFEMOCT for MR)
     - Choose fold (usually "all" or specific fold number)
   - Create or select an output segmentation node
   - Click "Run SeqSeg"

## Module Interface

### Inputs
- **Input Volume**: The medical imaging volume to segment (NIfTI format recommended)
- **Seed Point 1**: First markups fiducial node (must contain at least one point)
- **Seed Point 2**: Second markups fiducial node (must contain at least one point)
- **Radius Estimate**: Estimated radius of the structure to segment in millimeters (range: 0.1 - 100 mm)

### Advanced Parameters
- **Max Steps**: Maximum number of tracking steps (1 - 10000, default: 10)
- **Max Branches**: Maximum number of vessel branches to follow (1 - 100, default: 2)
- **Max Steps per Branch**: Maximum steps per vessel branch (1 - 1000, default: 5)
- **Image Unit**: Unit of the medical image (mm or cm, default: mm)

### nnUNet Configuration
- **nnUNet Results Path**: Path to the nnUNet results folder containing trained models
  - **Download Pretrained Weights Button**: Click to automatically download pretrained model weights (236.3 MB) from [Zenodo](https://zenodo.org/records/15020477). Default location: `~/SeqSeg_Weights/nnUNet_results`
- **nnUNet Type**: Type of nnUNet model (3d_fullres or 2d, default: 3d_fullres)
- **Train Dataset**: Name of dataset used to train nnUNet (default: Dataset005_SEQAORTANDFEMOMR for CT, Dataset006_SEQAORTANDFEMOCT for MR)
- **Fold**: Which fold to use for nnUNet model (all, 0, 1, 2, 3, 4, default: all)

### Output
- **Output Segmentation**: Segmentation node where the result will be stored
- **Output Directory**: Directory where SeqSeg saves all results including segmentation (.mha), surface mesh (.vtp), and intermediate files

### Visualization Features
After running SeqSeg, use the visualization buttons to load results:
- **Load Latest Segmentation**: Automatically loads the most recent .mha segmentation file as a proper segmentation overlay
- **Load Latest Surface Mesh**: Loads the most recent .vtp surface mesh as a 3D model with red coloring
- **Browse All Outputs**: Opens a dialog to view and selectively load all output files (segmentations, meshes, etc.)

Output files are organized in the structure:
```
output_directory/
├── images/           # Input volume (converted to .nii.gz)
├── seeds.json       # Seed points in SeqSeg format
└── output/          # SeqSeg results
    ├── *_seg_containing_seeds_*_steps.mha  # Segmentation
    └── *_surface_mesh_*_steps.vtp          # Surface mesh
```

## Technical Details

The extension follows the [SeqSeg CLI interface](https://github.com/numisveinsson/SeqSeg/tree/main):

1. **Creates data directory structure**: Sets up a temporary workspace with an `images/` subdirectory
2. **Saves input volume**: Exports the input volume as a NIfTI file in the `images/` subdirectory
3. **Creates seeds.json**: Generates a `seeds.json` file in the data directory with the format:
   ```json
   [
     {
       "name": "case_001",
       "seeds": [
         [[x1, y1, z1], [x2, y2, z2], radius_estimate]
       ]
     }
   ]
   ```
   Where `name` matches the image filename (without extension), the first point is the start seed, the second point is the direction seed, and the third value is the radius estimate in millimeters.
4. **Executes SeqSeg**: Runs the SeqSeg command-line tool with parameters:
   - `-data_dir`: Path to the temporary data directory
   - `-nnunet_results_path`: Path to trained nnUNet models
   - `-nnunet_type`: Model architecture (3d_fullres or 2d)
   - `-train_dataset`: Dataset name used for training
   - `-fold`: Cross-validation fold
   - `-img_ext`: Image file extension (.nii.gz)
   - `-config_name`: Configuration name (default: global)
   - `-outdir`: Output directory for results
   - `-unit`: Image coordinate units (mm or cm)
   - `-max_n_steps`: Maximum tracking steps
   - `-max_n_branches`: Maximum number of branches
   - `-max_n_steps_per_branch`: Maximum steps per branch
5. **Loads results**: Imports the resulting segmentation file back into 3D Slicer
6. **Converts to segmentation**: Converts the volume to a Slicer segmentation node for visualization

## Troubleshooting

- **"SeqSeg package not found"**: The extension will attempt automatic installation. If this fails, install manually using `pip install seqseg` or run `python setup_dependencies.py`
- **"Seed point is not defined"**: Make sure both markups nodes contain at least one fiducial point
- **"SeqSeg execution failed"**: Check that nnUNet models are properly installed and configured
- **"No output segmentation file found"**: SeqSeg may have failed silently - check the Slicer console for detailed error messages
- **Segmentation appears in wrong location**: Check that your volume and seed points are in the same coordinate system
- **Installation fails**: Try running 3D Slicer as administrator/with elevated privileges, or install dependencies manually

## Prerequisites for SeqSeg

SeqSeg requires:
1. nnUNet framework properly installed
2. Trained nnUNet models (e.g., Dataset005_SEQAORTANDFEMOMR or Dataset006_SEQAORTANDFEMOCT)
3. Proper nnUNet environment variables set
4. Compatible image formats (NIfTI recommended)

For more information about SeqSeg, see the [official SeqSeg repository](https://github.com/numisveinsson/SeqSeg).

## Development

This extension is developed in **SlicerSeqSeg**. For issues and contributions, use this repository’s issue tracker.

Add the GitHub topic **`3d-slicer-extension`** under repository settings so the project appears with other [Slicer extensions](https://github.com/topics/3d-slicer-extension).

## License

This extension is licensed under the **Apache License, Version 2.0**. See [LICENSE.txt](LICENSE.txt).

The [SeqSeg](https://github.com/numisveinsson/SeqSeg) Python package is a separate project; see that repository for its license and citation information.
