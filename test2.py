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
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Load dataset and assignment mappings
global news_data, user_to_rows, sets, set_to_users
news_data = []
user_to_rows = {}
sets = []
set_to_users = {}

# Load admin state from file
def load_admin_state():
    """Load the admin state from admin_state.json, initializing with defaults if not present or corrupted."""
    try:
        if os.path.exists(ADMIN_STATE_FILE):
            with open(ADMIN_STATE_FILE, "r") as f:
                return json.load(f)
    except json.JSONDecodeError:
        pass
    return {"logged_in": False, "excel_file": None, "account_ids_file": None, "num_sets": 1, "num_users_per_set": 1}

# Save admin state to file
def save_admin_state(state):
    """Save the admin state to admin_state.json."""
    with open(ADMIN_STATE_FILE, "w") as f:
        json.dump(state, f)

# Admin login function
def admin_login(username, password):
    """Handle admin login, updating visibility and component values based on authentication."""
    if username == "admin" and password == "adminpass":  # Replace with secure credentials in production
        state = load_admin_state()
        state["logged_in"] = True
        save_admin_state(state)
        return (
            gr.update(visible=False),  # Hide login_col
            gr.update(visible=True),   # Show upload_col
            gr.update(value=state.get("excel_file", "No file uploaded")),
            gr.update(value=state.get("account_ids_file", "No file uploaded")),
            gr.update(value=state.get("num_sets", 1)),
            gr.update(value=state.get("num_users_per_set", 1)),
            gr.update(value="Login successful!")
        )
    else:
        return (
            gr.update(visible=True),   # Keep login_col visible
            gr.update(visible=False),  # Keep upload_col hidden
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value=1),
            gr.update(value=1),
            gr.update(value="Incorrect credentials")
        )

# Admin logout function
def admin_logout():
    """Handle admin logout, resetting visibility and clearing component values."""
    state = load_admin_state()
    state["logged_in"] = False
    save_admin_state(state)
    return (
        gr.update(visible=True),   # Show login_col
        gr.update(visible=False),  # Hide upload_col
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=1),
        gr.update(value=1),
        gr.update(value="Logged out")
    )

# Admin reset function
def admin_reset():
    """Reset the admin state and remove uploaded files."""
    if os.path.exists(ADMIN_STATE_FILE):
        os.remove(ADMIN_STATE_FILE)
    for file in ["news_data.xlsx", "account_ids.txt"]:
        file_path = os.path.join(UPLOADS_DIR, file)
        if os.path.exists(file_path):
            os.remove(file_path)
    return (
        gr.update(visible=True),   # Show login_col
        gr.update(visible=False),  # Hide upload_col
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=1),
        gr.update(value=1),
        gr.update(value="State reset")
    )

# Admin upload function
def admin_upload(excel_file, account_ids_file, num_sets, num_users_per_set):
    """Handle file uploads, assign sets, and generate credentials."""
    global news_data, user_to_rows, sets, set_to_users
    state = load_admin_state()
    
    # Save new files if uploaded by copying them to the uploads directory
    if excel_file is not None:
        excel_path = os.path.join(UPLOADS_DIR, "news_data.xlsx")
        shutil.copy(excel_file, excel_path)
        state["excel_file"] = excel_path
    if account_ids_file is not None:
        account_ids_path = os.path.join(UPLOADS_DIR, "account_ids.txt")
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
            gr.update(value=state.get("account_ids_file", "No file uploaded"))
        )
    
    # Process the Excel file
    df = pd.read_excel(excel_file_path)
    if not {'URL', 'Company Name', 'Tag'}.issubset(df.columns):
        return (
            gr.update(value="**Error:** Excel file must contain 'URL', 'Company Name', and 'Tag'.", visible=True),
            None,
            None,
            gr.update(value=state.get("excel_file", "No file uploaded")),
            gr.update(value=state.get("account_ids_file", "No file uploaded"))
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
            gr.update(value=state.get("account_ids_file", "No file uploaded"))
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
        gr.update(value=state["account_ids_file"])
    )

# User authentication function
def authenticate(account_id, password):
    """Authenticate a user based on credentials file."""
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
    """Handle news tagging for authenticated users."""
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
    """Display a summary of tagged data."""
    if not os.path.exists(output_file):
        return "No data tagged yet."
    df = pd.read_csv(output_file)
    summary = df['Tag'].value_counts().to_dict()
    return "\n".join([f"{tag}: {count}" for tag, count in summary.items()])

