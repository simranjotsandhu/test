import pandas as pd
import os
import re
from IPython.display import display, HTML

def create_text_files_from_excel(excel_file, output_folder="output_files"):
    """
    Reads an Excel file and creates separate text files for each row based on the 'Body' column.
    Files are written into a specified output folder, named by concatenating 'ArticleID', 'Company', 
    and 'Date' with underscores. For 'Company', spaces are replaced with underscores before removing 
    special characters (except _ and -). Filenames are converted to lowercase. If 'Body' is empty, 
    a specific message is written to the file. After generation, clickable links are displayed in the 
    notebook to access each file via JupyterHub's /files/ endpoint.

    Parameters:
        excel_file (str): Name of the Excel file in the same directory as this script.
        output_folder (str): Name or path of the folder where files will be saved (default: 'output_files').
    """
    # Step 1: Create the output folder if it doesn’t exist
    try:
        os.makedirs(output_folder, exist_ok=True)
        print(f"Output folder '{output_folder}' is ready at {os.path.abspath(output_folder)}")
    except Exception as e:
        print(f"Error creating output folder '{output_folder}': {e}")
        return

    # Step 2: Read the Excel file into a DataFrame
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        print(f"Error: The file '{excel_file}' was not found.")
        return
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Step 3: Verify required columns exist
    required_columns = ['ArticleID', 'Company', 'Date', 'Body']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        return

    # Step 4: Process each row
    filenames = []  # To store relative paths of generated files
    for index, row in df.iterrows():
        article_id_str = str(row['ArticleID'])
        company_str = str(row['Company'])
        
        try:
            date_part = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            print(f"Error: Invalid date format in row {index}. Skipping this row.")
            continue

        # Clean the components
        company_with_underscores = company_str.replace(' ', '_')
        company_cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', company_with_underscores).lower()
        article_id_cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', article_id_str).lower()
        date_cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', date_part).lower()

        # Construct the filename
        filename = os.path.join(output_folder, f"{article_id_cleaned}_{company_cleaned}_{date_cleaned}.txt")
        
        # Determine the content
        body = row['Body']
        if pd.isna(body) or (isinstance(body, str) and body.strip() == ''):
            content = "This space is intentionally left blank, please tag using the Title information."
        else:
            content = str(body)

        # Write the content to a text file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created file: {filename}")
            relative_path = os.path.relpath(filename, os.getcwd())
            filenames.append(relative_path)
        except Exception as e:
            print(f"Error writing file '{filename}': {e}")

    # Step 5: Display clickable links
    if filenames:
        links = ''.join([
            f'<li><a href="/files/{filename}" target="_blank">{os.path.basename(filename)}</a></li>'
            for filename in filenames
        ])
        html_output = (
            '<p>The following files have been generated and can be accessed by clicking the links below '
            '(opens in a new tab):</p><ul>{}</ul>'.format(links)
        )
        display(HTML(html_output))
    else:
        print("No files were generated.")

# Example usage
excel_file = 'your_excel_file.xlsx'  # Replace with your actual Excel filename
if not os.path.exists(excel_file):
    print(f"Error: '{excel_file}' not found in the current directory: {os.getcwd()}")
else:
    create_text_files_from_excel(excel_file, 'output_files')

# Public server endpoint for accessing files:
# After running this script, the generated files can be accessed via:
# https://<your-jupyterhub-domain>/user/<your-username>/files/output_files/<filename>.txt
# Example: https://example.com/user/johndoe/files/output_files/001_abc_corp_2023-10-01.txt
# Replace <your-jupyterhub-domain> and <your-username> with your actual JupyterHub domain and username.
