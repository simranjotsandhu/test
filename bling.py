import pandas as pd
import os
import re
from flask import Flask, send_from_directory
from pyngrok import ngrok
import socket

# Function to create text files from Excel
def create_text_files_from_excel(excel_file, output_folder="output_files"):
    """
    Reads an Excel file and creates separate text files for each row based on the 'Body' column.
    Files are written into a specified output folder, named by concatenating 'ArticleID', 'Company', 
    and 'Date' with underscores. For 'Company', spaces are replaced with underscores before removing 
    special characters (except _ and -). Filenames are converted to lowercase. If 'Body' is empty, 
    a specific message is written to the file.

    Parameters:
        excel_file (str): Path to the Excel file.
        output_folder (str): Path to the folder where files will be saved (default: 'output_files').
    
    Returns:
        list: List of full paths to generated files, or empty list if an error occurs.
    """
    # Create the output folder if it doesn’t exist
    try:
        os.makedirs(output_folder, exist_ok=True)
        print(f"Output folder '{output_folder}' is ready at {os.path.abspath(output_folder)}")
    except Exception as e:
        print(f"Error creating output folder '{output_folder}': {e}")
        return []

    # Read the Excel file into a DataFrame
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        print(f"Error: The file '{excel_file}' was not found.")
        return []
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

    # Verify required columns exist
    required_columns = ['ArticleID', 'Company', 'Date', 'Body']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        return []

    # Process each row
    filenames = []
    for index, row in df.iterrows():
        # Extract and process columns for the filename
        article_id_str = str(row['ArticleID'])
        company_str = str(row['Company'])
        
        # Process the Date to YYYY-MM-DD format
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
        
        # Determine content
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
            filenames.append(filename)
        except Exception as e:
            print(f"Error writing file '{filename}': {e}")

    return filenames

# Initialize Flask app
app = Flask(__name__)
output_folder = "output_files"  # Must match the output folder used above

# Route to serve individual files
@app.route('/files/<filename>')
def serve_file(filename):
    """Serve a file from the output folder."""
    try:
        return send_from_directory(output_folder, filename)
    except Exception as e:
        return f"Error: {e}", 404

# Route for the index page
@app.route('/')
def index():
    """Display a list of all generated files with links."""
    files = [f for f in os.listdir(output_folder) if f.endswith('.txt')]
    links = ''.join([f'<li><a href="/files/{f}">{f}</a></li>' for f in files])
    return f'<h1>Generated Files</h1><ul>{links}</ul>'

# Main execution
if __name__ == "__main__":
    excel_file = 'your_excel_file.xlsx'  # Replace with your actual Excel filename
    output_folder = 'output_files'
    filenames = create_text_files_from_excel(excel_file, output_folder)
    if filenames:
        try:
            # Start ngrok for public access
            public_url = ngrok.connect(5000).public_url
            # Get local IP for local network access
            local_ip = socket.gethostbyname(socket.gethostname())
            local_url = f"http://{local_ip}:5000"
            print(f"Files generated successfully.")
            print(f"Access the index page at:")
            print(f"  Local URL: {local_url}")
            print(f"  Public URL (via ngrok): {public_url}")
            print("The index page lists all generated files with links.")
            print("Press Ctrl+C to stop the server.")
            # Optional: Uncomment to open the local URL in the default browser
            # import webbrowser
            # webbrowser.open(local_url)
            # Run the Flask app
            app.run(host='0.0.0.0', port=5000)
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("No files generated.")
