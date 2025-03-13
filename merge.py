import pandas as pd
import sys

def merge_excel_sheets(input_files, key_columns, output_file):
    """
    Merge four Excel files based on user-specified key columns, combining conflicting values in other columns.
    
    Parameters:
    input_files (list): List of four input Excel file paths.
    key_columns (list): List of column names to use for merging (provided by user).
    output_file (str): Path for the output Excel file.
    """
    try:
        # Step 1: Read all input Excel files and validate presence of key columns
        dfs = []
        for file in input_files:
            print(f"Reading {file}")
            df = pd.read_excel(file)
            # Check if all key columns are present in the file
            missing_cols = [col for col in key_columns if col not in df.columns]
            if missing_cols:
                print(f"Error: File {file} is missing columns: {', '.join(missing_cols)}")
                sys.exit(1)
            dfs.append(df)
        
        # Step 2: Concatenate all DataFrames into one
        print("Concatenating the sheets")
        combined_df = pd.concat(dfs, axis=0, ignore_index=True)
        print(f"Combined shape: {combined_df.shape}")
        
        # Step 3: Define function to combine unique values
        def combine_unique(series):
            # Remove NaN values and get unique values as strings
            s = series.dropna()
            if s.empty:
                return ''  # Return empty string if no non-NaN values
            else:
                return ', '.join(s.astype(str).unique())
        
        # Step 4: Group by key columns and aggregate other columns
        print(f"Merging rows based on columns: {', '.join(key_columns)}")
        # Define aggregation: 'first' for key columns, combine_unique for others
        agg_dict = {col: 'first' if col in key_columns else combine_unique 
                    for col in combined_df.columns}
        merged_df = combined_df.groupby(key_columns, as_index=False, dropna=False).agg(agg_dict)
        print(f"Merged shape: {merged_df.shape}")
        
        # Step 5: Write the result to the output file
        print(f"Writing to {output_file}")
        merged_df.to_excel(output_file, index=False)
        print("Merge completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: One of the input files was not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Check command-line arguments
    if len(sys.argv) != 9:
        print("Usage: python merge_sheets.py input1.xlsx input2.xlsx input3.xlsx input4.xlsx col1 col2 col3 output.xlsx")
        sys.exit(1)
    
    # Get input files, key columns, and output file from command-line arguments
    input_files = sys.argv[1:5]  # First 4 arguments after script name
    key_columns = sys.argv[5:8]  # Next 3 arguments are column names
    output_file = sys.argv[8]    # Last argument is output file
    
    # Execute the merge function
    merge_excel_sheets(input_files, key_columns, output_file)
