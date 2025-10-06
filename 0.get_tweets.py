import requests
import csv
import os
import sys
import time
from utils.twitter_utils import ACCESS_TOKEN

def get_user_id_by_username(username, access_token):
    """
    Get user ID from username using Twitter API v2.
    """
    # Remove @ if present
    username = username.lstrip('@')

    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            user_id = data.get('data', {}).get('id')
            user_name = data.get('data', {}).get('name')
            print(f"✅ Found user: {user_name} (@{username})")
            print(f"   User ID: {user_id}")
            return user_id
        else:
            print(f"❌ Error fetching user: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def get_original_tweets(user_id, access_token, max_results=100):
    """
    Fetch original tweets from a user (no retweets, replies, or quotes).
    Returns a list of tweet IDs.
    """
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    all_tweet_ids = []
    pagination_token = None
    page_count = 0

    print(f"\n Fetching original tweets...")

    while True:
        page_count += 1

        params = {
            "max_results": max_results,
            "tweet.fields": "id,referenced_tweets",
            "exclude": "retweets,replies"
        }

        if pagination_token:
            params["pagination_token"] = pagination_token

        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                tweets = data.get('data', [])
                meta = data.get('meta', {})

                # Filter out quote tweets (they have referenced_tweets with type 'quoted')
                for tweet in tweets:
                    referenced_tweets = tweet.get('referenced_tweets', [])
                    is_quote = any(ref.get('type') == 'quoted' for ref in referenced_tweets)

                    if not is_quote:
                        all_tweet_ids.append(tweet.get('id'))

                print(f"   Page {page_count}: Found {len(tweets)} tweets, {len([t for t in tweets if not any(ref.get('type') == 'quoted' for ref in t.get('referenced_tweets', []))])} are original")

                # Check for more pages
                pagination_token = meta.get('next_token')
                if pagination_token:
                    time.sleep(0.5)
                else:
                    break

            elif response.status_code == 429:
                print(f"⚠️  Rate limit reached. Waiting 15 minutes...")
                time.sleep(900)
                continue
            else:
                print(f"❌ Error fetching tweets: {response.status_code}")
                print(f"   Response: {response.text}")
                break

        except Exception as e:
            print(f"❌ Exception: {e}")
            break

    return all_tweet_ids


def save_tweet_ids_to_csv(tweet_ids, username):
    """
    Save tweet IDs to CSV file in organized folder structure.
    """
    output_dir = "twitter_files/0_original_tweets"
    os.makedirs(output_dir, exist_ok=True)

    clean_username = username.lstrip('@').lower()
    filename = os.path.join(output_dir, f"tweet_id_{clean_username}.csv")

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id'])

        for tweet_id in tweet_ids:
            writer.writerow([tweet_id])

    print(f"\n Saved {len(tweet_ids)} tweet IDs to {filename}")
    return filename


def main():
    print("Twitter Original Tweets Fetcher")
    print("=" * 50)

    # Check for command line argument
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide a Twitter username")
        print("\nUsage:")
        print("  python 0.get_tweets.py <username>")
        print("\nExample:")
        print("  python 0.get_tweets.py ethstatus")
        print("  python 0.get_tweets.py @ethstatus")
        return

    username = sys.argv[1]

    print(f"\n Looking up user: {username}")

    # Get user ID from username
    user_id = get_user_id_by_username(username, ACCESS_TOKEN)
    if not user_id:
        print("\n❌ Could not find user. Please check the username and try again.")
        return

    # Fetch original tweets
    tweet_ids = get_original_tweets(user_id, ACCESS_TOKEN)

    if not tweet_ids:
        print("\n❌ No original tweets found (or all tweets are retweets/replies/quotes)")
        return

    print(f"\n✅ Found {len(tweet_ids)} original tweets")

    # Save to CSV
    filename = save_tweet_ids_to_csv(tweet_ids, username)

    print(f"\n🎉 Done! Tweet IDs saved to {filename}")
    if len(tweet_ids) >= 3000:
        print(f"   You may have reached this limit ({len(tweet_ids)} tweets fetched)")


if __name__ == "__main__":
    main()
