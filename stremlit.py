import argparse
import gradio as gr
import pandas as pd
import os
import secrets

# Global variables
output_file = "tagged_results.csv"
admin_password = "x"  # Change this to a secure password
credentials_file = "user_credentials.csv"

# Load dataset
news_data = []

# Admin: Upload Excel and Account IDs

def upload_excel(file, account_ids_file, password):
    global news_data
    if password != admin_password:
        return "**Error:** Unauthorized - Incorrect password.", "", "", "", -1, pd.DataFrame()
    if file is None or account_ids_file is None:
        return "**Error:** Please upload both Excel and Account IDs files.", "", "", "", -1, pd.DataFrame()
    df = pd.read_excel(file.name)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return "**Error:** Excel file must contain 'URL', 'Company Name', and 'Tag'.", "", "", "", -1, pd.DataFrame()
    df.to_csv(output_file, index=False)
    news_data = df.to_dict(orient='records')

    # Generate passwords for account_ids
    with open(account_ids_file.name, 'r') as f:
        account_ids = [line.strip() for line in f if line.strip()]

    credentials = pd.DataFrame({
        'account_id': account_ids,
        'password': [secrets.token_urlsafe(8) for _ in account_ids]
    })
    credentials.to_csv(credentials_file, index=False)

    if news_data:
        news_url = news_data[0]['URL']
        company_name = news_data[0]['Company Name']
        embed_code = f'<iframe src="{news_url}" width="100%" height="500px"></iframe>'
        return "**Files uploaded successfully!**", news_url, company_name, embed_code, 0, credentials
    else:
        return "**File uploaded but contains no valid records.**", "", "", "", -1, pd.DataFrame()

# User authentication

def authenticate(account_id, password):
    if not os.path.exists(credentials_file):
        return False
    credentials = pd.read_csv(credentials_file)
    match = credentials[(credentials['account_id'] == account_id) & (credentials['password'] == password)]
    return not match.empty

# Tagging function for users

def tag_news(account_id, password, index, tag):
    global news_data
    if not authenticate(account_id, password):
        return "**Authentication failed.**", "", "", -1
    if index == -1 or not news_data:
        return "**All records tagged.**", "", "", -1
    if 0 <= index < len(news_data):
        news_data[index]['Tag'] = tag
        pd.DataFrame(news_data).to_csv(output_file, index=False)
    if index + 1 < len(news_data):
        next_url = news_data[index + 1]['URL']
        embed_code = f'<iframe src="{next_url}" width="100%" height="500px"></iframe>'
        return next_url, news_data[index + 1]['Company Name'], embed_code, index + 1
    else:
        return "**All records tagged.**", "", "", -1

# Summary for admin

def show_summary(password):
    if password != admin_password:
        return gr.update(visible=False)
    if not os.path.exists(output_file):
        return gr.update(value=pd.DataFrame({"Error": ["No data found."]}), visible=True)
    df = pd.read_csv(output_file)
    yes_count = df[df['Tag'] == 'Yes'].shape[0]
    no_count = df[df['Tag'] == 'No'].shape[0]
    return gr.update(value=pd.DataFrame({"Tag": ["Yes", "No"], "Count": [yes_count, no_count]}), visible=True)

# Main App

def main():
    parser = argparse.ArgumentParser(description="Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    with gr.Blocks(theme=gr.themes.Ocean()) as app:
        gr.Markdown("# News Tagging Application")

        with gr.Tab("Upload File"):
            admin_pwd = gr.Textbox(label="Admin Password", type="password")
            excel_file = gr.File(label="Upload Excel File (.xlsx)")
            account_ids_file = gr.File(label="Upload Account IDs (.txt)")
            upload_btn = gr.Button("Upload")
            upload_status = gr.Markdown()
            credentials_table = gr.DataFrame()

        with gr.Tab("Tag News"):
            user_id = gr.Textbox(label="Account ID")
            user_pwd = gr.Textbox(label="User Password", type="password")
            url_display = gr.Markdown()
            company_display = gr.Textbox(label="Company", interactive=False)
            preview = gr.HTML()
            idx_input = gr.Number(label="Index", value=0, interactive=False)
            tag_input = gr.Radio(["Yes", "No"], label="Related?")
            tag_btn = gr.Button("Submit")

        with gr.Tab("Summary"):
            summary_pwd = gr.Textbox(label="Admin Password", type="password")
            summary_btn = gr.Button("Show Summary")
            summary_output = gr.DataFrame(visible=False)

        upload_btn.click(upload_excel, [excel_file, account_ids_file, admin_pwd], [upload_status, url_display, company_display, preview, idx_input, credentials_table])
        tag_btn.click(tag_news, [user_id, user_pwd, idx_input, tag_input], [url_display, company_display, preview, idx_input])
        summary_btn.click(show_summary, [summary_pwd], summary_output)

    app.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
