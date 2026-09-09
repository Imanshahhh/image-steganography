import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from stego_core import hide_file_lsb, extract_file_lsb
from analysis import generate_histogram_comparison, get_file_size_analysis

class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LSB Image Steganography Tool")
        self.root.geometry("650x550")

        self.cover_path = ""
        self.secret_path = ""
        self.stego_path = ""

        # Title Label
        title = tk.Label(root, text="Image Steganography & Analysis Tool", font=("Helvetica", 16, "bold"))
        title.pack(pady=10)

        # Notebook Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_hide = ttk.Frame(self.notebook)
        self.tab_extract = ttk.Frame(self.notebook)
        self.tab_analysis = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_hide, text="Hide Data")
        self.notebook.add(self.tab_extract, text="Extract Data")
        self.notebook.add(self.tab_analysis, text="Analysis & Report")

        self.setup_hide_tab()
        self.setup_extract_tab()
        self.setup_analysis_tab()

    def setup_hide_tab(self):
        btn_cover = tk.Button(self.tab_hide, text="Select Cover Image", command=self.select_cover)
        btn_cover.pack(pady=5)
        self.lbl_cover = tk.Label(self.tab_hide, text="No cover image selected")
        self.lbl_cover.pack()

        btn_secret = tk.Button(self.tab_hide, text="Select Secret File (.txt, .pdf, .png, .doc)", command=self.select_secret)
        btn_secret.pack(pady=5)
        self.lbl_secret = tk.Label(self.tab_hide, text="No secret file selected")
        self.lbl_secret.pack()

        btn_process = tk.Button(self.tab_hide, text="Embed Secret into Image", bg="#4CAF50", fg="white", command=self.process_hide)
        btn_process.pack(pady=20)

    def setup_extract_tab(self):
        btn_stego = tk.Button(self.tab_extract, text="Select Stego Image", command=self.select_stego)
        btn_stego.pack(pady=10)
        self.lbl_stego = tk.Label(self.tab_extract, text="No stego image selected")
        self.lbl_stego.pack()

        btn_extract = tk.Button(self.tab_extract, text="Extract Secret File", bg="#2196F3", fg="white", command=self.process_extract)
        btn_extract.pack(pady=20)

    def setup_analysis_tab(self):
        btn_analyze = tk.Button(self.tab_analysis, text="Run Histogram & Size Analysis", command=self.run_analysis)
        btn_analyze.pack(pady=10)

        self.txt_report = tk.Text(self.tab_analysis, wrap="word", height=15, width=70)
        self.txt_report.pack(padx=10, pady=10)

    def select_cover(self):
        self.cover_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if self.cover_path:
            self.lbl_cover.config(text=f"Cover: {os.path.basename(self.cover_path)}")

    def select_secret(self):
        self.secret_path = filedialog.askopenfilename(filetypes=[("All Supported Files", "*.txt;*.pdf;*.png;*.jpg;*.doc;*.docx")])
        if self.secret_path:
            self.lbl_secret.config(text=f"Secret: {os.path.basename(self.secret_path)}")

    def select_stego(self):
        self.stego_path = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png")])
        if self.stego_path:
            self.lbl_stego.config(text=f"Stego: {os.path.basename(self.stego_path)}")

    def process_hide(self):
        if not self.cover_path or not self.secret_path:
            messagebox.showerror("Error", "Please select both a cover image and a secret file.")
            return
        
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not save_path:
            return

        try:
            output = hide_file_lsb(self.cover_path, self.secret_path, save_path)
            self.stego_path = output
            messagebox.showinfo("Success", f"Stego image successfully created:\n{output}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def process_extract(self):
        if not self.stego_path:
            messagebox.showerror("Error", "Please select a stego image.")
            return

        try:
            output_file = extract_file_lsb(self.stego_path)
            messagebox.showinfo("Success", f"File extracted successfully to:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run_analysis(self):
        if not self.cover_path or not self.stego_path or not self.secret_path:
            messagebox.showerror("Error", "Please embed a file first or select Cover, Stego, and Secret files.")
            return

        try:
            hist_path = generate_histogram_comparison(self.cover_path, self.stego_path)
            analysis_text = get_file_size_analysis(self.cover_path, self.stego_path, self.secret_path)

            self.txt_report.delete("1.0", tk.END)
            self.txt_report.insert(tk.END, analysis_text + f"\n\nHistogram plot saved to: {hist_path}")
            messagebox.showinfo("Analysis Complete", "Histogram plot generated and displayed in report tab!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = StegoApp(root)
    root.mainloop()