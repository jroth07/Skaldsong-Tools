import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Add parent directory to path to import shared_ui
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_ui import ScrollableFrame, DynamicForm, BaseListEditorTab

class CampaignEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Campaign Editor")
        self.geometry("1200x800")
        
        self.campaign_dir = None
        self.data = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Campaign Directory...", command=self.load_campaign)
        file_menu.add_command(label="Save All", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Placeholder tab
        self.placeholder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.placeholder_frame, text="Welcome")
        ttk.Label(self.placeholder_frame, text="Please open a campaign directory from the File menu.", font=("Arial", 14)).pack(pady=50)
        
    def load_campaign(self):
        directory = filedialog.askdirectory(title="Select Campaign Directory")
        if not directory:
            return
            
        self.campaign_dir = directory
        self.data = {}
        
        # Dynamically load all .json files in the directory
        try:
            json_files = [f for f in os.listdir(self.campaign_dir) if f.endswith('.json')]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read directory:\n{e}")
            return
            
        # Ensure core files exist in data even if not on disk yet
        core_files = ["campaign_meta.json", "programmatic_start.json", "game_state.json"]
        for f in core_files:
            if f not in json_files:
                json_files.append(f)
                
        for filename in json_files:
            filepath = os.path.join(self.campaign_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.data[filename] = json.load(f)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load {filename}:\n{e}")
            else:
                self.data[filename] = {}
                
        self.build_tabs()
        
    def build_tabs(self):
        # Clear existing tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
            
        game_state = self.data.get("game_state.json", {})
        
        # 1. General Tab (Meta + Game State top-level)
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="General")
        
        general_form = DynamicForm(general_frame)
        general_form.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Combine meta and top-level game_state strings for easy editing
        # We'll create a proxy dict that updates the real dicts
        class ProxyDict(dict):
            def __init__(self, meta, state):
                self.meta = meta
                self.state = state
                super().__init__()
                for k, v in meta.items():
                    if not isinstance(v, (dict, list)): self[f"[Meta] {k}"] = v
                for k, v in state.items():
                    if not isinstance(v, (dict, list)): self[f"[State] {k}"] = v
                    
            def __setitem__(self, key, value):
                super().__setitem__(key, value)
                if key.startswith("[Meta] "): self.meta[key[7:]] = value
                elif key.startswith("[State] "): self.state[key[8:]] = value
                
        proxy = ProxyDict(self.data.get("campaign_meta.json", {}), game_state)
        general_form.load_data(proxy, title="General Campaign Settings")
        
        # 2. Characters Tab
        if "game_characters" in game_state and isinstance(game_state["game_characters"], list):
            char_tab = BaseListEditorTab(self.notebook, game_state["game_characters"], display_key="name")
            self.notebook.add(char_tab, text="Characters")
            
        # 3. Locations Tab
        if "locations" in game_state and isinstance(game_state["locations"], list):
            loc_tab = BaseListEditorTab(self.notebook, game_state["locations"], display_key="name")
            self.notebook.add(loc_tab, text="Locations")
            
        # 4. Factions Tab
        if "factions" in game_state and isinstance(game_state["factions"], list):
            fac_tab = BaseListEditorTab(self.notebook, game_state["factions"], display_key="name")
            self.notebook.add(fac_tab, text="Factions")
            
        # 5. Lorebook Tab
        if "lorebook_entries" in game_state and isinstance(game_state["lorebook_entries"], list):
            lore_tab = BaseListEditorTab(self.notebook, game_state["lorebook_entries"], display_key="name")
            self.notebook.add(lore_tab, text="Lorebook")
            
        # 6. Raw JSON / Advanced Tab (Treeview)
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced (Raw JSON)")
        self.build_advanced_tab(advanced_frame)
        
    def build_advanced_tab(self, parent):
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=1)
        
        self.tree = ttk.Treeview(tree_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.adv_form = DynamicForm(paned)
        paned.add(self.adv_form, weight=3)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Populate tree
        for filename, content in self.data.items():
            root_node = self.tree.insert("", tk.END, text=filename, open=True, values=(filename,))
            self._populate_tree(root_node, content, [filename])
            
    def _populate_tree(self, parent_node, data, current_path):
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = current_path + [key]
                if isinstance(value, (dict, list)):
                    node_text = f"{key} [{len(value)} items]" if isinstance(value, list) else key
                    child_node = self.tree.insert(parent_node, tk.END, text=node_text, values=(json.dumps(new_path),))
                    self._populate_tree(child_node, value, new_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = current_path + [i]
                if isinstance(item, (dict, list)):
                    display_name = f"[{i}]"
                    if isinstance(item, dict):
                        for name_key in ['name', 'title', 'id']:
                            if name_key in item:
                                display_name = f"[{i}] {item[name_key]}"
                                break
                    child_node = self.tree.insert(parent_node, tk.END, text=display_name, values=(json.dumps(new_path),))
                    self._populate_tree(child_node, item, new_path)

    def get_data_at_path(self, path):
        current = self.data
        for key in path:
            current = current[key]
        return current

    def on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.tree.item(item, "values")
        if not values:
            return
            
        path_str = values[0]
        try:
            path = json.loads(path_str)
        except:
            path = [path_str]
            
        data = self.get_data_at_path(path)
        self.adv_form.load_data(data, title=" > ".join(str(p) for p in path))

    def save_all(self):
        if not self.campaign_dir:
            messagebox.showwarning("Warning", "No campaign loaded.")
            return
            
        for filename, content in self.data.items():
            if not content:
                continue
            filepath = os.path.join(self.campaign_dir, filename)
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=4)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save {filename}:\n{e}")
                return
                
        messagebox.showinfo("Success", "All files saved successfully.")

if __name__ == "__main__":
    app = CampaignEditor()
    app.mainloop()