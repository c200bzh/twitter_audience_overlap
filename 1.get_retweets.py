import requests
import csv
import os
import sys
import time
from datetime import datetime, timedelta
from utils.twitter_utils import ACCESS_TOKEN, test_authentication, RateLimiter

# Rate limit constants
RATE_LIMIT = 75  # requests per window
RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds


def get_retweeting_users(tweet_id, access_token):
    """
    Fetch ALL users who retweeted a specific tweet using Twitter API v2.
    Handles pagination to get all users beyond the 100-user limit per request.
    Returns a list of user data dictionaries and the total count.
    """
    url = f"https://api.twitter.com/2/tweets/{tweet_id}/retweeted_by"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    all_users = []
    pagination_token = None
    page_count = 0
    total_fetched = 0

    while True:
        page_count += 1

        # Request user fields for more detailed information
        params = {
            "max_results": 100,
            "user.fields": "id,name,username,created_at,description,location,verified"
        }

        if pagination_token:
            params["pagination_token"] = pagination_token

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                users = data.get('data', [])
                meta = data.get('meta', {})

                # Debug: Print raw response for first tweet
                if page_count == 1 and total_fetched == 0:
                    print(f"      🔍 Debug - API Response: {data}")

                # Add users from this page
                all_users.extend(users)
                total_fetched += len(users)

                # Check if there are more pages
                pagination_token = meta.get('next_token')

                if pagination_token:
                    print(f"  Fetched page {page_count}: {len(users)} users (total so far: {total_fetched})")
                    time.sleep(1)
                else:
                    break

            elif response.status_code == 429:
                print(f"⚠️  Rate limit reached. Waiting 15 minutes...")
                time.sleep(900)
                # Don't increment page_count, retry the same request
                continue
            elif response.status_code == 403:
                print(f"❌ Error fetching retweets for tweet {tweet_id}: 403 Forbidden")
                print(f"   Response: {response.text}")
                print(f"     This could mean:")
                print(f"       - The tweet is from a protected/private account")
                print(f"       - The tweet doesn't exist or was deleted")
                print(f"   Skipping this tweet...")
                break
            else:
                print(f"❌ Error fetching retweets for tweet {tweet_id}: {response.status_code}")
                print(f"   Response: {response.text}")
                break

        except Exception as e:
            print(f"❌ Exception for tweet {tweet_id}: {e}")
            break

    return all_users, total_fetched


def save_retweeting_users_to_csv(tweet_id, users, account_name=''):
    output_dir = "twitter_files/1_retweeting_users"
    os.makedirs(output_dir, exist_ok=True)

    if account_name:
        filename = os.path.join(output_dir, f"{account_name}_{tweet_id}_retweeting_users.csv")
    else:
        filename = os.path.join(output_dir, f"{tweet_id}_retweeting_users.csv")

    if not users:
        print(f"   No retweeting users found for tweet {tweet_id}")
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['user_id', 'username', 'name', 'created_at', 'description', 'location', 'verified'])
        return filename

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['user_id', 'username', 'name', 'created_at', 'description', 'location', 'verified'])

        for user in users:
            writer.writerow([
                user.get('id', ''),
                user.get('username', ''),
                user.get('name', ''),
                user.get('created_at', ''),
                user.get('description', '').replace('\n', ' '),  # Remove newlines from description
                user.get('location', ''),
                user.get('verified', False)
            ])

    print(f"   Saved {len(users)} retweeting users to {filename}")
    return filename


def read_tweet_ids(csv_file):
    """
    Read tweet IDs from the CSV file.
    """
    tweet_ids = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweet_id = row.get('id', '').strip()
            if tweet_id:  # Skip empty rows
                tweet_ids.append(tweet_id)
    return tweet_ids


def main():
    print(" Twitter Retweeting Users Fetcher")
    print("=" * 50)

    # Check for command line argument
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide a CSV file with tweet IDs")
        print("\nUsage:")
        print("  python 1.get_retweets.py <csv_file>")
        print("\nExample:")
        print("  python 1.get_retweets.py tweet_id_ethstatus.csv")
        return

    csv_file = sys.argv[1]

    # Extract account name from CSV filename
    account_name = ''
    if csv_file.startswith('tweet_id_') and csv_file.endswith('.csv'):
        account_name = csv_file.replace('tweet_id_', '').replace('.csv', '')
        print(f"\n Detected account: @{account_name}")

    # Test authentication first
    print("\n Testing authentication...")
    if not test_authentication(ACCESS_TOKEN):
        print("\n❌ Authentication failed. Please check your access token.")
        return

    # Check if file exists
    input_dir = "twitter_files/0_original_tweets"
    csv_path = os.path.join(input_dir, csv_file)

    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_file} not found!")
        print(f"   Looked in: {csv_path}")
        print(f"   Make sure you've run: python 0.get_tweets.py <username>")
        return

    print(f"\n📂 Reading tweet IDs from {csv_path}...")
    tweet_ids = read_tweet_ids(csv_path)
    print(f" Found {len(tweet_ids)} tweet IDs to process")

    # Rate limit information
    print(f"\n⚠️  Rate Limit Info:")
    print(f"   - Twitter API limit: {RATE_LIMIT} requests per 15 minutes")
    print(f"   - Your request count: {len(tweet_ids)} tweets")
    if len(tweet_ids) > RATE_LIMIT:
        batches = (len(tweet_ids) + RATE_LIMIT - 1) // RATE_LIMIT
        print(f"   - This will require {batches} batches with 15-minute waits between them")
    else:
        print(f"   - ✅ You're within the rate limit!")

    rate_limiter = RateLimiter(limit=RATE_LIMIT, window=RATE_LIMIT_WINDOW)

    for i, tweet_id in enumerate(tweet_ids, 1):
        rate_limiter.wait_if_needed()

        print(f"[{i}/{len(tweet_ids)}] Processing tweet {tweet_id}...")

        users, total_count = get_retweeting_users(tweet_id, ACCESS_TOKEN)

        # Count actual API requests made (including pagination)
        # Each page of 100 users = 1 API request
        pages_fetched = (total_count + 99) // 100 if total_count > 0 else 1
        rate_limiter.increment(pages_fetched)

        print(f"   ✅ Found {total_count} retweeting users (fetched in {pages_fetched} API request{'s' if pages_fetched > 1 else ''})")

        save_retweeting_users_to_csv(tweet_id, users, account_name)

        # Show progress on rate limit
        rate_limiter.show_progress(warn_threshold=10, total_items=len(tweet_ids), current_item=i)

        # Small delay between requests
        if i < len(tweet_ids):
            time.sleep(1)

    print(f"\n🎉 Done! Processed {len(tweet_ids)} tweets")


if __name__ == "__main__":
    main()
