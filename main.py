from constants import *
from mainWindow import Ui_MainWindow
from videoUtils import VideoMan
import subprocess
import platform
import time

def normalize_magnification(text):
    """Return the canonical CyberInv form of a magnification, or None if invalid.
    Accepts what the user is likely to type: 20, 20X, 6.2, 6d2, 6d2X -> 20X, 6d2X."""
    match = re.match(r"^(\d+)([.d](\d+))?X?$", text.strip())
    if match is None:
        return None
    whole, _, frac = match.groups()
    return f"{whole}d{frac}X" if frac else f"{whole}X"
# DD. MULTISTACKER
# multistacker = Mult()
# interp. program's main object
class Mult(QMainWindow):
    def __init__(self):
        super().__init__()
        self.videoManager = VideoMan()  #!!!
        self.mainUI = Ui_MainWindow()
        self.mainUI.setupUi(self)
        # Timer for updating webcam feed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_webcam_feed)
        self.timer.start(30)  # Update every 30 milliseconds (~33 FPS)
        
        # Button Behaviors
        self.mainUI.button_openFolder.clicked.connect(self.openFolder)
        self.mainUI.actionNew.triggered.connect(self.new_file_dialog)
        self.mainUI.actionOpen.triggered.connect(self.open_existing_project)
        self.mainUI.button_SingleShot.clicked.connect(self.singleShot)
        # Scale bar behaviors
        self.mainUI.button_calibrate_scale.clicked.connect(self.start_calibration)
        self.mainUI.button_import_scalebars.clicked.connect(self.import_scalebars)
        self.mainUI.actionImport_scalebars.triggered.connect(self.import_scalebars)
        self.mainUI.label.line_drawn.connect(self.finish_calibration)
        self.mainUI.button_scalebar_toggle.toggled.connect(self.on_scalebar_panel_toggled)
        self.mainUI.calib_microscope.currentTextChanged.connect(self.on_calib_microscope_changed)
        # Structured prefix fields. They compose the CyberInv lab image name:
        # <sex><type><structure><orientation><preparation>_<voucher>_<magnification>_<instrument>,
        # e.g. fphabd00_V0001_20X_Z10
        self.mainUI.prefix_voucher_prefix.setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[A-Z]{1,4}$")))
        # NOTE: validators on a combo's lineEdit must be parented (here to the
        # window): the lineEdit() wrapper is temporary, and an unparented
        # validator is garbage-collected with it, silently disabling validation
        self.mainUI.prefix_microscope.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[A-Za-z0-9]+$"), self))
        self.mainUI.prefix_magnification.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^(\\d+([.d]\\d+)?X?)$"), self))
        self.mainUI.calib_microscope.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[A-Za-z0-9]+$"), self))
        self.mainUI.calib_magnification.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^(\\d+([.d]\\d+)?X?)$"), self))
        structures, views, preparations = self.load_nomenclature()
        self.mainUI.prefix_structure.addItems(structures)
        self.mainUI.prefix_view.addItems(views)
        # 00 (no preparation) is always available and is the default
        if "00" not in preparations:
            preparations.insert(0, "00")
        self.mainUI.prefix_preparation.addItems(preparations)
        self.mainUI.prefix_preparation.setCurrentText("00")
        # New structures/orientations/preparations typed into the editable dropdowns
        # are validated, then registered into nomenclature.txt when the entry is finished
        self.mainUI.prefix_structure.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[a-z0-9]{3}$"), self))
        self.mainUI.prefix_view.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[a-z]$"), self))
        self.mainUI.prefix_preparation.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^\\d{2}$"), self))
        self.mainUI.prefix_structure.lineEdit().editingFinished.connect(
            lambda: self.register_nomenclature_entry("structures", self.mainUI.prefix_structure))
        self.mainUI.prefix_view.lineEdit().editingFinished.connect(
            lambda: self.register_nomenclature_entry("views", self.mainUI.prefix_view))
        self.mainUI.prefix_preparation.lineEdit().editingFinished.connect(
            lambda: self.register_nomenclature_entry("preparations", self.mainUI.prefix_preparation))
        self.populate_microscope_combos()
        self.mainUI.prefix_voucher_prefix.textChanged.connect(self.compose_prefix)
        self.mainUI.prefix_voucher_number.valueChanged.connect(self.compose_prefix)
        self.mainUI.prefix_sex.currentTextChanged.connect(self.compose_prefix)
        self.mainUI.prefix_type.currentTextChanged.connect(self.compose_prefix)
        self.mainUI.prefix_structure.currentTextChanged.connect(self.compose_prefix)
        self.mainUI.prefix_view.currentTextChanged.connect(self.compose_prefix)
        self.mainUI.prefix_preparation.currentTextChanged.connect(self.compose_prefix)
        self.mainUI.prefix_microscope.currentTextChanged.connect(self.on_microscope_changed)
        self.mainUI.prefix_magnification.currentTextChanged.connect(self.compose_prefix)
        # Camera settings
        self.mainUI.actionCamera_settings.triggered.connect(self.open_camera_settings)

    def open_camera_settings(self):
        dialog = CameraSettingsDialog(self.apply_camera_controls, self)
        dialog.exec_()

    def apply_camera_controls(self):
        """Push the current camera_settings to the camera. Applies live to the
        preview and carries over to full-resolution captures."""
        controls = {
            "Brightness": camera_settings["brightness"],
            "Contrast": camera_settings["contrast"],
            "Saturation": camera_settings["saturation"],
        }
        if camera_settings["awb"] == "manual":
            controls["AwbEnable"] = False
            controls["ColourGains"] = (camera_settings["gain_red"], camera_settings["gain_blue"])
        else:
            controls["AwbEnable"] = True
            controls["AwbMode"] = AWB_MODES[camera_settings["awb"]]
        try:
            cap.set_controls(controls)
        except Exception as e:
            print(f"Could not apply camera controls: {e}")

    def capture_photo(self, path, base):
        """Capture one photo in the selected format and post-process it (flip).

        The scale bar is never drawn by this program: the calibration is written
        into a metadata sidecar so the multistack step can insert the bar later."""
        ext = self.mainUI.format_combo.currentText()
        filename = self.videoManager.capture_full_res_photo(path, ext, self.next_repeat_name(path, base))
        if camera_settings["flip_h"] or camera_settings["flip_v"]:
            self.videoManager.apply_flip(filename, camera_settings["flip_h"], camera_settings["flip_v"])
        calibration = self.resolve_prefix_calibration() or scale_settings["calibration"]
        if calibration is not None:
            self.write_scalebar_metadata(filename, calibration)
        return filename

    def next_repeat_name(self, folder, base):
        """Return the name for the next shot of this view: the first image of a
        view is saved bare; re-shots of the same view (same base name) get a
        _2, _3, ... suffix, per the image naming protocol (the repeat is only
        for rotation series of one structure/orientation/magnification)."""
        stems = {os.path.splitext(file)[0] for file in os.listdir(folder)}
        if base not in stems:
            return base
        repeat = 2
        while f"{base}_{repeat}" in stems:
            repeat += 1
        return f"{base}_{repeat}"

    def write_scalebar_metadata(self, filename, calibration):
        """Write a <photo>.json sidecar with everything the multistack step needs
        to insert the scale bar later: the calibration and the full-resolution
        pixel ratio."""
        img = cv2.imread(filename)
        if img is None:
            print(f"Could not read {filename} to write scale bar metadata")
            return
        h, w = img.shape[:2]
        scale_to_fullres = w / PREVIEW_WIDTH
        metadata = {
            "image": os.path.basename(filename),
            "voucher": self.current_voucher(),
            "microscope": self.mainUI.prefix_microscope.currentText().strip(),
            "magnification": normalize_magnification(self.mainUI.prefix_magnification.currentText()),
            "calibration": calibration,
            "image_width": w,
            "image_height": h,
            "px_per_unit_fullres": calibration["pixels"] / calibration["distance"] * scale_to_fullres,
        }
        with open(os.path.splitext(filename)[0] + ".json", "w") as f:
            json.dump(metadata, f, indent=2)

    def calibration_file(self):
        """Path of the current project's calibration registry, or None if no project is open."""
        if os_settings["project_folder"] == "":
            return None
        return jn(os_settings["project_folder"], CALIBRATION_FILENAME)

    def load_registry(self):
        """Read the project's calibration.json; empty registry if missing or invalid."""
        path = self.calibration_file()
        if path is None or not os.path.exists(path):
            return {"microscopes": {}}
        try:
            with open(path) as f:
                registry = json.load(f)
            registry.setdefault("microscopes", {})
            return registry
        except (OSError, json.JSONDecodeError):
            return {"microscopes": {}}

    def save_registry(self, registry):
        with open(self.calibration_file(), "w") as f:
            json.dump(registry, f, indent=2)

    def get_calibration(self, microscope, magnification):
        """Return the calibration dict for a microscope/magnification pair, with its
        assembled name, or None if the pair has not been calibrated in this project."""
        entry = self.load_registry()["microscopes"].get(microscope, {}).get("magnifications", {}).get(magnification)
        if entry is None:
            return None
        return {"name": f"{microscope}_{magnification}", **entry}

    def resolve_prefix_calibration(self):
        """Look up the calibration matching the microscope/magnification in the prefix
        fields and make it the active one. Returns None if the pair is not calibrated."""
        microscope = self.mainUI.prefix_microscope.currentText().strip()
        magnification = normalize_magnification(self.mainUI.prefix_magnification.currentText())
        if magnification is None:
            return None
        calibration = self.get_calibration(microscope, magnification)
        if calibration is not None:
            scale_settings["calibration"] = calibration
            self.mainUI.label_scalebar_status.setText(f"Active: {calibration['name']}")
        return calibration

    def start_calibration(self):
        if os_settings["project_folder"] == "":
            QtWidgets.QMessageBox.critical(None, "No Project initialized",
                "A project is required before calibrating, since calibrations are stored in the project's calibration.json.\nPlease create or open a project before continuing.")
            return
        microscope = self.mainUI.calib_microscope.currentText().strip()
        magnification = normalize_magnification(self.mainUI.calib_magnification.currentText())
        if not re.match(r"^[A-Za-z0-9]+$", microscope):
            QtWidgets.QMessageBox.warning(None, "Invalid microscope code",
                "Enter a microscope code (letters and digits, e.g. Z10 or LeicaMZ7d5) in the calibration panel before calibrating.")
            return
        if magnification is None:
            QtWidgets.QMessageBox.warning(None, "Invalid magnification",
                "Enter a magnification (e.g. 20, or 6.2 for 6.2X) in the calibration panel before calibrating.")
            return
        self.mainUI.calib_magnification.setCurrentText(magnification)
        QtWidgets.QMessageBox.information(None, "Scale calibration",
            f"Calibrating {microscope} at {magnification}.\nPlace your metric reference in view, then click and drag a line along a known distance on the preview.\nRelease the mouse button when done.")
        self.mainUI.label.calibration_mode = True
        self.mainUI.label.line_start = None
        self.mainUI.label.line_end = None
        if cursor_settings["in_display"]:
            self.mainUI.label.setCursor(Qt.CrossCursor)

    def ask_reference_distance(self, pixels):
        """One dialog for the reference distance and its unit, side by side.
        Returns (distance, unit), or None if the user cancels."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Reference distance")
        layout = QtWidgets.QFormLayout(dialog)
        layout.addRow(QtWidgets.QLabel(f"The marked line is {pixels:.0f} px long.\nWhat real distance does it represent?"))
        distance = QtWidgets.QDoubleSpinBox(dialog)
        distance.setDecimals(4)
        distance.setRange(0.0001, 100000.0)
        distance.setValue(0.5)
        unit = QtWidgets.QComboBox(dialog)
        unit.addItems(["mm", "µm", "cm"])
        row = QtWidgets.QWidget(dialog)
        hbox = QtWidgets.QHBoxLayout(row)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(distance)
        hbox.addWidget(unit)
        layout.addRow("Distance", row)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return None
        return distance.value(), unit.currentText()

    def finish_calibration(self, line):
        start, end = line
        pixels = ((end.x() - start.x()) ** 2 + (end.y() - start.y()) ** 2) ** 0.5
        self.mainUI.label.calibration_mode = False
        self.mainUI.label.line_start = None
        self.mainUI.label.line_end = None
        if cursor_settings["in_display"]:
            self.mainUI.label.setCursor(Qt.BlankCursor)
        if pixels < 5:
            QtWidgets.QMessageBox.warning(None, "Line too short", "The reference line is too short to be reliable. Please try again with a longer line.")
            return
        microscope = self.mainUI.calib_microscope.currentText().strip()
        magnification = normalize_magnification(self.mainUI.calib_magnification.currentText())
        answer = self.ask_reference_distance(pixels)
        if answer is None:
            return
        distance, unit = answer
        registry = self.load_registry()
        magnifications = registry["microscopes"].setdefault(microscope, {}).setdefault("magnifications", {})
        if magnification in magnifications:
            overwrite = QtWidgets.QMessageBox.question(None, "Overwrite calibration",
                f"{microscope} at {magnification} is already calibrated in this project. Overwrite it?")
            if overwrite != QtWidgets.QMessageBox.Yes:
                return
        magnifications[magnification] = {"pixels": pixels, "distance": distance, "unit": unit,
                                         "calibrated_at": datetime.now().isoformat(timespec="seconds")}
        self.save_registry(registry)
        calibration = {"name": f"{microscope}_{magnification}", **magnifications[magnification]}
        scale_settings["calibration"] = calibration
        self.mainUI.label_scalebar_status.setText(f"Active: {calibration['name']}")
        self.populate_microscope_combos()  # register microscope/magnification in the prefix dropdowns
        self.populate_calib_combos()
        # the panel stays expanded: the user often calibrates several
        # magnifications in a row, and can collapse it themselves
        QtWidgets.QMessageBox.information(None, "Calibration saved",
            f"Saved '{calibration['name']}' ({pixels:.0f} px = {distance:g} {unit}) to the project's calibration.json.\nPhotos with this microscope and magnification can now be captured.")

    def import_scalebars(self):
        """Merge microscopes from another project's calibration.json into the current
        project's registry. Conflicting microscope names can be overwritten or skipped."""
        if os_settings["project_folder"] == "":
            QtWidgets.QMessageBox.critical(None, "No Project initialized",
                "A project is required before importing scalebars.\nPlease create or open a project before continuing.")
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Import scalebars", "", "Scale bar calibration (*.json)")
        if not path:
            return
        if os.path.abspath(path) == os.path.abspath(self.calibration_file()):
            QtWidgets.QMessageBox.warning(None, "Same file", "That file is already the current project's calibration.")
            return
        try:
            with open(path) as f:
                imported = json.load(f)["microscopes"]
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
            QtWidgets.QMessageBox.critical(None, "Invalid calibration", f"Could not read the scale bar file:\n{e}")
            return
        if not imported:
            QtWidgets.QMessageBox.information(None, "Nothing to import", "The selected file contains no microscopes.")
            return
        registry = self.load_registry()
        conflicts = [name for name in imported if name in registry["microscopes"]]
        overwrite = True
        if conflicts:
            answer = QtWidgets.QMessageBox.question(None, "Conflicting microscopes",
                f"Already calibrated in this project: {', '.join(sorted(conflicts))}.\nOverwrite them with the imported versions?")
            overwrite = answer == QtWidgets.QMessageBox.Yes
        count = 0
        for name, data in imported.items():
            if name in conflicts and not overwrite:
                continue
            registry["microscopes"][name] = data
            count += 1
        self.save_registry(registry)
        self.populate_microscope_combos()
        self.populate_calib_combos()
        QtWidgets.QMessageBox.information(None, "Import complete",
            f"Imported {count} microscope(s) into the project's calibration.json.")

    def on_scalebar_panel_toggled(self, checked):
        self.mainUI.scalebar_panel.setVisible(checked)
        self.mainUI.button_scalebar_toggle.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    def load_nomenclature(self):
        """Read the allowed structure codes, orientation letters and preparation
        codes from nomenclature.txt, recreating it with defaults if it has been
        deleted."""
        if not os.path.exists(NOMENCLATURE_FILE):
            with open(NOMENCLATURE_FILE, "w") as f:
                f.write(DEFAULT_NOMENCLATURE)
        structures, views, preparations = [], [], []
        with open(NOMENCLATURE_FILE) as f:
            for line in f:
                line = line.strip()
                if line == "" or line.startswith("#") or "=" not in line:
                    continue
                key, values = line.split("=", 1)
                items = [v.strip() for v in values.split(",") if v.strip()]
                if key.strip() == "structures":
                    structures = items
                elif key.strip() == "views":
                    views = items
                elif key.strip() == "preparations":
                    preparations = items
        return structures, views, preparations

    def register_nomenclature_entry(self, key, combo):
        """Register a newly typed structure/view: it must pass the field validator
        and not already exist; it is then added to the dropdown and appended to
        the matching key in nomenclature.txt, preserving comments."""
        value = combo.currentText().strip()
        if value == "" or not combo.lineEdit().hasAcceptableInput():
            return
        if combo.findText(value) != -1:
            return  # already registered
        combo.addItem(value)
        combo.setCurrentText(value)
        with open(NOMENCLATURE_FILE) as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            existing_key, values = stripped.split("=", 1)
            if existing_key.strip() == key:
                values = values.strip()
                lines[i] = f"{key}={values},{value}\n" if values != "" else f"{key}={value}\n"
                break
        else:
            lines.append(f"{key}={value}\n")
        with open(NOMENCLATURE_FILE, "w") as f:
            f.writelines(lines)
        print(f"Registered new nomenclature entry ({key}): {value}")

    def get_registered_microscopes(self):
        """Build {microscope: [magnification, ...]} from the project's calibration.json."""
        registry = {}
        for microscope, data in self.load_registry()["microscopes"].items():
            registry[microscope] = sorted(data.get("magnifications", {}).keys())
        return registry

    def populate_microscope_combos(self):
        """Refresh the microscope dropdown from the project calibrations, keeping the
        current selection if it is still registered."""
        previous = self.mainUI.prefix_microscope.currentText()
        registry = self.get_registered_microscopes()
        self.mainUI.prefix_microscope.blockSignals(True)
        self.mainUI.prefix_microscope.clear()
        self.mainUI.prefix_microscope.addItems(sorted(registry.keys()))
        if previous:
            self.mainUI.prefix_microscope.setCurrentText(previous)
        self.mainUI.prefix_microscope.blockSignals(False)
        self.on_microscope_changed(self.mainUI.prefix_microscope.currentText())

    def populate_calib_combos(self):
        """Refresh the calibration panel's microscope dropdown from the project
        calibrations, keeping the current selection if it is still registered."""
        previous = self.mainUI.calib_microscope.currentText()
        registry = self.get_registered_microscopes()
        self.mainUI.calib_microscope.blockSignals(True)
        self.mainUI.calib_microscope.clear()
        self.mainUI.calib_microscope.addItems(sorted(registry.keys()))
        if previous:
            self.mainUI.calib_microscope.setCurrentText(previous)
        self.mainUI.calib_microscope.blockSignals(False)
        self.on_calib_microscope_changed(self.mainUI.calib_microscope.currentText())

    def on_calib_microscope_changed(self, microscope):
        registry = self.get_registered_microscopes()
        previous = self.mainUI.calib_magnification.currentText()
        self.mainUI.calib_magnification.blockSignals(True)
        self.mainUI.calib_magnification.clear()
        self.mainUI.calib_magnification.addItems(registry.get(microscope, []))
        if previous:
            self.mainUI.calib_magnification.setCurrentText(previous)
        self.mainUI.calib_magnification.blockSignals(False)

    def on_microscope_changed(self, microscope):
        registry = self.get_registered_microscopes()
        previous = self.mainUI.prefix_magnification.currentText()
        self.mainUI.prefix_magnification.blockSignals(True)
        self.mainUI.prefix_magnification.clear()
        self.mainUI.prefix_magnification.addItems(registry.get(microscope, []))
        if previous:
            self.mainUI.prefix_magnification.setCurrentText(previous)
        self.mainUI.prefix_magnification.blockSignals(False)
        self.compose_prefix()

    def current_voucher(self):
        """The voucher number composed from the prefix and number fields,
        zero-padded to 4 digits, e.g. V + 1 -> V0001. Empty if the prefix is invalid."""
        if not self.mainUI.prefix_voucher_prefix.hasAcceptableInput():
            return ""
        prefix = self.mainUI.prefix_voucher_prefix.text().strip()
        return f"{prefix}{self.mainUI.prefix_voucher_number.value():04d}"

    def compose_prefix(self):
        """Assemble the image base name from the structured fields and highlight
        invalid ones. Expected shape (CyberInv lab image name):
        <sex><type><structure><orientation><preparation>_<voucher>_<magnification>_<instrument>,
        e.g. fphabd00_V0001_20X_Z10"""
        voucher = self.current_voucher()
        self.mainUI.prefix_voucher_prefix.setStyleSheet(
            "" if voucher != "" or self.mainUI.prefix_voucher_prefix.text() == "" else "border: 1px solid red;")
        preparation_ok = self.mainUI.prefix_preparation.lineEdit().hasAcceptableInput()
        self.mainUI.prefix_preparation.lineEdit().setStyleSheet(
            "" if preparation_ok or self.mainUI.prefix_preparation.currentText() == "" else "border: 1px solid red;")
        sex = self.mainUI.prefix_sex.currentText()
        image_type = self.mainUI.prefix_type.currentText()
        structure = self.mainUI.prefix_structure.currentText().strip()
        orientation = self.mainUI.prefix_view.currentText().strip()
        preparation = self.mainUI.prefix_preparation.currentText().strip()
        microscope = self.mainUI.prefix_microscope.currentText().strip()
        magnification = normalize_magnification(self.mainUI.prefix_magnification.currentText())
        self.mainUI.prefix_magnification.lineEdit().setStyleSheet(
            "" if magnification is not None or self.mainUI.prefix_magnification.currentText() == "" else "border: 1px solid red;")
        if (voucher != "" and preparation_ok and structure != "" and orientation != ""
                and microscope != "" and magnification is not None):
            prefix = f"{sex}{image_type}{structure}{orientation}{preparation}_{voucher}_{magnification}_{microscope}"
            self.mainUI.prefix_lineEdit.setText(prefix)
            self.resolve_prefix_calibration()
        else:
            self.mainUI.prefix_lineEdit.setText("")

    def singleShot(self):
        if os_settings["project_folder"]!= "":
            current_prefix = self.mainUI.prefix_lineEdit.text().strip()
            if current_prefix != "":
                if self.resolve_prefix_calibration() is None:
                    QtWidgets.QMessageBox.critical(None,"Calibration required",
                        "The microscope and magnification in the prefix have no calibration in this project.\nExpand the 'Scale bar / Calibration' panel, register the microscope and calibrate this magnification before capturing.")
                    return
                self.mainUI.buttonStatus.setIcon(self.mainUI.icon4)
                QApplication.processEvents()  # Method 1: Force update
                # Images of one voucher live in one folder named exactly by the
                # voucher number, per the CyberInv image protocol
                voucher = self.current_voucher()
                prefix_path = jn(os_settings["project_folder"],"images",voucher)
                if not os.path.exists(prefix_path):
                    os.mkdir(prefix_path)
                    # Snapshot the calibration registry so the series stays
                    # interpretable even if the project is recalibrated later
                    shutil.copy(self.calibration_file(), jn(prefix_path, CALIBRATION_FILENAME))
                self.capture_photo(prefix_path, current_prefix)
                self.mainUI.buttonStatus.setIcon(self.mainUI.icon3)
                QApplication.processEvents()  # Method 1: Force update
            else:
                QtWidgets.QMessageBox.critical(None,"Incomplete prefix", "All the prefix fields (voucher, sex, image type, structure, orientation, preparation, microscope and magnification) are required before capturing.\nCheck the highlighted fields and try again.")
        else:
            QtWidgets.QMessageBox.critical(None,"No Project initialized", "A project is required before enabling access to the main images folder and save a single shot.\nPlease create a new project before continuing...")

    def openFolder(self):
        if os_settings["project_folder"] != "":
            path = jn(os_settings["project_folder"],"images")
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        else:
            QtWidgets.QMessageBox.critical(None,"No Project initialized", "A project is required before enabling access to the main images folder.\nPlease create a new project before continuing...")

    def update_webcam_feed(self):
        """Capture and display a new frame from the webcam."""
        display_settings["image"] = self.videoManager.get_image_from_webcam()  # Load first frame from webcam
        self.update_image_display()

    def update_image_display(self):
        """Overlay the mask on top of the image using the mask's values wherever they are non-zero."""
        # Create a copy of the original image
        qimage = self.convert_cv_qt()
        # Draw the calibration reference line while the user is dragging it
        label = self.mainUI.label
        if label.calibration_mode and label.line_start is not None and label.line_end is not None:
            painter = QtGui.QPainter(qimage)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 2))
            painter.drawLine(label.line_start, label.line_end)
            painter.end()
        # Set the QPixmap on the QLabel
        self.mainUI.label.setPixmap(QPixmap.fromImage(qimage))
                
    def convert_cv_qt(self):
        """Convert from an OpenCV image to QImage, applying the user's flip settings."""
        rgb_image = cv2.cvtColor(display_settings["image"], cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        rgb_image = cv2.flip(rgb_image, -1)
        if camera_settings["flip_h"] and camera_settings["flip_v"]:
            rgb_image = cv2.flip(rgb_image, -1)
        elif camera_settings["flip_h"]:
            rgb_image = cv2.flip(rgb_image, 1)
        elif camera_settings["flip_v"]:
            rgb_image = cv2.flip(rgb_image, 0)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

    def refresh_project_state(self):
        """Reload all calibration-dependent UI after the project folder changes."""
        scale_settings["calibration"] = None
        self.mainUI.label_scalebar_status.setText("No calibration active")
        self.populate_microscope_combos()
        self.populate_calib_combos()

    def open_existing_project(self):
        options = QtWidgets.QFileDialog.Options()
        directory = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder", "", options=options)
        if directory:
            # os_settings["config"] = jn(directory, "config.json")
            if os.path.exists(jn(directory,"images")):
                os_settings["project_folder"] = directory
                if not os.path.exists(jn(directory, CALIBRATION_FILENAME)):
                    with open(jn(directory, CALIBRATION_FILENAME), "w") as f:
                        json.dump({"microscopes": {}}, f, indent=2)
                self.refresh_project_state()
                QtWidgets.QMessageBox.information(None, "Success!!", f"Project has been successfully loaded at location:\n {directory}")
            else:
                QtWidgets.QMessageBox.critical(None,"Folder Images Missing...","The directory selected appears to be missing a folder 'images'.\nYou can create a new project or make sure your directory has a folder with that name")
                    # You can add additional code here to handle the new file creation  


    def new_file_dialog(self):
        options = QtWidgets.QFileDialog.Options()
        directory = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder", "", options=options)
        if directory:
            # os_settings["config"] = jn(directory, "config.json")
            if os.path.exists(jn(directory,"images")):
                QtWidgets.QMessageBox.information(None, "There seems to be a folder labelled 'images' in the directory selected.\nPlease erase the folder or use Open instead")
            else:
                os.mkdir(jn(directory,"images"))
                with open(jn(directory, CALIBRATION_FILENAME), "w") as f:
                    json.dump({"microscopes": {}}, f, indent=2)
                os_settings["project_folder"] = directory
                self.refresh_project_state()
                QtWidgets.QMessageBox.information(None, "Success!!", f"A new project project has been created in the directory:\n {directory}")
                    # You can add additional code here to handle the new file creation  

# DD. CAMERA_SETTINGS_DIALOG
# dialog = CameraSettingsDialog(QDialog)
# interp. a dialog with sliders to adjust the camera image parameters live
class CameraSettingsDialog(QtWidgets.QDialog):
    DEFAULTS = {"brightness":0.0, "contrast":1.0, "saturation":1.0,
                "awb":"auto", "gain_red":1.0, "gain_blue":1.0,
                "flip_h":False, "flip_v":False}

    def __init__(self, apply_callback, parent=None):
        super().__init__(parent)
        self.apply_callback = apply_callback
        self.setWindowTitle("Camera settings")
        layout = QtWidgets.QFormLayout(self)

        # Presets row: dropdown to load, button to save
        preset_container = QtWidgets.QWidget(self)
        preset_hbox = QtWidgets.QHBoxLayout(preset_container)
        preset_hbox.setContentsMargins(0, 0, 0, 0)
        self.preset_combo = QtWidgets.QComboBox(preset_container)
        self.refresh_preset_combo()
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        self.button_save_preset = QtWidgets.QPushButton("Save preset", preset_container)
        self.button_save_preset.clicked.connect(self.save_preset)
        preset_hbox.addWidget(self.preset_combo)
        preset_hbox.addWidget(self.button_save_preset)
        layout.addRow("Presets", preset_container)

        self.brightness = self.make_slider(layout, "Brightness", -100, 100, camera_settings["brightness"])
        self.contrast = self.make_slider(layout, "Contrast", 0, 200, camera_settings["contrast"])
        self.saturation = self.make_slider(layout, "Saturation", 0, 200, camera_settings["saturation"])

        self.awb = QtWidgets.QComboBox(self)
        self.awb.addItems(list(AWB_MODES.keys()) + ["manual"])
        self.awb.setCurrentText(camera_settings["awb"])
        self.awb.currentTextChanged.connect(self.on_change)
        layout.addRow("White balance", self.awb)

        self.gain_red = self.make_slider(layout, "Red gain", 0, 400, camera_settings["gain_red"])
        self.gain_blue = self.make_slider(layout, "Blue gain", 0, 400, camera_settings["gain_blue"])

        self.flip_h = QtWidgets.QCheckBox("Flip horizontally", self)
        self.flip_h.setChecked(camera_settings["flip_h"])
        self.flip_h.toggled.connect(self.on_change)
        layout.addRow(self.flip_h)
        self.flip_v = QtWidgets.QCheckBox("Flip vertically", self)
        self.flip_v.setChecked(camera_settings["flip_v"])
        self.flip_v.toggled.connect(self.on_change)
        layout.addRow(self.flip_v)

        self.button_reset = QtWidgets.QPushButton("Reset to defaults", self)
        self.button_reset.clicked.connect(self.reset)
        layout.addRow(self.button_reset)

        self.update_gain_enabled()

    def make_slider(self, layout, title, lo, hi, initial):
        """Add a slider (scaled by 1/100) with a live value label; return the slider."""
        slider = QtWidgets.QSlider(Qt.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(int(round(initial * 100)))
        value_label = QtWidgets.QLabel(f"{initial:.2f}")
        value_label.setMinimumWidth(40)
        slider.value_label = value_label
        container = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(slider)
        hbox.addWidget(value_label)
        slider.valueChanged.connect(lambda v, lbl=value_label: lbl.setText(f"{v/100:.2f}"))
        slider.valueChanged.connect(self.on_change)
        layout.addRow(title, container)
        return slider

    def load_presets(self):
        """Read the saved presets file; empty dict if missing or invalid."""
        try:
            with open(PRESETS_FILE) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def refresh_preset_combo(self, select=""):
        presets = self.load_presets()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("")  # empty entry = no preset selected
        self.preset_combo.addItems(sorted(presets.keys()))
        self.preset_combo.setCurrentText(select)
        self.preset_combo.blockSignals(False)

    def save_preset(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save preset", "Preset name:")
        name = name.strip()
        if not ok or name == "":
            return
        presets = self.load_presets()
        if name in presets:
            answer = QtWidgets.QMessageBox.question(self, "Overwrite preset",
                f"A preset named '{name}' already exists. Overwrite it?")
            if answer != QtWidgets.QMessageBox.Yes:
                return
        presets[name] = dict(camera_settings)
        with open(PRESETS_FILE, "w") as f:
            json.dump(presets, f, indent=2)
        self.refresh_preset_combo(select=name)
        print(f"Camera preset saved: {name}")

    def load_preset(self, name):
        presets = self.load_presets()
        if name == "" or name not in presets:
            return
        # merge over defaults so presets saved before new settings existed still load
        camera_settings.update({**self.DEFAULTS, **presets[name]})
        widgets = [self.brightness, self.contrast, self.saturation,
                   self.gain_red, self.gain_blue, self.awb, self.flip_h, self.flip_v]
        for widget in widgets:
            widget.blockSignals(True)
        self.brightness.setValue(int(round(camera_settings["brightness"] * 100)))
        self.contrast.setValue(int(round(camera_settings["contrast"] * 100)))
        self.saturation.setValue(int(round(camera_settings["saturation"] * 100)))
        self.gain_red.setValue(int(round(camera_settings["gain_red"] * 100)))
        self.gain_blue.setValue(int(round(camera_settings["gain_blue"] * 100)))
        self.awb.setCurrentText(camera_settings["awb"])
        self.flip_h.setChecked(camera_settings["flip_h"])
        self.flip_v.setChecked(camera_settings["flip_v"])
        for slider in widgets[:5]:
            slider.value_label.setText(f"{slider.value()/100:.2f}")
        for widget in widgets:
            widget.blockSignals(False)
        self.update_gain_enabled()
        self.apply_callback()

    def update_gain_enabled(self):
        manual = self.awb.currentText() == "manual"
        self.gain_red.setEnabled(manual)
        self.gain_blue.setEnabled(manual)

    def on_change(self):
        camera_settings["brightness"] = self.brightness.value() / 100
        camera_settings["contrast"] = self.contrast.value() / 100
        camera_settings["saturation"] = self.saturation.value() / 100
        camera_settings["awb"] = self.awb.currentText()
        camera_settings["gain_red"] = self.gain_red.value() / 100
        camera_settings["gain_blue"] = self.gain_blue.value() / 100
        camera_settings["flip_h"] = self.flip_h.isChecked()
        camera_settings["flip_v"] = self.flip_v.isChecked()
        self.update_gain_enabled()
        self.apply_callback()

    def reset(self):
        camera_settings.update(self.DEFAULTS)
        self.awb.setCurrentText(self.DEFAULTS["awb"])
        self.brightness.setValue(int(self.DEFAULTS["brightness"] * 100))
        self.contrast.setValue(int(self.DEFAULTS["contrast"] * 100))
        self.saturation.setValue(int(self.DEFAULTS["saturation"] * 100))
        self.gain_red.setValue(int(self.DEFAULTS["gain_red"] * 100))
        self.gain_blue.setValue(int(self.DEFAULTS["gain_blue"] * 100))
        self.flip_h.setChecked(self.DEFAULTS["flip_h"])
        self.flip_v.setChecked(self.DEFAULTS["flip_v"])

if __name__ == "__main__":
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # Use the high-resolution icons and fonts
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = Mult()
    window.showMaximized()  # start occupying the whole screen
    sys.exit(app.exec_())