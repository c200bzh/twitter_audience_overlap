# Twitter Utils Module

Shared utility functions for Twitter API authentication and rate limiting used across all Twitter engagement analysis scripts.

## 📦 What's in this module

### 🔐 Authentication Functions

#### `ACCESS_TOKEN`, `REFRESH_TOKEN`, `CLIENT_ID`, `CLIENT_SECRET`
OAuth 2.0 credentials that can be set via environment variables or edited directly in the file.

**Environment variables:**
```bash
export TWITTER_ACCESS_TOKEN='your_access_token_here'
export TWITTER_REFRESH_TOKEN='your_refresh_token_here'
export TWITTER_CLIENT_ID='your_client_id_here'
export TWITTER_CLIENT_SECRET='your_client_secret_here'
```

#### `test_authentication(access_token)`
Tests if the provided access token is valid by calling `/2/users/me`.

**Returns:** `True` if authenticated, `False` otherwise


### ⏱️ Rate Limiting

#### `RateLimiter` Class
A class to elegantly manage Twitter API rate limits with automatic waiting and progress tracking.

**Constructor:**
```python
RateLimiter(limit, window=900)
```
- `limit`: Maximum requests per window
- `window`: Time window in seconds (default: 900 = 15 minutes)

**Complete Example:**
```python
from utils.twitter_utils import RateLimiter

# Initialize with rate limit parameters
rate_limiter = RateLimiter(limit=75, window=900)  # 75 requests per 15 minutes

# Process items with automatic rate limiting
for i, item in enumerate(items, 1):
    # Wait if rate limit is reached
    rate_limiter.wait_if_needed()

    # Make your API call
    result = make_api_call(item)

    # If API call used pagination (e.g., 3 pages), increment by that amount
    pages_used = 3
    rate_limiter.increment(pages_used)

    # Show progress with warnings
    rate_limiter.show_progress(
        warn_threshold=10,        # Warn when ≤10 requests remain
        total_items=len(items),   # Total items to process
        current_item=i            # Current item number
    )
```


## 🔧 Helper Scripts in this Directory

### `get_code_verifier_twitter.py`
Generates OAuth 2.0 authorization URL and code verifier for obtaining new tokens.
You need CLIENT_ID, CLIENT_SECRET, REDIRECT_URL, to run this script.

**Usage:**
```bash
cd utils
python get_code_verifier_twitter.py
```

**Output:**
- Code verifier (save this!)
- Authorization URL (visit in browser)

### `get_refresh_token.py`
Exchanges authorization code for access and refresh tokens.

**Usage:**
```bash
cd utils
python get_refresh_token.py
```

**Required:** Authorization code from the OAuth flow (from step above)

**Output:**
- Access token (valid for 2 hours)
- Refresh token (valid for extended period)

## 📊 Rate Limits Reference

| Endpoint | Script | Rate Limit (Pro Tier) |
|----------|--------|----------------------|
| `GET /2/users/:id/tweets` | 0, 3 | 900 per 15 min |
| `GET /2/tweets/:id/retweeted_by` | 1 | 75 per 15 min |

**Note:** Different API tiers have different limits. Edit the `RateLimiter` initialization in each script if you have a different tier.

## 🆘 Troubleshooting

### "Access token expired" or Missing Token Error
Generate new tokens using the helper scripts:
```bash
cd utils
python get_code_verifier_twitter.py  # Get authorization URL
# Visit the URL in your browser and authorize
python get_refresh_token.py          # Enter the authorization code
# Copy the tokens and set them as environment variables or in twitter_utils.py
```

### "Rate limit reached" Message
The script will automatically wait. You can:
- Wait for the script to continue (automatic)
- Stop and resume later (progress is saved to CSV files)
- Adjust rate limits in script if you have higher tier access

---

For the complete pipeline documentation, see `../README.md`
