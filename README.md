# Twitter Engagement Analysis Pipeline

This pipeline analyzes Twitter engagement patterns to discover influential accounts that your engaged audience follows. The goal is to identify what content resonates with people who interact with your tweets, providing inspiration for content strategy.

## 📊 What This Pipeline Does

**Overall Goal**: Find accounts that your engaged audience retweets, ranked by how many unique engaged users retweet them.


## 🔄 The Complete Workflow

```
Input: Twitter Handle (@ethstatus)
   ↓
[0] Get Original Tweets (up to ~3200 recent)
   → twitter_files/0_original_tweets/tweet_id_ethstatus.csv
   ↓
[1] Get Retweeting Users
   → twitter_files/1_retweeting_users/ethstatus_{tweet_id}_retweeting_users.csv
   ↓
[2] Aggregate Unique Users
   → twitter_files/2_engaged_accounts/ethstatus_engaged_accounts.csv
   ↓
[3] Get User Retweets (up to ~3200 recent per user)
   → twitter_files/3_user_retweets/ethstatus_{user_id}_tweets.csv
   ↓
[4] Analyze Retweeted Accounts
   → twitter_files/4_retweeted_accounts/ethstatus_retweeted_accounts.csv
   ↓
Output: Ranked list of influential accounts
```

## 📁 Folder Structure

All output files are organized in the `twitter_files/` directory:

```
├── twitter_files/
│   ├── 0_original_tweets/        # Step 0: Original tweets from target accounts
│   │   └── tweet_id_ethstatus.csv
│   ├── 1_retweeting_users/       # Step 1: Users who retweeted each tweet
│   │   ├── ethstatus_1234_retweeting_users.csv
│   │   └── ethstatus_5678_retweeting_users.csv
│   ├── 2_engaged_accounts/       # Step 2: Aggregated unique engaged users
│   │   └── ethstatus_engaged_accounts.csv
│   ├── 3_user_retweets/          # Step 3: Retweets from engaged users
│   │   ├── ethstatus_1111_tweets.csv
│   │   └── ethstatus_2222_tweets.csv
│   └── 4_retweeted_accounts/     # Step 4: Final ranked analysis
│       └── ethstatus_retweeted_accounts.csv
├── utils/                         # Helper utilities
│   ├── twitter_utils.py
│   ├── get_code_verifier_twitter.py
│   └── get_refresh_token.py
├── 0.get_tweets.py
├── 1.get_retweets.py
├── 2.get_engaged_accounts.py
├── 3.get_user_retweets.py
├── 4.get_retweeted_accounts.py
└── README.md
```


## 🚀 Quick Start Guide

### 1. Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Set your Twitter API credentials:
```bash
export TWITTER_ACCESS_TOKEN='your_access_token'
export TWITTER_REFRESH_TOKEN='your_refresh_token'
export TWITTER_CLIENT_ID='your_client_id'
export TWITTER_CLIENT_SECRET='your_client_secret'
```

Or edit `utils/twitter_utils.py` to set credentials directly.
(See Helper Utilities section to generate new tokens)

### 2. Run Complete Pipeline

```bash
# Step 0: Get original tweets
python 0.get_tweets.py ethstatus

# Step 1: Get users who retweeted those tweets
python 1.get_retweets.py tweet_id_ethstatus.csv

# Step 2: Aggregate unique engaged users
python 2.get_engaged_accounts.py ethstatus

# Step 3: Get what engaged users retweet
python 3.get_user_retweets.py ethstatus

# Step 4: Analyze and rank retweeted accounts
python 4.get_retweeted_accounts.py ethstatus
```

**Result**: `ethstatus_retweeted_accounts.csv` - ranked list of influential accounts!

### 3. Analyze Multiple Accounts

```bash
# Run steps 0-3 for each account
python 0.get_tweets.py ethstatus
python 1.get_retweets.py tweet_id_ethstatus.csv
python 2.get_engaged_accounts.py ethstatus
python 3.get_user_retweets.py ethstatus

python 0.get_tweets.py keycard
python 1.get_retweets.py tweet_id_keycard.csv
python 2.get_engaged_accounts.py keycard
python 3.get_user_retweets.py keycard

# Then combine in step 4
python 4.get_retweeted_accounts.py ethstatus keycard
```

---

## 📋 Requirements

- **Python 3.7+**
- **Twitter API Access** with OAuth 2.0
- **Required Scopes**: `tweet.read`, `users.read`, `offline.access`
- **API Tier**: Works with Pro tier (see rate limits below), if you don't have a Pro tier, you can still use the script but you will need to edit how the rate limiting is handled (the rate limiting is handled in the `utils/twitter_utils.py` file).


## 📝 Script Details

### Script 0: `0.get_tweets.py` - Fetch Original Tweets

**Purpose**: Get all original tweets from a target account (no retweets, replies, or quote tweets).

**Usage**:
```bash
python 0.get_tweets.py <username>
python 0.get_tweets.py ethstatus
python 0.get_tweets.py @keycard
```

**Input**: Twitter username/handle
**Output**: `twitter_files/0_original_tweets/tweet_id_{username}.csv`
**What it does**:
- Fetches up to ~3200 most recent original tweets (Twitter API limit)
- Excludes retweets, replies, and quote tweets - only original content
- Saves tweet IDs to CSV for next step

**Note**: Twitter API limits this endpoint to ~3200 most recent tweets per user.

---

### Script 1: `1.get_retweets.py` - Get Retweeting Users

