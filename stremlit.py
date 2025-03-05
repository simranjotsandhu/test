import argparse
import gradio as gr
import pandas as pd
import os
import requests
import json

# Global variable to store tagging results
output_file = "tagged_results.csv"
admin_password = "x"  # Change this to a secure password
user_passwords_file = "user_passwords.json"

def upload_excel(file, password, num_sets, num_users_per_set):
    """Handles file upload and validates the format, protected by a password."""
    if password != admin_password:
        return "**Error:** Unauthorized - Incorrect password.", "", "", -1
    if file is None:
        return "**Error:** Please upload an Excel file.", "", "", -1
    df = pd.read_excel(file.name)
    num_records = len(df)
    if num_sets > num_records:
        return "**Error:** Number of sets exceeds available records.", "", "", -1
    set_size = num_records // num_sets
    user_passwords = {}
    
    for i in range(num_sets):
        start_idx = i * set_size
        end_idx = (i + 1) * set_size if i != num_sets - 1 else num_records
        subset = df.iloc[start_idx:end_idx]
        subset_filename = f"tagging_set_{i+1}.csv"
        subset.to_csv(subset_filename, index=False)
        set_password = f"set_pass_{i+1}"  # Generate passwords
        user_passwords[set_password] = {"file": subset_filename, "users": num_users_per_set, "completed": 0}
    
    with open(user_passwords_file, "w") as f:
        json.dump(user_passwords, f)
    
    return "**File uploaded and sets created successfully!**", "", "", -1

def authenticate_user(password):
    """Checks if the user-provided password is valid and returns the assigned dataset."""
    if not os.path.exists(user_passwords_file):
        return "**Error:** No user data found.", ""
    with open(user_passwords_file, "r") as f:
        user_passwords = json.load(f)
    if password in user_passwords:
        return "**Login Successful!**", user_passwords[password]["file"]
    else:
        return "**Error:** Invalid password.", ""

def tag_news(index, tag, password):
    """Handles tagging of news items for users assigned to a subset."""
    if not os.path.exists(user_passwords_file):
        return "**Error:** No user data found.", "", "", "", -1
    with open(user_passwords_file, "r") as f:
        user_passwords = json.load(f)
    if password not in user_passwords:
        return "**Error:** Unauthorized - Invalid password.", "", "", "", -1
    
    dataset_file = user_passwords[password]["file"]
    df = pd.read_csv(dataset_file)
    if index == -1 or index >= len(df):
        return "**All records have been tagged.**", "", "", "", -1
    
    df.loc[index, "Tag"] = tag
    df.to_csv(dataset_file, index=False)
    
    if index + 1 < len(df):
        return df.iloc[index + 1]["URL"], df.iloc[index + 1]["Company Name"], f'<iframe src="{df.iloc[index + 1]["URL"]}" width="100%" height="500px"></iframe>', index + 1
    else:
        user_passwords[password]["completed"] += 1
        with open(user_passwords_file, "w") as f:
            json.dump(user_passwords, f)
        return "**All records have been tagged.**", "", "", "", -1

def check_summary_availability():
    """Checks if all users have completed tagging before allowing summary view."""
    if not os.path.exists(user_passwords_file):
        return "**Error:** No user data found.**"
    with open(user_passwords_file, "r") as f:
        user_passwords = json.load(f)
    incomplete_users = sum(user["users"] - user["completed"] for user in user_passwords.values())
    if incomplete_users == 0:
        return "**All users have completed tagging. You may view the summary.**"
    return f"**{incomplete_users} users still need to complete their tagging.**"

def main():
    parser = argparse.ArgumentParser(description="Run the Gradio News Tagging App")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the app on (default: 7860)")
    args = parser.parse_args()
    
    with gr.Blocks(title="News Tagging App", theme=gr.themes.Ocean()) as app:
        gr.Markdown("""# News Tagging App""")
        
        with gr.Tab("Upload File"):
            gr.Markdown("### **Upload an Excel File (Admin Only)**")
            password_input = gr.Textbox(label="Admin Password", type="password")
            num_sets_input = gr.Number(label="Number of Sets")
            num_users_input = gr.Number(label="Users per Set")
            upload_component = gr.File(label="Upload Excel File", file_types=[".xlsx"])
            upload_button = gr.Button("Upload", variant="primary")
            upload_output = gr.Markdown()
            upload_button.click(upload_excel, inputs=[upload_component, password_input, num_sets_input, num_users_input], outputs=[upload_output])
        
        with gr.Tab("Tag News"):
            gr.Markdown("### **User Login**")
            user_password_input = gr.Textbox(label="User Password", type="password")
            login_button = gr.Button("Login")
            login_output = gr.Markdown()
            login_button.click(authenticate_user, inputs=[user_password_input], outputs=[login_output])
            
            gr.Markdown("### **Tag News URL**")
            url_display = gr.Markdown()
            company_display = gr.Textbox(label="Company Name", interactive=False)
            news_preview = gr.HTML()
            index_input = gr.Number(label="Index", value=0, interactive=False)
            tag_input = gr.Radio(choices=["Yes", "No"], label="Is this news related to the company?")
            tag_button = gr.Button("Save Tag", variant="primary", interactive=False)
            tag_button.click(tag_news, inputs=[index_input, tag_input, user_password_input], outputs=[url_display, company_display, news_preview, index_input])
        
        with gr.Tab("Summary"):
            gr.Markdown("### **Tagging Summary**")
            summary_status = gr.Markdown()
            summary_button = gr.Button("Show Summary", variant="primary", visible=False)
            summary_button.click(check_summary_availability, inputs=[], outputs=[summary_status])
    
    app.launch(server_port=args.port)

if __name__ == "__main__":
    main()
