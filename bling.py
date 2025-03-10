import pandas as pd
import os
import re

def create_text_files_from_excel(excel_file, output_folder="output_files"):
    """
    Reads an Excel file and creates separate text files for each row based on the 'Body' column.
    Files are written into a specified output folder, named by concatenating 'ArticleID', 'Company', 
    and 'Date' with underscores. For 'Company', spaces are replaced with underscores before removing 
    special characters (except _ and -). Filenames are converted to lowercase. If 'Body' is empty, 
    a specific message is written to the file.
    
    Parameters:
        excel_file (str): Path to the Excel file to process.
        output_folder (str): Name or path of the folder where files will be saved (default: 'output_files').
    """
    # Step 1: Create the output folder if it doesn’t exist
    try:
        os.makedirs(output_folder, exist_ok=True)
        print(f"Output folder '{output_folder}' is ready.")
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
        # - For Company: Replace spaces with underscores FIRST, then remove special characters
        company_with_underscores = company_str.replace(' ', '_')
        company_cleaned = re.sub(r'[^a-zA-Z0-9_-]', '', company_with_underscores).lower()
        
        # - For ArticleID and Date: Remove special characters (except _ and -) and convert to lowercase
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
        except Exception as e:
            print(f"Error writing file '{filename}': {e}")

# Example usage
if __name__ == "__main__":
    # Replace 'your_excel_file.xlsx' with the path to your Excel file
    create_text_files_from_excel('your_excel_file.xlsx', 'output_files')
