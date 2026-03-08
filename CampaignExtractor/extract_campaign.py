import zipfile
import os
import sys
import argparse
import tkinter as tk
from tkinter import filedialog

def get_file_path():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select .campaign file",
        filetypes=[("Campaign files", "*.campaign"), ("ZIP files", "*.zip"), ("All files", "*.*")]
    )
    root.destroy()
    return file_path

def get_output_dir(initial_dir=None):
    root = tk.Tk()
    root.withdraw()
    output_dir = filedialog.askdirectory(
        title="Select Output Directory",
        initialdir=initial_dir
    )
    root.destroy()
    return output_dir

def extract_campaign(file_path, output_dir):
    """
    Extracts the contents of a .campaign file (which is a ZIP archive).
    """
    if not file_path or not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return False

    if not zipfile.is_zipfile(file_path):
        print(f"Error: File '{file_path}' is not a valid ZIP archive.")
        return False

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            print(f"Extracting '{file_path}' to '{output_dir}'...")
            zip_ref.extractall(output_dir)
            print("Extraction complete.")
            
            # List extracted files
            print("\nExtracted files:")
            for name in zip_ref.namelist():
                print(f"  - {name}")
        return True
    except Exception as e:
        print(f"An error occurred during extraction: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Extract Skaldsong .campaign files.")
    parser.add_argument("input_file", nargs='?', help="Path to the .campaign file")
    parser.add_argument("-o", "--output", help="Output directory (defaults to a folder named after the input file)")

    args = parser.parse_args()

    input_path = args.input_file
    if not input_path:
        input_path = get_file_path()
        if not input_path:
            print("No input file selected. Exiting.")
            return

    input_path = os.path.abspath(input_path)
    
    output_path = args.output
    if not output_path:
        # Default output directory: same name as file (without extension) in current dir
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        default_output = os.path.join(os.getcwd(), base_name)
        
        # Ask user for output directory, defaulting to the suggested one
        output_path = get_output_dir(initial_dir=os.getcwd())
        if not output_path:
            # If user cancels, use the default
            output_path = default_output
            print(f"No output directory selected. Using default: {output_path}")

    output_path = os.path.abspath(output_path)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    extract_campaign(input_path, output_path)

if __name__ == "__main__":
    main()
