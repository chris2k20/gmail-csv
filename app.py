import os
import base64
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_service():
    creds = None
    # Load existing token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

def list_labels(service):
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    return labels

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
    """ Recursive function to deeply extract email content from multipart messages. """
    if payload.get('mimeType') == 'text/plain' or payload.get('mimeType') == 'text/html':
        if payload.get('body').get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    if 'parts' in payload:
        # If this payload part has further parts, recursively search each part
        for part in payload['parts']:
            content = extract_content(part)
            if content:  # Return the first piece of text content found
                return content
    return None  # Return None if no text content found

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

    # Extracting the body of the email depending on its MIME type
    part = msg['payload']
    if part['mimeType'] == 'text/plain' or part['mimeType'] == 'text/html':
        email_data['content'] = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    else:
        # Handle multipart/alternative or other nested structures
        for sub_part in part['parts']:
            if sub_part['mimeType'] == 'text/plain' or sub_part['mimeType'] == 'text/html':
                email_data['content'] = base64.urlsafe_b64decode(sub_part['body']['data']).decode('utf-8')
                break

    return email_data

def download_emails(label_name):
    service = get_service()
    labels = list_labels(service)
    label_id = next((label['id'] for label in labels if label['name'].lower() == label_name.lower()), None)
    if not label_id:
        print(f"No label found with the name {label_name}")
        return

    messages = list_emails(service, [label_id])
    if not messages:
        print("No messages found with this label.")
        return

    emails = []
    for message in messages:
        email_info = get_message(service, message['id'])
        if email_info['subject'] and email_info['content']:
            emails.append(email_info)
        else:
            print(f"Message with ID {message['id']} has no content or subject.")

    print(f"Total emails collected: {len(emails)}")

    df = pd.DataFrame(emails)
    df.to_csv(f'{label_name}_emails.csv', index=False)
    print(f"Emails saved to {label_name}_emails.csv")

# Use the label name, not the label ID
download_emails('Sent')
