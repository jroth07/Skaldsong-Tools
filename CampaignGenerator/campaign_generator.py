import os
import json
import zipfile
import re
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
  "campaign_meta": {
    "title": "Campaign Title",
    "description": "A brief description of the campaign.",
    "music_files": []
  },
  "game_state": {
    "currency_name": "Gold",
    "date": "01 Jan, 1000",
    "distance_measurement": "Miles, m",
    "distance_measurement_number": "25",
    "game_loop": "Describe the core gameplay loop.",
    "genre": "Fantasy",
    "imagegen_style": "Fantasy Art",
    "location_description": "Initial location description.",
    "party_grid_coordinates": [0, 0],
    "party_location": {
      "name": "Starting Location",
      "description": "Description of the starting location.",
      "location_type": "city",
      "grid_position": [0, 0],
      "sub_grid_position": [50, 50],
      "is_civilized": true
    },
    "setting": "Description of the setting.",
    "time": "08:00",
    "game_characters": [
      {
        "name": "NPC Name",
        "role": "Role in the story",
        "description": "Description of the NPC."
      }
    ],
    "locations": [
      {
        "name": "Location Name",
        "description": "Description of the location."
      }
    ],
    "factions": [
      {
        "name": "Faction Name",
        "description": "Description of the faction."
      }
    ],
    "lorebook_entries": [
      {
        "name": "Lore Entry Title (e.g., The Ancient War, Magic System, The First King)",
        "description": "Detailed background lore, history, or rules for the AI to reference. These are not story chapters, but world-building details.",
        "encounters": [
          {
            "name": "Encounter Name (if this lore triggers a specific encounter)",
            "type": "combat|social|exploration",
            "description": "Details of the encounter."
          }
        ]
      }
    ]
  },
  "programmatic_start": {
    "allow_custom_character": true,
    "predefined_characters": [],
    "steps": [
      {
        "id": "char_name",
        "type": "text_input",
        "question": "What is your character's name?",
        "placeholder": "Enter your name...",
        "use_ai_generation": true,
        "collect_data": { "Name": "{value}" }
      },
      {
        "id": "char_appearance",
        "type": "text_input",
        "question": "Describe your appearance:",
        "placeholder": "Tall with dark hair...",
        "multiline": true,
        "use_ai_generation": true,
        "collect_data": { "BodyAppearance": "{value}" }
      },
      {
        "id": "char_background",
        "type": "text_input",
        "question": "Tell your backstory:",
        "placeholder": "An orphan from a distant land...",
        "multiline": true,
        "use_ai_generation": true,
        "collect_data": { "BackgroundHistory": "{value}" }
      },
      {
        "id": "stats",
        "type": "stat_allocation",
        "question": "Distribute your ability scores:",
        "description": "You have 30 points to allocate (each stat starts at 10)",
        "point_pool": 30,
        "min_value": 8,
        "max_value": 50,
        "default_value": 10,
        "stats": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
        "stat_codes": ["Str", "Dex", "Con", "Int", "Wis", "Cha"],
        "use_ai_generation": true,
        "collect_data": { "Stats": "{value}" }
      },
      {
        "id": "review",
        "type": "review",
        "question": "Review your character:",
        "description": "The AI will generate a complete character based on your choices.",
        "use_ai_generation": true,
        "options": [
          {
            "label": "Create Character with AI",
            "value": "confirm",
            "finalize_tags": "[Create_Character Name=\"{Name}\" BackgroundHistory=\"{BackgroundHistory}\" BodyAppearance=\"{BodyAppearance}\" Stats=\"{Stats}\" Raw=\"True\" IsNPC=\"False\" InParty=\"True\"]"
          }
        ]
      }
    ],
    "title": "Campaign Setup"
  }
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
            content = content.strip()
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if match:
                content = match.group(1)
            else:
                # Fallback: try to find the first { and last }
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx:end_idx+1]
                
            campaign_data = json.loads(content)
            
            # Add filler values for ai_notes and game_notes
            if "game_state" in campaign_data:
                campaign_data["game_state"]["ai_notes"] = "Enter AI notes here..."
                campaign_data["game_state"]["game_notes"] = "Enter game notes here..."
            
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
        
        meta = campaign_data.get("campaign_meta", {})
        raw_name = meta.get("title", campaign_data.get("title", "Generated Campaign"))
        # Replace spaces with underscores, convert to lowercase, and remove invalid characters
        default_name = re.sub(r'[^\w\-]', '', raw_name.replace(" ", "_").lower())
        
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
            
            # Create images directory
            os.makedirs(os.path.join(campaign_dir, "images"), exist_ok=True)
            
            # Save campaign_meta.json
            meta_path = os.path.join(campaign_dir, "campaign_meta.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(campaign_data.get("campaign_meta", {}), f, indent=4)
                
            # Save game_state.json
            state_path = os.path.join(campaign_dir, "game_state.json")
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(campaign_data.get("game_state", {}), f, indent=4)
                
            # Save programmatic_start.json
            prog_path = os.path.join(campaign_dir, "programmatic_start.json")
            with open(prog_path, "w", encoding="utf-8") as f:
                json.dump(campaign_data.get("programmatic_start", {}), f, indent=4)
                
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
