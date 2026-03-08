# CampaignEditor

CampaignEditor is a Python utility with a graphical user interface (GUI) for editing Skaldsong campaign files. It allows you to easily navigate and modify the JSON data structures within your extracted campaign directories.

## Requirements

- Python 3.x
- `tkinter` (Usually included with standard Python installations. On some Linux distributions, you may need to install it separately, e.g., `sudo apt-get install python3-tk`).

## Usage

Run the script to open the Campaign Editor GUI:

```bash
python campaign_editor.py
```

1. Go to **File > Open Campaign Directory...** and select the folder containing your extracted campaign files (e.g., `campaign_meta.json`, `game_state.json`, `programmatic_start.json`).
2. Use the **Treeview** on the left to navigate through the hierarchical structure of your campaign data.
3. When you select a node in the tree, its primitive fields (text, numbers, booleans) will appear in the **Form** on the right.
4. Edit the fields as needed and click **Apply Changes to Memory** to update the data in the application.
5. Once you are satisfied with your edits, go to **File > Save All** to write the changes back to the JSON files on your disk.

## Features

- **Dynamic Form Generation:** Automatically creates appropriate input fields (text boxes, checkboxes, multi-line text areas) based on the data types in the JSON files.
- **Hierarchical Navigation:** Easily browse through complex, deeply nested data structures like characters, locations, and items.
- **Safe Editing:** Changes are applied to memory first, allowing you to review them before committing to disk with "Save All".