from constants import *

class VideoMan():
    def __init__(self):
        pass 

    def get_image_from_webcam(self):
        frame = cap.capture_array()
        surface = cv2.cvtColor(frame,0)
        # surface = cv2.rotate(surface, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # surface = cv2.flip(surface,0)
        surface = cv2.resize(surface, (720,480))  #HEIGHT AND WIDTH get flipped because or the counterclockwise rotation
        return surface

    
    def get_next_number_in_sequence(self,path):
        # open a container file
        files = [file.split('_')[-1].split('.')[0] for file in os.listdir(path)]
        print(files)
        if len(files) == 0:
            return 0
        else:
            maxVal = max([int(file) for file in files])
            return maxVal + 1

    def capture_full_res_photo(self, path):
        # Generate filename with timestamp
        # filename = !!!
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        next_in_seq = self.get_next_number_in_sequence(path)
        # print(path)
        filename = jn(path,f'{os_settings["current_prefix"]}_{next_in_seq}.png')
        
        # Capture full resolution image
        # Capture full resolution image using still configuration
        still_config = cap.create_still_configuration(main={"size": cap.sensor_resolution, "format": "RGB888"})
        cap.switch_mode_and_capture_file(still_config, filename)
        # cam.capture_file(filename)
        print(f"Captured full-resolution photo: {filename}")
        
        # Optional: Display a "Photo Taken" message on the preview
        return filename

    def calibrate_shutter_duration(self, path):
        start_time = time.time()
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # print(path)
        filename = jn(path,f'calibrationTest.png')
        
        # Capture full resolution image
        # Capture full resolution image using still configuration
        still_config = cap.create_still_configuration(main={"size": cap.sensor_resolution, "format": "RGB888"})
        cap.switch_mode_and_capture_file(still_config, filename)
        end_time = time.time()
        capture_duration = end_time - start_time
        # cam.capture_file(filename)
        
        # Optional: Display a "Photo Taken" message on the preview
        return capture_duration