#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import base64
import email
import datetime
from apiclient import errors

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials john.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('gmail', 'v1', credentials=creds)

results = service.users().labels().list(userId='me').execute()
labels = results.get('labels', [])
labels_df = pd.DataFrame.from_dict(labels)
labels_df = labels_df[["name", "id"]].sort_values(by = ["name"]).reset_index(drop=True)
labels_df.columns = ["Label Name", "Label ID"]
labels_df = labels_df[labels_df["Label Name"].apply(lambda x: "Tippers/Betting" in x)].reset_index(drop=True)

tipper = "Timeline"

now = datetime.datetime.now()

start_time_str = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
stop_time_str = now.replace(hour=23, minute=59,second=59,microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')


label_id = labels_df[labels_df["Label Name"].apply(lambda x: tipper in x)]["Label ID"].to_list()[0]

response = service.users().messages().list(userId = "me", labelIds = label_id).execute()
messages = []

if 'messages' in response:
    messages.extend(response['messages'])

while 'nextPageToken' in response:
    page_token = response['nextPageToken']
    response = service.users().messages().list(userId="me",
                                             labelIds=label_id,
                                             pageToken=page_token).execute()
    messages.extend(response['messages'])

message_id_df = pd.DataFrame.from_dict(messages)[["id"]]
message_id_df["Tipper"] = "Allan Darke"
message_id_df.columns = ["Message ID", "Tipper"]

today_date = datetime.datetime.today().strftime("%d-%b-%y")

cols = ["Message ID", "Message Date", "Subject"]
wanted_messages_df = pd.DataFrame(columns = cols)

for message_id in message_id_df["Message ID"].to_list():
    message = service.users().messages().get(userId = "me",
                                         id = message_id, 
                                         format = 'raw').execute()
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    message_date = pd.to_datetime(str(msg_str).split("Date: ")[1].split("+")[0].strip())
    new_message_date = message_date.date().strftime("%d-%b-%y")

    if new_message_date == today_date:
        subject = str(msg_str).split('Subject: ')[1].split("\\r\\n")[0]
        data = [[message_id, message_date, subject]]
        data = pd.DataFrame(data, columns = cols)
        wanted_messages_df = wanted_messages_df.append(data, ignore_index = True)
    else:
        break


for message_id in wanted_messages_df["Message ID"].to_list():

    message = service.users().messages().get(userId = "me",
                                                 id = message_id, 
                                                 format = 'raw').execute()
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

