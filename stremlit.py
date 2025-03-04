import argparse
import gradio as gr
import pandas as pd
import os

# Global variable to store tagging results
output_file = "tagged_results.csv"
admin_password = "securepassword"  # Change this to a secure password

# Load the dataset globally to maintain state
news_data = []

def upload_excel(file, password):
    """Handles file upload and validates the format, protected by a password."""
    global news_data
    if password != admin_password:
        return "Unauthorized: Incorrect password.", "", "", -1
    if file is None:
        return "Please upload an Excel file.", "", "", -1
    df = pd.read_excel(file.name)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return "The Excel file must contain 'URL', 'Company Name', and 'Tag' columns.", "", "", -1
    df.to_csv(output_file, index=False)
    news_data = df.to_dict(orient='records')  # Store the dataset as a list of dictionaries
    if news_data:
        return "File uploaded and saved successfully.", news_data[0]['URL'], news_data[0]['Company Name'], 0
    else:
        return "File uploaded but contains no valid records.", "", "", -1

def tag_news(index, tag):
    """Handles tagging of news items, updates the correct row in the dataset."""
    global news_data
    if not os.path.exists(output_file) or not news_data:
        return "No uploaded data found. Please upload a file first.", "", "", -1
    
    # Update the tag for the corresponding row
    if 0 <= index < len(news_data):
        news_data[index]['Tag'] = tag
        pd.DataFrame(news_data).to_csv(output_file, index=False)
    
    # Move to the next item
    if index + 1 < len(news_data):
        return news_data[index + 1]['URL'], news_data[index + 1]['Company Name'], index + 1
    else:
        return "No more records to tag.", "", "", -1

def show_summary():
    """Displays summary of tagging results."""
    if not os.path.exists(output_file):
        return "No tagging data found."
    df = pd.read_csv(output_file)
    total = len(df)
    yes_count = len(df[df['Tag'] == 'Yes'])
    no_count = len(df[df['Tag'] == 'No'])
    return f"Total URLs: {total}\nRelated to Company (Yes): {yes_count}\nNot Related to Company (No): {no_count}"

def main():
    parser = argparse.ArgumentParser(description="Run the Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the app on (default: 7860)")
    parser.add_argument("--share", action="store_true", help="Generate a public Gradio link")
    args = parser.parse_args()
    
    with gr.Blocks() as app:
        with gr.Tab("Upload File"):
            gr.Markdown("## Upload Excel File (Admin Only)")
            password_input = gr.Textbox(label="Admin Password", type="password")
            upload_component = gr.File(label="Upload Excel File", file_types=[".xlsx"])
            with gr.Row():
                upload_button = gr.Button("Upload")
                upload_output = gr.Textbox(label="Upload Status", interactive=False)
            first_url = gr.Textbox(label="First News URL", interactive=False)
            first_company = gr.Textbox(label="First Company Name", interactive=False)
            first_index = gr.Number(label="Start Index", interactive=False)
            upload_button.click(upload_excel, inputs=[upload_component, password_input], outputs=[upload_output, first_url, first_company, first_index])
        
        with gr.Tab("Tag News"):
            gr.Markdown("## Tag News URLs")
            url_display = gr.Textbox(label="News URL", interactive=False)
            company_display = gr.Textbox(label="Company Name", interactive=False)
            index_input = gr.Number(label="Index", value=0, interactive=False)
            tag_input = gr.Radio(choices=["Yes", "No"], label="Is this news related to the company?")
            tag_button = gr.Button("Save Tag")
            tag_button.click(tag_news, inputs=[index_input, tag_input], outputs=[url_display, company_display, index_input])
            upload_button.click(fn=lambda: (news_data[0]['URL'], news_data[0]['Company Name'], 0) if news_data else ("", "", -1), inputs=[], outputs=[url_display, company_display, index_input])
        
        with gr.Tab("Summary"):
            gr.Markdown("## Tagging Summary")
            summary_button = gr.Button("Show Summary")
            summary_output = gr.Textbox(label="Summary")
            summary_button.click(show_summary, inputs=[], outputs=[summary_output])
    
    app.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
