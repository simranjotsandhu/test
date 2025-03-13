import pandas as pd
import sys

def merge_excel_sheets(input_files, key_columns, special_col, output_file):
    """
    Merge four Excel files based on user-specified key columns, combining conflicting values in other columns,
    and add a 'filename' column for conflicts in the special column. Exclude rows from a file if it has multiple
    values in the special column for the same key column values.
    
    Parameters:
    input_files (list): List of four input Excel file paths.
    key_columns (list): List of column names to use for merging (provided by user).
    special_col (str): The special column name to check for conflicts (provided by user).
    output_file (str): Path for the output Excel file.
    """
    try:
        # Step 1: Read files and filter out invalid rows
        dfs = []
        for file in input_files:
            print(f"Reading {file}")
            df = pd.read_excel(file)
            df['filename'] = file  # Add filename column to track source
            
            # Validate required columns
            missing_cols = [col for col in key_columns + [special_col] if col not in df.columns]
            if missing_cols:
                print(f"Error: File {file} is missing columns: {', '.join(missing_cols)}")
                sys.exit(1)
            
            # Check for multiple special column values for same key columns
            grouped = df.groupby(key_columns, dropna=False)[special_col].nunique(dropna=False)
            valid_keys = grouped[grouped <= 1].index  # Keep only groups with 1 or 0 unique values
            if len(valid_keys) < len(grouped):
                print(f"Warning: Excluding rows from {file} with multiple {special_col} values for same {', '.join(key_columns)}")
            df_filtered = df[df.set_index(key_columns).index.isin(valid_keys)].reset_index(drop=True)
            if not df_filtered.empty:
                dfs.append(df_filtered)
            else:
                print(f"Warning: No valid rows remain in {file} after filtering")
        
        if not dfs:
            print("Error: No valid data to merge after filtering all files")
            sys.exit(1)
        
        # Step 2: Concatenate filtered DataFrames
        print("Concatenating the sheets")
        combined_df = pd.concat(dfs, axis=0, ignore_index=True)
        print(f"Combined shape: {combined_df.shape}")
        
        # Step 3: Define function to combine unique values in non-key columns
        def combine_unique(series):
            s = series.dropna()
            if s.empty:
                return ''
            else:
                return ', '.join(s.astype(str).unique())
        
        # Step 4: Define function to aggregate filenames based on conflicts in the special column
        def aggregate_filenames(group):
            special_series = group[special_col].dropna()
            if special_series.empty:
                return ''
            unique_values = special_series.unique()
            if len(unique_values) <= 1:
                return ''
            else:
                filenames = []
                for val in unique_values:
                    first_row = group[(group[special_col] == val) & group[special_col].notna()].iloc[0]
                    filenames.append(first_row['filename'])
                return ', '.join(filenames)
        
        # Step 5: Set up aggregation dictionary
        agg_dict = {col: 'first' if col in key_columns else combine_unique for col in combined_df.columns}
        agg_dict['filename'] = aggregate_filenames
        
        # Step 6: Merge rows by grouping on key columns
        print(f"Merging rows based on columns: {', '.join(key_columns)}")
        merged_df = combined_df.groupby(key_columns, as_index=False, dropna=False).agg(agg_dict)
        print(f"Merged shape: {merged_df.shape}")
        
        # Step 7: Write the merged DataFrame to the output file
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
    if len(sys.argv) != 10:
        print("Usage: python merge_sheets.py input1.xlsx input2.xlsx input3.xlsx input4.xlsx key_col1 key_col2 key_col3 special_col output.xlsx")
        sys.exit(1)
    
    input_files = sys.argv[1:5]
    key_columns = sys.argv[5:8]
    special_col = sys.argv[8]
    output_file = sys.argv[9]
    
    merge_excel_sheets(input_files, key_columns, special_col, output_file)
