# Skaldsong Campaign Generator

A tool to generate tabletop RPG campaigns using the OpenRouter API.

## Features

- **AI-Powered Generation**: Uses large language models via OpenRouter to generate detailed campaign structures based on a simple prompt.
- **Customizable Prompts**: Provide a theme, setting, or specific plot points to guide the generation.
- **Skaldsong Format**: Automatically packages the generated JSON into a `.campaign` file (ZIP archive) compatible with the Skaldsong ecosystem.
- **Simple GUI**: Easy-to-use graphical interface built with Tkinter.

## Requirements

- Python 3.6+
- `requests` library (`pip install requests`)
- An OpenRouter API Key (get one at [openrouter.ai](https://openrouter.ai/))

## Usage

1. Install the required dependencies:
   ```bash
   pip install requests
   ```

2. Run the generator:
   ```bash
   python campaign_generator.py
   ```

3. Enter your OpenRouter API Key.
4. (Optional) Change the model if desired (defaults to `google/gemini-2.5-flash`).
5. Enter a prompt describing the campaign you want to generate.
6. Click "Generate Campaign".
7. Once generation is complete, you will be prompted to select a directory to save the extracted campaign format (a folder containing `campaign.json`).
8. You can then click "Export to .campaign" to package the generated campaign into a `.campaign` file.

## Output Format

The generated campaign is saved as a directory containing a `campaign.json` file with the following structure:

```json
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
```

This directory can be edited directly using the `CampaignEditor`. You can also export it to a `.campaign` file (a ZIP archive) for distribution.
