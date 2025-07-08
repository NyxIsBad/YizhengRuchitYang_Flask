import gspread
import configparser
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession
from oauth2client.service_account import ServiceAccountCredentials

def authenticate_google_sheets(credentials_file, sheet_id, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
   # creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
    
    session = AuthorizedSession(creds)
    session.timeout = 10  # Timeout in seconds

    client = gspread.Client(auth=creds)
    client.session = session

    sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    return sheet

config = configparser.ConfigParser()
config.read('config.cfg')

global_cred_file = config.get('settings', 'json_file')
global_sheet_id = config.get('settings', 'sheet_id')
global_worksheet_name = config.get('settings', 'sheet_tab')

sheet = authenticate_google_sheets(global_cred_file, global_sheet_id, global_worksheet_name)
print(sheet.title)