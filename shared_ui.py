import tkinter as tk
from tkinter import ttk, messagebox

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
            
        new_values = {}
        for key, (val_type, widget_or_var) in self.form_widgets.items():
            new_val = None
            if val_type == 'bool':
                new_val = widget_or_var.get()
            elif val_type == 'text':
                new_val = widget_or_var.get("1.0", "end-1c")
            else:
                raw_val = widget_or_var.get()
                if val_type == 'int':
                    try: 
                        new_val = int(raw_val)
                    except ValueError: 
                        messagebox.showerror("Type Error", f"Invalid integer for '{key}': {raw_val}")
                        return
                elif val_type == 'float':
                    try: 
                        new_val = float(raw_val)
                    except ValueError: 
                        messagebox.showerror("Type Error", f"Invalid float for '{key}': {raw_val}")
                        return
                else:
                    new_val = raw_val
            new_values[key] = new_val
            
        for key, val in new_values.items():
            self.current_data[key] = val
            
        if self.on_change_callback:
            self.on_change_callback()
        messagebox.showinfo("Success", "Changes applied to memory.")

class BaseListEditorTab(ttk.Frame):
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
        
        # Add/Delete buttons
        self.btn_frame = ttk.Frame(self.left_frame)
        self.btn_frame.pack(fill=tk.X, pady=(0, 5))
        self.btn_add = ttk.Button(self.btn_frame, text="Add", command=self.add_item)
        self.btn_add.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        self.btn_delete = ttk.Button(self.btn_frame, text="Delete", command=self.delete_item)
        self.btn_delete.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(2, 0))
        
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
        
    def get_display_name(self, item, idx):
        display_name = str(item.get(self.display_key, f"Item {idx}"))
        if "grid_position" in item:
            grid_pos = item.get("grid_position")
            parent_id = item.get("parent_location_id")
            sub_ids = item.get("sub_location_ids", [])
            
            loc_info = []
            if isinstance(grid_pos, list) and len(grid_pos) == 2:
                loc_info.append(f"Grid: {grid_pos[0]},{grid_pos[1]}")
            
            if parent_id is not None:
                loc_info.append("Sublocation")
            elif sub_ids and len(sub_ids) > 0:
                loc_info.append("Parent")
                
            if loc_info:
                display_name += f" ({', '.join(loc_info)})"
        return display_name

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
                display_name = self.get_display_name(item, i)
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
        display_name = self.get_display_name(item, idx)
        self.form.load_data(item, title=f"Editing: {display_name}")

    def add_item(self):
        new_item = {self.display_key: "New Item"}
        # Try to infer structure from existing items
        if self.data_list and isinstance(self.data_list[0], dict):
            for k, v in self.data_list[0].items():
                if k != self.display_key:
                    if isinstance(v, str): new_item[k] = ""
                    elif isinstance(v, int): new_item[k] = 0
                    elif isinstance(v, float): new_item[k] = 0.0
                    elif isinstance(v, bool): new_item[k] = False
                    elif isinstance(v, list): new_item[k] = []
                    elif isinstance(v, dict): new_item[k] = {}
        self.data_list.append(new_item)
        
        if self.search_var.get() != "Search...":
            self.search_var.set("Search...")
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, "Search...")
            
        self.update_list()
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(tk.END)
        self.listbox.see(tk.END)
        self.on_select(None)
        
    def delete_item(self):
        selection = self.listbox.curselection()
        if not selection:
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?"):
            idx = self.filtered_indices[selection[0]]
            del self.data_list[idx]
            self.form.load_data(None, title="No item selected")
            self.update_list()
