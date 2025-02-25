import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
import zipfile

# Define the image file extensions we want to consider.
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

def bytes_to_mb(num_bytes):
    """Convert bytes to megabytes with two decimal precision."""
    return num_bytes / (1024 * 1024)

def set_file_times(filename, timestamp):
    """
    Set the modification and access times using os.utime.
    On Windows, also attempt to set the creation time using Windows API.
    """
    # Set modification and access times (portable)
    os.utime(filename, (timestamp, timestamp))
    
    if os.name == 'nt':
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

            FILE_WRITE_ATTRIBUTES = 0x0100
            OPEN_EXISTING = 3
            FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

            # Open the file with write attributes
            handle = kernel32.CreateFileW(
                filename,
                FILE_WRITE_ATTRIBUTES,
                0,
                None,
                OPEN_EXISTING,
                FILE_FLAG_BACKUP_SEMANTICS,
                None
            )
            if handle == wintypes.HANDLE(-1).value:
                return
            
            # Convert Python timestamp (seconds since epoch) to Windows FILETIME.
            # Windows FILETIME is in 100-nanosecond intervals since January 1, 1601.
            ft = int((timestamp + 11644473600) * 10000000)
            low = ft & 0xFFFFFFFF
            high = ft >> 32
            filetime = wintypes.FILETIME(low, high)
            
            # Set creation, access, and modification times to the same value.
            kernel32.SetFileTime(handle, ctypes.byref(filetime), ctypes.byref(filetime), ctypes.byref(filetime))
            kernel32.CloseHandle(handle)
        except Exception:
            # If setting creation time fails, do nothing.
            pass

