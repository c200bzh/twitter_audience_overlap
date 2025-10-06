import requests
import base64

client_id = "your client id"
client_secret = "your client secret"
redirect_uri = "your redirect uri"
code_verifier = "your code verifier" #from the get_code_verifier_twitter.py
authorization_code = "your authorization code" #from the get_code_verifier_twitter.py

# Encode client_id:client_secret in base64
credentials = f"{client_id}:{client_secret}"
b64_credentials = base64.b64encode(credentials.encode()).decode()

# Twitter's token endpoint
token_url = "https://api.twitter.com/2/oauth2/token"

data = {
    "grant_type": "authorization_code",
    "code": authorization_code,
    "redirect_uri": redirect_uri,
    "code_verifier": code_verifier,
    "client_id": client_id
}

response = requests.post(
    token_url,
    data=data,
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_credentials}"
    }
)

if response.ok:
    print("✅ Token response:")
    print(response.json())
else:
    print("❌ Error exchanging code:")
    print(response.status_code)
    print(response.text)
