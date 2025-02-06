import os
import toml

# 🔹 Explicit Path to Streamlit Secrets File
SECRETS_FILE = ".streamlit/secrets.toml"

def ensure_secrets_file():
    """Ensure that secrets.toml exists and has the correct structure."""
    if not os.path.exists(SECRETS_FILE):
        os.makedirs(".streamlit", exist_ok=True)
        with open(SECRETS_FILE, "w") as f:
            toml.dump({"google": {}, "passcodes": {}}, f)

def load_secrets():
    """Load the entire secrets file, ensuring both [google] and [passcodes] exist."""
    ensure_secrets_file()
    try:
        data = toml.load(SECRETS_FILE)
        if "passcodes" not in data:
            data["passcodes"] = {}
        if "google" not in data:
            data["google"] = {}
        return data
    except toml.TomlDecodeError:
        print("⚠️ ERROR: Could not decode secrets.toml. Check for formatting issues.")
        return {"google": {}, "passcodes": {}}

def save_secrets(data):
    """Save the entire secrets file, preserving all keys."""
    with open(SECRETS_FILE, "w") as f:
        toml.dump(data, f)

def display_secrets():
    """Display all stored secrets, including the API key and passcodes."""
    secrets = load_secrets()

    print("\nStored Secrets:")
    print("=" * 50)
    print("[google]")
    for key, value in secrets.get("google", {}).items():
        print(f"{key} = {value}")

    print("\n[passcodes]")
    for user, code in secrets.get("passcodes", {}).items():
        print(f"{user} = {code}")
    print("=" * 50, "\n")

def add_passcode():
    """Add a new passcode with a username."""
    secrets = load_secrets()
    passcodes = secrets["passcodes"]

    user = input("Enter username (e.g., johndoe): ").strip()
    if user in passcodes:
        print("This username already exists. Choose a different name.")
        return

    code = input(f"Enter a passcode for {user}: ").strip()
    passcodes[user] = code

    save_secrets(secrets)
    print(f"✅ Passcode for {user} added successfully.\n")

def remove_passcode():
    """Remove a passcode by username."""
    secrets = load_secrets()
    passcodes = secrets["passcodes"]

    if not passcodes:
        print("\n⚠️ No passcodes to remove.\n")
        return

    display_secrets()
    user = input("Enter the username to remove: ").strip()

    if user not in passcodes:
        print("⚠️ Username not found.")
        return

    del passcodes[user]
    save_secrets(secrets)
    print(f"✅ Passcode for {user} removed successfully.\n")

def main():
    """Passcode Manager Menu"""
    while True:
        print("\nPasscode Manager")
        print("1) View stored secrets (API + Passcodes)")
        print("2) Add a new passcode")
        print("3) Remove a passcode")
        print("4) Exit")

        choice = input("\nSelect an option: ").strip()

        if choice == "1":
            display_secrets()
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