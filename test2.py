import argparse
import gradio as gr
import pandas as pd
import os
import secrets
import random
import json
import shutil

# Global variables
output_file = "tagged_results.csv"
admin_password = "x"  # Change to a secure password in production
credentials_file = "user_credentials.csv"
progress_file = "user_progress.csv"
ADMIN_STATE_FILE = "admin_state.json"

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Load dataset and assignment mappings
global news_data, user_to_rows, sets, set_to_users
news_data = []
user_to_rows = {}
sets = []
set_to_users = {}

# Load admin state from file
def load_admin_state():
    if os.path.exists(ADMIN_STATE_FILE):
        with open(ADMIN_STATE_FILE, "r") as f:
            return json.load(f)
    return {"logged_in": False, "excel_file": None, "account_ids_file": None, "num_sets": 1, "num_users_per_set": 1}

# Save admin state to file
def save_admin_state(state):
    with open(ADMIN_STATE_FILE, "w") as f:
        json.dump(state, f)

# Admin login function
def admin_login(username, password):
    if username == "admin" and password == "adminpass":
        state = load_admin_state()
        state["logged_in"] = True
        save_admin_state(state)
        return (
            gr.update(visible=False),  # admin_username
            gr.update(visible=False),  # admin_password
            gr.update(visible=False),  # admin_login_btn
            gr.update(value=state.get("excel_file", "No file uploaded"), visible=True),  # current_excel_label
            gr.update(value=state.get("account_ids_file", "No file uploaded"), visible=True),  # current_account_ids_label
            gr.update(value=state.get("num_sets", 1), visible=True),  # num_sets_input
            gr.update(value=state.get("num_users_per_set", 1), visible=True),  # num_users_per_set_input
            gr.update(visible=True),  # excel_file
            gr.update(visible=True),  # account_ids_file
            gr.update(visible=True),  # upload_btn
            gr.update(visible=True),  # logout_btn
            gr.update(visible=True),  # reset_btn
            gr.update(value="Login successful!", visible=True)  # admin_auth_status
        )
    else:
        return (
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(value="Incorrect credentials", visible=True)
        )

# Admin logout function
def admin_logout():
    state = load_admin_state()
    state["logged_in"] = False
    save_admin_state(state)
    return (
        gr.update(visible=True),  # admin_username
        gr.update(value="", visible=True),  # admin_password
        gr.update(visible=True),  # admin_login_btn
        gr.update(visible=False),  # current_excel_label
        gr.update(visible=False),  # current_account_ids_label
        gr.update(visible=False),  # num_sets_input
        gr.update(visible=False),  # num_users_per_set_input
        gr.update(visible=False),  # excel_file
        gr.update(visible=False),  # account_ids_file
        gr.update(visible=False),  # upload_btn
        gr.update(visible=False),  # logout_btn
        gr.update(visible=False),  # reset_btn
        gr.update(value="Logged out", visible=True)  # admin_auth_status
    )

# Admin reset function
def admin_reset():
    if os.path.exists(ADMIN_STATE_FILE):
        os.remove(ADMIN_STATE_FILE)
    for file in ["news_data.xlsx", "account_ids.txt"]:
        file_path = os.path.join("uploads", file)
        if os.path.exists(file_path):
            os.remove(file_path)
    return (
        gr.update(visible=True),  # admin_username
        gr.update(value="", visible=True),  # admin_password
        gr.update(visible=True),  # admin_login_btn
        gr.update(visible=False),  # current_excel_label
        gr.update(visible=False),  # current_account_ids_label
        gr.update(value=1, visible=False),  # num_sets_input
        gr.update(value=1, visible=False),  # num_users_per_set_input
        gr.update(visible=False),  # excel_file
        gr.update(visible=False),  # account_ids_file
        gr.update(visible=False),  # upload_btn
        gr.update(visible=False),  # logout_btn
        gr.update(visible=False),  # reset_btn
        gr.update(value="State reset", visible=True)  # admin_auth_status
    )

