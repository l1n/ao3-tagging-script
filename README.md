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