# Main app
def main():
    """Launch the Gradio news tagging application."""
    parser = argparse.ArgumentParser(description="Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    args = parser.parse_args()

    state = load_admin_state()
    admin_logged_in = state["logged_in"]

    with gr.Blocks(theme=gr.themes.Ocean()) as app:
        gr.Markdown("# News Tagging Application")

        ### Upload File Tab
        with gr.Tab("Upload File"):
            with gr.Column(visible=not admin_logged_in) as login_col:
                admin_username = gr.Textbox(label="Admin Username")
                admin_password = gr.Textbox(label="Admin Password", type="password")
                admin_login_btn = gr.Button("Login")
                admin_auth_status = gr.Markdown()

            with gr.Column(visible=admin_logged_in) as upload_col:
                current_excel_label = gr.Textbox(
                    label="Current Excel File",
                    value=state.get("excel_file", "No file uploaded"),
                    interactive=False
                )
                current_account_ids_label = gr.Textbox(
                    label="Current Account IDs File",
                    value=state.get("account_ids_file", "No file uploaded"),
                    interactive=False
                )
                excel_file = gr.File(label="Excel File (.xlsx)", type="filepath")
                account_ids_file = gr.File(label="Account IDs (.txt)", type="filepath")
                num_sets_input = gr.Number(
                    label="Number of Sets",
                    value=state.get("num_sets", 1),
                    precision=0
                )
                num_users_per_set_input = gr.Number(
                    label="Number of Users per Set",
                    value=state.get("num_users_per_set", 1),
                    precision=0
                )
                upload_btn = gr.Button("Upload", variant="primary")
                logout_btn = gr.Button("Logout", variant="secondary")
                reset_btn = gr.Button("Reset", variant="secondary")
                upload_status = gr.Markdown()
                credentials_table = gr.DataFrame()
                full_credentials = gr.State()
                show_passwords = gr.Checkbox(label="Show Passwords", value=False)

            # Event handlers for Upload File tab
            admin_login_btn.click(
                fn=admin_login,
                inputs=[admin_username, admin_password],
                outputs=[login_col, upload_col, current_excel_label, current_account_ids_label, num_sets_input, num_users_per_set_input, admin_auth_status]
            )

            logout_btn.click(
                fn=admin_logout,
                outputs=[login_col, upload_col, current_excel_label, current_account_ids_label, num_sets_input, num_users_per_set_input, admin_auth_status]
            )

            reset_btn.click(
                fn=admin_reset,
                outputs=[login_col, upload_col, current_excel_label, current_account_ids_label, num_sets_input, num_users_per_set_input, admin_auth_status]
            )

            upload_btn.click(
                fn=admin_upload,
                inputs=[excel_file, account_ids_file, num_sets_input, num_users_per_set_input],
                outputs=[upload_status, credentials_table, full_credentials, current_excel_label, current_account_ids_label]
            ).then(
                lambda hidden: gr.update(value=hidden),
                inputs=[credentials_table],
                outputs=[credentials_table]
            )

            show_passwords.change(
                fn=lambda show, hidden, full: full if show else hidden,
                inputs=[show_passwords, credentials_table, full_credentials],
                outputs=[credentials_table]
            )

        ### Tag News Tab
        with gr.Tab("Tag News"):
            account_id_input = gr.Textbox(label="Account ID")
            password_input = gr.Textbox(label="Password", type="password")
            tag_input = gr.Textbox(label="Tag")
            submit_tag_btn = gr.Button("Submit Tag")
            tag_status = gr.Markdown()
            tagged_data = gr.DataFrame()
            submit_tag_btn.click(
                fn=tag_news,
                inputs=[account_id_input, password_input, tag_input],
                outputs=[tag_status, tagged_data]
            )

        ### Summary Tab
        with gr.Tab("Summary"):
            summary_btn = gr.Button("View Summary")
            summary_output = gr.Textbox(label="Tag Summary")
            summary_btn.click(
                fn=view_summary,
                outputs=[summary_output]
            )

    app.launch(share=args.share, server_port=args.port)

if __name__ == "__main__":
    main()
