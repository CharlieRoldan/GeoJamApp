import os
import toml
import subprocess

USER_SECRETS_FILE = "/Users/charlieroldan/coding/geojam-project/.streamlit/secrets.toml"
SYSTEM_SECRETS_FILE = "/System/Volumes/Data/Users/charlieroldan/coding/geojam-project/.streamlit/secrets.toml"

SECRETS_FILES = [USER_SECRETS_FILE, SYSTEM_SECRETS_FILE]

def ensure_secrets_files():
    """Ensure secrets.toml exists with correct structure."""
    for path in SECRETS_FILES:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w") as f:
                toml.dump({"google": {}, "passcodes": {}}, f)

def load_secrets():
    """Load secrets from the first available location."""
    ensure_secrets_files()
    for path in SECRETS_FILES:
        if os.path.exists(path):
            try:
                return toml.load(path)
            except toml.TomlDecodeError:
                print(f"⚠️ ERROR: Could not decode {path}. Check formatting.")
    return {"google": {}, "passcodes": {}}

def save_secrets(new_data):
    """Save secrets to both locations securely."""
    
    # 🔹 1️⃣ Save User’s secrets.toml (No sudo needed)
    with open(USER_SECRETS_FILE, "w") as f:
        toml.dump(new_data, f)
    print(f"✅ Updated secrets in {USER_SECRETS_FILE}")

    # 🔹 2️⃣ Save System secrets.toml (Requires sudo dynamically)
    system_toml_str = toml.dumps(new_data)
    
    try:
        # Use `sudo tee` to write system secrets securely
        process = subprocess.Popen(["sudo", "tee", SYSTEM_SECRETS_FILE], stdin=subprocess.PIPE, text=True)
        process.communicate(input=system_toml_str)
        print(f"✅ Updated secrets in {SYSTEM_SECRETS_FILE} (with sudo)")
    except Exception as e:
        print(f"⚠️ ERROR: Could not write to {SYSTEM_SECRETS_FILE}. Try running with sudo.")
        print(f"Details: {e}")

def add_passcode():
    """Add a new passcode without storing passwords in code."""
    secrets = load_secrets()
    passcodes = secrets["passcodes"]

    user = input("Enter username (e.g., johndoe): ").strip()
    if user in passcodes:
        print("This username already exists. Choose a different name.")
        return

    code = input(f"Enter a passcode for {user}: ").strip()
    max_pages = input(f"Enter max pages allowed for {user} (default 1): ").strip()

    try:
        max_pages = int(max_pages) if max_pages.isdigit() else 1
    except ValueError:
        max_pages = 1

    passcodes[user] = {"code": code, "max_pages": max_pages}
    save_secrets(secrets)
    print(f"✅ Passcode for {user} added successfully.")

def remove_passcode():
    """Remove a passcode safely."""
    secrets = load_secrets()
    passcodes = secrets["passcodes"]

    if not passcodes:
        print("\n⚠️ No passcodes to remove.\n")
        return

    user = input("Enter the username to remove: ").strip()

    if user not in passcodes:
        print("⚠️ Username not found.")
        return

    del passcodes[user]
    save_secrets(secrets)
    print(f"✅ Passcode for {user} removed successfully.")

def main():
    """Passcode Manager Menu"""
    while True:
        print("\nPasscode Manager")
        print("1) View stored passcodes")
        print("2) Add a new passcode")
        print("3) Remove a passcode")
        print("4) Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            print(load_secrets())  # Print current secrets
        elif choice == "2":
            add_passcode()
        elif choice == "3":
            remove_passcode()
        elif choice == "4":
            print("Exiting... Have a great day.")
            break
        else:
            print("⚠️ Invalid option. Please try again.")

if __name__ == "__main__":
    main()