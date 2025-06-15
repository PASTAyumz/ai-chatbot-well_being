import os

# Create required directories
REQUIRED_DIRS = [
    'config',
    'data',
    'logs',
    'conversations'
]

for directory in REQUIRED_DIRS:
    dir_path = os.path.join(os.path.dirname(__file__), '..', directory)
    os.makedirs(dir_path, exist_ok=True)