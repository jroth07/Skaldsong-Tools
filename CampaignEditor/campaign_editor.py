import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class DynamicForm(ttk.Frame):
    def __init__(self, parent, on_change_callback=None):
        super().__init__(parent)
        self.on_change_callback = on_change_callback
        
        # Top bar
        self.top_bar = ttk.Frame(self)
        self.top_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.lbl_title = ttk.Label(self.top_bar, text="No item selected", font=("Arial", 10, "bold"))
        self.lbl_title.pack(side=tk.LEFT)
        
        self.btn_apply = ttk.Button(self.top_bar, text="Apply Changes", command=self.apply_changes)
        self.btn_apply.pack(side=tk.RIGHT)
        
        # Scrollable form area
        self.scrollable = ScrollableFrame(self)
        self.scrollable.pack(fill=tk.BOTH, expand=True)
        
        self.current_data = None
        self.form_widgets = {}
        
    def load_data(self, data, title="Editing Item"):
        self.current_data = data
        self.lbl_title.config(text=title)
        
        # Clear existing widgets
        for widget in self.scrollable.scrollable_frame.winfo_children():
            widget.destroy()
        self.form_widgets = {}
        
        if not isinstance(data, (dict, list)):
            ttk.Label(self.scrollable.scrollable_frame, text="Selected item is not a dictionary or list.").pack(padx=5, pady=5)
            return
            
        row = 0
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(value, (dict, list)):
                    self._create_field(key, value, row, key)
                    row += 1
        elif isinstance(data, list):
            for i, value in enumerate(data):
                if not isinstance(value, (dict, list)):
                    self._create_field(f"Item {i}", value, row, i)
                    row += 1
                
        if row == 0:
            ttk.Label(self.scrollable.scrollable_frame, text="No primitive fields to edit.").pack(padx=5, pady=5)
            
    def _create_field(self, label_text, value, row, data_key):
        lbl = ttk.Label(self.scrollable.scrollable_frame, text=label_text, width=20, anchor="e")
        lbl.grid(row=row, column=0, padx=5, pady=5, sticky="ne")
        
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            widget = ttk.Checkbutton(self.scrollable.scrollable_frame, variable=var)
            widget.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            self.form_widgets[data_key] = ('bool', var)
        elif isinstance(value, (int, float)):
            var = tk.StringVar(value=str(value))
            widget = ttk.Entry(self.scrollable.scrollable_frame, textvariable=var, width=50)
            widget.grid(row=row, column=1, padx=5, pady=5, sticky="we")
            self.form_widgets[data_key] = (type(value).__name__, var)
        else:
            str_val = "" if value is None else str(value)
            if len(str_val) > 100 or '\n' in str_val:
                widget = tk.Text(self.scrollable.scrollable_frame, width=60, height=5, wrap=tk.WORD)
                widget.insert("1.0", str_val)
                widget.grid(row=row, column=1, padx=5, pady=5, sticky="we")
                self.form_widgets[data_key] = ('text', widget)
            else:
                var = tk.StringVar(value=str_val)
                widget = ttk.Entry(self.scrollable.scrollable_frame, textvariable=var, width=60)
                widget.grid(row=row, column=1, padx=5, pady=5, sticky="we")
                self.form_widgets[data_key] = ('str', var)
                
        self.scrollable.scrollable_frame.columnconfigure(1, weight=1)
        
    def apply_changes(self):
        if self.current_data is None:
            return
            
        for key, (val_type, widget_or_var) in self.form_widgets.items():
            new_val = None
            if val_type == 'bool':
                new_val = widget_or_var.get()
            elif val_type == 'text':
                new_val = widget_or_var.get("1.0", tk.END).strip()
            else:
                raw_val = widget_or_var.get()
                if val_type == 'int':
                    try: new_val = int(raw_val)
                    except ValueError: new_val = raw_val
                elif val_type == 'float':
                    try: new_val = float(raw_val)
                    except ValueError: new_val = raw_val
                else:
                    new_val = raw_val
            self.current_data[key] = new_val
            
        if self.on_change_callback:
            self.on_change_callback()
        messagebox.showinfo("Success", "Changes applied to memory.")

class ListEditorTab(ttk.Frame):
    def __init__(self, parent, data_list, display_key="name"):
        super().__init__(parent)
        self.data_list = data_list
        self.display_key = display_key
        
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left: Listbox with search
        self.left_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame, weight=1)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_list)
        self.search_entry = ttk.Entry(self.left_frame, textvariable=self.search_var)
        self.search_entry.pack(fill=tk.X, pady=(0, 5))
        self.search_entry.insert(0, "Search...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_var.get() == "Search..." else None)
        
        self.listbox = tk.Listbox(self.left_frame)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        
        scrollbar = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        # Right: Dynamic Form
        self.form = DynamicForm(self.paned, on_change_callback=self.update_list)
        self.paned.add(self.form, weight=3)
        
        self.filtered_indices = []
        self.update_list()
        
    def update_list(self, *args):
        search_term = self.search_var.get().lower()
        if search_term == "search...":
            search_term = ""
            
        current_selection = self.listbox.curselection()
        selected_idx = self.filtered_indices[current_selection[0]] if current_selection else None
            
        self.listbox.delete(0, tk.END)
        self.filtered_indices = []
        
        if not isinstance(self.data_list, list):
            return
            
        new_selection_index = None
        for i, item in enumerate(self.data_list):
            if isinstance(item, dict):
                display_name = str(item.get(self.display_key, f"Item {i}"))
                if search_term in display_name.lower():
                    self.listbox.insert(tk.END, display_name)
                    self.filtered_indices.append(i)
                    if i == selected_idx:
                        new_selection_index = len(self.filtered_indices) - 1
                        
        if new_selection_index is not None:
            self.listbox.selection_set(new_selection_index)
            self.listbox.see(new_selection_index)
                    
    def on_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
            
        idx = self.filtered_indices[selection[0]]
        item = self.data_list[idx]
        display_name = str(item.get(self.display_key, f"Item {idx}"))
        self.form.load_data(item, title=f"Editing: {display_name}")

class CampaignEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Campaign Editor")
        self.geometry("1200x800")
        
        self.campaign_dir = None
        self.data = {}
        self.files_to_load = ["campaign_meta.json", "programmatic_start.json", "game_state.json"]
        
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
        
        for filename in self.files_to_load:
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
            char_tab = ListEditorTab(self.notebook, game_state["game_characters"], display_key="name")
            self.notebook.add(char_tab, text="Characters")
            
        # 3. Locations Tab
        if "locations" in game_state and isinstance(game_state["locations"], list):
            loc_tab = ListEditorTab(self.notebook, game_state["locations"], display_key="name")
            self.notebook.add(loc_tab, text="Locations")
            
        # 4. Factions Tab
        if "factions" in game_state and isinstance(game_state["factions"], list):
            fac_tab = ListEditorTab(self.notebook, game_state["factions"], display_key="name")
            self.notebook.add(fac_tab, text="Factions")
            
        # 5. Lorebook Tab
        if "lorebook_entries" in game_state and isinstance(game_state["lorebook_entries"], list):
            lore_tab = ListEditorTab(self.notebook, game_state["lorebook_entries"], display_key="name")
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