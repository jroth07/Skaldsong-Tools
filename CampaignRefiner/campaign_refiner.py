import os
import json
import re
import threading
import requests
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import sys

# Add parent directory to path to import shared_ui
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_ui import ScrollableFrame, DynamicForm, BaseListEditorTab

class AIRefinementPanel(ttk.Frame):
    def __init__(self, parent, app, section_name, get_data_callback, update_data_callback):
        super().__init__(parent)
        self.app = app
        self.section_name = section_name
        self.get_data_callback = get_data_callback
        self.update_data_callback = update_data_callback
        
        # UI Elements
        ttk.Label(self, text=f"AI Refinement: {section_name}", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        self.prompt_text = tk.Text(self, height=4, width=50, wrap=tk.WORD)
        self.prompt_text.pack(fill=tk.X, pady=(0, 5))
        self.prompt_text.insert("1.0", f"Refine the {section_name.lower()}...")
        
        self.btn_refine = ttk.Button(self, text="Refine with AI", command=self.start_refinement)
        self.btn_refine.pack(anchor=tk.E)
        
        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, foreground="blue").pack(anchor=tk.W)

    def start_refinement(self):
        api_key = self.app.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an OpenRouter API Key in the main window.")
            return
            
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter a refinement prompt.")
            return
            
        current_data = self.get_data_callback()
        if current_data is None:
            messagebox.showerror("Error", "No data available to refine.")
            return
            
        self.btn_refine.config(state=tk.DISABLED)
        self.status_var.set("Refining... Please wait.")
        
        threading.Thread(target=self.refine_data, args=(api_key, self.app.model_var.get(), prompt, current_data), daemon=True).start()

    def refine_data(self, api_key, model, prompt, current_data):
        system_prompt = f"""You are an expert tabletop RPG campaign designer and editor.
The user wants to refine the '{self.section_name}' section of their campaign.
I will provide the current JSON data for this section.
Your task is to modify, expand, or rewrite the JSON data based on the user's prompt.
Return ONLY valid JSON representing the updated data structure. Do not include markdown formatting like ```json.
The returned JSON must match the structure of the input JSON (e.g., if input is a list of objects, return a list of objects)."""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        user_content = f"User Prompt: {prompt}\n\nCurrent JSON Data:\n{json.dumps(current_data, indent=2)}"
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        }
        
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Clean up potential markdown
            content = content.strip()
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if match:
                content = match.group(1)
            else:
                # Fallback: try to find the first { or [ and last } or ]
                start_idx_obj = content.find('{')
                start_idx_arr = content.find('[')
                end_idx_obj = content.rfind('}')
                end_idx_arr = content.rfind(']')
                
                start_idx = -1
                if start_idx_obj != -1 and start_idx_arr != -1:
                    start_idx = min(start_idx_obj, start_idx_arr)
                elif start_idx_obj != -1:
                    start_idx = start_idx_obj
                elif start_idx_arr != -1:
                    start_idx = start_idx_arr
                    
                end_idx = -1
                if end_idx_obj != -1 and end_idx_arr != -1:
                    end_idx = max(end_idx_obj, end_idx_arr)
                elif end_idx_obj != -1:
                    end_idx = end_idx_obj
                elif end_idx_arr != -1:
                    end_idx = end_idx_arr
                    
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx:end_idx+1]
                
            refined_data = json.loads(content)
            
            self.app.root.after(0, self.on_refinement_success, refined_data)
            
        except Exception as e:
            self.app.root.after(0, self.on_refinement_error, str(e))

    def on_refinement_success(self, refined_data):
        self.status_var.set("Refinement complete!")
        self.btn_refine.config(state=tk.NORMAL)
        self.update_data_callback(refined_data)
        messagebox.showinfo("Success", f"{self.section_name} refined successfully.")

    def on_refinement_error(self, error_msg):
        self.status_var.set("Error occurred.")
        self.btn_refine.config(state=tk.NORMAL)
        messagebox.showerror("Refinement Error", f"Failed to refine data:\n{error_msg}")

