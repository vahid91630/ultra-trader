from cryptography.fernet import Fernet
import json

def decrypt_binance_key(json_path="binance_secure.json", key_path="encryption.key"):
    with open(key_path, "rb") as k:
        key = k.read()
    cipher = Fernet(key)
    with open(json_path, "r") as f:
        enc = json.load(f)
    token = cipher.decrypt(enc["encrypted_key"].encode()).decode()
    return token
