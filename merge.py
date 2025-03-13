import pandas as pd
import sys

def merge_excel_sheets(input_files, key_columns, special_col, output_file):
    """
    Merge four Excel files based on user-specified key columns, combining conflicting values in other columns,
    and add a 'filename' column that lists filenames only when there are conflicts in the special column.
    
    Parameters:
    input_files (list): List of four input Excel file paths.
    key_columns (list): List of column names to use for merging (provided by user).
    special_col (str): The special column name to check for conflicts (provided by user).
    output_file (str): Path for the output Excel file.
    """
    try:
        # Read all input Excel files and add 'filename' column
        dfs = []
        for file in input_files:
            print(f"Reading {file}")
            df = pd.read_excel(file)
            df['filename'] = file  # Add filename column to track source file
            # Validate that all key columns and the special column are present
            missing_cols = [col for col in key_columns + [special_col] if col not in df.columns]
            if missing_cols:
                print(f"Error: File {file} is missing columns: {', '.join(missing_cols)}")
                sys.exit(1)
            dfs.append(df)
        
        # Concatenate all DataFrames
        print("Concatenating the sheets")
        combined_df = pd.concat(dfs, axis=0, ignore_index=True)
        print(f"Combined shape: {combined_df.shape}")
        
        # Define function to combine unique values in non-key columns
        def combine_unique(series):
            s = series.dropna()
            if s.empty:
                return ''
            else:
                return ', '.join(s.astype(str).unique())
        
        # Define function to aggregate filenames based on conflicts in the special column
        def aggregate_filenames(group):
            special_series = group[special_col].dropna()
            if special_series.empty:
                return ''  # All values are NaN, no conflict
            unique_values = special_series.unique()
            if len(unique_values) <= 1:
                return ''  # Only one unique value or none, no conflict
            else:
                # Collect filenames for the first occurrence of each unique value
                filenames = []
                for val in unique_values:
                    first_row = group[(group[special_col] == val) & group[special_col].notna()].iloc[0]
                    filenames.append(first_row['filename'])
                return ', '.join(filenames)
        
        # Set up aggregation dictionary
        agg_dict = {col: 'first' if col in key_columns else combine_unique for col in combined_df.columns}
        agg_dict['filename'] = aggregate_filenames  # Override with custom aggregation for 'filename'
        
        # Merge rows by grouping on key columns
        print(f"Merging rows based on columns: {', '.join(key_columns)}")
        merged_df = combined_df.groupby(key_columns, as_index=False, dropna=False).agg(agg_dict)
        print(f"Merged shape: {merged_df.shape}")
        
        # Write the merged DataFrame to the output file
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
    # Validate command-line arguments
    if len(sys.argv) != 10:
        print("Usage: python merge_sheets.py input1.xlsx input2.xlsx input3.xlsx input4.xlsx key_col1 key_col2 key_col3 special_col output.xlsx")
        sys.exit(1)
    
    # Parse command-line arguments
    input_files = sys.argv[1:5]
    key_columns = sys.argv[5:8]
    special_col = sys.argv[8]
    output_file = sys.argv[9]
    
    # Execute the merge function
    merge_excel_sheets(input_files, key_columns, special_col, output_file)
