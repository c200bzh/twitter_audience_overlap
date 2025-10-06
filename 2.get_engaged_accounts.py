import csv
import os
import sys
import glob

def read_retweeting_users_files(account_name=''):
    """
    Read retweeting users CSV files for a specific account and collect unique users.
    Returns a dictionary of users keyed by user_id.
    """
    users_dict = {}

    input_dir = "twitter_files/1_retweeting_users"

    if account_name:
        pattern = os.path.join(input_dir, f'{account_name}_*_retweeting_users.csv')
    else:
        pattern = os.path.join(input_dir, '*_retweeting_users.csv')

    csv_files = glob.glob(pattern)

    if not csv_files:
        print(f"❌ No files matching pattern '{pattern}' found in current directory")
        return users_dict

    print(f" Found {len(csv_files)} retweeting users files")
    print()

    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    user_id = row.get('user_id', '').strip()

                    # Skip empty rows or header rows
                    if not user_id or user_id == 'user_id':
                        continue

                    # Store user info (only keep first occurrence of each user)
                    if user_id not in users_dict:
                        users_dict[user_id] = {
                            'user_id': user_id,
                            'username': row.get('username', ''),
                            'name': row.get('name', ''),
                            'created_at': row.get('created_at', ''),
                            'description': row.get('description', ''),
                            'location': row.get('location', ''),
                            'verified': row.get('verified', '')
                        }

            print(f"   ✅ Processed {csv_file}")

        except Exception as e:
            print(f"   ❌ Error reading {csv_file}: {e}")

    return users_dict


def save_engaged_accounts(users_dict, account_name=''):
    """
    Save unique engaged accounts to CSV file with account name prefix in organized folder structure.
    """
    output_dir = "twitter_files/2_engaged_accounts"
    os.makedirs(output_dir, exist_ok=True)

    if account_name:
        filename = os.path.join(output_dir, f'{account_name}_engaged_accounts.csv')
    else:
        filename = os.path.join(output_dir, 'engaged_accounts.csv')

    if not users_dict:
        print(f"\n❌ No engaged accounts found to save")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['user_id', 'username', 'name', 'created_at', 'description', 'location', 'verified'])

        for user_id in sorted(users_dict.keys()):
            user = users_dict[user_id]
            writer.writerow([
                user['user_id'],
                user['username'],
                user['name'],
                user['created_at'],
                user['description'],
                user['location'],
                user['verified']
            ])

    print(f"\n💾 Saved {len(users_dict)} unique engaged accounts to {filename}")
    return filename


def main():
    print(" Engaged Accounts Aggregator")
    print("=" * 50)

    # Check for command line argument
    if len(sys.argv) < 2:
        print("\n❌ Error: Please provide an account name")
        print("\nUsage:")
        print("  python 2.get_engaged_accounts.py <account_name>")
        print("\nExample:")
        print("  python 2.get_engaged_accounts.py ethstatus")
        print("\nThis will process all files matching: ethstatus_*_retweeting_users.csv")
        return

    account_name = sys.argv[1].lstrip('@')  # Remove @ if present
    print(f"\n Processing files for account: @{account_name}")
    print()

    users_dict = read_retweeting_users_files(account_name)

    if not users_dict:
        print(f"\n❌ No engaged accounts found for @{account_name}.")
        print(f"   Make sure you've run: python 1.get_retweets.py tweet_id_{account_name}.csv")
        return

    print(f"\n Statistics:")
    print(f"   - Total unique accounts: {len(users_dict)}")

    save_engaged_accounts(users_dict, account_name)

    print(f"\n🎉 Done! Engaged accounts saved to {account_name}_engaged_accounts.csv")


if __name__ == "__main__":
    main()
