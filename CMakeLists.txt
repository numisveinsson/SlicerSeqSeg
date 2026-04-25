cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SeqSegVesselSegmentation)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/numisveinsson/SlicerSeqSeg")
set(EXTENSION_CONTRIBUTORS "Numi Sveinsson Cepero (UT Austin)")
set(EXTENSION_DESCRIPTION "SeqSegVesselSegmentation: 3D Slicer extension for vascular (and other tubular) seed-based segmentation using the SeqSeg Python package and nnUNet. Pretrained nnUNet weights install from the module via download buttons—no manual training.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/numisveinsson/SlicerSeqSeg/main/seqseg/Resources/Icons/seqseg.jpg")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/numisveinsson/SlicerSeqSeg/main/seqseg/Resources/screenshot/coronary.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

# Python package dependencies
set(EXTENSION_BUILD_SUBDIRECTORY ".")
set(EXTENSION_SUPERBUILD_BINARY_DIR ${CMAKE_CURRENT_BINARY_DIR})

# Specify Python packages that need to be installed
if(NOT DEFINED Slicer_USE_PYTHONQT_WITH_TCL)
  set(Slicer_USE_PYTHONQT_WITH_TCL OFF)
endif()

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(seqseg)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
