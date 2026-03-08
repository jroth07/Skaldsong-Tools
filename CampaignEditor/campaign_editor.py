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

class CampaignEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Campaign Editor")
        self.geometry("1000x700")
        
        self.campaign_dir = None
        self.data = {}
        self.files_to_load = ["campaign_meta.json", "programmatic_start.json", "game_state.json"]
        
        self.current_node_path = None
        self.form_widgets = {} # To keep track of widgets and their corresponding keys
        
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
        
        # Main PanedWindow
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left Pane: Treeview
        self.tree_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tree_frame, weight=1)
        
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Right Pane: Form
        self.form_container = ttk.Frame(self.paned_window)
        self.paned_window.add(self.form_container, weight=3)
        
        # Top bar for right pane (Apply changes button)
        self.form_top_bar = ttk.Frame(self.form_container)
        self.form_top_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.lbl_current_path = ttk.Label(self.form_top_bar, text="No node selected", font=("Arial", 10, "bold"))
        self.lbl_current_path.pack(side=tk.LEFT)
        
        self.btn_apply = ttk.Button(self.form_top_bar, text="Apply Changes to Memory", command=self.apply_changes)
        self.btn_apply.pack(side=tk.RIGHT)
        
        # Scrollable frame for the actual form fields
        self.scrollable_form = ScrollableFrame(self.form_container)
        self.scrollable_form.pack(fill=tk.BOTH, expand=True)
        
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
                self.data[filename] = {} # Empty dict if file doesn't exist
                
        self.build_tree()
        self.clear_form()
        self.lbl_current_path.config(text="Campaign loaded. Select a node to edit.")
        
    def build_tree(self):
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Build tree from self.data
        for filename, content in self.data.items():
            root_node = self.tree.insert("", tk.END, text=filename, open=True, values=(filename,))
            self._populate_tree(root_node, content, [filename])
            
    def _populate_tree(self, parent_node, data, current_path):
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = current_path + [key]
                # If value is dict or list, it's a branch
                if isinstance(value, (dict, list)):
                    node_text = f"{key} [{len(value)} items]" if isinstance(value, list) else key
                    child_node = self.tree.insert(parent_node, tk.END, text=node_text, values=(json.dumps(new_path),))
                    self._populate_tree(child_node, value, new_path)
                else:
                    # Primitive value, don't add to tree, it will be shown in the form when parent is selected
                    pass
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = current_path + [i]
                if isinstance(item, (dict, list)):
                    # Try to find a 'name' or 'id' or 'title' to display
                    display_name = f"[{i}]"
                    if isinstance(item, dict):
                        for name_key in ['name', 'title', 'id']:
                            if name_key in item:
                                display_name = f"[{i}] {item[name_key]}"
                                break
                    child_node = self.tree.insert(parent_node, tk.END, text=display_name, values=(json.dumps(new_path),))
                    self._populate_tree(child_node, item, new_path)
                else:
                    # Primitive list item
                    pass

    def get_data_at_path(self, path):
        current = self.data
        for key in path:
            current = current[key]
        return current

    def set_data_at_path(self, path, value):
        current = self.data
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = value

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
            self.current_node_path = json.loads(path_str)
        except:
            self.current_node_path = [path_str] # Root nodes
            
        self.lbl_current_path.config(text=" > ".join(str(p) for p in self.current_node_path))
        self.build_form()
        
    def clear_form(self):
        for widget in self.scrollable_form.scrollable_frame.winfo_children():
            widget.destroy()
        self.form_widgets = {}
        
    def build_form(self):
        self.clear_form()
        if not self.current_node_path:
            return
            
        data = self.get_data_at_path(self.current_node_path)
        
        row = 0
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(value, (dict, list)):
                    self._create_form_field(key, value, row, key)
                    row += 1
        elif isinstance(data, list):
            for i, value in enumerate(data):
                if not isinstance(value, (dict, list)):
                    self._create_form_field(f"Item {i}", value, row, i)
                    row += 1
        else:
            # It's a primitive itself (shouldn't happen often with our tree structure, but just in case)
            self._create_form_field("Value", data, row, None)
            
        if row == 0:
            ttk.Label(self.scrollable_form.scrollable_frame, text="No primitive fields to edit in this node.\nExpand the node to edit its children.").grid(row=0, column=0, padx=5, pady=5)

    def _create_form_field(self, label_text, value, row, data_key):
        lbl = ttk.Label(self.scrollable_form.scrollable_frame, text=label_text, width=20, anchor="e")
        lbl.grid(row=row, column=0, padx=5, pady=5, sticky="ne")
        
        # Determine widget type based on value type and length
        if isinstance(value, bool):
            var = tk.BooleanVar(value=value)
            widget = ttk.Checkbutton(self.scrollable_form.scrollable_frame, variable=var)
            widget.grid(row=row, column=1, padx=5, pady=5, sticky="w")
            self.form_widgets[data_key] = ('bool', var)
        elif isinstance(value, (int, float)):
            var = tk.StringVar(value=str(value))
            widget = ttk.Entry(self.scrollable_form.scrollable_frame, textvariable=var, width=50)
            widget.grid(row=row, column=1, padx=5, pady=5, sticky="we")
            self.form_widgets[data_key] = (type(value).__name__, var)
        else:
            # String or None
            str_val = "" if value is None else str(value)
            if len(str_val) > 100 or '\n' in str_val:
                widget = tk.Text(self.scrollable_form.scrollable_frame, width=60, height=5, wrap=tk.WORD)
                widget.insert("1.0", str_val)
                widget.grid(row=row, column=1, padx=5, pady=5, sticky="we")
                self.form_widgets[data_key] = ('text', widget)
            else:
                var = tk.StringVar(value=str_val)
                widget = ttk.Entry(self.scrollable_form.scrollable_frame, textvariable=var, width=60)
                widget.grid(row=row, column=1, padx=5, pady=5, sticky="we")
                self.form_widgets[data_key] = ('str', var)
                
        self.scrollable_form.scrollable_frame.columnconfigure(1, weight=1)

    def apply_changes(self):
        if not self.current_node_path:
            return
            
        data = self.get_data_at_path(self.current_node_path)
        
        for data_key, (val_type, widget_or_var) in self.form_widgets.items():
            new_val = None
            if val_type == 'bool':
                new_val = widget_or_var.get()
            elif val_type == 'text':
                new_val = widget_or_var.get("1.0", tk.END).strip()
            else:
                raw_val = widget_or_var.get()
                if val_type == 'int':
                    try: new_val = int(raw_val)
                    except ValueError: new_val = raw_val # Fallback to string if invalid
                elif val_type == 'float':
                    try: new_val = float(raw_val)
                    except ValueError: new_val = raw_val
                else:
                    new_val = raw_val
                    
            if data_key is None:
                # Updating the primitive itself
                self.set_data_at_path(self.current_node_path, new_val)
            else:
                data[data_key] = new_val
                
        messagebox.showinfo("Success", "Changes applied to memory. Don't forget to 'Save All' to write to disk.")
        
        # Refresh tree node text if name/title/id was changed
        selected_items = self.tree.selection()
        if selected_items and isinstance(data, dict):
            item = selected_items[0]
            for name_key in ['name', 'title', 'id']:
                if name_key in data:
                    # If it's a list item, we need to format it with index
                    parent = self.tree.parent(item)
                    if parent:
                        parent_path = json.loads(self.tree.item(parent, "values")[0])
                        parent_data = self.get_data_at_path(parent_path)
                        if isinstance(parent_data, list):
                            idx = self.current_node_path[-1]
                            self.tree.item(item, text=f"[{idx}] {data[name_key]}")
                            break
                    self.tree.item(item, text=data[name_key])
                    break

    def save_all(self):
        if not self.campaign_dir:
            messagebox.showwarning("Warning", "No campaign loaded.")
            return
            
        for filename, content in self.data.items():
            if not content: # Skip empty files
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