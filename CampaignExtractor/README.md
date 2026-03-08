# CampaignExtractor

CampaignExtractor is a Python utility for extracting Skaldsong `.campaign` files. Since `.campaign` files are essentially ZIP archives, this tool provides a convenient way to extract their contents either via a command-line interface (CLI) or a graphical user interface (GUI).

## Requirements

- Python 3.x
- `tkinter` (Usually included with standard Python installations. On some Linux distributions, you may need to install it separately, e.g., `sudo apt-get install python3-tk`).

## Usage

You can use CampaignExtractor in two ways: through the command line or via a graphical file dialog.

### 1. Graphical User Interface (GUI) Mode

If you run the script without any arguments, it will open a file dialog for you to select the `.campaign` file, followed by a directory dialog to choose where to extract the contents.

```bash
python extract_campaign.py
```

1. A window will appear asking you to select a `.campaign` or `.zip` file.
2. After selecting the file, another window will prompt you to choose an output directory.
3. If you cancel the output directory selection, it will default to creating a folder with the same name as the input file in your current working directory.

### 2. Command-Line Interface (CLI) Mode

You can also provide the input file and output directory directly as command-line arguments.

```bash
python extract_campaign.py [input_file] [-o output_dir]
```

**Arguments:**

- `input_file`: (Optional) The path to the `.campaign` file you want to extract. If omitted, the GUI file dialog will open.
- `-o`, `--output`: (Optional) The path to the directory where the contents should be extracted. If omitted, the GUI directory dialog will open. If you cancel that dialog, it defaults to a folder named after the input file in the current directory.

**Examples:**

Extract a file and be prompted for the output directory:
```bash
python extract_campaign.py my_adventure.campaign
```

Extract a file to a specific directory:
```bash
python extract_campaign.py my_adventure.campaign -o ./extracted_files
```
