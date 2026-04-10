#!/usr/bin/env python3
"""
Setup script for PrudentSigma Dashboard authentication credentials
This script hashes passwords and creates the config.yaml file
"""
import yaml
from streamlit_authenticator.utilities.hasher import Hasher

def setup_credentials():
    """Setup credentials with default passwords (user should change asap)"""
    print("\n" + "="*60)
    print("PrudentSigma Dashboard - Credential Setup")
    print("="*60 + "\n")
    
    # Default credentials - USER SHOULD CHANGE THESE
    default_passwords = {
        'admin': 'admin123',
        'trader': 'trader123'
    }
    
    credentials = {}
    users = {
        'admin': {
            'email': 'admin@prudentsigma.com',
            'name': 'Administrator'
        },
        'trader': {
            'email': 'trader@prudentsigma.com', 
            'name': 'Trader'
        }
    }
    
    print("Creating default credentials (CHANGE THESE AFTER LOGIN!)\n")
    
    for username, user_info in users.items():
        password = default_passwords[username]
        
        # Hash the password
        hasher = Hasher()
        hashed_password = hasher.hash(password)
        
        credentials[username] = {
            'email': user_info['email'],
            'name': user_info['name'],
            'password': hashed_password
        }
        print("[OK] {:10} | password: {}".format(username, password))
    
    # Create config
    config = {
        'credentials': {
            'usernames': credentials
        },
        'cookie': {
            'expiry_days': 30,
            'key': 'prudentsigma_dashboard_key',
            'name': 'prudentsigma_auth'
        },
        'preauthorized': {
            'emails': []
        }
    }
    
    # Save to config.yaml
    try:
        with open('config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
        print("\n" + "="*60)
        print("[OK] Credentials saved to config.yaml")
        print("="*60)
        print("\nWARNING: Default passwords are for testing only!")
        print("Change them immediately after first login.")
        return True
    except Exception as e:
        print("\n[ERROR] Error saving config: {}".format(e))
        return False

if __name__ == "__main__":
    setup_credentials()
