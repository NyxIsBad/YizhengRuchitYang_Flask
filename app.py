import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template, request, redirect, url_for
import configparser
from markupsafe import escape, Markup

app = Flask(__name__)

# Global variables for starting row, and current page
start_row = 2
current_row = start_row
alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
a_to_index = {char: index for index, char in enumerate(alphabet)}

# global variables for actual columns to select
Single_Turn = a_to_index['E']
Interaction_Type = a_to_index['F']
J_Semantic_Adherence = a_to_index['G'] # judgement
J_Interaction_Type = a_to_index['H'] #judgement
Multi_Turn_1 = a_to_index['I']
Multi_Turn_2 = a_to_index['J']
Multi_Turn_3 = a_to_index['K']
Misc_Comments = a_to_index['L']
Corrected_Turn_1 = a_to_index['M']
Corrected_Turn_2 = a_to_index['N']
Corrected_Turn_3 = a_to_index['O']

# Google Sheets authentication
def authenticate_google_sheets(credentials_file, sheet_id, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    return sheet

def convert_newlines(text):
    return str(escape(text)).replace("\n", "<br>").replace(r"\n", "<br>")

def highlight_matching_lines(single_text, multi_text):
    import re
    from markupsafe import Markup, escape

    # Normalize text for comparison
    def normalize(s):
        return s.replace('\\\\', '\\').strip()

    # Normalize all lines in the single turn text
    single_lines_normalized = set(
        normalize(line) for line in single_text.splitlines() if line.strip()
    )

    # Regex to match standalone 3-digit numbers
    three_digit_re = re.compile(r'\b\d{3}\b')

    highlighted_lines = []
    for line in multi_text.splitlines():
        raw_line = line
        norm_line = normalize(line)

        # Escape
        escaped_line = escape(raw_line)

        # Possible error codes? 
        escaped_line = three_digit_re.sub(
            lambda m: f'<span style="color: red">{m.group()}</span>',
            escaped_line
        )

        # Highlight matching lines in yellow background
        if norm_line in single_lines_normalized:
            highlighted_line = f'<span style="background-color: yellow">{escaped_line}</span>'
        else:
            highlighted_line = escaped_line

        highlighted_lines.append(highlighted_line)

    return Markup('<br>'.join(highlighted_lines))




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
    global current_row, sheet, Single_Turn, Interaction_Type, J_Semantic_Adherence, J_Interaction_Type, Multi_Turn_1, Multi_Turn_2, Multi_Turn_3, Misc_Comments, Corrected_Turn_1, Corrected_Turn_2, Corrected_Turn_3
    # Get the number of rows in the sheet

    # If row_id is provided, use it; otherwise, use the global current_row
    if row_id is not None:
        current_row = row_id
        current = row_id
    else:
        current = current_row

    # Ensure the current page is within valid bounds
    if current < 2:
        current = 2  # Skip the first 2 rows of headers

    # Fetch the specific row directly from the sheet by row_id
    row = sheet.row_values(current)  # Fetch the specific row instead of all rows
    print(row)
    if len(row) < 22:
        row.extend([''] * (22 - len(row)))  # Extend the row with empty strings up to 22 columns
    
    data = {
        'index': current,
        'single_turn': convert_newlines(row[Single_Turn]),  # Column E
        'j_semantic_adherence': row[J_Semantic_Adherence],  # Column G
        'j_interaction_type': row[J_Interaction_Type],  # Column H
        'interaction_type': row[Interaction_Type],  # Column F
        'multi_turn_1': highlight_matching_lines(row[Single_Turn], row[Multi_Turn_1]),  # Column I
        'multi_turn_2': highlight_matching_lines(row[Single_Turn], row[Multi_Turn_2]),  # Column J
        'multi_turn_3': highlight_matching_lines(row[Single_Turn], row[Multi_Turn_3]),  # Column K
        'misc_comments': convert_newlines(row[Misc_Comments]),  # Column L
        'corrected_turn_1': row[Corrected_Turn_1],  # Column M
        'corrected_turn_2': row[Corrected_Turn_2],  # Column N
        'corrected_turn_3': row[Corrected_Turn_3],
        'start_row': current_row,
    }

    return render_template('process.html', data=data)

@app.route('/update/<int:row_id>', methods=['POST'])
def update(row_id):
    global sheet, Single_Turn, Interaction_Type, J_Semantic_Adherence, J_Interaction_Type, Multi_Turn_1, Multi_Turn_2, Multi_Turn_3, Misc_Comments, Corrected_Turn_1, Corrected_Turn_2, Corrected_Turn_3

    new_semantic_judgement = request.form.get('j_semantic', '')  # Get Semantic Adherence judgement, default to empty string if missing
    new_interaction_judgement = request.form.get('j_interaction', '')  # Get Interaction judgement, default to empty string if missing
    new_misc_comments = request.form.get('misc', '')  # Get Misc Comments, default to empty string if missing
    new_corrected_turn_1 = request.form.get('corrected_turn_1', '')  # Get Corrected Turn 1, default to empty string if missing
    new_corrected_turn_2 = request.form.get('corrected_turn_2', '')  # Get Corrected Turn 2, default to empty string if missing
    new_corrected_turn_3 = request.form.get('corrected_turn_3', '')  # Get Corrected Turn 3, default to empty string if missing
    # Update the cells based on the user input
    sheet.update_cell(row_id, J_Semantic_Adherence + 1, new_semantic_judgement)
    sheet.update_cell(row_id, J_Interaction_Type + 1, new_interaction_judgement)
    sheet.update_cell(row_id, Misc_Comments + 1, new_misc_comments)
    sheet.update_cell(row_id, Corrected_Turn_1 + 1, new_corrected_turn_1)
    sheet.update_cell(row_id, Corrected_Turn_2 + 1, new_corrected_turn_2)
    sheet.update_cell(row_id, Corrected_Turn_3 + 1, new_corrected_turn_3)

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
