"""
Twitter API Utility Functions
Common functions for authentication, rate limiting, and API interactions.
"""

import os
import time
import requests

# OAuth 2.0 credentials - set via environment variables or defaults
ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
REFRESH_TOKEN = os.getenv('TWITTER_REFRESH_TOKEN', '')
CLIENT_ID = os.getenv('TWITTER_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('TWITTER_CLIENT_SECRET', '')


def test_authentication(access_token):
    url = "https://api.twitter.com/2/users/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Authentication successful!")
            print(f"   Authenticated as: @{user_data['data']['username']} (ID: {user_data['data']['id']})")
            return True
        else:
            print(f"❌ Authentication test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        return False


class RateLimiter:
    """
    Helper class to manage Twitter API rate limits.

    Usage:
        limiter = RateLimiter(limit=75, window=900)
        for item in items:
            limiter.wait_if_needed()
            # make API call
            limiter.increment()
    """

    def __init__(self, limit, window=900):
        self.limit = limit
        self.window = window
        self.request_count = 0
        self.window_start = time.time()

    def wait_if_needed(self):
        """
        Check if rate limit is reached and wait if necessary.
        Resets the counter and window after waiting.
        """
        if self.request_count >= self.limit:
            elapsed = time.time() - self.window_start
            if elapsed < self.window:
                wait_time = self.window - elapsed
                print(f"\n⏳ Rate limit reached. Waiting {wait_time/60:.1f} minutes before continuing...")
                time.sleep(wait_time)
            # Reset counter and window
            self.request_count = 0
            self.window_start = time.time()

    def increment(self, count=1):
        self.request_count += count

    def get_remaining(self):
        return self.limit - self.request_count

    def show_progress(self, warn_threshold=10, total_items=None, current_item=None):
        remaining = self.get_remaining()
        print(f"   📊 API requests remaining in current window: {remaining}/{self.limit}")
