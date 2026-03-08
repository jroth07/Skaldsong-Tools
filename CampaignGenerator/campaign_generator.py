import os
import json
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading

class CampaignGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Skaldsong Campaign Generator")
        self.root.geometry("600x500")
        
        self.api_key_var = tk.StringVar(value=os.environ.get("OPENROUTER_API_KEY", ""))
        self.model_var = tk.StringVar(value="google/gemini-2.5-flash")
        self.prompt_var = tk.StringVar()
        self.current_campaign_dir = None
        
        self.create_widgets()
        
    def create_widgets(self):
        padding = {'padx': 10, 'pady': 5}
        
        # API Key
        ttk.Label(self.root, text="OpenRouter API Key:").grid(row=0, column=0, sticky=tk.W, **padding)
        ttk.Entry(self.root, textvariable=self.api_key_var, width=50, show="*").grid(row=0, column=1, sticky=tk.EW, **padding)
        
        # Model
        ttk.Label(self.root, text="Model:").grid(row=1, column=0, sticky=tk.W, **padding)
        ttk.Entry(self.root, textvariable=self.model_var, width=50).grid(row=1, column=1, sticky=tk.EW, **padding)
        
        # Prompt
        ttk.Label(self.root, text="Campaign Prompt:").grid(row=2, column=0, sticky=tk.NW, **padding)
        self.prompt_text = tk.Text(self.root, height=10, width=50)
        self.prompt_text.grid(row=2, column=1, sticky=tk.EW, **padding)
        self.prompt_text.insert("1.0", "A dark fantasy campaign about a group of mercenaries hunting a vampire lord.")
        
        # Buttons Frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Generate Button
        self.generate_btn = ttk.Button(btn_frame, text="Generate Campaign", command=self.start_generation)
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Export Button
        self.export_btn = ttk.Button(btn_frame, text="Export to .campaign", command=self.export_campaign, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, **padding)
        
        self.root.columnconfigure(1, weight=1)
        
    def start_generation(self):
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an OpenRouter API Key.")
            return
            
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt.")
            return
            
        self.generate_btn.config(state=tk.DISABLED)
        self.status_var.set("Generating campaign... This may take a minute.")
        
        # Run in a separate thread to keep GUI responsive
        threading.Thread(target=self.generate_campaign, args=(api_key, self.model_var.get(), prompt), daemon=True).start()
        
    def generate_campaign(self, api_key, model, prompt):
        system_prompt = """You are an expert tabletop RPG campaign designer. 
Generate a detailed campaign structure in JSON format based on the user's prompt.
The JSON should have the following structure:
{
  "title": "Campaign Title",
  "description": "A brief description of the campaign.",
  "setting": "Description of the setting.",
  "chapters": [
    {
      "title": "Chapter 1 Title",
      "description": "What happens in this chapter.",
      "encounters": [
        {
          "name": "Encounter Name",
          "type": "combat|social|exploration",
          "description": "Details of the encounter."
        }
      ]
    }
  ],
  "npcs": [
    {
      "name": "NPC Name",
      "role": "Role in the story",
      "description": "Description of the NPC."
    }
  ]
}
Return ONLY valid JSON. Do not include markdown formatting like ```json."""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Clean up potential markdown
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            campaign_data = json.loads(content)
            
            self.root.after(0, self.save_campaign, campaign_data)
            
        except Exception as e:
            self.root.after(0, self.show_error, f"Failed to generate campaign: {str(e)}")
            
    def show_error(self, message):
        self.status_var.set("Error occurred.")
        self.generate_btn.config(state=tk.NORMAL)
        messagebox.showerror("Error", message)
        
    def save_campaign(self, campaign_data):
        self.status_var.set("Campaign generated successfully. Select save directory.")
        self.generate_btn.config(state=tk.NORMAL)
        
        default_name = campaign_data.get("title", "Generated Campaign").replace(" ", "_").lower()
        
        # Ask for a directory to save the extracted format
        dir_path = filedialog.askdirectory(
            title="Select Directory to Save Campaign"
        )
        
        if not dir_path:
            self.status_var.set("Save cancelled.")
            return
            
        try:
            # Create a folder for the campaign
            campaign_dir = os.path.join(dir_path, default_name)
            os.makedirs(campaign_dir, exist_ok=True)
            
            # Save campaign.json
            json_path = os.path.join(campaign_dir, "campaign.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(campaign_data, f, indent=4)
                
            self.current_campaign_dir = campaign_dir
            self.export_btn.config(state=tk.NORMAL)
            
            self.status_var.set(f"Campaign saved to {campaign_dir}")
            messagebox.showinfo("Success", f"Campaign successfully generated and saved to:\n{campaign_dir}")
            
        except Exception as e:
            self.show_error(f"Failed to save campaign: {str(e)}")

    def export_campaign(self):
        if not self.current_campaign_dir or not os.path.exists(self.current_campaign_dir):
            messagebox.showerror("Error", "No campaign directory available to export.")
            return
            
        default_name = os.path.basename(self.current_campaign_dir) + ".campaign"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".campaign",
            initialfile=default_name,
            filetypes=[("Campaign files", "*.campaign"), ("All files", "*.*")],
            title="Export Campaign As"
        )
        
        if not file_path:
            return
            
        try:
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root_dir, _, files in os.walk(self.current_campaign_dir):
                    for file in files:
                        file_full_path = os.path.join(root_dir, file)
                        arcname = os.path.relpath(file_full_path, self.current_campaign_dir)
                        zipf.write(file_full_path, arcname)
                        
            self.status_var.set(f"Campaign exported to {file_path}")
            messagebox.showinfo("Success", f"Campaign successfully exported to:\n{file_path}")
            
        except Exception as e:
            self.show_error(f"Failed to export campaign: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CampaignGeneratorApp(root)
    root.mainloop()