# Admin upload function (updated to handle file paths)
def admin_upload(excel_file, account_ids_file, num_sets, num_users_per_set):
    global news_data, user_to_rows, sets, set_to_users
    state = load_admin_state()
    
    # Save new files if uploaded by copying them to the uploads directory
    if excel_file is not None:
        excel_path = "uploads/news_data.xlsx"
        shutil.copy(excel_file, excel_path)
        state["excel_file"] = excel_path
    if account_ids_file is not None:
        account_ids_path = "uploads/account_ids.txt"
        shutil.copy(account_ids_file, account_ids_path)
        state["account_ids_file"] = account_ids_path
    
    # Update settings
    state["num_sets"] = int(num_sets)
    state["num_users_per_set"] = int(num_users_per_set)
    save_admin_state(state)
    
    # Use files from state for processing
    excel_file_path = state.get("excel_file")
    account_ids_file_path = state.get("account_ids_file")
    if not excel_file_path or not os.path.exists(excel_file_path) or not account_ids_file_path or not os.path.exists(account_ids_file_path):
        return (
            gr.update(value="**Error:** Files not uploaded.", visible=True),
            None,
            None,
            gr.update(value=state.get("excel_file", "No file uploaded")),
            gr.update(value=state.get("account_ids_file", "No file uploaded")),
            gr.update(visible=True),
            gr.update(visible=True)
        )
    
    # Original upload logic
    df = pd.read_excel(excel_file_path)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return (
            gr.update(value="**Error:** Excel file must contain 'URL', 'Company Name', and 'Tag'.", visible=True),
            None,
            None,
            gr.update(value=state.get("excel_file", "No file uploaded")),
            gr.update(value=state.get("account_ids_file", "No file uploaded")),
            gr.update(visible=True),
            gr.update(visible=True)
        )
    
    news_data = [{'URL': row['URL'], 'Company Name': row['Company Name'], 'Tag': row.get('Tag', '')} for _, row in df.iterrows()]
    N = len(df)
    with open(account_ids_file_path, "r") as f:
        account_ids = f.read().splitlines()
    M = len(account_ids)
    
    num_sets = int(num_sets)
    num_users_per_set = int(num_users_per_set)
    if num_sets <= 0 or num_users_per_set <= 0:
        return (
            gr.update(value="**Error:** Number of sets and users per set must be positive.", visible=True),
            None,
            None,
            gr.update(value=state.get("excel_file", "No file uploaded")),
            gr.update(value=state.get("account_ids_file", "No file uploaded")),
            gr.update(visible=True),
            gr.update(visible=True)
        )
    
    # Divide rows into sets
    indices = list(range(N))
    sets = [indices[i::num_sets] for i in range(num_sets)]
    
    # Distribute users evenly across sets
    base_users_per_set = M // num_sets
    extra_users = M % num_sets
    set_to_users = {}
    shuffled_users = account_ids.copy()
    random.shuffle(shuffled_users)
    user_idx = 0
    for set_idx in range(num_sets):
        num_users = base_users_per_set + (1 if set_idx < extra_users else 0)
        assigned_users = shuffled_users[user_idx:user_idx + num_users]
        set_to_users[set_idx] = assigned_users
        user_idx += num_users
    
    # Compute user to row mapping
    user_to_sets = {account_id: [] for account_id in account_ids}
    for set_idx, users in set_to_users.items():
        for user in users:
            user_to_sets[user].append(set_idx)
    user_to_rows = {}
    for account_id in account_ids:
        assigned_sets = user_to_sets[account_id]
        rows = sum([sets[set_idx] for set_idx in assigned_sets], [])
        user_to_rows[account_id] = sorted(rows)
    
    # Generate credentials
    passwords = [secrets.token_urlsafe(8) for _ in account_ids]
    credentials_hidden = pd.DataFrame({
        'account_id': account_ids,
        'password': ['[Hidden]' for _ in account_ids]
    })
    credentials_full = pd.DataFrame({
        'account_id': account_ids,
        'password': passwords
    })
    credentials_full.to_csv(credentials_file, index=False)
    df.to_csv(output_file, index=False)
    
    # Initialize user progress
    progress_df = pd.DataFrame({'account_id': account_ids, 'current_idx': [0] * len(account_ids)})
    progress_df.to_csv(progress_file, index=False)
    
    return (
        gr.update(value="**Files uploaded, sets assigned evenly, and credentials created successfully!**", visible=True),
        credentials_hidden,
        credentials_full,
        gr.update(value=state["excel_file"]),
        gr.update(value=state["account_ids_file"]),
        gr.update(visible=True),
        gr.update(visible=True)
    )

# User authentication function
def authenticate(account_id, password):
    if not os.path.exists(credentials_file):
        return False, "No credentials found. Please upload files first."
    credentials = pd.read_csv(credentials_file)
    if account_id in credentials['account_id'].values:
        stored_password = credentials[credentials['account_id'] == account_id]['password'].values[0]
        if stored_password == password:
            return True, "Login successful!"
        return False, "Incorrect password."
    return False, "Account ID not found."

# Tag news function
def tag_news(account_id, password, tag):
    success, message = authenticate(account_id, password)
    if not success:
        return message, None
    if not os.path.exists(progress_file) or not os.path.exists(output_file):
        return "Files not uploaded yet.", None
    
    progress_df = pd.read_csv(progress_file)
    tagged_df = pd.read_csv(output_file)
    if account_id not in user_to_rows:
        return "No rows assigned to this user.", None
    
    current_idx = progress_df[progress_df['account_id'] == account_id]['current_idx'].values[0]
    assigned_rows = user_to_rows[account_id]
    
    if current_idx >= len(assigned_rows):
        return "All assigned rows tagged!", tagged_df
    
    row_idx = assigned_rows[current_idx]
    tagged_df.at[row_idx, 'Tag'] = tag
    tagged_df.to_csv(output_file, index=False)
    
    progress_df.loc[progress_df['account_id'] == account_id, 'current_idx'] = current_idx + 1
    progress_df.to_csv(progress_file, index=False)
    
    next_idx = current_idx + 1
    if next_idx < len(assigned_rows):
        next_row = news_data[assigned_rows[next_idx]]
        return f"Tagged row {current_idx + 1}/{len(assigned_rows)}. Next: {next_row['Company Name']} - {next_row['URL']}", tagged_df
    return "All assigned rows tagged!", tagged_df

