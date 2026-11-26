from constants import *

class VideoMan():
    def __init__(self):
        pass 

    def get_image_from_webcam(self):
        frame = cap.capture_array()
        surface = cv2.cvtColor(frame,0)
        # surface = cv2.rotate(surface, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # surface = cv2.flip(surface,0)
        surface = cv2.resize(surface, (980, 740))  #HEIGHT AND WIDTH get flipped because or the counterclockwise rotation
        return surface

    
    def capture_full_res_photo(self, path, ext, base):
        # The base name is composed by the caller (structured prefix fields plus
        # the repeat suffix for re-shot views, when needed)
        filename = jn(path,f'{base}.{ext}')

        # Capture full resolution image using still configuration
        still_config = cap.create_still_configuration(main={"size": cap.sensor_resolution, "format": "RGB888"})
        cap.switch_mode_and_capture_file(still_config, filename)
        # cam.capture_file(filename)
        print(f"Captured full-resolution photo: {filename}")

        # Optional: Display a "Photo Taken" message on the preview
        return filename

    def apply_flip(self, image_path, flip_h, flip_v):
        """Mirror an already saved image horizontally and/or vertically, in place."""
        img = cv2.imread(image_path)
        if img is None:
            print(f"Could not read {image_path} to apply flip")
            return
        code = -1 if (flip_h and flip_v) else (1 if flip_h else 0)
        cv2.imwrite(image_path, cv2.flip(img, code))
        print(f"Flip applied to: {image_path}")
