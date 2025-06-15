import json
import os
from typing import Dict
from pathlib import Path
import sys

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def print_assistant(msg: str):
    print(f"{Colors.BLUE}Assistant:{Colors.END} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}Error:{Colors.END} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}Warning:{Colors.END} {msg}") 

def load_config() -> Dict:
    """Load configuration from config file"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load config: {str(e)}")