**Purpose**: For each tweet, fetch all users who retweeted it.

**Usage**:
```bash
python 1.get_retweets.py <csv_file>
python 1.get_retweets.py tweet_id_ethstatus.csv
```

**Input**: CSV file with tweet IDs (from Script 0, reads from `twitter_files/0_original_tweets/`)
**Output**: `twitter_files/1_retweeting_users/{account}_{tweet_id}_retweeting_users.csv` (one file per tweet)
**What it does**:
- Uses the [`GET /2/tweets/:id/retweeted_by`](https://docs.x.com/x-api/posts/get-reposted-by) endpoint
- Reads tweet IDs from input CSV
- For each tweet, fetches ALL users who retweeted it (handles pagination)
- Saves user details (ID, username, name, bio, location, etc.)
- Manages rate limits (75 requests per 15 minutes)

**Note**: This is where we identify your "engaged audience", people who actively share your content.

---

### Script 2: `2.get_engaged_accounts.py` - Aggregate Unique Users

**Purpose**: Combine all retweeting users into a single list of unique engaged accounts.

**Usage**:
```bash
python 2.get_engaged_accounts.py <account_name>
python 2.get_engaged_accounts.py ethstatus
```

**Input**: Account name (reads from `twitter_files/1_retweeting_users/`)
**Output**: `twitter_files/2_engaged_accounts/{account}_engaged_accounts.csv`
**What it does**:
- Finds all retweeting users files for the specified account
- Deduplicates users (same person may retweet multiple tweets)
- Creates consolidated list of unique engaged accounts

**Why**: This gives you the universe of users who actively engage with your content.

---

### Script 3: `3.get_user_retweets.py` - Get User Retweets

**Purpose**: Fetch what each engaged user retweets.

**Usage**:
```bash
python 3.get_user_retweets.py <account_name>
python 3.get_user_retweets.py ethstatus
```

**Input**: Account name (reads from `twitter_files/2_engaged_accounts/`)
**Output**: `twitter_files/3_user_retweets/{account}_{user_id}_tweets.csv` (one file per engaged user)
**What it does**:
- Reads the engaged accounts list
- For each user, fetches ONLY their retweets (not original content)
- Filters out original tweets, replies, quotes - keeps only retweets
- Manages rate limits (900 requests per 15 minutes - high limit!)

**Why**: By analyzing what your engaged audience retweets, you discover what content they find valuable enough to share.

**Note**: Twitter API limits this to ~3200 most recent tweets per user (same as Script 0).

---

### Script 4: `4.get_retweeted_accounts.py` - Analyze Retweeted Accounts

**Purpose**: Extract and rank accounts that your engaged audience retweets.

**Usage**:
```bash
# Single account
python 4.get_retweeted_accounts.py ethstatus

# Multiple accounts (combines data)
python 4.get_retweeted_accounts.py ethstatus keycard logos
```

**Input**: One or more account names (reads from `twitter_files/3_user_retweets/`)
**Output**: `twitter_files/4_retweeted_accounts/{accounts}_retweeted_accounts.csv`
**What it does**:
- Reads all tweet files from engaged users
- Extracts Twitter handles from retweet text (RT @username: ...)
- Counts unique users who retweeted each account (not total retweets)
- Ranks accounts by influence (most unique engaged users first)

**Why**: This reveals the most influential accounts in your community. If many of your engaged users retweet the same account, that account is likely relevant and valuable.

**Pro tip**: Can aggregate across multiple accounts to find broader patterns! Run steps 0-3 for each account, then combine in step 4:
```bash
python 4.get_retweeted_accounts.py ethstatus keycard logos
```

---

### Rate Limits (Pro Tier)

| Script | Endpoint | Rate Limit | Additional Limits |
|--------|----------|------------|-------------------|
| 0 | `GET /2/users/:id/tweets` | 900 per 15 min | ~3200 most recent tweets per user |
| 1 | `GET /2/tweets/:id/retweeted_by` | 75 per 15 min | 100 users per request (paginated) |
| 3 | `GET /2/users/:id/tweets` | 900 per 15 min | ~3200 most recent tweets per user |

**Important**:
- All scripts automatically handle rate limiting and wait when necessary
- The 3200 tweet limit is a Twitter API restriction, not a script limitation
- Pagination is handled automatically where available

---

## 🔍 Why Retweets Instead of Likes?

Twitter made all like activity private in August 2024. The `GET /2/tweets/:id/liking_users` endpoint now only returns data for tweets from the authenticated account.

**Solution**: We pivoted to analyzing retweets, which remain public. While retweets are less common than likes, they indicate stronger engagement - someone valued the content enough to share it with their audience.

**Benefit**: Retweets often signal higher-quality engagement and are more actionable for content strategy.

---

## 🛠️ Helper Utilities

All helper utilities are located in the `utils/` directory:

### `utils/twitter_utils.py`
Shared module containing:
- OAuth 2.0 authentication logic
- Token refresh functionality
- `RateLimiter` class for elegant rate limit management
- Centralized error handling

### `utils/get_code_verifier_twitter.py`
Generates OAuth 2.0 authorization URL and code verifier for getting new tokens.

### `utils/get_refresh_token.py`
Exchanges authorization code for access and refresh tokens.

See `utils/README_twitter_utils.md` for detailed documentation.

### Getting New Tokens

If your tokens expire:

1. Generate authorization URL:
```bash
cd utils
python get_code_verifier_twitter.py
```

2. Get tokens:
```bash
python get_refresh_token.py
cd ..
```