class ZipImageExtractor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zip Image Extractor")
        # Expanded window: 1200 pixels wide.
        self.geometry("1200x600")
        self.current_dir = os.getcwd()  # start in the working directory
        self.selected_zip = None
        self.filtered_images = []  # list of ZipInfo objects for images (passing min size)

        # --- Layout Setup ---
        # Left frame: directory navigation
        self.dir_frame = ttk.Frame(self)
        self.dir_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        self.dir_label = ttk.Label(self.dir_frame, text="Current Directory:")
        self.dir_label.pack(anchor=tk.W)
        self.dir_path_label = ttk.Label(self.dir_frame, text=self.current_dir, foreground="blue")
        self.dir_path_label.pack(anchor=tk.W, pady=(0, 10))
        
        self.dir_listbox = tk.Listbox(self.dir_frame, width=40)
        self.dir_listbox.pack(fill=tk.BOTH, expand=True)
        self.dir_listbox.bind("<Double-Button-1>", self.on_item_double_click)
        
        self.up_button = ttk.Button(self.dir_frame, text="Up", command=self.go_up)
        self.up_button.pack(pady=5)
        
        # Top-right frame: zip file contents and statistics
        self.zip_frame = ttk.Frame(self)
        self.zip_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.zip_label = ttk.Label(self.zip_frame, text="Zip Contents (Image Files):")
        self.zip_label.pack(anchor=tk.W)
        
        self.zip_listbox = tk.Listbox(self.zip_frame)
        self.zip_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Status label for overall zip statistics and filtering details
        self.status_label = ttk.Label(self.zip_frame, text="Status: ")
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # Progress bar for extraction progress
        self.progress = ttk.Progressbar(self.zip_frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Bottom frame: controls (min size, load, extract)
        self.control_frame = ttk.Frame(self)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.size_label = ttk.Label(self.control_frame, 
            text="Minimum file size (bytes) [change value and click 'Load Zip' to update]:")
        self.size_label.pack(side=tk.LEFT)
        self.size_entry = ttk.Entry(self.control_frame, width=10)
        self.size_entry.insert(0, "0")
        self.size_entry.pack(side=tk.LEFT, padx=5)
        
        self.load_zip_button = ttk.Button(self.control_frame, text="Load Zip", command=self.load_zip_contents)
        self.load_zip_button.pack(side=tk.LEFT, padx=5)
        
        self.extract_button = ttk.Button(self.control_frame, text="Extract Images", command=self.extract_images)
        self.extract_button.pack(side=tk.LEFT, padx=5)
        
        # Initially, list directory contents.
        self.refresh_directory()
    
    def refresh_directory(self):
        """Refresh the listbox with directories and zip files in the current directory."""
        self.dir_listbox.delete(0, tk.END)
        try:
            items = os.listdir(self.current_dir)
            items.sort(key=str.lower)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        
        # Offer a way to go up (if not at root)
        if os.path.dirname(self.current_dir) != self.current_dir:
            self.dir_listbox.insert(tk.END, "[DIR] ..")
        
        for item in items:
            full_path = os.path.join(self.current_dir, item)
            if os.path.isdir(full_path):
                self.dir_listbox.insert(tk.END, f"[DIR] {item}")
            elif os.path.isfile(full_path) and item.lower().endswith(".zip"):
                self.dir_listbox.insert(tk.END, f"[ZIP] {item}")
    
    def on_item_double_click(self, event):
        """Handle double-click events in the directory listbox."""
        selection = self.dir_listbox.curselection()
        if not selection:
            return
        item_text = self.dir_listbox.get(selection[0])
        if item_text.startswith("[DIR]"):
            if item_text == "[DIR] ..":
                self.go_up()
            else:
                dir_name = item_text.replace("[DIR] ", "", 1)
                new_path = os.path.join(self.current_dir, dir_name)
                if os.path.isdir(new_path):
                    self.current_dir = new_path
                    self.dir_path_label.config(text=self.current_dir)
                    self.refresh_directory()
                    self.zip_listbox.delete(0, tk.END)
                    self.selected_zip = None
                    self.status_label.config(text="Status: ")
        elif item_text.startswith("[ZIP]"):
            zip_name = item_text.replace("[ZIP] ", "", 1)
            self.selected_zip = os.path.join(self.current_dir, zip_name)
            self.load_zip_contents()
    
    def go_up(self):
        """Move up one level in the directory tree."""
        parent = os.path.dirname(self.current_dir)
        if parent and parent != self.current_dir:
            self.current_dir = parent
            self.dir_path_label.config(text=self.current_dir)
            self.refresh_directory()
            self.zip_listbox.delete(0, tk.END)
            self.selected_zip = None
            self.status_label.config(text="Status: ")
    
    def load_zip_contents(self):
        """Load and display image files (above a minimum size) from the selected zip,
           and update the status with detailed zip statistics."""
        try:
            min_size = int(self.size_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Minimum file size must be an integer.")
            return
        
        if not self.selected_zip:
            selection = self.dir_listbox.curselection()
            if selection:
                item_text = self.dir_listbox.get(selection[0])
                if item_text.startswith("[ZIP]"):
                    zip_name = item_text.replace("[ZIP] ", "", 1)
                    self.selected_zip = os.path.join(self.current_dir, zip_name)
        
        if not self.selected_zip:
            messagebox.showinfo("Info", "Please select a zip file.")
            return
        
        # Clear previous zip contents.
        self.zip_listbox.delete(0, tk.END)
        self.filtered_images = []
        self.progress['value'] = 0
        
        # Initialize counters for overall zip statistics.
        dir_count = 0
        file_count = 0
        total_comp_all = 0
        total_exp_all = 0
        
        # Statistics for image files.
        image_count = 0
        total_comp_img = 0
        total_exp_img = 0
        
        # For filtering statistics.
        excluded_count = 0
        excluded_example = ""
        
        try:
            with zipfile.ZipFile(self.selected_zip, 'r') as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        dir_count += 1
                    else:
                        file_count += 1
                        total_comp_all += info.compress_size
                        total_exp_all += info.file_size
                        # Check if this is an image file.
                        if any(info.filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                            image_count += 1
                            total_comp_img += info.compress_size
                            total_exp_img += info.file_size
                            # Filtering based on minimum file size.
                            if info.file_size >= min_size:
                                self.filtered_images.append(info)
                                display_text = f"{info.filename} ({info.file_size} bytes)"
                                self.zip_listbox.insert(tk.END, display_text)
                            else:
                                excluded_count += 1
                                if not excluded_example:
                                    # Show only the basename, not the full path
                                    excluded_example = os.path.basename(info.filename)
            
            # Convert sizes to MB.
            total_comp_all_mb = bytes_to_mb(total_comp_all)
            total_exp_all_mb = bytes_to_mb(total_exp_all)
            total_comp_img_mb = bytes_to_mb(total_comp_img)
            total_exp_img_mb = bytes_to_mb(total_exp_img)
            
            # Build the statistics message.
            stats_msg = "Zip File Statistics:\n"
            stats_msg += f"  Directories: {dir_count}\n"
            stats_msg += (f"  Files: {file_count} (Compressed: {total_comp_all_mb:.2f} MB, "
                          f"Expanded: {total_exp_all_mb:.2f} MB)\n")
            stats_msg += (f"  Image Files: {image_count} (Compressed: {total_comp_img_mb:.2f} MB, "
                          f"Expanded: {total_exp_img_mb:.2f} MB)\n\n")
            stats_msg += f"Image Filtering (Minimum size: {min_size} bytes):\n"
            stats_msg += f"  Included: {len(self.filtered_images)} image file(s)\n"
            stats_msg += f"  Excluded: {excluded_count} image file(s); Example excluded: {excluded_example if excluded_example else 'None'}"
            self.status_label.config(text=stats_msg)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read zip file: {str(e)}")
    
    def extract_images(self):
        """Extract the filtered image files from the selected zip into a new subdirectory,
           with a progress indication, and preserve file timestamps."""
        if not self.selected_zip:
            messagebox.showinfo("Info", "Please select a zip file and load its contents first.")
            return
        if not self.filtered_images:
            messagebox.showinfo("Info", "No images found matching the criteria.")
            return
        
        zip_basename = os.path.basename(self.selected_zip)
        name_without_ext = os.path.splitext(zip_basename)[0]
        extract_dir = os.path.join(os.getcwd(), f"photos_{name_without_ext}")
        os.makedirs(extract_dir, exist_ok=True)
        
        self.extract_button.config(state=tk.DISABLED)
        self.progress.config(maximum=len(self.filtered_images))
        self.progress['value'] = 0
        
        try:
            with zipfile.ZipFile(self.selected_zip, 'r') as zf:
                for idx, info in enumerate(self.filtered_images, start=1):
                    extracted_path = zf.extract(info, path=extract_dir)
                    # Convert the zip file's stored date_time to a timestamp.
                    mod_time = time.mktime(info.date_time + (0, 0, -1))
                    # Set modification, access, and (on Windows) creation times.
                    set_file_times(extracted_path, mod_time)
                    
                    self.progress['value'] = idx
                    self.update_idletasks()
            messagebox.showinfo("Success", f"Extracted {len(self.filtered_images)} images to:\n{extract_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Extraction failed: {str(e)}")
        finally:
            self.extract_button.config(state=tk.NORMAL)
            self.progress['value'] = 0

if __name__ == "__main__":
    app = ZipImageExtractor()
    app.mainloop()
