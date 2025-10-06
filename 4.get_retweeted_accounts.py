import csv
import os
import sys
import glob
import re

def extract_retweeted_handle(text):
    """
    Extract the handle from a retweet text.
    Format: "RT @username: ..."
    Returns the username (without @) or None if not found.
    """
    pattern = r'^RT @(\w+):'
    match = re.match(pattern, text)

    if match:
        return match.group(1)
    return None


def read_tweets_files(account_names=None):
    """
    Read all *_tweets.csv files for specific accounts and collect retweeted handles.
    Returns a dictionary mapping handles to sets of users who retweeted them.
    """
    handles_users = {}
    all_csv_files = []

    input_dir = "twitter_files/3_user_retweets"

    if account_names:
        for account_name in account_names:
            pattern = os.path.join(input_dir, f'{account_name}_*_tweets.csv')
            csv_files = glob.glob(pattern)
            all_csv_files.extend(csv_files)
            if csv_files:
                print(f" Found {len(csv_files)} tweet files for @{account_name}")
    else:
        pattern = os.path.join(input_dir, '*_tweets.csv')
        all_csv_files = glob.glob(pattern)

    if not all_csv_files:
        print(f"❌ No matching tweet files found")
        return handles_users

    print(f" Total files to process: {len(all_csv_files)}")
    print()

    total_tweets_processed = 0
    total_handles_extracted = 0

    for csv_file in all_csv_files:
        try:
            filename = os.path.basename(csv_file)

            user_id = filename
            if account_names:
                for account_name in account_names:
                    user_id = user_id.replace(f'{account_name}_', '')
            user_id = user_id.replace('_tweets.csv', '')

            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    text = row.get('text', '').strip()

                    if not text:
                        continue

                    total_tweets_processed += 1

                    handle = extract_retweeted_handle(text)

                    if handle:
                        total_handles_extracted += 1
                        # Track which users retweeted this handle (deduplicated by set)
                        if handle in handles_users:
                            handles_users[handle].add(user_id)
                        else:
                            handles_users[handle] = {user_id}

            print(f"   ✅ Processed {csv_file}")

        except Exception as e:
            print(f"   ❌ Error reading {csv_file}: {e}")

    print()
    print(f"📊 Statistics:")
    print(f"   - Total tweets processed: {total_tweets_processed}")
    print(f"   - Total retweets with handles: {total_handles_extracted}")
    print(f"   - Unique retweeted accounts: {len(handles_users)}")

    return handles_users


def save_retweeted_accounts(handles_users, account_names=None):
    """
    Save retweeted accounts to CSV, sorted by number of unique users.
    """
    output_dir = "twitter_files/4_retweeted_accounts"
    os.makedirs(output_dir, exist_ok=True)

    if account_names:
        accounts_str = '_'.join(account_names)
        filename = os.path.join(output_dir, f'{accounts_str}_retweeted_accounts.csv')
    else:
        filename = os.path.join(output_dir, 'retweeted_accounts.csv')

    if not handles_users:
        print(f"\n❌ No retweeted accounts found to save")
        return

    # Convert sets to counts and sort by count (descending), then by username (ascending)
    handles_count = [(handle, len(users)) for handle, users in handles_users.items()]
    sorted_handles = sorted(handles_count, key=lambda x: (-x[1], x[0]))

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['username', 'unique_users_count'])

        for username, count in sorted_handles:
            writer.writerow([username, count])

    print(f"\n Saved {len(handles_users)} unique retweeted accounts to {filename}")
    print(f"   (Sorted by unique user count, highest first)")

    # Show top 10
    print(f"\n Top 10 most retweeted accounts (by unique users):")
    for i, (username, count) in enumerate(sorted_handles[:10], 1):
        print(f"   {i}. @{username} - retweeted by {count} unique user{'s' if count > 1 else ''}")

    return filename


def main():
    print(" Retweeted Accounts Extractor")
    print("=" * 50)

    # Check for command line arguments
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide at least one account name")
        print("\nUsage:")
        print("  python 4.get_retweeted_accounts.py <account_name1> [account_name2] [account_name3] ...")
        print("\nExamples:")
        print("  python 4.get_retweeted_accounts.py ethstatus")
        print("  python 4.get_retweeted_accounts.py ethstatus keycard")
        print("  python 4.get_retweeted_accounts.py ethstatus keycard logos")
        print("\nThis will process all files matching: <account>_*_tweets.csv")
        return

    account_names = [arg.lstrip('@') for arg in sys.argv[1:]]

    print(f"\n Processing tweet files for {len(account_names)} account(s):")
    for account in account_names:
        print(f"   - @{account}")
    print()

    handles_users = read_tweets_files(account_names)

    if not handles_users:
        print(f"\n❌ No retweeted accounts found.")
        print(f"   Make sure you've run 3.get_user_retweets.py for these accounts:")
        for account in account_names:
            print(f"   - python 3.get_user_retweets.py {account}")
        return

    save_retweeted_accounts(handles_users, account_names)

    accounts_str = '_'.join(account_names)
    output_file = f'{accounts_str}_retweeted_accounts.csv'
    print(f"\n🎉 Done! All retweeted accounts saved to {output_file}")


if __name__ == "__main__":
    main()
