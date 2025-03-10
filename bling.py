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
    """Generate text files from an Excel file based on 'ArticleID', 'Company', 'Date', and 'Body' columns."""
    # Check if the Excel file exists
    if not os.path.exists(excel_file):
        print(f"Error: '{excel_file}' not found.")
        return []

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # Read the Excel file
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []

    # List to store generated filenames
    filenames = []

    # Process each row in the DataFrame
    for index, row in df.iterrows():
        try:
            # Extract required columns
            article_id = str(row['ArticleID']).strip()
            company = str(row['Company']).strip()
            date = pd.to_datetime(row['Date']).strftime('%Y%m%d')  # Format date as YYYYMMDD
            body = str(row['Body']).strip() if pd.notna(row['Body']) else ""

            # Construct the filename
            # Replace invalid filename characters with underscores
            company_cleaned = re.sub(r'[<>:"/\\|?*]', '_', company)
            filename = f"{article_id}_{company_cleaned}_{date}.txt"
            file_path = os.path.join(output_folder, filename)

            # Write to the text file
            with open(file_path, 'w', encoding='utf-8') as f:
                if body and body.lower() != 'nan':
                    f.write(body)
                else:
                    f.write("No body content available for this article.")
            
            filenames.append(file_path)
            print(f"Generated file: {filename}")
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue

    if not filenames:
        print("No files were generated due to errors or empty data.")
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
        return f"Error: {e}", 404

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
            # Connect ngrok to port 5000
            public_url = ngrok.connect(5000, bind_tls=True).public_url
            print(f"ngrok tunnel started: {public_url}")

            # Generate clickable links using the ngrok public URL
            links = ''.join([
                f'<li><a href="{public_url}/files/{os.path.basename(filename)}" target="_blank">{os.path.basename(filename)}</a></li>'
                for filename in filenames
            ])
            html_output = (
                '<p>Files can be accessed via the following links (opens in a new tab):</p>'
                '<ul>{}</ul>'.format(links)
            )

            # Display the links in the Jupyter notebook
            display(HTML(html_output))
            print("Links to files are displayed above. Click them to access the files via the ngrok URL.")
        except Exception as e:
            print(f"Error starting ngrok: {e}")
    else:
        print("No links to display because no files were generated.")

if __name__ == "__main__":
    main()
