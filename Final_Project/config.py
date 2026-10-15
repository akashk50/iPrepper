"""Local configuration shared by the original class-project scripts.

Importing this module does not initialize clients or contact services.
"""
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'dsci351-project')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'user_scores')
AWS_REGION = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo-0125')


def camera_index():
    """Validate device configuration only when a camera is requested."""
    try:
        return int(os.environ.get('CAMERA_INDEX', '0'))
    except ValueError:
        raise ValueError('CAMERA_INDEX must be an integer (for example, 0).') from None


def asset_path(filename):
    """Resolve bundled assets independently of the working directory."""
    return PROJECT_DIR / filename


def vosk_model_path():
    value = os.environ.get('VOSK_MODEL_PATH')
    if not value:
        raise ValueError('Set VOSK_MODEL_PATH to an unpacked Vosk model directory.')
    path = Path(value).expanduser().resolve()
    if not path.is_dir():
        raise ValueError('VOSK_MODEL_PATH must point to an existing directory.')
    return path


def openai_client():
    value = os.environ.get('OPENAI_API_KEY')
    if not value or not value.strip():
        raise ValueError('Set OPENAI_API_KEY before launching iPrepper.')
    from openai import OpenAI
    return OpenAI(api_key=value)


def dynamodb_resource():
    """Use boto3's standard environment/profile credential chain."""
    import boto3
    return boto3.resource('dynamodb', region_name=AWS_REGION)
