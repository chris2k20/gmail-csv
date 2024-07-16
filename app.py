import os
import base64
import pandas as pd
import csv
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def list_labels(service):
    results = service.users().labels().list(userId='me').execute()
    return results.get('labels', [])

def list_emails(service, label_ids):
    messages = []
    next_page_token = None
    while True:
        results = service.users().messages().list(userId='me', labelIds=label_ids, pageToken=next_page_token).execute()
        messages.extend(results.get('messages', []))
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break
    return messages

def extract_content(payload):
    if payload.get('mimeType') in ['text/plain', 'text/html'] and payload.get('body').get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    for part in payload.get('parts', []):
        content = extract_content(part)
        if content:
            return content
    return None

def get_message(service, msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    headers = msg['payload']['headers']
    email_data = {
        'subject': next((header['value'] for header in headers if header['name'] == 'Subject'), None),
        'from': next((header['value'] for header in headers if header['name'] == 'From'), None),
        'to': next((header['value'] for header in headers if header['name'] == 'To'), None),
        'date': next((header['value'] for header in headers if header['name'] == 'Date'), None),
        'content': extract_content(msg['payload'])
    }
    if email_data['subject'] and email_data['content']:  # Ensure both subject and content are not None
        return email_data
    return None

def download_emails(label_name):
    service = get_service()
    label_id = next((label['id'] for label in list_labels(service) if label['name'].lower() == label_name.lower()), None)
    if not label_id:
        print(f"No label found with the name {label_name}")
        return
    messages = list_emails(service, [label_id])
    emails = [get_message(service, message['id']) for message in messages]
    emails = [email for email in emails if email is not None]  # Filter out None results
    csv_file = f"docs/{label_name}_emails.csv"
    if emails:
        df = pd.DataFrame(emails)
        df.to_csv(csv_file, index=False, sep=',', quotechar='"', quoting=csv.QUOTE_ALL)
        print(f"Total emails collected: {len(emails)}")
        print(f"Emails saved to {csv_file}")
    else:
        print("No emails with content and subject were found.")

download_emails('Sent')
