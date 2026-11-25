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

    
    def get_next_number_in_sequence(self,path):
        # open a container file
        files = [file.split('_')[-1].split('.')[0] for file in os.listdir(path)]
        print(files)
        if len(files) == 0:
            return 0
        else:
            maxVal = max([int(file) for file in files])
            return maxVal + 1

    def capture_full_res_photo(self, path, ext="png"):
        # Generate filename with timestamp
        # filename = !!!
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        next_in_seq = self.get_next_number_in_sequence(path)
        # print(path)
        filename = jn(path,f'{os_settings["current_prefix"]}_{next_in_seq}.{ext}')
        
        # Capture full resolution image
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

    def apply_scale_bar(self, image_path, calibration, length, thickness, color_rgb, position, label=None):
        """Draw a scale bar with a text label onto an already saved image, in place.

        calibration: dict with "pixels" (float, preview px), "distance" (float, real
        distance those pixels represent) and "unit" (str), measured on the preview.
        length: physical length the bar should represent, in calibration units.
        thickness: bar height in preview pixels (scaled up to the image resolution).
        color_rgb: (r, g, b) tuple.
        position: one of "bottom-right", "bottom-left", "top-right", "top-left".
        label: text drawn next to the bar; defaults to "<length> <calibration unit>".
        """
        img = cv2.imread(image_path)
        if img is None:
            print(f"Could not read {image_path} to apply scale bar")
            return
        h, w = img.shape[:2]
        ratio = w / PREVIEW_WIDTH
        px_per_unit = calibration["pixels"] / calibration["distance"]
        bar_w = max(1, int(px_per_unit * length * ratio))
        bar_h = max(1, int(thickness * ratio))
        margin = int(20 * ratio)
        x = w - margin - bar_w if "right" in position else margin
        y = h - margin - bar_h if "bottom" in position else margin
        color_bgr = (int(color_rgb[2]), int(color_rgb[1]), int(color_rgb[0]))
        cv2.rectangle(img, (x, y), (x + bar_w, y + bar_h), color_bgr, -1)
        if label is None:
            label = f"{length:g} {calibration['unit']}"
        text = label.replace("µm", "um")  # cv2.putText cannot render non-ASCII glyphs
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8 * ratio
        text_thickness = max(1, int(2 * ratio))
        (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, text_thickness)
        text_x = x + bar_w - text_w
        text_y = y - int(8 * ratio) if "bottom" in position else y + bar_h + text_h + int(8 * ratio)
        cv2.putText(img, text, (text_x, text_y), font, font_scale, color_bgr, text_thickness, cv2.LINE_AA)
        cv2.imwrite(image_path, img)
        print(f"Scale bar applied to: {image_path}")
