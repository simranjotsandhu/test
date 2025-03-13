import pandas as pd
import sys

def merge_excel_sheets(input_files, output_file):
    """
    Merge four Excel files based on columns A, B, and C, combining conflicting values in other columns.
    
    Parameters:
    input_files (list): List of four input Excel file paths.
    output_file (str): Path for the output Excel file.
    """
    try:
        # Step 1: Read all input Excel files and validate presence of columns A, B, C
        dfs = []
        for file in input_files:
            print(f"Reading {file}")
            df = pd.read_excel(file)
            # Check if required columns exist
            if not all(col in df.columns for col in ['A', 'B', 'C']):
                print(f"Error: File {file} does not have columns A, B, and C")
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
        
        # Step 4: Group by A, B, C and aggregate other columns
        print("Merging rows based on columns A, B, C")
        # Define aggregation: 'first' for key columns, combine_unique for others
        agg_dict = {col: 'first' if col in ['A', 'B', 'C'] else combine_unique 
                   for col in combined_df.columns}
        merged_df = combined_df.groupby(['A', 'B', 'C'], as_index=False).agg(agg_dict)
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
    if len(sys.argv) != 6:
        print("Usage: python merge_sheets.py input1.xlsx input2.xlsx input3.xlsx input4.xlsx output.xlsx")
        sys.exit(1)
    
    # Get input and output file paths from command-line arguments
    input_files = sys.argv[1:5]
    output_file = sys.argv[5]
    
    # Execute the merge function
    merge_excel_sheets(input_files, output_file)
