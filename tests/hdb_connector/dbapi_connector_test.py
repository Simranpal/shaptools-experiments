"""
Unitary tests for hdb_connector/connector/dbapi_connector.py.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-05-14
"""

# pylint:disable=C0103,C0111,W0212,W0611

import os
import sys
import logging
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from unittest import mock
except ImportError:
    import mock


class DbapiException(Exception):
    """
    dbapi.Error mock exception
    """


class TestDbapiConnector(unittest.TestCase):
    """
    Unitary tests for dbapi_connector.py.
    """

    @classmethod
    def setUpClass(cls):
        """
        Global setUp.
        """

        logging.basicConfig(level=logging.INFO)
        sys.modules['hdbcli'] = mock.Mock()
        from shaptools.hdb_connector.connectors import dbapi_connector
        cls._dbapi_connector = dbapi_connector

    def setUp(self):
        """
        Test setUp.
        """
        self._conn = self._dbapi_connector.DbapiConnector()

    def tearDown(self):
        """
        Test tearDown.
        """

    @classmethod
    def tearDownClass(cls):
        """
        Global tearDown.
        """
        sys.modules.pop('hdbcli')

    @mock.patch('shaptools.hdb_connector.connectors.dbapi_connector.dbapi')
    @mock.patch('logging.Logger.info')
    def test_connect(self, mock_logger, mock_dbapi):
        self._conn.connect('host', 1234, user='user', password='pass')
        mock_dbapi.connect.assert_called_once_with(
            address='host', port=1234, user='user', password='pass')
        mock_logger.assert_has_calls([
            mock.call('connecting to SAP HANA database at %s:%s', 'host', 1234),
            mock.call('connected successfully')
        ])

    @mock.patch('shaptools.hdb_connector.connectors.dbapi_connector.dbapi')
    @mock.patch('logging.Logger.info')
    def test_connect_error(self, mock_logger, mock_dbapi):
        mock_dbapi.Error = DbapiException
        mock_dbapi.connect.side_effect = DbapiException('error')
        with self.assertRaises(self._dbapi_connector.base_connector.ConnectionError) as err:
            self._conn.connect('host', 1234, user='user', password='pass')

        self.assertTrue('connection failed: {}'.format('error') in str(err.exception))
        mock_dbapi.connect.assert_called_once_with(
            address='host', port=1234, user='user', password='pass')

        mock_logger.assert_called_once_with(
            'connecting to SAP HANA database at %s:%s', 'host', 1234)

    @mock.patch('shaptools.hdb_connector.connectors.base_connector.QueryResult')
    @mock.patch('logging.Logger.info')
    def test_query(self, mock_logger, mock_result):
        cursor_mock_instance = mock.Mock()
        cursor_mock = mock.Mock(return_value=cursor_mock_instance)
        mock_result_inst = mock.Mock()
        mock_result_inst.records = ['data1', 'data2']
        mock_result_inst.metadata = 'metadata'
        mock_result.load_cursor.return_value = mock_result_inst
        context_manager_mock = mock.Mock(
            __enter__ = cursor_mock,
            __exit__ = mock.Mock()
        )
        self._conn._connection = mock.Mock()
        self._conn._connection.cursor.return_value = context_manager_mock

        result = self._conn.query('query')

        cursor_mock_instance.execute.assert_called_once_with('query')
        mock_result.load_cursor.assert_called_once_with(cursor_mock_instance)

        self.assertEqual(result.records, ['data1', 'data2'])
        self.assertEqual(result.metadata, 'metadata')
        mock_logger.assert_called_once_with('executing sql query: %s', 'query')

    @mock.patch('shaptools.hdb_connector.connectors.dbapi_connector.dbapi')
    @mock.patch('logging.Logger.info')
    def test_query_error(self, mock_logger, mock_dbapi):
        mock_dbapi.Error = DbapiException
        self._conn._connection = mock.Mock()
        self._conn._connection.cursor.side_effect = DbapiException('error')
        with self.assertRaises(self._dbapi_connector.base_connector.QueryError) as err:
            self._conn.query('query')

        self.assertTrue('query failed: {}'.format('error') in str(err.exception))
        self._conn._connection.cursor.assert_called_once_with()
        mock_logger.assert_called_once_with('executing sql query: %s', 'query')

    @mock.patch('logging.Logger.info')
    def test_disconnect(self, mock_logger):
        self._conn._connection = mock.Mock()
        self._conn.disconnect()
        self._conn._connection.close.assert_called_once_with()
        mock_logger.assert_has_calls([
            mock.call('disconnecting from SAP HANA database'),
            mock.call('disconnected successfully')
        ])
