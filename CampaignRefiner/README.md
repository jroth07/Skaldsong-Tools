# Campaign Refiner

The Campaign Refiner is an AI-powered tool designed to help you optimize, expand, and refine your Skaldsong campaigns. It builds upon the functionality of the Campaign Editor by integrating with the OpenRouter API to provide intelligent suggestions and automated content generation for specific sections of your campaign.

## Features

- **AI-Powered Refinement:** Use natural language prompts to refine specific sections of your campaign (General Settings, Characters, Locations, Factions, Lorebook).
- **Section-Specific Editing:** The AI context is limited to the specific tab you are currently viewing, ensuring that it only modifies the relevant data (e.g., refining characters won't accidentally change your locations).
- **Visual Editor:** A user-friendly interface to view and manually edit your campaign data, just like the standard Campaign Editor.
- **Advanced Raw JSON Editing:** Access the raw JSON structure for fine-grained control over your campaign files.

## Requirements

- Python 3.x
- `requests` library (`pip install requests`)
- An OpenRouter API Key

## Usage

1. Run the application:
   ```bash
   python campaign_refiner.py
   ```
2. Enter your OpenRouter API Key and select your preferred model in the "Global AI Settings" panel at the top.
3. Go to `File > Open Campaign Directory...` and select a folder containing your campaign JSON files.
4. Navigate to the tab you want to refine (e.g., "Characters").
5. In the "AI Refinement" panel at the top of the tab, enter a prompt describing how you want to change the data (e.g., "Add two new villainous characters", "Make all characters more mysterious", "Fix any spelling errors").
6. Click "Refine with AI". The tool will send the current section's data to the AI, process the response, and update the UI with the new data.
7. Review the changes in the list and form below.
8. Go to `File > Save All` to save your refined campaign back to the directory.

## How it Works

When you click "Refine with AI", the tool packages the current JSON data for that specific tab along with your prompt and sends it to the OpenRouter API. The AI is instructed to return a modified version of the JSON data that matches the original structure. The tool then parses this response and updates the internal data and the user interface.
