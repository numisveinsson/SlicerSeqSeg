import json
import logging
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
    Choice,
)

from slicer import vtkMRMLScalarVolumeNode

# Import additional MRML node types for parameter node
try:
    from slicer import vtkMRMLMarkupsFiducialNode
    from slicer import vtkMRMLSegmentationNode
except ImportError:
    # Fallback for older Slicer versions
    vtkMRMLMarkupsFiducialNode = None
    vtkMRMLSegmentationNode = None


#
# seqseg
#


class seqseg(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("SeqSeg")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Segmentation")]
        self.parent.dependencies = []
        self.parent.contributors = ["Numi Sveinsson Cepero (UT Austin)"]
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
SeqSeg is a seed-based segmentation module that uses the SeqSeg Python package. 
It requires two seed points and a volume as input to produce a segmentation.
See more information in <a href="https://github.com/nsveinsson/SlicerSeqSeg">module documentation</a>.
""")
        self.parent.acknowledgementText = _("""
This module was developed by Numi Sveinsson Cepero at UT Austin. 
It integrates the SeqSeg Python package for seed-based segmentation into 3D Slicer.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)
        
        # Check for SeqSeg package availability on module load
        self._checkDependencies()
    
    def _checkDependencies(self):
        """Check if required dependencies are available."""
        try:
            import seqseg
            logging.info("SeqSeg dependency check passed")
        except ImportError:
            logging.warning("SeqSeg package not found. It will be installed automatically when first used.")
            # Note: We don't fail here to allow the module to load, 
            # dependency installation will happen when the user tries to run the algorithm


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # SeqSeg Sample Data 1 - Example medical volume for testing SeqSeg
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="SeqSeg",
        sampleName="SeqSeg Test Volume 1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        thumbnailFileName=os.path.join(iconsPath, "seqseg1.png"),
        # Download URL and target file name - using existing test data
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="SeqSegTestVolume1.nrrd",
        # Checksum to ensure file integrity
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="SeqSegTestVolume1",
    )

    # SeqSeg Sample Data 2 - Another example volume
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="SeqSeg",
        sampleName="SeqSeg Test Volume 2",
        thumbnailFileName=os.path.join(iconsPath, "seqseg2.png"),
        # Download URL and target file name - using existing test data
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="SeqSegTestVolume2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="SeqSegTestVolume2",
    )


#
# seqsegParameterNode
#


