import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for
import configparser
import re

app = Flask(__name__)

# Global variables for starting row, and current page
start_row = 2
current_row = start_row

# Google Sheets authentication
def authenticate_google_sheets(credentials_file, sheet_id, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    return sheet

# Read configuration from config.cfg
config = configparser.ConfigParser()
config.read('config.cfg')

global_cred_file = config.get('settings', 'json_file')
global_sheet_id = config.get('settings', 'sheet_id')
global_worksheet_name = config.get('settings', 'sheet_tab')

sheet = authenticate_google_sheets(global_cred_file, global_sheet_id, global_worksheet_name)

@app.route('/')
def home():
    # Home page to input start row 
    return render_template('home.html')

@app.route('/set_parameters', methods=['POST'])
def set_parameters():
    global start_row, current_row
    start_row = int(request.form['start_row'])
    current_row = start_row
    return redirect(url_for('process', row_id=start_row))

@app.route('/process/<int:row_id>', methods=['GET'])
def process(row_id=None):
    global current_row, sheet
    rows = sheet.get_all_values()
    num_rows = len(rows)

    # If row_id is provided, use it, otherwise use the global current_row
    if row_id is not None:
        current = row_id
        current_row = row_id
    else:
        current = current_row
    
    # Ensure the current page is within valid bounds
    if current < 2 or current >= num_rows:
        current = 2  # Skip first 2 rows of headers

    row = rows[current]  # Fetch the specific row
    
    if len(row) < 20:  # Ensure row has enough columns
        return redirect(url_for('process', row_id=current))  # Skip if row doesn't have enough columns
    
    M, N = row[12], row[13]  # Columns M, N (zero-indexed: 12, 13)
    K, L = row[10], row[11]  # Columns K, L
    U = row[20]  # Column U
    instructions = row[14:20]  # Columns O-T
    
    instructions = [instr.replace("\n", "<br>") for instr in instructions]
    # Instructions should be 6 long; lets provide strong to 0, 2, 4 (the instructions)
    instructions[0] = "<strong>" + instructions[0] + "</strong>"
    instructions[2] = "<strong>" + instructions[2] + "</strong>"
    instructions[4] = "<strong>" + instructions[4] + "</strong>"
    M = M.replace("\n", "<br>")
    N = N.replace("\n", "<br>")
    K = K.replace("\n", "<br>")
    L = L.replace("\n", "<br>")
    U = U.replace("\\n", "<br>")
    # Prepare data to pass to the template
    data = {
        'index': current,
        'K': K,
        'L': L,
        'M': M,
        'N': N,
        'U': U,
        'instructions': instructions,
        'start_row': current_row,
    }

    return render_template('process.html', data=data)

@app.route('/update/<int:row_id>', methods=['POST'])
def update(row_id):
    global sheet
    M = request.form['M']
    N = request.form['N']
    
    # Update the cells based on the user input
    sheet.update_cell(row_id+1, 11, M)  # Column K
    sheet.update_cell(row_id+1, 12, N)  # Column L
    
    # After updating, redirect to the process page with the updated row_id
    return redirect(url_for('process', row_id=row_id))

def main():
    global sheet
    credentials_file = global_cred_file
    sheet_id = global_sheet_id
    sheet_name = global_worksheet_name
    sheet = authenticate_google_sheets(credentials_file, sheet_id, sheet_name)

    app.run(debug=True)

if __name__ == "__main__":
    main()
