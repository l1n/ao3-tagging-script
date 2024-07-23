import csv
import re
from bs4 import BeautifulSoup
import requests
import time
import yaml
import os
from pathlib import Path
from AO3 import Work, Session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'google_sheets_token.pickle'
SERVICE_FILE = 'google_sheets_service.pickle'
CONFIG_PATH = Path.home() / '.config' / 'ao3-tagging-script.yaml'

import pickle

class Collection:
    def __init__(self, collection_id, session=None):
        self.collection_id = collection_id
        self.url = f"https://archiveofourown.org/collections/{collection_id}/items"
        print(self.url)
        self.works = []
        self.session = session or self.load_session()
        if not self.session:
            raise ValueError("No valid session provided or found.")
        self.fetch_collection()

    def load_session(self):
        if os.path.exists('ao3_session.pkl'):
            with open('ao3_session.pkl', 'rb') as f:
                return pickle.load(f)
        return None

    def save_session(self):
        with open('ao3_session.pkl', 'wb') as f:
            pickle.dump(self.session, f)

    def fetch_collection(self):
        assert self.session.session
        print(self.session.session)
        print(self.session.bookmarks)
        response = self.session.request(self.url)
        assert "logout" in response.text, "Session does not appear to be authed"
        assert self.collection_id in response.text, "Unable to retrieve collection"
        if response.status_code == 200:
            self.parse_collection_page(response.text)
        else:
            raise Exception(f"Failed to fetch collection: {response.status_code}")

    def parse_collection_page(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        work_items = soup.find_all('li', class_='collection item')
        
        for item in work_items:
            work = {}
            work['title'] = item.find('h4', class_='heading').text.strip()
            work['author'] = item.find('h5', class_='heading').contents[0].strip()
            
            recipient = item.find('span', class_='recipients')
            if recipient:
                work['recipient'] = recipient.text.strip().replace('for ', '')
            
            work['date'] = item.find('p', class_='datetime').text.strip()
            
            # Check if work is unrevealed/anonymous
            mystery = item.find('div', class_='mystery')
            work['unrevealed'] = bool(mystery)
            
            # Extract work ID from the link
            link = item.find('a', href=True)
            if link:
                work['id'] = link['href'].split('/')[-1]
            
            self.works.append(work)

    def get_works(self):
        return self.works

def get_authenticated_session(username, password):
    if os.path.exists('ao3_session.pkl'):
        with open('ao3_session.pkl', 'rb') as f:
            session = pickle.load(f)
        if session.is_authed:
            print("Using saved session.")
            return session

    print("Authenticating with AO3...")
    session = Session(username, password)
    if session.is_authed:
        print("Authentication successful.")
        with open('ao3_session.pkl', 'wb') as f:
            pickle.dump(session, f)
        return session
    else:
        raise Exception("Authentication failed.")

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    return {}

def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f)

def get_input_with_default(prompt, key, config):
    default = config.get(key, '')
    user_input = input(f"{prompt} [{default}]: ").strip()
    return user_input if user_input else default

def get_google_sheet_service():
    creds = None
    service = None

    # Try to load the service from disk
    if os.path.exists(SERVICE_FILE):
        with open(SERVICE_FILE, 'rb') as token:
            service = pickle.load(token)
        print("Loaded Google Sheets service from cache.")
        return service

    # If service not found, try to load credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)

    # If credentials are invalid or don't exist, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)

    # Build the service
    service = build('sheets', 'v4', credentials=creds)

    # Cache the service
    with open(SERVICE_FILE, 'wb') as f:
        pickle.dump(service, f)

    print("Created and cached new Google Sheets service.")
    return service

