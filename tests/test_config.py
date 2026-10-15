import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Final_Project'))
import config


class ConfigurationTests(unittest.TestCase):
    def test_defaults_and_overrides(self):
        with patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            self.assertEqual(config.AWS_REGION, 'us-east-1')
            self.assertEqual(config.camera_index(), 0)
        with patch.dict(os.environ, {'AWS_REGION': 'test-region', 'DYNAMODB_TABLE': 'test-scores',
                                     'MONGODB_DATABASE': 'test-questions', 'CAMERA_INDEX': '2'}, clear=True):
            importlib.reload(config)
            self.assertEqual(config.AWS_REGION, 'test-region')
            self.assertEqual(config.DYNAMODB_TABLE, 'test-scores')
            self.assertEqual(config.MONGODB_DATABASE, 'test-questions')
            self.assertEqual(config.camera_index(), 2)
        importlib.reload(config)

    def test_invalid_camera_setting_does_not_block_database_import(self):
        for value in ('', 'not-an-integer'):
            with self.subTest(value=value), patch.dict(os.environ, {'CAMERA_INDEX': value}, clear=True):
                # Reproduce a database-only import with bad camera configuration.
                importlib.reload(config)
                import dynamoDB
                importlib.reload(dynamoDB)
                self.assertEqual(config.DYNAMODB_TABLE, 'user_scores')
                # Validation still fails clearly when a camera is actually requested.
                with self.assertRaisesRegex(ValueError, 'CAMERA_INDEX must be an integer'):
                    config.camera_index()

    def test_assets_resolve_from_module(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path.cwd()
            try:
                os.chdir(directory)
                self.assertTrue(config.asset_path('questions.csv').is_file())
                self.assertTrue(config.asset_path('logo.ppm').is_file())
            finally:
                os.chdir(old)

    def test_vosk_requires_local_directory(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'VOSK_MODEL_PATH'):
                config.vosk_model_path()
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'VOSK_MODEL_PATH': directory}):
                self.assertEqual(config.vosk_model_path(), Path(directory).resolve())
            with patch.dict(os.environ, {'VOSK_MODEL_PATH': str(Path(directory) / 'missing')}):
                with self.assertRaisesRegex(ValueError, 'existing directory'):
                    config.vosk_model_path()

    def test_openai_requires_key_and_passes_only_synthetic_value(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'OPENAI_API_KEY'):
                config.openai_client()
        fake = Mock()
        with patch.dict(sys.modules, {'openai': fake}), patch.dict(
                os.environ, {'OPENAI_API_KEY': 'offline-test-placeholder'}, clear=True):
            self.assertIs(config.openai_client(), fake.OpenAI.return_value)
        fake.OpenAI.assert_called_once_with(api_key='offline-test-placeholder')

    def test_aws_uses_default_credential_chain(self):
        fake = Mock()
        with patch.dict(sys.modules, {'boto3': fake}):
            self.assertIs(config.dynamodb_resource(), fake.resource.return_value)
        fake.resource.assert_called_once_with('dynamodb', region_name=config.AWS_REGION)
