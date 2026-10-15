"""Exercise original storage behavior without SDKs, Tk, hardware, or network."""
import importlib
from decimal import Decimal
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import MagicMock, Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Final_Project'))
import config
import dynamoDB

# These tests use Table's storage/controller functions, never create widgets.
# Stub Tk imports so a Python without the optional Tk extension can run them.
tk_stub = types.ModuleType('tkinter')
tk_stub.ttk = types.ModuleType('tkinter.ttk')
with patch.dict(sys.modules, {'tkinter': tk_stub, 'tkinter.ttk': tk_stub.ttk}):
    import tableClass


class DataOperationTests(unittest.TestCase):
    def test_fetch_scans_all_pages_and_uses_requested_table(self):
        resource = Mock()
        table = resource.Table.return_value
        table.scan.side_effect = [
            {'Items': [{'Question': 'one'}], 'LastEvaluatedKey': {'dateSubmitted': 'first'}},
            {'Items': [{'Question': 'two'}]},
        ]
        with patch.object(config, 'dynamodb_resource', return_value=resource):
            self.assertEqual(tableClass.fetch_dynamodb_data('offline-table'),
                             [{'Question': 'one'}, {'Question': 'two'}])
        resource.Table.assert_called_once_with('offline-table')
        self.assertEqual(table.scan.call_args_list, [call(), call(ExclusiveStartKey={'dateSubmitted': 'first'})])

    def test_fetch_empty_table(self):
        resource = Mock()
        resource.Table.return_value.scan.return_value = {'Items': []}
        with patch.object(config, 'dynamodb_resource', return_value=resource):
            self.assertEqual(tableClass.fetch_dynamodb_data('empty'), [])

    def test_filter_is_case_insensitive_substring(self):
        view = Mock()
        items = [{'Question': 'Tell me about yourself'}, {'Question': 'Why this role?'}]
        with patch.object(tableClass, 'fetch_dynamodb_data', return_value=items) as fetch:
            tableClass.filter_by_question(view, 'ABOUT')
            view.populate_table.assert_called_once_with([items[0]])
            fetch.assert_called_once_with(config.DYNAMODB_TABLE)
            tableClass.filter_by_question(view, '')
            view.populate_table.assert_called_with(items)

    def test_add_and_edit_preserve_storage_fields(self):
        table, view = Mock(), Mock()
        expected = dict(dateSubmitted='2026-01-01', Feedback='practice feedback', Question='Why?',
                        Happy='0.4', Neutral='0.3', **{'Other Emotions': '0.3'})
        for edit in (False, True):
            with self.subTest(edit=edit):
                table.reset_mock(); view.reset_mock()
                tableClass.submit_new_entry('row1', edit, '2026-01-01', 'practice feedback',
                                            'Why?', '0.4', '0.3', '0.3', table, view)
                table.put_item.assert_called_once_with(Item=expected)
                if edit:
                    view.edit_row.assert_called_once_with(row_id='row1', new_data=expected)
                    view.add_row.assert_not_called()
                else:
                    view.add_row.assert_called_once_with(expected)
                    view.edit_row.assert_not_called()

    def test_delete_only_checked_rows(self):
        table, view = Mock(), Mock()
        view.get_checked_items.return_value = {'yes': True, 'no': False}
        view.get_row_data.return_value = ['☑', '2026-01-01']
        tableClass.delete_entries(view, table)
        table.delete_item.assert_called_once_with(Key={'dateSubmitted': '2026-01-01'})
        view.delete_from_checked_items.assert_called_once_with('yes')
        view.remove_row.assert_called_once_with('yes')

    def test_write_failure_does_not_update_view(self):
        table, view = Mock(), Mock()
        table.put_item.side_effect = RuntimeError('offline failure')
        with self.assertRaises(RuntimeError):
            tableClass.submit_new_entry('row', False, 'date', 'feedback', 'question', '0', '0', '0', table, view)
        view.add_row.assert_not_called()

    def test_original_demo_score_decimal_ratios(self):
        resource = Mock()
        with patch.object(config, 'dynamodb_resource', return_value=resource):
            dynamoDB.get_dynamodb_headers('offline-table')
        item = resource.Table.return_value.put_item.call_args.kwargs['Item']
        self.assertEqual(item['Question'], dynamoDB.question)
        self.assertEqual(item['Feedback'], dynamoDB.out)
        self.assertEqual(item['Happy'], Decimal('0.346'))
        self.assertEqual(item['Neutral'], Decimal('0.154'))
        self.assertEqual(item['Other Emotions'], Decimal('0.5'))

    def test_mongo_import_has_no_query_side_effect(self):
        fake_pymongo, fake_pandas = MagicMock(), MagicMock()
        with patch.dict(sys.modules, {'pymongo': fake_pymongo, 'pandas': fake_pandas}):
            sys.modules.pop('mongoDB', None)
            mongo = importlib.import_module('mongoDB')
            fake_pymongo.MongoClient.assert_not_called()
            mongo.loadMongo()
            fake_pandas.read_csv.assert_called_once_with(config.asset_path('questions.csv'))
            fake_pymongo.MongoClient.assert_called_once_with(config.MONGODB_URI)
            database = fake_pymongo.MongoClient.return_value.__getitem__.return_value
            database.questions.insert_many.assert_called_once_with(
                fake_pandas.read_csv.return_value.to_dict.return_value)
