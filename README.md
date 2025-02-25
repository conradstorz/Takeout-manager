# Zip Image Extractor

## Overview
Zip Image Extractor is a Python-based graphical tool that allows you to navigate your file system, select ZIP archives, and extract image files from them. The application provides detailed statistics about the ZIP file contents—including directories, files, and image files (with both compressed and expanded sizes in megabytes)—and it filters images based on a minimum file size. Moreover, it preserves as much file metadata as possible (timestamps) during extraction.

## Features
- **Directory Navigation:**  
  - Browse your current working directory and navigate up or down the directory tree.
  - View directories and ZIP archives in an intuitive list view.

- **ZIP File Analysis:**  
  - Load a ZIP file to display overall statistics:
    - Total number of directories.
    - Total number of files (with combined compressed and expanded sizes in MB).
    - Total number of image files (with combined compressed and expanded sizes in MB).
  - Filter image files by a user-specified minimum file size to exclude thumbnails or other small images.
  - Show filtering statistics including:
    - Number of image files included.
    - Number of image files excluded.
    - An example (basename only) of an excluded file.

- **Image Extraction:**  
  - Extract filtered image files to a subdirectory named `photos_<zipfilename>` within the working directory.
  - Display a progress bar to indicate the extraction process.
  - Preserve file metadata:
    - Set the extracted file’s modification and access times using `os.utime()`.
    - On Windows, attempt to set the file’s creation time using the Windows API (via `ctypes`).

## Requirements
- **Python 3.x**
- **Tkinter** (usually bundled with Python distributions)
- Standard Python libraries: `os`, `time`, `zipfile`, `ctypes` (on Windows), and `tkinter`.

## Installation
No special installation is needed. Simply clone the repository or download the `zip_image_extractor.py` script to your local machine.

```bash
git clone https://github.com/yourusername/zip-image-extractor.git
cd zip-image-extractor
```

## Usage
Run the script using Python:

```bash
python zip_image_extractor.py
```

### How to Use the Application:
1. **Directory Navigation:**
   - The left panel displays your current directory’s contents.
   - Double-click on a directory to enter it or click the "Up" button to move to the parent directory.
   - ZIP files are marked with `[ZIP]`, while directories are marked with `[DIR]`.

2. **Loading a ZIP File:**
   - Double-click a `[ZIP]` file to load its contents.
   - The application scans the ZIP file, displaying image files that meet the minimum file size criteria in the right panel.
   - Detailed statistics about the ZIP (including total counts and sizes) are shown above the progress bar.

3. **Filtering Images:**
   - Use the "Minimum file size (bytes)" input field to set a threshold for image files.
   - **Note:** Change the value and click the "Load Zip" button to update the display and filtering statistics.
  
4. **Extracting Images:**
   - Click "Extract Images" to begin the extraction process.
   - The progress bar will update as files are extracted.
   - Extracted images are saved in a subdirectory named `photos_<zipfilename>` in your working directory.
   - File timestamps are preserved during extraction as much as possible.

## Timestamp Preservation
The tool preserves file metadata by:
- Setting modification and access times via `os.utime()`.
- On Windows, using the Windows API (via `ctypes`) to also set the creation time.
  
If the ZIP file does not include certain metadata, the tool re-creates or preserves as much as possible using the available data.

## Contributing
Contributions are welcome! If you have suggestions, encounter issues, or would like to enhance the tool further, please open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact
For questions, feedback, or further information, please contact [Your Name](mailto:your.email@example.com).

