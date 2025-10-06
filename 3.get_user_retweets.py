import requests
import csv
import os
import sys
import time
from datetime import datetime, timedelta
from utils.twitter_utils import ACCESS_TOKEN, test_authentication, RateLimiter

# Rate limit constants
RATE_LIMIT = 900  # requests per window
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds


def get_user_tweets(user_id, access_token, max_results=100):
    """
    Fetch retweets from a specific user using Twitter API v2.
    Filters to get only retweets (not original tweets, replies, or quotes).
    Handles pagination to get all retweets beyond the 100-tweet limit per request.
    Returns a list of retweet data dictionaries and the total count.

    """
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    all_tweets = []
    pagination_token = None
    page_count = 0
    total_fetched = 0

    while True:
        page_count += 1

        params = {
            "max_results": max_results,
            "tweet.fields": "id,text,author_id,created_at,public_metrics,lang,conversation_id,referenced_tweets"
        }

        if pagination_token:
            params["pagination_token"] = pagination_token

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                tweets = data.get('data', [])
                meta = data.get('meta', {})

                # Filter to keep only retweets
                retweets = []
                for tweet in tweets:
                    referenced_tweets = tweet.get('referenced_tweets', [])
                    is_retweet = any(ref.get('type') == 'retweeted' for ref in referenced_tweets)
                    if is_retweet:
                        retweets.append(tweet)

                # Add retweets from this page
                all_tweets.extend(retweets)
                total_fetched += len(retweets)

                pagination_token = meta.get('next_token')

                if pagination_token:
                    print(f"      📄 Fetched page {page_count}: {len(tweets)} tweets (total so far: {total_fetched})")
                    time.sleep(0.5)  # Small delay between pagination requests
                else:
                    break

            elif response.status_code == 429:
                print(f"⚠️  Rate limit reached. Waiting 15 minutes...")
                time.sleep(900)
                # Don't increment page_count, retry the same request
                continue
            elif response.status_code == 403:
                print(f"❌ Error fetching tweets for user {user_id}: 403 Forbidden")
                print(f"   Response: {response.text}")
                print(f"   ⚠️  This could mean:")
                print(f"       - The user account is protected/private")
                print(f"       - The user doesn't exist or was suspended")
                print(f"   Skipping this user...")
                break
            elif response.status_code == 401:
                print(f"❌ Authorization error for user {user_id}: 401 Unauthorized")
                print(f"   Your access token may have expired. Please refresh it.")
                break
            else:
                print(f"❌ Error fetching tweets for user {user_id}: {response.status_code}")
                print(f"   Response: {response.text}")
                break

        except Exception as e:
            print(f"❌ Exception for user {user_id}: {e}")
            break

    return all_tweets, total_fetched


def save_user_tweets_to_csv(user_id, username, tweets, account_name=''):
    """
    Save user tweets data to a CSV file in organized folder structure.
    """
    output_dir = "twitter_files/3_user_retweets"
    os.makedirs(output_dir, exist_ok=True)


    if account_name:
        filename = os.path.join(output_dir, f"{account_name}_{user_id}_tweets.csv")
    else:
        filename = os.path.join(output_dir, f"{user_id}_tweets.csv")

    if not tweets:
        print(f"   No retweets found for user @{username}")
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['retweet_id', 'text', 'created_at', 'retweeted_tweet_id', 'lang', 'conversation_id'])
        return filename

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['retweet_id', 'text', 'created_at', 'retweeted_tweet_id', 'lang', 'conversation_id'])

        for tweet in tweets:
            referenced_tweets = tweet.get('referenced_tweets', [])

            retweeted_tweet_id = ''
            for ref in referenced_tweets:
                if ref.get('type') == 'retweeted':
                    retweeted_tweet_id = ref.get('id', '')
                    break

            writer.writerow([
                tweet.get('id', ''),
                tweet.get('text', '').replace('\n', ' '),
                tweet.get('created_at', ''),
                retweeted_tweet_id,
                tweet.get('lang', ''),
                tweet.get('conversation_id', '')
            ])

    print(f"   💾 Saved {len(tweets)} tweets to {filename}")
    return filename


