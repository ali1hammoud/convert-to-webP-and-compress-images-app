from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QRadioButton, QLabel, QSlider, QProgressBar, QWidget
from PySide6.QtCore import Qt, QThread, Signal
from PIL import Image
import os
import sys

class ImageConverterThread(QThread):
    progress_update = Signal(int)

    def __init__(self, image_path, quality, is_single_file):
        super(ImageConverterThread, self).__init__()
        self.image_path = image_path
        self.quality = quality
        self.is_single_file = is_single_file

    def run(self):
        if self.is_single_file:
            self.convert_single_file()
        else:
            self.convert_all_files()

    def create_output_path_file(self, image_path, quality=85):
        base_name = os.path.basename(image_path)
        filename, _ = os.path.splitext(base_name)
        path_to_img = os.path.dirname(image_path)

        # Define the output directory
        output_dir = os.path.join(path_to_img, "webP_compress")

        # Check if the output directory exists
        if not os.path.exists(output_dir):
            # If it doesn't exist, create it
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, f"{filename}_quality_{quality}.webp")
        return output_path

    def convert_to_webp_compress(self, image_path, quality=85):
        try:
        # Try to open the image file
            img = Image.open(image_path)
            img.verify() # verify that it is, in fact, an image
        except (IOError, SyntaxError) as e:
            print("Bad file:", image_path)
            return None

        output_path = self.create_output_path_file(image_path, quality)
        img = Image.open(image_path)
        img = img.convert("RGB")
        img.save(output_path, 'webp', quality=quality)
        print(f'image saved to: {output_path}')
        
    def convert_single_file(self):
        self.convert_to_webp_compress(self.image_path, self.quality)
        self.progress_update.emit(100)

    def convert_all_files(self):
        images = [filename for filename in os.listdir(self.image_path) if filename.lower().endswith(('.png', '.jpeg', '.jpg'))]
        total_images = len(images)
        
        for i, filename in enumerate(images):
            image_path = os.path.join(self.image_path, filename)
            self.convert_to_webp_compress(image_path, self.quality)
            progress = int((i + 1) / total_images * 100)
            self.progress_update.emit(progress)

class ImageConverterApp(QMainWindow):
    def __init__(self):
        super(ImageConverterApp, self).__init__()

        self.init_ui()
        self.converter_thread = None  # Initialize the thread as None

    def init_ui(self):
        self.setWindowTitle("Image Converter")
        self.setGeometry(100, 100, 500, 300)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.radio_single_file = QRadioButton("Convert Single File")
        self.radio_single_file.setChecked(True)
        self.radio_single_file.toggled.connect(self.toggle_file_options)
        layout.addWidget(self.radio_single_file)

        self.radio_all_files = QRadioButton("Convert All Files in Folder")
        self.radio_all_files.toggled.connect(self.toggle_file_options)
        layout.addWidget(self.radio_all_files)

        self.file_label = QLabel("Select File/s:")
        layout.addWidget(self.file_label)

        self.file_button = QPushButton("Choose File/Folder")
        self.file_button.clicked.connect(self.choose_file)
        layout.addWidget(self.file_button)

        self.progress_bar = QProgressBar(self)
        layout.addWidget(self.progress_bar)

        self.quality_label = QLabel("Quality:")
        layout.addWidget(self.quality_label)

        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(85)
        self.quality_slider.valueChanged.connect(self.update_slider_value)  # Connect the slider value changed signal
        layout.addWidget(self.quality_slider)
        
        self.quality_value_label = QLabel(f"Quality Value: {self.quality_slider.value()}")  # Display the initial value
        layout.addWidget(self.quality_value_label)
        
        self.convert_button = QPushButton("Convert")
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)

        central_widget.setLayout(layout)

    def toggle_file_options(self):
        is_single_file = self.radio_single_file.isChecked()
        self.file_label.setText("Select File:" if is_single_file else "Select Folder:")

    def choose_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        if self.radio_single_file.isChecked():
            file_path, _ = QFileDialog.getOpenFileName(self, "Choose Image File", "", "Image Files (*.png *.jpeg *.jpg);;All Files (*)", options=options)
        else:
            file_path = QFileDialog.getExistingDirectory(self, "Choose Folder", "", options=options)

        if file_path:
            self.file_label.setText(file_path)

    def start_conversion(self):
        file_path = self.file_label.text()
        quality = self.quality_slider.value()
        print(f'quality = {quality}')
        is_single_file = self.radio_single_file.isChecked()

        self.progress_bar.setValue(0)

        # Check if a thread is already running, and wait for it to finish
        if self.converter_thread and self.converter_thread.isRunning():
            self.converter_thread.wait()

        # Create a new thread for the conversion
        self.converter_thread = ImageConverterThread(file_path, quality, is_single_file)
        self.converter_thread.progress_update.connect(self.update_progress)
        self.converter_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_slider_value(self):
        # Update the label to show the current value of the slider
        self.quality_value_label.setText(f"Quality Value: {self.quality_slider.value()}")

if __name__ == "__main__":
    app = QApplication([])
    main_win = ImageConverterApp()
    main_win.show()
    sys.exit(app.exec())
