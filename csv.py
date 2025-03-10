import pandas as pd
import unicodedata

# Define the common prefix for link generation (modify as needed)
common_prefix = "https://example.com/files/"

# Read the Excel file (replace 'input.xlsx' with your actual file name)
df = pd.read_excel('input.xlsx')

# Convert 'Date' column to datetime, coercing invalid dates to NaT
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Generate the suffix: ArticleID_Company_Date
df['suffix'] = (
    df['ArticleID'].astype(str) + '_' +
    df['Company'].str.replace(' ', '_') + '_' +
    df['Date'].dt.strftime('%Y-%m-%d')
)

# Clean the suffix: keep only letters, numbers, underscores, and hyphens
df['clean_suffix'] = df['suffix'].str.lower().str.replace(r'[^a-z0-9_-]', '', regex=True)

# Create the link: use URL if non-empty; otherwise, use common_prefix + clean_suffix
df['link'] = df['URL'].where(
    df['URL'].notna() & (df['URL'].str.strip() != ''),
    common_prefix + df['clean_suffix']
)

# Function to clean text by removing control characters and specified characters
def clean_text(text, remove_chars):
    # Remove control characters (Unicode category 'C')
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
    # Remove specified characters (e.g., commas, backticks)
    text = text.translate(str.maketrans('', '', remove_chars))
    return text

# Create the CSV DataFrame
csv_df = pd.DataFrame({
    # Index: 1 to number of rows
    'Index': range(1, len(df) + 1),
    
    # Title: Clean (remove commas and control chars), take first 50 chars, append "..."
    'Title': df['Title'].fillna('').apply(lambda x: clean_text(x, ',')).str[:50] + "...",
    
    # Body: Clean (remove backticks, commas, control chars), take first 50 chars, append "...", then "`" and link
    'Body': (df['Body'].fillna('').apply(lambda x: clean_text(x, '`,')).str[:50] + "...") + "`" + df['link'],
    
    # Date: Format as YYYY-MM-DD
    'Date': df['Date'].dt.strftime('%Y-%m-%d'),
    
    # HiddenMarker: Copy as is
    'HiddenMarker': df['hiddenMarker']
})

# Write to CSV with UTF-8 encoding
csv_df.to_csv('output.csv', index=False, encoding='utf-8')

print("CSV file 'output.csv' has been generated successfully.")