def read_engaged_accounts(csv_file):
    """
    Read user IDs from the engaged_accounts.csv file.
    """
    user_accounts = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_id = row.get('user_id', '').strip()
            username = row.get('username', '').strip()
            if user_id:  # Skip empty rows
                user_accounts.append({'user_id': user_id, 'username': username})
    return user_accounts


def main():
    print(" Twitter User Retweets Fetcher")
    print("=" * 50)

    # Check for command line argument
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide an account name")
        print("\nUsage:")
        print("  python 3.get_user_retweets.py <account_name>")
        print("\nExample:")
        print("  python 3.get_user_retweets.py ethstatus")
        print("\nThis will read from: ethstatus_engaged_accounts.csv")
        return

    account_name = sys.argv[1].lstrip('@')  # Remove @ if present
    print(f"\n Processing engaged accounts for: @{account_name}")

    # Test authentication first
    print("\n Testing authentication...")
    if not test_authentication(ACCESS_TOKEN):
        print("\n❌ Authentication failed. Please check your access token.")
        return

    # Read engaged accounts from CSV with account name prefix
    input_dir = "twitter_files/2_engaged_accounts"
    csv_filename = f'{account_name}_engaged_accounts.csv'
    csv_path = os.path.join(input_dir, csv_filename)

    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_filename} not found in {input_dir}!")
        print(f"   Please run: python 2.get_engaged_accounts.py {account_name}")
        return

    print(f"\n Reading engaged accounts from {csv_path}...")
    user_accounts = read_engaged_accounts(csv_path)
    print(f" Found {len(user_accounts)} engaged accounts to process")

    # Rate limit information
    print(f"\n⚠️  Rate Limit Info:")
    print(f"   - Twitter API limit: {RATE_LIMIT} requests per 15 minutes")
    print(f"   - This is a HIGH rate limit endpoint!")
    print(f"   - Note: Each user may require multiple API requests if they have >100 tweets")
    print(f"   - The script will automatically manage rate limits and wait when needed")

    rate_limiter = RateLimiter(limit=RATE_LIMIT, window=RATE_LIMIT_WINDOW)
    successful_accounts = 0
    failed_accounts = 0
    total_tweets = 0

    for i, account in enumerate(user_accounts, 1):
        user_id = account['user_id']
        username = account['username']

        rate_limiter.wait_if_needed()

        print(f"[{i}/{len(user_accounts)}] Processing @{username} (ID: {user_id})...")

        tweets, total_count = get_user_tweets(user_id, ACCESS_TOKEN)

        # Count actual API requests made (including pagination)
        # Each page of 100 tweets = 1 API request
        pages_fetched = (total_count + 99) // 100 if total_count > 0 else 1
        rate_limiter.increment(pages_fetched)

        if total_count > 0:
            successful_accounts += 1
            total_tweets += total_count
            print(f"   ✅ Found {total_count} retweets (fetched in {pages_fetched} API request{'s' if pages_fetched > 1 else ''})")
        else:
            failed_accounts += 1

        save_user_tweets_to_csv(user_id, username, tweets, account_name)

        rate_limiter.show_progress(warn_threshold=50, total_items=len(user_accounts), current_item=i)

        # Small delay between requests
        if i < len(user_accounts):
            time.sleep(0.5)

    print(f"\n🎉 Done! Processed {len(user_accounts)} accounts")
    print(f"   ✅ Successful: {successful_accounts}")
    print(f"   ❌ Failed/Empty: {failed_accounts}")
    print(f"   📊 Total retweets collected: {total_tweets}")
    print(f"\n💾 Output files: {account_name}_{{user_id}}_tweets.csv")


if __name__ == "__main__":
    main()