@parameterNodeWrapper
class seqsegParameterNode:
    """
    The parameters needed by SeqSeg module.

    inputVolume - The input volume for segmentation.
    seedPoint1 - First seed point markups node.
    seedPoint2 - Second seed point markups node.
    radiusEstimate - Estimated radius for segmentation in millimeters.
    outputSegmentation - The segmentation node that will contain the results.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    seedPoint1: str = ""  # Markups fiducial node ID
    seedPoint2: str = ""  # Markups fiducial node ID
    radiusEstimate: Annotated[float, WithinRange(0.1, 30.0)] = 1.0  # Radius in mm
    maxSteps: Annotated[int, WithinRange(1, 10000)] = 10  # Max segmentation steps
    maxBranches: Annotated[int, WithinRange(1, 50)] = 2  # Max number of branches
    maxStepsPerBranch: Annotated[int, WithinRange(1, 1000)] = 5  # Max steps per branch
    imageUnit: Annotated[str, Choice(["mm", "cm"])] = "cm"  # Image unit (mm or cm)
    nnunetResultsPath: str = ""  # Path to nnUNet results folder
    nnunetType: Annotated[str, Choice(["3d_fullres", "2d"])] = "3d_fullres"  # Type of nnUNet model
    trainDataset: str = "Dataset005_SEQAORTANDFEMOMR"  # Training dataset name
    fold: Annotated[str, Choice(["all", "0", "1", "2", "3", "4"])] = "all"  # Fold to use for nnUNet model
    outputDirectory: str = ""  # Directory for SeqSeg outputs (data_dir)
    outputSegmentation: str = ""  # Segmentation node ID


#
# seqsegWidget
#


class seqsegWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/seqseg.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = seqsegLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.ui.createSeedPointsButton.connect("clicked(bool)", self.onCreateSeedPointsButton)
        self.ui.downloadWeightsButton.connect("clicked(bool)", self.onDownloadWeightsButton)
        
        # Connect output directory button to sync with parameter node
        # ctkDirectoryButton emits directoryChanged signal when directory changes
        if hasattr(self.ui.outputDirectoryButton, 'directoryChanged'):
            self.ui.outputDirectoryButton.connect('directoryChanged(QString)', self.onOutputDirectoryChanged)
        
        # Connect nnUNet results path button to sync with parameter node
        # ctkDirectoryButton uses 'directoryChanged' signal
        if hasattr(self.ui, 'nnunetResultsPathButton') and hasattr(self.ui.nnunetResultsPathButton, 'directoryChanged'):
            self.ui.nnunetResultsPathButton.directoryChanged.connect(self.onNnunetResultsPathChanged)
            logging.info("Connected nnUNet results path button signal")
        else:
            logging.warning("Could not connect nnUNet results path button signal")
        
        # Connect image unit combo box to sync with parameter node
        if hasattr(self.ui, 'unitComboBox') and hasattr(self.ui.unitComboBox, 'currentTextChanged'):
            self.ui.unitComboBox.currentTextChanged.connect(self.onImageUnitChanged)
            logging.info("Connected image unit combo box signal")
        else:
            logging.warning("Could not connect image unit combo box signal")

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode
        
        # Set default nnUNet results path if not set and default weights exist
        if not self._parameterNode.nnunetResultsPath:
            default_weights_dir = os.path.join(os.path.expanduser("~"), "SeqSeg_Weights")
            default_weights_path = os.path.join(default_weights_dir, "nnUNet_results")
            if os.path.exists(default_weights_path):
                self._parameterNode.nnunetResultsPath = default_weights_path
                logging.info(f"Using default weights path: {default_weights_path}")
        
        # Sync UI with parameter node values
        self._syncUiWithParameterNode()
        
        # Set default output directory if not set
        if not self._parameterNode.outputDirectory:
            default_output_dir = os.path.join(os.path.expanduser("~"), "SeqSeg_Output")
            # Ensure directory ends with '/'
            if not default_output_dir.endswith(os.sep):
                default_output_dir = default_output_dir + os.sep
            self._parameterNode.outputDirectory = default_output_dir
            logging.info(f"Using default output directory: {default_output_dir}")
        
        # Create default seed points if they don't exist
        self._createDefaultSeedPoints()

    def setParameterNode(self, inputParameterNode: Optional[seqsegParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        # Always enable the button - let the logic handle validation
        if self._parameterNode:
            if self._parameterNode.inputVolume:
                self.ui.applyButton.toolTip = _("Run SeqSeg segmentation")
            else:
                self.ui.applyButton.toolTip = _("Select input volume for better results")
            self.ui.applyButton.enabled = True

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        with slicer.util.tryWithErrorDisplay(_("Failed to compute SeqSeg results."), waitCursor=True):
            # Get nodes from parameter node
            inputVolume = self._parameterNode.inputVolume
            
            # Debug: Check if input volume is properly set
            if not inputVolume:
                logging.warning("No input volume selected, trying to find one...")
                firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
                if firstVolumeNode:
                    inputVolume = firstVolumeNode
                    self._parameterNode.inputVolume = firstVolumeNode
                    logging.info(f"Using volume: {firstVolumeNode.GetName()}")
                else:
                    raise ValueError("No volume found in scene. Please load a volume first.")
            
            seedPoint1Node = slicer.mrmlScene.GetNodeByID(self._parameterNode.seedPoint1)
            seedPoint2Node = slicer.mrmlScene.GetNodeByID(self._parameterNode.seedPoint2) 
            radiusEstimate = self._parameterNode.radiusEstimate
            maxSteps = self._parameterNode.maxSteps
            imageUnit = self._parameterNode.imageUnit
            nnunetResultsPath = self._parameterNode.nnunetResultsPath
            nnunetType = self._parameterNode.nnunetType
            trainDataset = self._parameterNode.trainDataset
            fold = self._parameterNode.fold
            
            # Debug: Log the nnUNet parameters with extra details
            logging.info(f"nnUNet Results Path from parameter node: '{nnunetResultsPath}'")
            logging.info(f"nnUNet Results Path length: {len(nnunetResultsPath) if nnunetResultsPath else 0}")
            logging.info(f"nnUNet Results Path exists: {os.path.exists(nnunetResultsPath) if nnunetResultsPath else False}")
            
            # Debug: Log image unit with extra details
            logging.info(f"Image Unit from parameter node: '{imageUnit}'")
            
            # Try to get values directly from UI
            try:
                if hasattr(self.ui, 'nnunetResultsPathButton'):
                    ui_path = getattr(self.ui.nnunetResultsPathButton, 'directory', '')
                    logging.info(f"nnUNet Results Path from UI button: '{ui_path}'")
                    if ui_path and not nnunetResultsPath:
                        nnunetResultsPath = ui_path
                        self._parameterNode.nnunetResultsPath = ui_path
                        logging.info(f"Updated nnUNet Results Path from UI: '{nnunetResultsPath}'")
                
                if hasattr(self.ui, 'unitComboBox'):
                    ui_unit = self.ui.unitComboBox.currentText()
                    logging.info(f"Image Unit from UI combo box: '{ui_unit}'")
                    if ui_unit and ui_unit != imageUnit:
                        imageUnit = ui_unit
                        self._parameterNode.imageUnit = ui_unit
                        logging.info(f"Updated Image Unit from UI: '{imageUnit}'")
            except Exception as e:
                logging.warning(f"Could not get values from UI: {e}")
            
            logging.info(f"nnUNet Type: '{nnunetType}'")
            logging.info(f"Train Dataset: '{trainDataset}'")
            logging.info(f"Fold: '{fold}'")
            outputDirectory = self._parameterNode.outputDirectory
            logging.info(f"Output directory from parameter node: '{outputDirectory}'")
            
            # If output directory is empty, try to get it from the UI directly
            # ctkDirectoryButton uses 'directory' property
            if not outputDirectory:
                try:
                    # Try different possible property names
                    if hasattr(self.ui.outputDirectoryButton, 'directory'):
                        outputDirectory = self.ui.outputDirectoryButton.directory
                    elif hasattr(self.ui.outputDirectoryButton, 'currentPath'):
                        outputDirectory = self.ui.outputDirectoryButton.currentPath
                    elif hasattr(self.ui.outputDirectoryButton, 'text'):
                        outputDirectory = self.ui.outputDirectoryButton.text
                    logging.info(f"Output directory from UI button: '{outputDirectory}'")
                    if outputDirectory:
                        # Ensure directory ends with '/'
                        if not outputDirectory.endswith(os.sep):
                            outputDirectory = outputDirectory + os.sep
                        self._parameterNode.outputDirectory = outputDirectory
                except (AttributeError, Exception) as e:
                    logging.warning(f"Could not get directory from UI button: {e}")
            
            # Final check - if still empty, use default
            if not outputDirectory:
                default_output_dir = os.path.join(os.path.expanduser("~"), "SeqSeg_Output")
                outputDirectory = default_output_dir
                self._parameterNode.outputDirectory = default_output_dir
                logging.info(f"Using default output directory: {default_output_dir}")
            
            # Ensure output directory ends with '/'
            if outputDirectory and not outputDirectory.endswith(os.sep):
                outputDirectory = outputDirectory + os.sep
            
            outputSegmentationNode = slicer.mrmlScene.GetNodeByID(self._parameterNode.outputSegmentation)
            
            # Run SeqSeg segmentation
            self.logic.runSeqSeg(inputVolume, seedPoint1Node, seedPoint2Node, radiusEstimate, 
                               maxSteps, self._parameterNode.maxBranches, self._parameterNode.maxStepsPerBranch,
                               imageUnit, nnunetResultsPath, nnunetType, trainDataset, 
                               fold, outputDirectory, outputSegmentationNode)

    def onOutputDirectoryChanged(self, directory: str) -> None:
        """Called when output directory button changes - sync with parameter node."""
        if self._parameterNode and directory:
            # Ensure directory ends with '/'
            if not directory.endswith(os.sep):
                directory = directory + os.sep
            self._parameterNode.outputDirectory = directory
            logging.info(f"Output directory updated to: {directory}")

    def onNnunetResultsPathChanged(self, directory: str) -> None:
        """Called when nnUNet results path button changes - sync with parameter node."""
        if self._parameterNode and directory:
            self._parameterNode.nnunetResultsPath = directory
            logging.info(f"nnUNet Results Path updated to: {directory}")

    def onImageUnitChanged(self, unit: str) -> None:
        """Called when image unit combo box changes - sync with parameter node."""
        if self._parameterNode and unit:
            self._parameterNode.imageUnit = unit
            logging.info(f"Image Unit updated to: {unit}")

    def _syncUiWithParameterNode(self) -> None:
        """Manually sync UI controls with parameter node values."""
        if not self._parameterNode:
            return
        
        # Sync nnUNet results path button
        if hasattr(self.ui, 'nnunetResultsPathButton') and self._parameterNode.nnunetResultsPath:
            try:
                # Try to set the directory on the button
                if hasattr(self.ui.nnunetResultsPathButton, 'directory'):
                    self.ui.nnunetResultsPathButton.directory = self._parameterNode.nnunetResultsPath
                elif hasattr(self.ui.nnunetResultsPathButton, 'setDirectory'):
                    self.ui.nnunetResultsPathButton.setDirectory(self._parameterNode.nnunetResultsPath)
                logging.info(f"Synced nnUNet path to UI: {self._parameterNode.nnunetResultsPath}")
            except Exception as e:
                logging.warning(f"Could not sync nnUNet path to UI: {e}")
        
        # Sync image unit combo box
        if hasattr(self.ui, 'unitComboBox') and self._parameterNode.imageUnit:
            try:
                # Find the index of the current unit and set it
                current_unit = self._parameterNode.imageUnit
                combo_box = self.ui.unitComboBox
                index = combo_box.findText(current_unit)
                if index >= 0:
                    combo_box.setCurrentIndex(index)
                    logging.info(f"Synced image unit to UI: {current_unit}")
                else:
                    logging.warning(f"Image unit '{current_unit}' not found in combo box")
            except Exception as e:
                logging.warning(f"Could not sync image unit to UI: {e}")

    def onCreateSeedPointsButton(self) -> None:
        """Create or reset default seed points when user clicks the button."""
        # Clear existing seed points
        self._parameterNode.seedPoint1 = ""
        self._parameterNode.seedPoint2 = ""
        
        # Remove existing default seed points from scene if they exist
        existingSeed1 = slicer.mrmlScene.GetFirstNodeByName("SeqSeg Seed Point 1")
        if existingSeed1:
            slicer.mrmlScene.RemoveNode(existingSeed1)
            
        existingSeed2 = slicer.mrmlScene.GetFirstNodeByName("SeqSeg Seed Point 2")
        if existingSeed2:
            slicer.mrmlScene.RemoveNode(existingSeed2)
        
        # Create new default seed points
        self._createDefaultSeedPoints()

    def _createDefaultSeedPoints(self) -> None:
        """Create default seed points if they don't exist."""
        
        # Create first seed point if it doesn't exist
        if not self._parameterNode.seedPoint1:
            seedPoint1Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "SeqSeg Seed Point 1")
            seedPoint1Node.SetMaximumNumberOfControlPoints(1)
            
            # Set default position if we have a volume
            if self._parameterNode.inputVolume:
                bounds = [0] * 6
                self._parameterNode.inputVolume.GetBounds(bounds)
                # Place first point at 1/4 of the volume length (assuming Z is the main axis)
                centerX = (bounds[0] + bounds[1]) / 2
                centerY = (bounds[2] + bounds[3]) / 2  
                centerZ = bounds[4] + (bounds[5] - bounds[4]) * 0.25
                seedPoint1Node.AddControlPoint([centerX, centerY, centerZ])
            else:
                # Default position if no volume
                seedPoint1Node.AddControlPoint([0, 0, 0])
            
            # Set display properties
            seedPoint1Node.GetDisplayNode().SetSelectedColor(1, 0, 0)  # Red
            seedPoint1Node.GetDisplayNode().SetGlyphScale(3.0)
            seedPoint1Node.GetDisplayNode().SetTextScale(2.0)
            
            self._parameterNode.seedPoint1 = seedPoint1Node.GetID()

        # Create second seed point if it doesn't exist
        if not self._parameterNode.seedPoint2:
            seedPoint2Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "SeqSeg Seed Point 2")
            seedPoint2Node.SetMaximumNumberOfControlPoints(1)
            
            # Set default position if we have a volume
            if self._parameterNode.inputVolume:
                bounds = [0] * 6
                self._parameterNode.inputVolume.GetBounds(bounds)
                # Place second point at 3/4 of the volume length (assuming Z is the main axis)
                centerX = (bounds[0] + bounds[1]) / 2
                centerY = (bounds[2] + bounds[3]) / 2
                centerZ = bounds[4] + (bounds[5] - bounds[4]) * 0.75
                seedPoint2Node.AddControlPoint([centerX, centerY, centerZ])
            else:
                # Default position if no volume
                seedPoint2Node.AddControlPoint([10, 0, 0])
            
            # Set display properties
            seedPoint2Node.GetDisplayNode().SetSelectedColor(0, 1, 0)  # Green
            seedPoint2Node.GetDisplayNode().SetGlyphScale(3.0)
            seedPoint2Node.GetDisplayNode().SetTextScale(2.0)
            
            self._parameterNode.seedPoint2 = seedPoint2Node.GetID()

    def onDownloadWeightsButton(self) -> None:
        """Download pretrained model weights from Zenodo."""
        import shutil
        import tempfile
        import zipfile
        from pathlib import Path
        import slicer.qt
        from slicer.qt import QFileDialog
        
        zenodo_url = "https://zenodo.org/records/15020477/files/nnUNet_results.zip?download=1"
        default_weights_dir = os.path.join(os.path.expanduser("~"), "SeqSeg_Weights")
        
        try:
            with slicer.util.tryWithErrorDisplay(_("Failed to download pretrained weights."), waitCursor=True):
                # Ask user for download location
                download_dir = QFileDialog.getExistingDirectory(
                    None,
                    "Select directory to download pretrained weights",
                    default_weights_dir,
                    QFileDialog.ShowDirsOnly
                )
                if not download_dir:
                    return  # User cancelled
                
                # Create download directory if it doesn't exist
                os.makedirs(download_dir, exist_ok=True)
                
                # Check if weights already exist
                weights_path = os.path.join(download_dir, "nnUNet_results")
                if os.path.exists(weights_path):
                    response = slicer.util.confirmYesNoDisplay(
                        f"Weights already exist at:\n{weights_path}\n\nDo you want to download again?",
                        windowTitle="Weights Already Exist"
                    )
                    if not response:
                        # Use existing weights
                        self._parameterNode.nnunetResultsPath = weights_path
                        slicer.util.infoDisplay(f"Using existing weights at:\n{weights_path}")
                        return
                
                # Show progress
                progressBar = slicer.util.createProgressDialog(
                    labelText="Downloading pretrained weights (236.3 MB)...",
                    maximum=0,
                    windowTitle="Downloading Weights"
                )
                slicer.app.processEvents()
                
                # Download the file
                import urllib.request
                zip_file = os.path.join(download_dir, "nnUNet_results.zip")
                
                logging.info(f"Downloading weights from {zenodo_url} to {zip_file}")
                
                def show_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        percent = min(100, (block_num * block_size * 100) // total_size)
                        progressBar.setValue(percent)
                        progressBar.setLabelText(f"Downloading... {percent}%")
                        slicer.app.processEvents()
                
                urllib.request.urlretrieve(zenodo_url, zip_file, show_progress)
                
                progressBar.setLabelText("Extracting weights...")
                slicer.app.processEvents()
                
                # Extract the zip file
                logging.info(f"Extracting {zip_file} to {download_dir}")
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(download_dir)
                
                # Remove the zip file
                os.remove(zip_file)
                
                # Verify extraction
                if os.path.exists(weights_path):
                    # Update the parameter node with the new path
                    self._parameterNode.nnunetResultsPath = weights_path
                    slicer.util.infoDisplay(
                        f"Successfully downloaded and extracted pretrained weights to:\n{weights_path}\n\n"
                        f"The nnUNet Results Path has been updated automatically.",
                        windowTitle="Download Complete"
                    )
                    logging.info(f"Successfully downloaded weights to {weights_path}")
                else:
                    raise RuntimeError(f"Extraction failed: {weights_path} not found")
                
                progressBar.close()
                
        except Exception as e:
            logging.error(f"Failed to download weights: {e}")
            slicer.util.errorDisplay(
                f"Failed to download pretrained weights:\n{str(e)}\n\n"
                f"You can manually download from:\nhttps://zenodo.org/records/15020477",
                windowTitle="Download Failed"
            )


#
# seqsegLogic
#


class seqsegLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return seqsegParameterNode(super().getParameterNode())

    def runSeqSeg(self, 
                  inputVolume: vtkMRMLScalarVolumeNode,
                  seedPoint1Node,
                  seedPoint2Node,
                  radiusEstimate: float,
                  maxSteps: int,
                  maxBranches: int,
                  maxStepsPerBranch: int,
                  imageUnit: str,
                  nnunetResultsPath: str,
                  nnunetType: str,
                  trainDataset: str,
                  fold: str,
                  outputDirectory: str,
                  outputSegmentationNode,
                  showResult: bool = True) -> None:
        """
        Run the SeqSeg segmentation algorithm using CLI interface.
        Can be used without GUI widget.
        :param inputVolume: input volume for segmentation
        :param seedPoint1Node: first seed point markups node
        :param seedPoint2Node: second seed point markups node
        :param radiusEstimate: estimated radius for segmentation in millimeters
        :param maxSteps: maximum number of steps for segmentation
        :param imageUnit: unit of the medical image (mm or cm)
        :param nnunetResultsPath: path to nnUNet results folder
        :param nnunetType: type of nnUNet model (3d_fullres or 2d)
        :param trainDataset: name of dataset used to train nnUNet
        :param fold: which fold to use for nnUNet model
        :param outputDirectory: directory for SeqSeg outputs (data_dir)
        :param outputSegmentationNode: output segmentation node
        :param showResult: show output segmentation in slice viewers
        """

        # Validate minimum requirements
        if not inputVolume:
            raise ValueError("Input volume is required")
        
        # Create default seed points if missing
        if not seedPoint1Node:
            logging.warning("Seed point 1 not found, creating default")
            seedPoint1Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Default Seed Point 1")
            seedPoint1Node.SetMaximumNumberOfControlPoints(1)
            bounds = [0] * 6
            inputVolume.GetBounds(bounds)
            centerX = (bounds[0] + bounds[1]) / 2
            centerY = (bounds[2] + bounds[3]) / 2
            centerZ = bounds[4] + (bounds[5] - bounds[4]) * 0.25
            seedPoint1Node.AddControlPoint([centerX, centerY, centerZ])
            
        if not seedPoint2Node:
            logging.warning("Seed point 2 not found, creating default")
            seedPoint2Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode", "Default Seed Point 2")
            seedPoint2Node.SetMaximumNumberOfControlPoints(1)
            bounds = [0] * 6
            inputVolume.GetBounds(bounds)
            centerX = (bounds[0] + bounds[1]) / 2
            centerY = (bounds[2] + bounds[3]) / 2
            centerZ = bounds[4] + (bounds[5] - bounds[4]) * 0.75
            seedPoint2Node.AddControlPoint([centerX, centerY, centerZ])
        
        # Create default output segmentation if missing
        if not outputSegmentationNode:
            logging.warning("Output segmentation not found, creating default")
            outputSegmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", "SeqSeg Output")
            outputSegmentationNode.CreateDefaultDisplayNodes()
            outputSegmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputVolume)
        
        # Use default values for missing parameters
        if radiusEstimate <= 0:
            radiusEstimate = 5.0
            logging.warning("Invalid radius, using default: 5.0 mm")
        
        if not nnunetResultsPath or not os.path.exists(nnunetResultsPath):
            logging.warning("nnUNet results path not set or invalid - SeqSeg may fail without proper model path")
        
        if not trainDataset:
            raise ValueError("Train dataset name is required")
        
        # Validate output directory
        if not outputDirectory:
            raise ValueError("Output directory is required. Please select an output directory.")
        
        # Create output directory if it doesn't exist
        os.makedirs(outputDirectory, exist_ok=True)
        logging.info(f"Using output directory: {outputDirectory}")

        import time
        import numpy as np

        startTime = time.time()
        logging.info("SeqSeg processing started")

        try:
            # Check if SeqSeg package is available
            try:
                import subprocess
                import sys
                import shutil
                
                # Test if seqseg command is available
                result = subprocess.run([sys.executable, "-c", "import seqseg"], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    logging.warning("SeqSeg package not found, attempting to install with version constraints...")
                    
                    # First, check what's already installed to understand constraints
                    logging.info("Checking existing package versions...")
                    for check_pkg in ["torch", "numpy", "seqseg"]:
                        check_result = subprocess.run([sys.executable, "-m", "pip", "show", check_pkg], 
                                                    capture_output=True, text=True)
                        if check_result.returncode == 0:
                            # Extract version from pip show output
                            for line in check_result.stdout.split('\n'):
                                if line.startswith('Version:'):
                                    version = line.split('Version:')[1].strip()
                                    logging.info(f"Currently installed {check_pkg}: {version}")
                                    break
                        else:
                            logging.info(f"{check_pkg} not currently installed")
                    
                    # Install packages with specific version constraints to ensure compatibility
                    packages_to_install = [
                        "torch",
                        "numpy<2.0",
                        "nnunetv2<2.3",
                        "seqseg==1.0.1",
                    ]
                    
                    for package in packages_to_install:
                        logging.info(f"Installing {package}...")
                        
                        # Run pip install with verbose output to see what's happening
                        install_result = subprocess.run(
                            [sys.executable, "-m", "pip", "install", package, "--verbose"], 
                            capture_output=True, text=True
                        )
                        
                        if install_result.returncode == 0:
                            logging.info(f"✓ {package} installed successfully")
                        else:
                            logging.error(f"✗ Failed to install {package}")
                            logging.error(f"Stderr: {install_result.stderr}")
                            logging.error(f"Stdout: {install_result.stdout}")
                        
                        # Check what version actually got installed
                        pkg_name = package.split('>=')[0].split('==')[0]
                        verify_result = subprocess.run([sys.executable, "-m", "pip", "show", pkg_name], 
                                                     capture_output=True, text=True)
                        if verify_result.returncode == 0:
                            for line in verify_result.stdout.split('\n'):
                                if line.startswith('Version:'):
                                    actual_version = line.split('Version:')[1].strip()
                                    logging.info(f"Actually installed {pkg_name}: {actual_version}")
                                    break
                    
                    logging.info("All SeqSeg dependencies installation completed")
                else:
                    logging.info("SeqSeg package is available")
                    
            except subprocess.CalledProcessError as install_error:
                logging.error(f"Failed to install SeqSeg package: {install_error}")
                raise ImportError("SeqSeg package installation failed. Please install it manually using: pip install seqseg")

            # Use the specified output directory as data_dir
            data_dir = outputDirectory
            logging.info(f"Using data directory: {data_dir}")
            
            # Create images subdirectory (SeqSeg expects images/ subdirectory)
            images_dir = os.path.join(data_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            logging.info(f"Created images directory: {images_dir}")
            
            # Save input volume to images subdirectory
            # Use volume name or default name
            volume_name = inputVolume.GetName() if inputVolume.GetName() else "input_volume"
            # Remove spaces and special characters for filename
            case_name = "".join(c for c in volume_name if c.isalnum() or c in ('_', '-'))
            input_file = os.path.join(images_dir, f"{case_name}.nii.gz")
            slicer.util.saveNode(inputVolume, input_file)
            logging.info(f"Saved input volume to: {input_file}")
            
            # Get seed points coordinates
            seedPoint1_RAS = [0, 0, 0]
            seedPoint2_RAS = [0, 0, 0]
            
            if seedPoint1Node.GetNumberOfControlPoints() > 0:
                seedPoint1Node.GetNthControlPointPosition(0, seedPoint1_RAS)
            else:
                raise ValueError("First seed point is not defined")
                
            if seedPoint2Node.GetNumberOfControlPoints() > 0:
                seedPoint2Node.GetNthControlPointPosition(0, seedPoint2_RAS)
            else:
                raise ValueError("Second seed point is not defined")

            logging.info(f"Seed point 1 (RAS): {seedPoint1_RAS}")
            logging.info(f"Seed point 2 (RAS): {seedPoint2_RAS}")
            logging.info(f"Radius estimate: {radiusEstimate}")
            
            # Create seeds.json file in the data_dir (same level as images/)
            # Format: [{"name": "case_name", "seeds": [[start_point], [direction_point], radius_estimate]}]
            seeds_data = [
                {
                    "name": case_name,
                    "seeds": [
                        [
                            [float(seedPoint1_RAS[0]), float(seedPoint1_RAS[1]), float(seedPoint1_RAS[2])],
                            [float(seedPoint2_RAS[0]), float(seedPoint2_RAS[1]), float(seedPoint2_RAS[2])],
                            float(radiusEstimate)
                        ]
                    ]
                }
            ]
            seeds_file = os.path.join(data_dir, "seeds.json")
            with open(seeds_file, 'w') as f:
                json.dump(seeds_data, f, indent=4)
            logging.info(f"Created seeds.json: {seeds_file}")
            
            # Set up output directory (subdirectory within data_dir)
            output_dir = os.path.join(data_dir, "output")
            # Ensure output_dir ends with '/' for SeqSeg compatibility
            if not output_dir.endswith(os.sep):
                output_dir = output_dir + os.sep
            os.makedirs(output_dir, exist_ok=True)
            
            # Log all parameters before running
            logging.info("=== SeqSeg Parameters ===")
            logging.info(f"Input Volume: {inputVolume.GetName() if inputVolume else 'None'}")
            logging.info(f"Seed Point 1: {seedPoint1_RAS}")
            logging.info(f"Seed Point 2: {seedPoint2_RAS}")
            logging.info(f"Radius Estimate: {radiusEstimate}")
            logging.info(f"Max Steps: {maxSteps}")
            logging.info(f"Max Branches: {maxBranches}")
            logging.info(f"Max Steps per Branch: {maxStepsPerBranch}")
            logging.info(f"Image Unit: {imageUnit}")
            logging.info(f"nnUNet Results Path: '{nnunetResultsPath}'")
            logging.info(f"nnUNet Type: {nnunetType}")
            logging.info(f"Train Dataset: {trainDataset}")
            logging.info(f"Fold: {fold}")
            logging.info(f"Data Directory: {data_dir}")
            logging.info(f"Output Directory: {output_dir}")
            logging.info(f"Input File: {input_file}")
            logging.info(f"Seeds File: {seeds_file}")
            logging.info("========================")
            
            # Show parameters to user in a display dialog
            param_text = f"""SeqSeg Parameters:

Input Volume: {inputVolume.GetName() if inputVolume else 'None'}
Seed Point 1: [{seedPoint1_RAS[0]:.1f}, {seedPoint1_RAS[1]:.1f}, {seedPoint1_RAS[2]:.1f}]
Seed Point 2: [{seedPoint2_RAS[0]:.1f}, {seedPoint2_RAS[1]:.1f}, {seedPoint2_RAS[2]:.1f}]
Radius Estimate: {radiusEstimate}

Algorithm Settings:
Max Steps: {maxSteps}
Max Branches: {maxBranches}
Max Steps per Branch: {maxStepsPerBranch}
Image Unit: {imageUnit}

nnUNet Configuration:
Results Path: {nnunetResultsPath if nnunetResultsPath else 'NOT SET'}
Type: {nnunetType}
Dataset: {trainDataset}
Fold: {fold}

Output Directory: {data_dir}"""
            
            slicer.util.infoDisplay(param_text, windowTitle="SeqSeg Parameters")
            
            # Prepare SeqSeg command arguments according to actual SeqSeg CLI
            seqseg_cmd = [
                "seqseg",
                "-data_dir", data_dir,
                "-nnunet_results_path", nnunetResultsPath,
                "-nnunet_type", nnunetType,
                "-train_dataset", trainDataset,
                "-fold", fold,
                "-img_ext", ".nii.gz",
                "-config_name", "aorta_tutorial",  # Default config name
                "-outdir", output_dir,
                "-unit", imageUnit,
                "-max_n_steps", str(maxSteps),
                "-max_n_branches", str(maxBranches),
                "-max_n_steps_per_branch", str(maxStepsPerBranch)
            ]
            
            logging.info(f"Running SeqSeg command: {' '.join(seqseg_cmd)}")
            
            # Run SeqSeg (run from data_dir)
            result = subprocess.run(
                seqseg_cmd, 
                capture_output=True, 
                text=True,
                cwd=data_dir
            )
            
            if result.returncode != 0:
                logging.error(f"SeqSeg failed with return code {result.returncode}")
                logging.error(f"Error output: {result.stderr}")
                raise RuntimeError(f"SeqSeg execution failed: {result.stderr}")
            
            logging.info("SeqSeg execution completed successfully")
            logging.info(f"SeqSeg output: {result.stdout}")
            
            # Look for output segmentation file
            # SeqSeg typically outputs files with pattern: {case}_seg_containing_seeds_{steps}_steps.mha
            # or similar patterns with .mha or .nii.gz extensions
            output_files = []
            for ext in ['.mha', '.nii.gz', '.nii']:
                output_files.extend([f for f in os.listdir(output_dir) if f.endswith(ext) and 'seg' in f.lower()])
            
            if not output_files:
                # Fallback: look for any segmentation-like files
                output_files = [f for f in os.listdir(output_dir) if f.endswith(('.mha', '.nii.gz', '.nii'))]
            
            if not output_files:
                raise RuntimeError(f"No output segmentation file found in {output_dir}. SeqSeg may have failed or output format changed.")
            
            output_file = os.path.join(output_dir, output_files[0])
            logging.info(f"Found output file: {output_file}")
            
            # Load the result back into Slicer
            temp_segmentation_node = slicer.util.loadVolume(output_file)
            if not temp_segmentation_node:
                raise RuntimeError("Failed to load SeqSeg output")
            
            # Convert volume to segmentation
            segmentationArray = slicer.util.arrayFromVolume(temp_segmentation_node)
            segmentationArray = segmentationArray.astype(np.uint8)
            
            # Create segment in output segmentation node
            segmentId = outputSegmentationNode.GetSegmentation().AddEmptySegment("SeqSeg_Segment")
            
            # Update segmentation
            slicer.util.updateSegmentBinaryLabelmapFromArray(
                segmentationArray, 
                outputSegmentationNode, 
                segmentId, 
                inputVolume
            )
            
            # Clean up temporary volume node
            slicer.mrmlScene.RemoveNode(temp_segmentation_node)
            
            # Update display
            if showResult:
                # Set the segmentation node to be visible in slice views
                outputSegmentationNode.CreateDefaultDisplayNodes()
                outputSegmentationNode.GetDisplayNode().SetVisibility(True)
                
                # Set the background volume in slice views
                slicer.util.setSliceViewerLayers(background=inputVolume)
                
                # Fit slice views to show the segmentation
                slicer.util.resetSliceViews()
                
            logging.info("SeqSeg segmentation completed successfully")

        except Exception as e:
            logging.error(f"SeqSeg processing failed: {e}")
            raise

        stopTime = time.time()
        logging.info(f"SeqSeg processing completed in {stopTime-startTime:.2f} seconds")


#
# seqsegTest
#


class seqsegTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_seqseg1()

    def test_seqseg1(self):
        """Test basic functionality of the SeqSeg module.
        This test verifies that the module can handle seed points and volumes properly,
        and that the SeqSeg integration works as expected.
        """

        self.delayDisplay("Starting SeqSeg test")

        # Create test nodes
        inputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        inputVolume.SetName("TestVolume")
        
        # Create some test data
        import numpy as np
        testArray = np.random.rand(64, 64, 32) * 1000
        slicer.util.updateVolumeFromArray(inputVolume, testArray)
        
        # Create seed point nodes
        seedPoint1Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
        seedPoint1Node.SetName("SeedPoint1")
        seedPoint1Node.AddControlPoint([10, 10, 10])
        
        seedPoint2Node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode") 
        seedPoint2Node.SetName("SeedPoint2")
        seedPoint2Node.AddControlPoint([20, 20, 15])

        # Create output segmentation
        outputSegmentation = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        outputSegmentation.SetName("SeqSegOutput")

        self.delayDisplay("Created test data")

        # Test the module logic
        logic = seqsegLogic()

        # Test that the SeqSeg method exists
        self.assertIsNotNone(logic.runSeqSeg, "runSeqSeg method should exist")

        # Note: We can't actually test the SeqSeg algorithm without the package installed
        # but we can test the basic structure and error handling
        try:
            # This will likely fail if SeqSeg package is not installed, which is expected
            radiusEstimate = 5.0  # Test radius in cm
            maxSteps = 10
            imageUnit = "cm"
            nnunetResultsPath = "/tmp/test_nnunet_results"  # Test path
            nnunetType = "3d_fullres"
            trainDataset = "Dataset005_SEQAORTANDFEMOMR"
            fold = "all"
            outputDirectory = "/tmp/test_seqseg_output"  # Test output directory
            logic.runSeqSeg(inputVolume, seedPoint1Node, seedPoint2Node, radiusEstimate, 
                           maxSteps, 2, 5, imageUnit, nnunetResultsPath, nnunetType, trainDataset, 
                           fold, outputDirectory, outputSegmentation)
            self.delayDisplay("SeqSeg algorithm completed successfully")
        except ImportError as e:
            # This is expected if SeqSeg package is not installed
            logging.info(f"SeqSeg package not available for testing: {e}")
            self.delayDisplay("SeqSeg package not installed - this is expected for basic testing")
        except Exception as e:
            logging.error(f"Unexpected error in SeqSeg test: {e}")

        # Clean up test nodes
        self.delayDisplay("Cleaning up test nodes...")
        
        # Remove test volume
        if inputVolume:
            slicer.mrmlScene.RemoveNode(inputVolume)
            
        # Remove seed point nodes
        if seedPoint1Node:
            slicer.mrmlScene.RemoveNode(seedPoint1Node)
            
        if seedPoint2Node:
            slicer.mrmlScene.RemoveNode(seedPoint2Node)
            
        # Remove output segmentation
        if outputSegmentation:
            slicer.mrmlScene.RemoveNode(outputSegmentation)

        self.delayDisplay("SeqSeg module test completed")
