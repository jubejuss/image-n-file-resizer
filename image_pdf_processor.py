import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from PIL import Image
import PyPDF2
from pathlib import Path
import unicodedata

class ImagePDFProcessor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Image & PDF Processor")
        self.geometry("600x500")
        
        self.selected_images = []  # Store selected image paths

        # Create notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(pady=10, expand=True)

        # Image processing tab
        image_frame = ttk.Frame(notebook)
        notebook.add(image_frame, text="Image Processing")

        # PDF processing tab
        pdf_frame = ttk.Frame(notebook)
        notebook.add(pdf_frame, text="PDF Processing")

        # Image processing components
        ttk.Label(image_frame, text="Select images to convert:").pack(pady=5)
        ttk.Button(image_frame, text="Browse Images", command=self.select_images).pack(pady=5)
        
        # Selected files counter
        self.files_label = ttk.Label(image_frame, text="No files selected")
        self.files_label.pack(pady=5)
        
        # Add prefix/suffix frame
        name_frame = ttk.Frame(image_frame)
        name_frame.pack(pady=10, padx=10, fill='x')
        
        ttk.Label(name_frame, text="New filename prefix (optional):").pack(anchor='w')
        self.filename_prefix = ttk.Entry(name_frame)
        self.filename_prefix.pack(fill='x', pady=(0, 10))
        
        ttk.Label(name_frame, text="Keep original filename if left empty").pack(anchor='w')
        
        # Convert button
        ttk.Button(image_frame, text="Convert Images", command=self.process_images).pack(pady=10)
        
        self.image_status = ttk.Label(image_frame, text="")
        self.image_status.pack(pady=5)

        # PDF processing components
        ttk.Label(pdf_frame, text="Select PDF to process:").pack(pady=5)
        ttk.Button(pdf_frame, text="Browse PDF", command=self.select_pdf).pack(pady=5)
        
        # Page range frame
        page_frame = ttk.Frame(pdf_frame)
        page_frame.pack(pady=10)
        
        ttk.Label(page_frame, text="From page:").pack(side=tk.LEFT)
        self.start_page = ttk.Entry(page_frame, width=5)
        self.start_page.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(page_frame, text="To page:").pack(side=tk.LEFT)
        self.end_page = ttk.Entry(page_frame, width=5)
        self.end_page.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(pdf_frame, text="Extract Pages", command=self.process_pdf).pack(pady=5)
        self.pdf_status = ttk.Label(pdf_frame, text="")
        self.pdf_status.pack(pady=5)

    def normalize_filename(self, filename):
        # Convert to lowercase
        filename = filename.lower()
        
        # Replace umlauts and special characters
        umlaut_map = {
            'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss',
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
            'ñ': 'n', 'í': 'i', 'ì': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u'
        }
        
        for umlaut, replacement in umlaut_map.items():
            filename = filename.replace(umlaut, replacement)
        
        # Normalize Unicode characters
        filename = unicodedata.normalize('NFKD', filename)
        filename = ''.join([c for c in filename if not unicodedata.combining(c)])
        
        # Replace spaces and special characters with dashes
        filename = ''.join(c if c.isalnum() or c in '-_' else '-' for c in filename)
        
        # Remove multiple dashes
        while '--' in filename:
            filename = filename.replace('--', '-')
        
        # Remove leading/trailing dashes
        filename = filename.strip('-')
        
        return filename

    def select_images(self):
        self.selected_images = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")]
        )
        if self.selected_images:
            self.files_label.config(text=f"Selected {len(self.selected_images)} files")
        else:
            self.files_label.config(text="No files selected")

    def generate_filename(self, original_filename, prefix="", suffix=""):
        if prefix:
            normalized_prefix = self.normalize_filename(prefix)
            return f"{normalized_prefix}{suffix}.webp"
        else:
            normalized_name = self.normalize_filename(original_filename)
            return f"{normalized_name}{suffix}.webp"

    def process_images(self):
        if not self.selected_images:
            messagebox.showwarning("Warning", "Please select images first")
            return

        output_dir = filedialog.askdirectory(title="Select output directory")
        if not output_dir:
            return

        prefix = self.filename_prefix.get().strip()
        processed = 0
        
        for file in self.selected_images:
            try:
                img = Image.open(file)
                original_filename = Path(file).stem

                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # First size: 556x400 (crop and scale) - with _thumb suffix
                aspect_ratio = 556/400
                if img.width/img.height > aspect_ratio:
                    new_width = int(img.height * aspect_ratio)
                    left = (img.width - new_width) // 2
                    img_cropped = img.crop((left, 0, left + new_width, img.height))
                else:
                    new_height = int(img.width / aspect_ratio)
                    top = (img.height - new_height) // 2
                    img_cropped = img.crop((0, top, img.width, top + new_height))
                
                img_cropped = img_cropped.resize((556, 400), Image.Resampling.LANCZOS)
                thumb_filename = self.generate_filename(original_filename, prefix, "_thumb")
                img_cropped.save(os.path.join(output_dir, thumb_filename), 
                               "WEBP", quality=85)

                # Second size: max width 575
                width_ratio = 575 / img.width
                new_width = 575
                new_height = int(img.height * width_ratio)
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                large_filename = self.generate_filename(original_filename, prefix, "")
                img_resized.save(os.path.join(output_dir, large_filename), 
                               "WEBP", quality=85)

                processed += 1
                # Update status after each image
                self.image_status.config(
                    text=f"Processing: {processed}/{len(self.selected_images)} images completed"
                )
                self.update()  # Update the GUI
                
            except Exception as e:
                messagebox.showerror("Error", f"Error processing {file}: {str(e)}")

        self.image_status.config(
            text=f"Successfully processed {processed} images to {output_dir}"
        )
        # Clear selection after processing
        self.selected_images = []
        self.files_label.config(text="No files selected")

    def select_pdf(self):
        self.pdf_file = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if self.pdf_file:
            with open(self.pdf_file, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                self.pdf_status.config(
                    text=f"Selected PDF has {len(pdf.pages)} pages"
                )

    def process_pdf(self):
        if not hasattr(self, 'pdf_file') or not self.pdf_file:
            messagebox.showerror("Error", "Please select a PDF file first")
            return

        try:
            start = int(self.start_page.get())
            end = int(self.end_page.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid page numbers")
            return

        # Get original filename without extension
        original_filename = Path(self.pdf_file).stem
        # Normalize the filename
        normalized_filename = self.normalize_filename(original_filename)
        # Add page range to filename
        suggested_filename = f"{normalized_filename}-pages-{start}-to-{end}.pdf"

        output_file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=suggested_filename  # Suggest normalized filename
        )
        if not output_file:
            return

        try:
            with open(self.pdf_file, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if start < 1 or end > len(pdf_reader.pages) or start > end:
                    messagebox.showerror("Error", "Invalid page range")
                    return

                pdf_writer = PyPDF2.PdfWriter()
                
                # PyPDF2 uses 0-based indexing
                for page_num in range(start - 1, end):
                    pdf_writer.add_page(pdf_reader.pages[page_num])

                # Normalize the final output filename if user changed it
                final_output_path = Path(output_file)
                normalized_path = final_output_path.parent / f"{self.normalize_filename(final_output_path.stem)}.pdf"
                
                with open(normalized_path, 'wb') as output:
                    pdf_writer.write(output)
                
                self.pdf_status.config(
                    text=f"Successfully extracted pages {start}-{end} to {normalized_path.name}"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    app = ImagePDFProcessor()
    app.mainloop()