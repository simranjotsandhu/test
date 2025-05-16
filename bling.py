import requests

# Replace with your actual credentials
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'

# Step 1: Get the access token
auth_url = 'https://api.refinitiv.com/auth/oauth2/v1/token'
auth_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
auth_data = {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'scope': 'trapi'
}

auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)
auth_response.raise_for_status()  # Raise an error if failed

access_token = auth_response.json()['access_token']
print("Access Token acquired!")

# Step 2: Fetch news story
story_guid = 'urn:newsml:reuters.com:20250514:nRSN6136Ia'  # Replace with your GUID
news_url = f'https://api.refinitiv.com/data/news/v1/stories/{story_guid}'
news_headers = {
    'Authorization': f'Bearer {access_token}'
}

news_response = requests.get(news_url, headers=news_headers)
news_response.raise_for_status()

news_json = news_response.json()
print("News Story Title:", news_json.get('title'))
print("News Story Body:", news_json.get('body', 'No content found.'))