def fetch_giftless_treatless_list(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    giftless_treatless_list = []

    # Find the table rows
    rows = soup.find_all('tr')

    for row in rows[1:]:  # Skip the header row
        cells = row.find_all('td')
        if cells and len(cells) > 0:
            recipient = cells[0].text.strip().lower()
            if recipient:
                giftless_treatless_list.append(recipient)

    return giftless_treatless_list

def fetch_work_data(work_id, collection_name, giftless_treatless_list, session):
    try:
        work = Work(work_id, session=session)
        time.sleep(15)  # Rate limiting: 1 request per 15 seconds
        claimed_tags, is_giftless_treatless = parse_authors_note(work.notes, giftless_treatless_list)
        
        data = {
            'Team': collection_name,
            'Stage': 'Board 3',
            'Art': 'Yes' if any('art' in tag.lower() for tag in claimed_tags) else '',
            'Podfic': 'Yes' if any('podfic' in tag.lower() for tag in claimed_tags) else '',
            'Fic': 'Yes' if any('fic' in tag.lower() for tag in claimed_tags) else '',
            'Points': '',  # To be filled manually
            'Wordcount': work.words,
            'Creator 1': work.authors[0].name if work.authors else 'Anonymous',
            'Creator 2': work.authors[1].name if len(work.authors) > 1 else '',
            'Creator 3': work.authors[2].name if len(work.authors) > 2 else '',
            'Recipient': work.recipients[0] if work.recipients else '',
            'Link': f"https://archiveofourown.org/works/{work_id}",
            'Rating': work.rating,
            'Ship': ', '.join(work.relationships[:3]),  # Limit to 3 ships
            'Warning': ', '.join(work.warnings),
            'claimed_tags': claimed_tags,
            'is_giftless_treatless': is_giftless_treatless,
            'questionable': is_questionable(work, claimed_tags)
        }
        return data
    except Exception as e:
        print(f"Error fetching work {work_id}: {str(e)}")
        return None

def parse_authors_note(notes, giftless_treatless_list):
    tag_match = re.search(r'Claimed Tags:(.*?)(?:\n|$)', notes, re.IGNORECASE | re.DOTALL)
    claimed_tags = [tag.strip() for tag in tag_match.group(1).split(',')] if tag_match else []
    
    is_giftless_treatless = False
    if 'Giftless/Treatless' in claimed_tags:
        claimed_tags.remove('Giftless/Treatless')
        is_giftless_treatless = any(recipient.lower() in giftless_treatless_list for recipient in work.recipients)
    
    return claimed_tags, is_giftless_treatless

def is_questionable(work, claimed_tags):
    return len(work.tags) > 20 and work.words < 1000

def load_existing_works(sheet_id, service):
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id, range="Work Input Manual!A2:Z").execute()
    rows = result.get('values', [])
    return {row[11].split('/')[-1]: row for row in rows if row and len(row) > 11}  # Use the work ID as the key

def update_google_sheet(sheet_id, collection_name, giftless_treatless_list, session):
    service = get_google_sheet_service()
    sheet = service.spreadsheets()

    existing_works = load_existing_works(sheet_id, service)

    # Fetch works from the collection
    collection = Collection(collection_name, session=session)
    works = collection.works

    rows = []
    questionable_works = []

    for work in works:
        work_id = str(work.id)
        if work_id in existing_works:
            rows.append(existing_works[work_id])
            continue

        work_data = fetch_work_data(work_id, collection_name, giftless_treatless_list, session)
        if work_data:
            row = [
                work_data['Team'], work_data['Stage'], work_data['Art'], work_data['Podfic'],
                work_data['Fic'], work_data['Points'], work_data['Wordcount'],
                work_data['Creator 1'], work_data['Creator 2'], work_data['Creator 3'],
                work_data['Recipient'], work_data['Link'], work_data['Rating'],
                work_data['Ship'], work_data['Warning']
            ]
            
            # Add claimed tags
            row.extend(work_data['claimed_tags'][:10])  # Limit to 10 tags
            row.extend([''] * (10 - len(work_data['claimed_tags'])))  # Fill remaining tag columns

            if work_data['is_giftless_treatless']:
                row.append('Giftless/Treatless')
            
            rows.append(row)

            if work_data['questionable']:
                questionable_works.append(work_data['Link'])

    # Update the sheet
    range_name = 'Work Input Manual!A2:Z'  # Adjust as needed
    body = {'values': rows}
    result = sheet.values().update(spreadsheetId=sheet_id, range=range_name,
                                   valueInputOption='USER_ENTERED', body=body).execute()

    print(f"{result.get('updatedCells')} cells updated.")
    
    if questionable_works:
        print("Questionable works for mod review:")
        for link in questionable_works:
            print(link)

def main():
    config = load_config()

    sheet_id = get_input_with_default("Enter the Google Sheet ID", 'sheet_id', config)
    collection_name = get_input_with_default("Enter the AO3 collection name", 'collection_name', config)
    ao3_username = get_input_with_default("Enter your AO3 username", 'ao3_username', config)
    ao3_password = get_input_with_default("Enter your AO3 password", 'ao3_password', config)
    giftless_treatless_url = get_input_with_default(
        "Enter the Giftless/Treatless list URL",
        'giftless_treatless_url',
        config
    ) or "https://docs.google.com/spreadsheets/d/e/2PACX-1vST8p8S_FQze2UI3Bf_0TZXvLZ1AUQ-55ea-1sj3Hz9fsEZTr9jdjH6lSsvhGo2Q3nJhMDShMhfj8h9/pubhtml?gid=267409686&single=true"

    # Update config with new values
    config.update({
        'sheet_id': sheet_id,
        'collection_name': collection_name,
        'ao3_username': ao3_username,
        'ao3_password': ao3_password,
        'giftless_treatless_url': giftless_treatless_url
    })
    save_config(config)
    
    giftless_treatless_list = fetch_giftless_treatless_list(giftless_treatless_url)
    
    # Authenticate with AO3
    session = get_authenticated_session(ao3_username, ao3_password)
    if session.is_authed:
        print("Successfully authenticated with AO3")
    else:
        print("Failed to authenticate with AO3")
        return

    update_google_sheet(sheet_id, collection_name, giftless_treatless_list, session)

if __name__ == "__main__":
    main()