# Summary function
def view_summary():
    if not os.path.exists(output_file):
        return "No data tagged yet."
    df = pd.read_csv(output_file)
    summary = df['Tag'].value_counts().to_dict()
    return "\n".join([f"{tag}: {count}" for tag, count in summary.items()])

# Main app
def main():
    parser = argparse.ArgumentParser(description="Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    state = load_admin_state()
    admin_logged_in = state["logged_in"]

    with gr.Blocks(theme=gr.themes.Ocean()) as app:
        gr.Markdown("# News Tagging Application")

        with gr.Tab("Upload File"):
            admin_auth_status = gr.Markdown(value="", visible=True)
            admin_username = gr.Textbox(label="Admin Username", visible=not admin_logged_in)
            admin_password = gr.Textbox(label="Admin Password", type="password", visible=not admin_logged_in)
            admin_login_btn = gr.Button("Login", visible=not admin_logged_in)
            
            current_excel_label = gr.Textbox(label="Current Excel File", value=state.get("excel_file", "No file uploaded"), interactive=False, visible=admin_logged_in)
            current_account_ids_label = gr.Textbox(label="Current Account IDs File", value=state.get("account_ids_file", "No file uploaded"), interactive=False, visible=admin_logged_in)
            excel_file = gr.File(label="Excel File (.xlsx)", type="filepath", visible=admin_logged_in)
            account_ids_file = gr.File(label="Upload Account IDs (.txt)", type="filepath", visible=admin_logged_in)
            num_sets_input = gr.Number(label="Number of Sets", value=state.get("num_sets", 1), precision=0, visible=admin_logged_in)
            num_users_per_set_input = gr.Number(label="Number of Users per Set", value=state.get("num_users_per_set", 1), precision=0, visible=admin_logged_in)
            upload_btn = gr.Button("Upload", variant="primary", visible=admin_logged_in)
            logout_btn = gr.Button("Logout", variant="secondary", visible=admin_logged_in)
            reset_btn = gr.Button("Reset", variant="secondary", visible=admin_logged_in)
            upload_status = gr.Markdown(visible=admin_logged_in)
            credentials_table = gr.DataFrame(visible=admin_logged_in)
            full_credentials = gr.State(None)
            show_passwords = gr.Checkbox(label="Show Passwords", value=False, visible=admin_logged_in)

            admin_login_btn.click(
                admin_login,
                inputs=[admin_username, admin_password],
                outputs=[
                    admin_username, admin_password, admin_login_btn,
                    current_excel_label, current_account_ids_label,
                    num_sets_input, num_users_per_set_input,
                    excel_file, account_ids_file, upload_btn, logout_btn, reset_btn,
                    admin_auth_status
                ]
            )

            logout_btn.click(
                admin_logout,
                outputs=[
                    admin_username, admin_password, admin_login_btn,
                    current_excel_label, current_account_ids_label,
                    num_sets_input, num_users_per_set_input,
                    excel_file, account_ids_file, upload_btn, logout_btn, reset_btn,
                    admin_auth_status
                ]
            )

            reset_btn.click(
                admin_reset,
                outputs=[
                    admin_username, admin_password, admin_login_btn,
                    current_excel_label, current_account_ids_label,
                    num_sets_input, num_users_per_set_input,
                    excel_file, account_ids_file, upload_btn, logout_btn, reset_btn,
                    admin_auth_status
                ]
            )

            upload_btn.click(
                admin_upload,
                inputs=[excel_file, account_ids_file, num_sets_input, num_users_per_set_input],
                outputs=[upload_status, credentials_table, full_credentials,
                         current_excel_label, current_account_ids_label,
                         credentials_table, show_passwords]
            ).then(
                lambda df: df,
                inputs=[credentials_table],
                outputs=[full_credentials]
            )

            show_passwords.change(
                lambda show, hidden, full: full if show else hidden,
                inputs=[show_passwords, credentials_table, full_credentials],
                outputs=[credentials_table]
            )

        with gr.Tab("Tag News"):
            account_id_input = gr.Textbox(label="Account ID")
            password_input = gr.Textbox(label="Password", type="password")
            tag_input = gr.Textbox(label="Tag")
            submit_tag_btn = gr.Button("Submit Tag")
            tag_status = gr.Markdown()
            tagged_data = gr.DataFrame()
            submit_tag_btn.click(tag_news, inputs=[account_id_input, password_input, tag_input], outputs=[tag_status, tagged_data])

        with gr.Tab("Summary"):
            summary_btn = gr.Button("View Summary")
            summary_output = gr.Textbox(label="Tag Summary")
            summary_btn.click(view_summary, outputs=[summary_output])

    app.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
