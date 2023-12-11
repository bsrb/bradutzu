from dotenv import load_dotenv
import hashlib
import os
import sys

if len(sys.argv) != 2:
    print(f'Usage: {sys.argv[0]} <username>')
    sys.exit(1)

load_dotenv(os.path.join('flask_app', '.env'))
secret = os.environ.get('REGISTER_SECRET')
if secret is None:
    print(f'REGISTER_SECRET is not set')
    sys.exit(1)
hash = hashlib.sha256(f'{sys.argv[1]}{secret}'.encode('utf-8')).hexdigest()
print(f'Invite code for {sys.argv[1]}: {hash}')