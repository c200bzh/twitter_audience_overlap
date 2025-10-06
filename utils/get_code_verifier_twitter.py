import secrets
import base64
import hashlib
import urllib.parse

# Generate a random code verifier and gets the url to authorize the app
# Step 1. run the code
# Step 2. copy the code verifier in the answer
# Step 3. copy the url in the browser and authorize the app
# Step 4. copy the code in the url after the redirect (this is the authorization code)


def generate_code_verifier():
    random_bytes = secrets.token_bytes(32)
    code_verifier = base64.urlsafe_b64encode(random_bytes).rstrip(b'=').decode('utf-8')
    return code_verifier

def generate_code_challenge(code_verifier):
    sha256 = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(sha256).rstrip(b'=').decode('utf-8')
    return code_challenge

def build_authorization_url(client_id, redirect_uri, scope, state, code_challenge):
    base_url = "https://twitter.com/i/oauth2/authorize"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    url = base_url + "?" + urllib.parse.urlencode(params)
    return url

CLIENT_ID = "your client id"
REDIRECT_URI = "your redirect uri"
SCOPE = "tweet.read users.read offline.access space.read like.read"
STATE = "random_string_for_csrf_protection"  # any random string

# Generate PKCE code verifier and challenge
code_verifier = generate_code_verifier()
code_challenge = generate_code_challenge(code_verifier)

auth_url = build_authorization_url(CLIENT_ID, REDIRECT_URI, SCOPE, STATE, code_challenge)

print("Open this URL in your browser to authorize the app:\n")
print(auth_url)

print("\nSave this code_verifier securely for the token exchange step:\n")
print(code_verifier)
