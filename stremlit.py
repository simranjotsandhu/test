import argparse
import gradio as gr
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from readability import Document

# Global variable to store tagging results
output_file = "tagged_results.csv"
admin_password = "x"  # Change this to a secure password

# Load the dataset globally to maintain state
news_data = []

def upload_excel(file, password):
    """Handles file upload and validates the format, protected by a password."""
    global news_data
    if password != admin_password:
        return "**Error:** Unauthorized - Incorrect password.", "", "", -1
    if file is None:
        return "**Error:** Please upload an Excel file.", "", "", -1
    df = pd.read_excel(file.name)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return "**Error:** The Excel file must contain 'URL', 'Company Name', and 'Tag' columns.", "", "", -1
    df.to_csv(output_file, index=False)
    news_data = df.to_dict(orient='records')  # Store the dataset as a list of dictionaries
    if news_data:
        return "**File uploaded and saved successfully!**", f"{news_data[0]['URL']}", news_data[0]['Company Name'], 0
    else:
        return "**File uploaded but contains no valid records.**", "", "", -1

def fetch_news_content(url):
    """Fetches the news content from the given URL using readability-lxml."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        paragraphs = soup.find_all('p')
        news_text = '\n'.join([para.get_text() for para in paragraphs[:5]])  # Get first 5 paragraphs
        return news_text if news_text.strip() else "**Could not extract content. Visit the URL to read more.**"
    except Exception as e:
        return f"**Failed to load preview: {str(e)}**\nPlease visit the URL manually."

def tag_news(index, tag):
    """Handles tagging of news items, updates the correct row in the dataset."""
    global news_data
    if not os.path.exists(output_file) or not news_data or index == -1:
        return "**All records have been tagged.**", "", "", -1
    
    # Update the tag for the corresponding row
    if 0 <= index < len(news_data):
        news_data[index]['Tag'] = tag
        pd.DataFrame(news_data).to_csv(output_file, index=False)
    
    # Move to the next item
    if index + 1 < len(news_data):
        news_url = news_data[index + 1]['URL']
        preview_text = fetch_news_content(news_url)
        return news_url, news_data[index + 1]['Company Name'], preview_text, index + 1
    else:
        return "**All records have been tagged.**", "", "", -1

def show_summary():
    """Displays a summary of Yes and No counts using Gradio components."""
    if not os.path.exists(output_file):
        return "**No tagging data found.**"
    df = pd.read_csv(output_file)
    total = len(df)
    yes_count = df[df['Tag'] == 'Yes'].shape[0]
    no_count = df[df['Tag'] == 'No'].shape[0]
    
    return gr.DataFrame(pd.DataFrame({"Tag": ["Yes", "No"], "Count": [yes_count, no_count]}))

def main():
    parser = argparse.ArgumentParser(description="Run the Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the app on (default: 7860)")
    parser.add_argument("--share", action="store_true", help="Generate a public Gradio link")
    args = parser.parse_args()
    
    with gr.Blocks(theme=gr.themes.Ocean()) as app:
        gr.Markdown("""# News Tagging Application\n### Upload, Tag, and Analyze News Data""")
        
        with gr.Tab("Upload File"):
            gr.Markdown("### **Upload an Excel File (Admin Only)**")
            password_input = gr.Textbox(label="Admin Password", type="password")
            upload_component = gr.File(label="Upload Excel File", file_types=[".xlsx"])
            upload_button = gr.Button("Upload", variant="primary")
            upload_output = gr.Markdown()
            first_url = gr.Markdown()
            first_company = gr.Textbox(label="First Company Name", interactive=False)
            first_index = gr.Number(label="Start Index", interactive=False)
            upload_button.click(upload_excel, inputs=[upload_component, password_input], outputs=[upload_output, first_url, first_company, first_index])
        
        with gr.Tab("Tag News"):
            gr.Markdown("### **Tag News URLs**")
            url_display = gr.Markdown()
            company_display = gr.Textbox(label="Company Name", interactive=False)
            news_preview = gr.Textbox(label="News Preview", interactive=False)
            index_input = gr.Number(label="Index", value=0, interactive=False)
            tag_input = gr.Radio(choices=["Yes", "No"], label="Is this news related to the company?")
            tag_button = gr.Button("Save Tag", variant="primary", interactive=False)
            tag_input.change(fn=lambda tag: gr.update(interactive=True) if tag else gr.update(interactive=False), inputs=[tag_input], outputs=[tag_button])
            tag_button.click(tag_news, inputs=[index_input, tag_input], outputs=[url_display, company_display, news_preview, index_input])
            upload_button.click(fn=lambda: (f"{news_data[0]['URL']}", news_data[0]['Company Name'], fetch_news_content(news_data[0]['URL']), 0) if news_data else ("", "", "", -1), inputs=[], outputs=[url_display, company_display, news_preview, index_input])
        
        with gr.Tab("Summary"):
            gr.Markdown("### **Tagging Summary**")
            summary_button = gr.Button("Show Summary", variant="primary")
            summary_output = gr.DataFrame()
            summary_button.click(show_summary, inputs=[], outputs=[summary_output])
    
    app.launch(share=True, server_port=args.port)

if __name__ == "__main__":
    main()
