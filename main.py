from constants import *
from mainWindow import Ui_MainWindow
from videoUtils import VideoMan
import subprocess
import platform
import time
# DD. MULTISTACKER
# multistacker = Mult()
# interp. program's main object
class Mult(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowState(QtCore.Qt.WindowMaximized)  # Maximize window
        # self.setFixedSize(self.size())  # Prevent resizing
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
        self.mainUI.button_load_scalebar.clicked.connect(self.load_scalebar_dialog)
        self.mainUI.button_scalebar_color.clicked.connect(self.pick_scalebar_color)
        self.mainUI.label.line_drawn.connect(self.finish_calibration)
        self.mainUI.checkbox_show_scalebar.toggled.connect(self.on_scalebar_toggled)
        # Structured prefix fields
        self.mainUI.prefix_taxon.setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[A-Za-z]{5}SP\\d{3}$")))
        self.mainUI.prefix_microscope.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[a-z0-9]+$")))
        self.mainUI.prefix_magnification.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^(\\d+d\\d+|\\d+)x$")))
        structures, views = self.load_nomenclature()
        self.mainUI.prefix_structure.addItems(structures)
        self.mainUI.prefix_view.addItems(views)
        # New structures/views typed into the editable dropdowns are validated,
        # then registered into nomenclature.txt when the entry is finished
        self.mainUI.prefix_structure.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[a-z]{3}$")))
        self.mainUI.prefix_view.lineEdit().setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression("^[a-z]$")))
        self.mainUI.prefix_structure.lineEdit().editingFinished.connect(
            lambda: self.register_nomenclature_entry("structures", self.mainUI.prefix_structure))
        self.mainUI.prefix_view.lineEdit().editingFinished.connect(
            lambda: self.register_nomenclature_entry("views", self.mainUI.prefix_view))
        self.populate_microscope_combos()
        self.mainUI.prefix_taxon.textChanged.connect(self.compose_prefix)
        self.mainUI.prefix_structure.currentTextChanged.connect(self.compose_prefix)
        self.mainUI.prefix_view.currentTextChanged.connect(self.compose_prefix)
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

    def capture_photo(self, path):
        """Capture one photo in the selected format and post-process it (flip, scale bar)."""
        ext = self.mainUI.format_combo.currentText()
        filename = self.videoManager.capture_full_res_photo(path, ext)
        if camera_settings["flip_h"] or camera_settings["flip_v"]:
            self.videoManager.apply_flip(filename, camera_settings["flip_h"], camera_settings["flip_v"])
        self.maybe_apply_scalebar(filename)
        return filename

    def maybe_apply_scalebar(self, filename):
        """Draw the scale bar on a captured photo if enabled and a calibration is available.

        A saved calibration whose name appears in the current prefix takes precedence
        over a manually loaded one.
        """
        if not self.mainUI.checkbox_show_scalebar.isChecked():
            return
        calibration = self.detect_calibration_from_prefix() or scale_settings["calibration"]
        if calibration is None:
            return
        # Convert the user-entered bar length (in the selected unit) into the
        # calibration's unit, which is what the pixel ratio is expressed in
        display_length = self.mainUI.scalebar_length.value()
        display_unit = self.mainUI.scalebar_unit.currentText()
        length_in_calib_units = display_length * UNIT_TO_MM[display_unit] / UNIT_TO_MM[calibration["unit"]]
        self.videoManager.apply_scale_bar(
            filename, calibration,
            length_in_calib_units,
            self.mainUI.scalebar_thickness.value(),
            scale_settings["color"],
            self.mainUI.scalebar_position.currentText(),
            label=f"{display_length:g} {display_unit}")

    def detect_calibration_from_prefix(self):
        """Return the saved calibration whose name is a substring of the current prefix.

        Longest names are checked first so overlapping microscope/magnification
        names resolve to the most specific calibration."""
        prefix = self.mainUI.prefix_lineEdit.text().strip()
        if prefix == "" or not os.path.isdir(CALIBRATIONS_DIR):
            return None
        names = [file[:-5] for file in os.listdir(CALIBRATIONS_DIR) if file.endswith(".json")]
        for name in sorted(names, key=len, reverse=True):
            if name in prefix:
                return self.load_calibration(jn(CALIBRATIONS_DIR, f"{name}.json"))
        return None

    def load_calibration(self, path):
        try:
            with open(path, "r") as f:
                calibration = json.load(f)
            scale_settings["calibration"] = calibration
            self.mainUI.scalebar_length.setValue(calibration["distance"])
            if calibration["unit"] in UNIT_TO_MM:
                self.mainUI.scalebar_unit.setCurrentText(calibration["unit"])
            self.mainUI.label_scalebar_status.setText(f"Active: {calibration['name']}")
            return calibration
        except (OSError, json.JSONDecodeError, KeyError) as e:
            QtWidgets.QMessageBox.critical(None, "Invalid calibration", f"Could not load the scale bar file:\n{e}")
            return None

    def start_calibration(self):
        QtWidgets.QMessageBox.information(None, "Scale calibration",
            "Place your metric reference in view, then click and drag a line along a known distance on the preview.\nRelease the mouse button when done.")
        self.mainUI.label.calibration_mode = True
        self.mainUI.label.line_start = None
        self.mainUI.label.line_end = None
        if cursor_settings["in_display"]:
            self.mainUI.label.setCursor(Qt.CrossCursor)

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
        name, ok = QtWidgets.QInputDialog.getText(None, "Scale bar name",
            "Name this calibration as <microscope>_<magnification>\n(use 'd' for the decimal point, e.g. leicamz7d5_0d63x):")
        if not ok or name.strip() == "":
            return
        distance, ok = QtWidgets.QInputDialog.getDouble(None, "Reference distance",
            f"The marked line is {pixels:.0f} px long.\nWhat real distance does it represent?",
            0.5, 0.0001, 100000.0, 4)
        if not ok:
            return
        unit, ok = QtWidgets.QInputDialog.getItem(None, "Unit", "Unit of the distance:", ["mm", "µm", "cm"], 0, False)
        if not ok:
            return
        calibration = {"name": name.strip(), "pixels": pixels, "distance": distance, "unit": unit}
        with open(jn(CALIBRATIONS_DIR, f"{calibration['name']}.json"), "w") as f:
            json.dump(calibration, f)
        scale_settings["calibration"] = calibration
        self.mainUI.scalebar_length.setValue(distance)
        self.mainUI.scalebar_unit.setCurrentText(unit)
        self.mainUI.label_scalebar_status.setText(f"Active: {calibration['name']}")
        self.populate_microscope_combos()  # register microscope/magnification in the dropdowns
        QtWidgets.QMessageBox.information(None, "Calibration saved",
            f"Saved '{calibration['name']}' ({pixels:.0f} px = {distance:g} {unit}).\nIt will be applied automatically to any prefix containing '{calibration['name']}'.")

    def load_scalebar_dialog(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Load scale bar", CALIBRATIONS_DIR, "Scale bar calibrations (*.json)")
        if path:
            self.load_calibration(path)

    def pick_scalebar_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            scale_settings["color"] = (color.red(), color.green(), color.blue())
            self.mainUI.button_scalebar_color.setStyleSheet(
                f"background-color:rgb({color.red()},{color.green()},{color.blue()});color:black;")

    def load_nomenclature(self):
        """Read the allowed structure codes and view letters from nomenclature.txt,
        recreating it with defaults if it has been deleted."""
        if not os.path.exists(NOMENCLATURE_FILE):
            with open(NOMENCLATURE_FILE, "w") as f:
                f.write(DEFAULT_NOMENCLATURE)
        structures, views = [], []
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
        return structures, views

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
        """Build {microscope: [magnification, ...]} from saved calibration files
        named <microscope>_<magnification>.json."""
        registry = {}
        if os.path.isdir(CALIBRATIONS_DIR):
            for file in os.listdir(CALIBRATIONS_DIR):
                name = file[:-5] if file.endswith(".json") else ""
                if "_" in name:
                    microscope, magnification = name.rsplit("_", 1)
                    registry.setdefault(microscope, [])
                    if magnification not in registry[microscope]:
                        registry[microscope].append(magnification)
        for magnifications in registry.values():
            magnifications.sort()
        return registry

    def populate_microscope_combos(self):
        """Refresh the microscope dropdown from saved calibrations, keeping the
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

    def compose_prefix(self):
        """Assemble the prefix from the structured fields and highlight invalid ones.
        Expected shape: <TaxonSP000>_<structure><view>_<microscope>_<magnification>,
        e.g. TetraSP001_opid_leicamz7d5_1d0x"""
        taxon_ok = self.mainUI.prefix_taxon.hasAcceptableInput()
        self.mainUI.prefix_taxon.setStyleSheet(
            "" if taxon_ok or self.mainUI.prefix_taxon.text() == "" else "border: 1px solid red;")
        structure = self.mainUI.prefix_structure.currentText().strip()
        view = self.mainUI.prefix_view.currentText().strip()
        microscope = self.mainUI.prefix_microscope.currentText().strip()
        magnification = self.mainUI.prefix_magnification.currentText().strip()
        if taxon_ok and structure != "" and view != "" and microscope != "" and magnification != "":
            prefix = f"{self.mainUI.prefix_taxon.text()}_{structure}{view}_{microscope}_{magnification}"
            self.mainUI.prefix_lineEdit.setText(prefix)
            if self.mainUI.checkbox_show_scalebar.isChecked():
                self.detect_calibration_from_prefix()

    def on_scalebar_toggled(self, checked):
        """When the scale bar is turned back on, re-resolve the calibration from
        the current prefix so a changed prefix takes effect immediately."""
        if checked:
            if self.detect_calibration_from_prefix() is None and scale_settings["calibration"] is None:
                self.mainUI.label_scalebar_status.setText("No scale bar loaded")

    def singleShot(self):
        if os_settings["project_folder"]!= "":
            current_prefix = self.mainUI.prefix_lineEdit.text().strip()
            os_settings["current_prefix"] = current_prefix
            if current_prefix != "":
                self.mainUI.buttonStatus.setIcon(self.mainUI.icon4)
                QApplication.processEvents()  # Method 1: Force update
                prefix_path = jn(os_settings["project_folder"],"images",current_prefix)
                if not os.path.exists(prefix_path):
                    os.mkdir(prefix_path)
                self.capture_photo(prefix_path)
                self.mainUI.buttonStatus.setIcon(self.mainUI.icon3)
                QApplication.processEvents()  # Method 1: Force update
            else:
                QtWidgets.QMessageBox.critical(None,"Prefix should not be empty", "An empty prefix would create a subfolder without name. Please provide at least one alpha-numberic character as prefix before continuing..")
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

    def open_existing_project(self):
        options = QtWidgets.QFileDialog.Options()
        directory = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder", "", options=options)
        if directory:
            # os_settings["config"] = jn(directory, "config.json")
            if os.path.exists(jn(directory,"images")):
                os_settings["project_folder"] = directory
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
                os_settings["project_folder"] = directory
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
    window.show()
    sys.exit(app.exec_())