class ListEditorTab(BaseListEditorTab):
    def __init__(self, parent, app, data_list, display_key="name", section_name="Items"):
        super().__init__(parent, data_list, display_key)
        self.app = app
        self.section_name = section_name
        
        # AI Refinement Panel at the top
        self.ai_panel = AIRefinementPanel(
            self,
            app=self.app,
            section_name=self.section_name,
            get_data_callback=self.get_current_data,
            update_data_callback=self.update_data_from_ai
        )
        self.ai_panel.pack(fill=tk.X, padx=5, pady=5, before=self.paned)
        
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.pack(fill=tk.X, padx=5, pady=5, before=self.paned)
        
    def get_current_data(self):
        return self.data_list
        
    def update_data_from_ai(self, new_data):
        if isinstance(new_data, list):
            self.data_list.clear()
            self.data_list.extend(new_data)
            self.update_list()
            self.form.load_data(None, title="No item selected")
        else:
            messagebox.showerror("Error", "AI returned invalid data format (expected a list).")

class GeneralTab(ttk.Frame):
    def __init__(self, parent, app, proxy_dict):
        super().__init__(parent)
        self.app = app
        self.proxy_dict = proxy_dict
        
        # AI Refinement Panel at the top
        self.ai_panel = AIRefinementPanel(
            self, 
            app=self.app, 
            section_name="General Settings",
            get_data_callback=self.get_current_data,
            update_data_callback=self.update_data_from_ai
        )
        self.ai_panel.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=5)
        
        self.form = DynamicForm(self)
        self.form.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.form.load_data(self.proxy_dict, title="General Campaign Settings")
        
    def get_current_data(self):
        # Reconstruct a clean dict for AI
        data = {}
        for k, v in self.proxy_dict.items():
            data[k] = v
        return data
        
    def update_data_from_ai(self, new_data):
        if isinstance(new_data, dict):
            for k, v in new_data.items():
                if k in self.proxy_dict:
                    self.proxy_dict[k] = v
            self.form.load_data(self.proxy_dict, title="General Campaign Settings")
        else:
            messagebox.showerror("Error", "AI returned invalid data format (expected a dictionary).")

class CampaignRefiner(tk.Tk):
    def __init__(self):
        super().__init__()
        self.root = self # For compatibility with AIRefinementPanel
        self.title("Campaign Refiner (AI-Powered)")
        self.geometry("1200x900")
        
        self.campaign_dir = None
        self.data = {}
        
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENROUTER_API_KEY", ""))
        self.model_var = tk.StringVar(value="google/gemini-2.5-flash")
        
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
        
        # Top Frame for AI Settings
        settings_frame = ttk.LabelFrame(self, text="Global AI Settings")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="OpenRouter API Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(settings_frame, textvariable=self.api_key_var, width=50, show="*").grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(settings_frame, text="Model:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Entry(settings_frame, textvariable=self.model_var, width=30).grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
        
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
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
        general_tab = GeneralTab(self.notebook, self, proxy)
        self.notebook.add(general_tab, text="General")
        
        # 2. Characters Tab
        if "game_characters" in game_state and isinstance(game_state["game_characters"], list):
            char_tab = ListEditorTab(self.notebook, self, game_state["game_characters"], display_key="name", section_name="Characters")
            self.notebook.add(char_tab, text="Characters")
            
        # 3. Locations Tab
        if "locations" in game_state and isinstance(game_state["locations"], list):
            loc_tab = ListEditorTab(self.notebook, self, game_state["locations"], display_key="name", section_name="Locations")
            self.notebook.add(loc_tab, text="Locations")
            
        # 4. Factions Tab
        if "factions" in game_state and isinstance(game_state["factions"], list):
            fac_tab = ListEditorTab(self.notebook, self, game_state["factions"], display_key="name", section_name="Factions")
            self.notebook.add(fac_tab, text="Factions")
            
        # 5. Lorebook Tab
        if "lorebook_entries" in game_state and isinstance(game_state["lorebook_entries"], list):
            lore_tab = ListEditorTab(self.notebook, self, game_state["lorebook_entries"], display_key="name", section_name="Lorebook")
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
    app = CampaignRefiner()
    app.mainloop()
