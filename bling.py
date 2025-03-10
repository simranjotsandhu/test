import pandas as pd

def create_text_files_from_excel(excel_file):
    """
    Reads an Excel file and creates separate text files for each row based on the 'Body' column.
    Files are named by concatenating 'ArticleID', 'Company', and 'Date' with underscores.
    If 'Body' is empty, a specific message is written to the file.
    
    Parameters:
        excel_file (str): Path to the Excel file to process.
    """
    # Step 1: Read the Excel file into a DataFrame
    try:
        df = pd.read_excel(excel_file)
    except FileNotFoundError:
        print(f"Error: The file '{excel_file}' was not found.")
        return
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Step 2: Verify required columns exist
    required_columns = ['ArticleID', 'Company', 'Date', 'Body']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        return

    # Step 3: Process each row
    for index, row in df.iterrows():
        # Extract and process the columns for the filename
        article_id_str = str(row['ArticleID'])  # Convert ArticleID to string
        company_str = str(row['Company'])       # Convert Company to string
        company_processed = company_str.replace(' ', '_')  # Replace spaces with underscores
        
        # Process the Date to extract YYYY-MM-DD
        try:
            date_part = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            print(f"Error: Invalid date format in row {index}. Skipping this row.")
            continue

        # Construct the filename
        filename = f"{article_id_str}_{company_processed}_{date_part}.txt"

        # Determine the content based on the Body column
        body = row['Body']
        if pd.isna(body) or (isinstance(body, str) and body.strip() == ''):
            content = "This space is intentionally left blank, please tag using the Title information."
        else:
            content = str(body)  # Ensure content is a string, preserving original text

        # Step 4: Write the content to a text file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created file: {filename}")
        except Exception as e:
            print(f"Error writing file '{filename}': {e}")

# Example usage
if __name__ == "__main__":
    # Replace 'your_excel_file.xlsx' with the path to your Excel file
    create_text_files_from_excel('your_excel_file.xlsx')
