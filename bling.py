# Import necessary libraries
import pandas as pd
import os
import re
from flask import Flask, send_from_directory
from pyngrok import ngrok
import threading
from IPython.display import display, HTML

# Define the function to create text files from Excel
def create_text_files_from_excel(excel_file, output_folder="output_files"):
    """
    Generate text files from an Excel file based on 'ArticleID', 'Company', 'Date', and 'Body' columns.
    Returns a list of generated file paths.
    """
    # Step 1: Create the output folder if it doesn’t exist
    try:
        os.makedirs(output_folder, exist_ok=True)
        print(f"Output folder '{output_folder}' is ready at {os.path.abspath(output_folder)}")
    except Exception as e:
        print(f"Error creating output folder '{output_folder}': {e}")
        return []

    # Step 2: Read the Excel file into a DataFrame
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        print(f"Error: The file '{excel_file}' was not found.")
        return []
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

    # Step 3: Verify required columns exist
    required_columns = ['ArticleID', 'Company', 'Date', 'Body']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        return []

    # Step 4: Process each row and generate files
    filenames = []  # To store full paths of generated files
    for index, row in df.iterrows():
        # Extract and process the columns for the filename
        article_id_str = str(row['ArticleID'])  # Convert ArticleID to string
        company_str = str(row['Company'])       # Convert Company to string
        
        # Process the Date to extract YYYY-MM-DD
        try:
            date_part = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            print(f"Error: Invalid date format in row {index}. Skipping this row.")
            continue

        # Clean the components:
        # For Company: Replace spaces with underscores FIRST, then remove special characters
        company_with_underscores = company_str.replace(' ', '_')
        company_cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', company_with_underscores).lower()
        
        # For ArticleID and Date: Remove special characters (except _ and -) and convert to lowercase
        article_id_cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', article_id_str).lower()
        date_cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', date_part).lower()  # Date already has hyphens

        # Construct the filename with the output folder path
        filename = os.path.join(output_folder, f"{article_id_cleaned}_{company_cleaned}_{date_cleaned}.txt")
        
        # Determine the content based on the Body column
        body = row['Body']
        if pd.isna(body) or (isinstance(body, str) and body.strip() == ''):
            content = "This space is intentionally left blank, please tag using the Title information."
        else:
            content = str(body)  # Ensure content is a string, preserving original text

        # Step 5: Write the content to a text file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created file: {filename}")
            filenames.append(filename)  # Store the full path
        except Exception as e:
            print(f"Error writing file '{filename}': {e}")

    return filenames

# Initialize the Flask app
app = Flask(__name__)
output_folder = "output_files"  # Must match the output folder used above

# Define Flask route to serve files
@app.route('/files/<filename>')
def serve_file(filename):
    """Serve a file from the output folder."""
    try:
        return send_from_directory(output_folder, filename)
    except Exception as e:
        return f"Error: File not found - {e}", 404

# Function to run the Flask app
def run_flask():
    """Run the Flask app on port 5000."""
    app.run(host='0.0.0.0', port=5000)

# Main execution
def main():
    # Specify your Excel file here
    excel_file = 'your_excel_file.xlsx'  # Replace with your actual Excel filename

    # Generate text files
    filenames = create_text_files_from_excel(excel_file, output_folder)

    if filenames:
        # Start the Flask app in a separate thread
        print("Starting Flask app in the background...")
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()

        # Start ngrok to expose the Flask app
        try:
            # Connect ngrok to port 5000 with HTTPS
            public_url = ngrok.connect(5000, bind_tls=True).public_url
            print(f"ngrok tunnel started: {public_url}")

            # Generate clickable links and list public URLs
            links_html = ""
            for filename in filenames:
                basename = os.path.basename(filename)
                full_url = f"{public_url}/files/{basename}"
                links_html += (
                    f'<li>'
                    f'<a href="{full_url}" target="_blank">{basename}</a> '
                    f'(<span style="font-family: monospace">{full_url}</span>)'
                    f'</li>'
                )

            html_output = (
                '<p>The following files have been generated. Click the links to access them '
                '(opens in a new tab), or copy the public URLs:</p>'
                '<ul>{}</ul>'.format(links_html)
            )

            # Display the links and URLs in the Jupyter notebook
            display(HTML(html_output))
            print("Links and public URLs to files are displayed above.")
        except Exception as e:
            print(f"Error starting ngrok: {e}")
    else:
        print("No files were generated, so no URLs to display.")

if __name__ == "__main__":
    main()

# Notes:
# - Ensure 'your_excel_file.xlsx' is in the same directory as this script.
# - Install required packages: pip install pandas openpyxl flask pyngrok ipython
# - ngrok requires an account for prolonged use; get an auth token from ngrok.com if needed:
#   ngrok.set_auth_token("your_ngrok_auth_token")
# - The Flask app runs on port 5000; adjust if this port is in use.
