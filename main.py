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
        self.setFixedSize(self.size())  # Prevent resizing
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
        self.mainUI.button_timelapse.clicked.connect(self.multistack)

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
                self.videoManager.capture_full_res_photo(prefix_path)
                self.mainUI.buttonStatus.setIcon(self.mainUI.icon3)
                QApplication.processEvents()  # Method 1: Force update
            else:
                QtWidgets.QMessageBox.critical(None,"Prefix should not be empty", "An empty prefix would create a subfolder without name. Please provide at least one alpha-numberic character as prefix before continuing..")
        else:
            QtWidgets.QMessageBox.critical(None,"No Project initialized", "A project is required before enabling access to the main images folder and save a single shot.\nPlease create a new project before continuing...")

    def multistack(self):
        value = self.mainUI.number_frames_spinbox.value()
        if os_settings["project_folder"] == "":
            QtWidgets.QMessageBox.critical(None, "No Project initialized", 
                "A project is required before enabling access to the main images folder and begin timelapse image capture.\nPlease create a new project before continuing...")
            return

        current_prefix = self.mainUI.prefix_lineEdit.text().strip()
        if current_prefix == "":
            QtWidgets.QMessageBox.critical(None, "Prefix should not be empty", 
                "An empty prefix would create a subfolder without name. Please provide at least one alpha-numberic character as prefix before continuing..")
            return

        # self.mainUI.buttonStatus.setIcon(self.mainUI.icon4)
        # Get capture duration in seconds
        capture_duration = self.videoManager.calibrate_shutter_duration(os_settings["project_folder"])
        
        # Get user's desired interval in milliseconds
        user_interval = int(self.mainUI.waitingTime_spinbox.value() * 1000)
        
        # Calculate actual timer interval by subtracting capture duration
        # Convert capture_duration to milliseconds first
        capture_duration_ms = int(capture_duration * 1000)
        actual_interval = max(0, user_interval + capture_duration_ms)
        
        prefix_path = jn(os_settings["project_folder"], "images", current_prefix)
        os_settings["current_prefix"] = current_prefix
        if not os.path.exists(prefix_path):
            os.mkdir(prefix_path)

        # Store sequence parameters as instance variables
        self.frames_remaining = value
        self.capture_path = prefix_path
        
        # Create a timer for sequence capture
        self.sequence_timer = QTimer()
        self.sequence_timer.timeout.connect(self.capture_sequence_frame)
        self.sequence_timer.start(actual_interval)  # native interval

        # print(f"Capture duration: {capture_duration:.3f}s")
        # print(f"User requested interval: {user_interval/1000:.3f}s")
        # print(f"Actual timer interval: {user_interval/1000:.3f}s")

    def capture_sequence_frame(self):
        """Captures a single frame in the sequence"""
        if self.frames_remaining > 0:
            self.mainUI.buttonStatus.setIcon(self.mainUI.icon4)
            QApplication.processEvents()  # Method 1: Force update
            self.videoManager.capture_full_res_photo(self.capture_path)
            self.frames_remaining -= 1
            print("image captured")
            self.mainUI.buttonStatus.setIcon(self.mainUI.icon3)
            QApplication.processEvents()  # Method 1: Force update
        else:
            self.sequence_timer.stop()
            del self.sequence_timer  # Cleanup

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
        # Set the QPixmap on the QLabel
        self.mainUI.label.setPixmap(QPixmap.fromImage(qimage))
                
    def convert_cv_qt(self):
        """Convert from an OpenCV image to QImage."""
        rgb_image = cv2.cvtColor(display_settings["image"], cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
        rgb_image = cv2.flip(rgb_image, -1)
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

if __name__ == "__main__":
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    # Use the high-resolution icons and fonts
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    window = Mult()
    window.show()
    sys.exit(app.exec_())