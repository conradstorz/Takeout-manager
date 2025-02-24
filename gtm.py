import os
import tkinter as tk
from tkinter import ttk, messagebox
import zipfile

# Define the image file extensions we want to consider.
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

class ZipImageExtractor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zip Image Extractor")
        self.geometry("800x600")
        self.current_dir = os.getcwd()  # start in the working directory
        self.selected_zip = None
        self.filtered_images = []  # list of ZipInfo objects for images

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
        
        # Top-right frame: zip file contents
        self.zip_frame = ttk.Frame(self)
        self.zip_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.zip_label = ttk.Label(self.zip_frame, text="Zip Contents (Image Files):")
        self.zip_label.pack(anchor=tk.W)
        
        self.zip_listbox = tk.Listbox(self.zip_frame)
        self.zip_listbox.pack(fill=tk.BOTH, expand=True)
        
        # New status box to display file counts and an example excluded filename
        self.status_label = ttk.Label(self.zip_frame, text="Status: ")
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # Bottom frame: controls (min size, load, extract)
        self.control_frame = ttk.Frame(self)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        self.size_label = ttk.Label(self.control_frame, text="Minimum file size (bytes):")
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
            # If the item is the parent directory (..), go up.
            if item_text == "[DIR] ..":
                self.go_up()
            else:
                # Navigate into the selected directory.
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
            # Select the zip file and load its contents.
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
           and update status with counts of found and excluded files."""
        try:
            min_size = int(self.size_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Minimum file size must be an integer.")
            return
        
        # If no zip file is already selected, try to select one from the list.
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
        
        total_images = 0
        excluded_images = 0
        excluded_example = ""
        
        try:
            with zipfile.ZipFile(self.selected_zip, 'r') as zf:
                for info in zf.infolist():
                    filename = info.filename
                    if any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                        total_images += 1
                        if info.file_size >= min_size:
                            self.filtered_images.append(info)
                            display_text = f"{filename} ({info.file_size} bytes)"
                            self.zip_listbox.insert(tk.END, display_text)
                        else:
                            excluded_images += 1
                            if not excluded_example:
                                excluded_example = filename
            # Update status label.
            status_msg = (f"Found {total_images} image file(s); "
                          f"Excluded by file size: {excluded_images}; "
                          f"Example excluded file: {excluded_example if excluded_example else 'None'}")
            self.status_label.config(text=status_msg)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read zip file: {str(e)}")
    
    def extract_images(self):
        """Extract the filtered image files from the selected zip into a new subdirectory."""
        if not self.selected_zip:
            messagebox.showinfo("Info", "Please select a zip file and load its contents first.")
            return
        if not self.filtered_images:
            messagebox.showinfo("Info", "No images found matching the criteria.")
            return
        
        # Build extraction directory name: 'photos_' prepended to the zip base name (without extension)
        zip_basename = os.path.basename(self.selected_zip)
        name_without_ext = os.path.splitext(zip_basename)[0]
        extract_dir = os.path.join(os.getcwd(), f"photos_{name_without_ext}")
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(self.selected_zip, 'r') as zf:
                for info in self.filtered_images:
                    # Extract each image file, preserving its internal path structure.
                    zf.extract(info, path=extract_dir)
            messagebox.showinfo("Success", f"Extracted {len(self.filtered_images)} images to:\n{extract_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Extraction failed: {str(e)}")

if __name__ == "__main__":
    app = ZipImageExtractor()
    app.mainloop()
