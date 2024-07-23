# UserScript
# AO3 Collection and Work Info Extractor

## Description

This userscript automates the process of extracting information from works in an Archive of Our Own (AO3) collection. It's designed to help moderators or organizers of fandom events, such as exchanges or challenges, to easily compile data about the submitted works.

## Features

- Extracts key information from AO3 works, including:
  - Team name
  - Work type (Fic, Art, Podfic)
  - Word count
  - Creators and recipients
  - Rating
  - Ship category
  - Warnings
  - Tags
- Automatically opens works from a collection one by one
- Copies extracted information to clipboard in a tab-separated format, ready for pasting into a spreadsheet
- Provides a user-friendly button on collection pages to start the extraction process
- Shows notifications to guide the user through the process

## Installation

1. Install a userscript manager like Tampermonkey in your browser.
2. Create a new script in your userscript manager.
3. Copy and paste the entire script into the editor.
4. Save the script.

## Usage

1. Navigate to an AO3 collection page.
2. Click the "Process All Works" button that appears in the top right corner.
3. The script will open each work in the collection in a new tab.
4. For each work, the script will automatically extract the information and copy it to your clipboard.
5. Paste the copied information into your spreadsheet.
6. Close the work's tab and confirm to move to the next work.

## Notes

- The script is set to extract information for "Board 3". You may need to modify this if you're using it for a different event or stage.
- The script attempts to extract tags from the author's notes rather than the AO3 tags. Make sure your participants are following the correct format for including tags in their notes.
- The script currently doesn't calculate points automatically. You'll need to fill in the "Points" column manually based on your event's rules.

## Customization

You can modify the script to change:
- The fields being extracted
- The way certain fields are mapped (e.g., ratings, ship categories)
- The format of the output (currently tab-separated values)

## Limitations

- The script can't access drafts or locked works.
- It relies on the structure of AO3 pages, so it may break if AO3 significantly changes its HTML structure.

## Disclaimer

This script is not affiliated with or endorsed by Archive of Our Own. Use it responsibly and in accordance with AO3's Terms of Service.

# Python

# AO3 Collection Tracker

This script automates the process of tracking and updating information about works in an Archive of Our Own (AO3) collection. It fetches data from AO3, processes it, and updates a Google Sheet with the information.

## Features

- Fetches works from a specified AO3 collection
- Extracts detailed information about each work, including authors, recipients, tags, and more
- Updates a Google Sheet with the collected data
- Handles authentication for both AO3 and Google Sheets
- Supports tracking of "Giftless/Treatless" works
- Identifies potentially questionable works for moderator review

## Prerequisites

- Python 3.6+
- A Google Cloud Platform project with the Sheets API enabled
- AO3 account credentials
- The following Python libraries:
  - `csv`
  - `bs4` (BeautifulSoup)
  - `requests`
  - `pyyaml`
  - `AO3`
  - `google-auth`
  - `google-auth-oauthlib`
  - `google-auth-httplib2`
  - `google-api-python-client`

## Setup

1. Clone this repository to your local machine.
2. Install the required Python libraries:
   ```
   pip install -r requirements.txt
   ```
3. Set up Google Sheets API credentials:
   - Create a project in the Google Cloud Console
   - Enable the Google Sheets API
   - Create credentials (OAuth client ID)
   - Download the credentials and save them as `credentials.json` in the project directory

## Usage

Run the script using Python:

```
python ao3_collection_tracker.py
```

The script will prompt you for the following information:
- Google Sheet ID
- AO3 collection name
- AO3 username and password
- URL for the Giftless/Treatless list (optional)

After providing the necessary information, the script will:
1. Authenticate with AO3
2. Fetch works from the specified collection
3. Process each work and extract relevant data
4. Update the Google Sheet with the collected information
5. Identify any questionable works for moderator review

## Configuration

You can store default values in the configuration file (`~/.config/ao3-tagging-script.yaml`) to avoid entering them each time. The script will use these values as defaults but allow you to override them when prompted.

## Notes

- The script implements rate limiting to avoid overwhelming the AO3 servers. It waits 15 seconds between requests.
- Make sure to comply with AO3's Terms of Service when using this script.
- The script caches authentication tokens to minimize the need for re-authentication.

## Troubleshooting

- If you encounter authentication issues, try deleting the `ao3_session.pkl`, `google_sheets_token.pickle`, and `google_sheets_service.pickle` files to force re-authentication.
- Ensure your Google Cloud project has the necessary API enabled and that your credentials are correctly set up.

## Contributing

Contributions to improve the script are welcome. Please submit a pull request or open an issue to discuss proposed changes.
