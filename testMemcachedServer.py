import unittest
from unittest.mock import MagicMock, call
from memcachedserver import MemcachedServer
import asyncio
import sqlite3


class TestMemcachedServer(unittest.TestCase):

    # Static variables for response strings
    CLIENT_ERROR_FORMATTING_SET = b'CLIENT_ERROR incorrect # of arguments for set command\r\n'
    CLIENT_ERROR_FORMATTING_SET_NOREPLY = b'CLIENT_ERROR incorrect 6th argument to set command. Expected \'noreply\'\r\n'
    CLIENT_ERROR_FORMATTING_SET_KEY_LENGTH_TOO_LONG = b'CLIENT_ERROR key length of set command exceeds 250 characters\r\n'
    CLIENT_ERROR_FORMATTING_SET_DATA_BLOCK = b'CLIENT_ERROR the data block does not match the # of bytes passed in the set command\r\n'
    CLIENT_ERROR_FORMATTING_SET_NOT_NUMERIC_VALUES = b'CLIENT_ERROR at least one of the <flags> <exptime> <bytes> parameters contained one or more non-digit character\r\n'
    CLIENT_ERROR_FORMATTING_SET_FLAGS_VALUE = b'CLIENT_ERROR the <flags> parameter is greater than the 16 bit unsigned maximum of 65535\r\n'

    CLIENT_ERROR_FORMATTING_GET = b'CLIENT_ERROR incorrect # of arguments for get command\r\n'

    CLIENT_ERROR_FORMATTING_DELETE = b'CLIENT_ERROR incorrect # of arguments for delete command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE_NOREPLY = b'CLIENT_ERROR incorrect 3rd argument to set command. Expected \'noreply\'\r\n'

    SERVER_ERROR_SET_FAILURE = b'SERVER_ERROR error storing data\r\n'
    SERVER_ERROR_GET_FAILURE = b'SERVER_ERROR error retrieving stored data\r\n'
    SERVER_ERROR_DELETE_FAILURE = b'SERVER_ERROR error deleting stored data\r\n'

    SET_SUCCESS = b'STORED\r\n'
    DELETE_SUCCESS = b'DELETED\r\n'

    DELETE_NOT_FOUND = b'NOT FOUND\r\n'

    END = b'END\r\n'

    INSERT_OR_REPLACE_SQL_QUERY = """ INSERT OR REPLACE INTO keysTable(key, flags, bytes, dataBlock) VALUES (?, ?, ?, ?) """
    DELETE_SQL_QUERY = """ DELETE FROM keysTable WHERE key=? """

    TIMEOUT = 60

    def setUp(self):
        self.memCachedServer = MemcachedServer(None)
        self.memCachedServer.transport = lambda: None
        self.memCachedServer.timeout_handle = lambda: None
        self.memCachedServer.sqliteConnection = lambda: None

    def testInit(self):
        runningLoop = lambda: None
        runningLoop.call_later = MagicMock(return_value='timeoutHandle')
        asyncio.get_running_loop = MagicMock(return_value=runningLoop)
        memCachedInstance = MemcachedServer('databasePath')
        self.assertEqual(memCachedInstance.databaseFile, 'databasePath')
        self.assertEqual(memCachedInstance.expectingDataBlock, None)
        self.assertEqual(memCachedInstance.timeout_handle, 'timeoutHandle')
        asyncio.get_running_loop.assert_called()
        runningLoop.call_later.assert_called_with(self.TIMEOUT, memCachedInstance._timeout)

    def testSqliteConnection(self):
        sqlite3.connect = MagicMock(return_value='databaseConnection')
        databaseConnection = self.memCachedServer.create_sqlite_connection()
        self.assertEqual(databaseConnection, 'databaseConnection')
        sqlite3.connect.assert_called_with(None)

    def testConnectionMade(self):
        self.memCachedServer.create_sqlite_connection = MagicMock()
        self.memCachedServer.connection_made('TransportParameter')
        self.assertEqual('TransportParameter', self.memCachedServer.transport)
        self.memCachedServer.create_sqlite_connection.assert_called()

    def testConnectionLost(self):
        self.memCachedServer.transport.close = MagicMock()
        self.memCachedServer.connection_lost(None)
        self.memCachedServer.transport.close.assert_not_called()
        self.memCachedServer.connection_lost(Exception('ConnectionLostError'))
        self.memCachedServer.transport.close.assert_called()

    def testDataReceived(self):
        self.memCachedServer.timeout_handle.cancel = MagicMock()
        self.memCachedServer.handleReceivedData = MagicMock()
        self.memCachedServer.data_received('Data')
        self.memCachedServer.timeout_handle.cancel.assert_called()
        self.memCachedServer.handleReceivedData.assert_called_with('Data')

    def testHandleReceivedDataSetFormattingCorrect(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        inputMessageCorrect = b'set capitalOfChina 14 2400 16\r\n'
        self.memCachedServer.handleReceivedData(inputMessageCorrect)
        self.assertEqual(self.memCachedServer.expectingDataBlock, [b'set', b'capitalOfChina', b'14', b'2400', b'16'])

    def testHandleReceivedDataSetFormattingCorrectNoReply(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        inputMessageCorrect = b'set capitalOfChina 14 2400 16 noreply\r\n'
        self.memCachedServer.handleReceivedData(inputMessageCorrect)
        self.assertEqual(self.memCachedServer.expectingDataBlock, [b'set', b'capitalOfChina', b'14', b'2400', b'16', b'noreply'])

    def testHandleReceivedDataSetFormattingCorrectDataBlockSuccess(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        inputMessageCorrect = b'set capitalOfChina 14 2400 16\r\n'
        self.memCachedServer.setKeyData = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageCorrect)
        self.memCachedServer.setKeyData.assert_not_called()
        self.assertEqual(self.memCachedServer.expectingDataBlock, [b'set', b'capitalOfChina', b'14', b'2400', b'16'])
        dataBlockCorrect = b'hello world!!!!!'
        self.memCachedServer.handleReceivedData(dataBlockCorrect)
        self.memCachedServer.setKeyData.assert_called_with(dataBlockCorrect)

    def testHandleReceivedDataSetFormattingFail(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        inputMessageNoFlag = b'set keyValue 2400 16\r\n'
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageNoFlag)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_SET)

    def testHandleReceivedDataSetFormattingFailNoReply(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        inputMessageNoReplyFail = b'set capitalOfChina 14 2400 16 norely\r\n'
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageNoReplyFail)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_SET_NOREPLY)

    def testHandleReceivedDataSetFormattingFailDigitParameters(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        inputMessageDigitParametersFailures = [
            b'set capitalOfChina 14.0 2400 16\r\n',
            b'set capitalOfChina 14 2400.0 16\r\n',
            b'set capitalOfChina 14 2400 16.0\r\n',
            b'set capitalOfChina -14 2400 16\r\n',
            b'set capitalOfChina 14 -2400 16\r\n',
            b'set capitalOfChina 14 2400 -16\r\n'
        ]
        self.memCachedServer.transport.write = MagicMock()
        for inputMessage in inputMessageDigitParametersFailures:
            self.memCachedServer.handleReceivedData(inputMessage)
            self.assertEqual(self.memCachedServer.expectingDataBlock, None)
            self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_SET_NOT_NUMERIC_VALUES)

    def testHandleReceivedDataSetFormattingFailFlagValue(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        self.memCachedServer.transport.write = MagicMock()
        inputMessageFlagsValueFail = b'set capitalOfChina 67777 2400 16\r\n'
        self.memCachedServer.handleReceivedData(inputMessageFlagsValueFail)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
        self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_SET_FLAGS_VALUE)

    def testHandleReceivedDataGetFormattingCorrect(self):
        inputMessageCorrect = b'get capitalOfChina continentOfLatvia hemisphereOfBrasil'
        self.memCachedServer.getKeyData = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageCorrect)
        self.memCachedServer.getKeyData.assert_called_with([b'get', b'capitalOfChina', b'continentOfLatvia', b'hemisphereOfBrasil'])

    def testHandleReceivedDataGetFormattingFail(self):
        inputMessageFail = b'get'
        self.memCachedServer.getKeyData = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageFail)
        self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_GET)
        self.memCachedServer.getKeyData.assert_not_called()

    def testHandleReceivedDataDeleteFormattingCorrect(self):
        inputMessageCorrect = b'delete capitalOfChina'
        self.memCachedServer.deleteKeyData = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageCorrect)
        self.memCachedServer.transport.write.assert_not_called()
        self.memCachedServer.deleteKeyData.assert_called_with([b'delete', b'capitalOfChina'])

    def testHandleReceivedDataDeleteFormattingCorrectNoReply(self):
        inputMessageCorrect = b'delete capitalOfChina noreply'
        self.memCachedServer.deleteKeyData = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageCorrect)
        self.memCachedServer.transport.write.assert_not_called()
        self.memCachedServer.deleteKeyData.assert_called_with([b'delete', b'capitalOfChina', b'noreply'])

    def testHandleReceivedDataDeleteFormattingFail(self):
        inputMessageFail = b'delete '
        self.memCachedServer.deleteKeyData = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageFail)
        self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_DELETE)
        self.memCachedServer.deleteKeyData.assert_not_called()

    def testHandleReceivedDataDeleteFormattingFailNoReply(self):
        inputMessageFailNoReply = b'delete continentOfLatvia norel'
        self.memCachedServer.deleteKeyData = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.handleReceivedData(inputMessageFailNoReply)
        self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_DELETE_NOREPLY)
        self.memCachedServer.deleteKeyData.assert_not_called()

    def testSetKeyData(self):
        self.memCachedServer.expectingDataBlock = [b'set', b'capitalOfChina', b'14', b'2400', b'16']
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        cursor = lambda: None
        cursor.execute = MagicMock()
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.setKeyData(b'the data block!!\r\n')
        sqlQueryValues = ('capitalOfChina', '14', '16', 'the data block!!')
        cursor.execute.assert_called_with(self.INSERT_OR_REPLACE_SQL_QUERY, sqlQueryValues)
        self.memCachedServer.sqliteConnection.cursor.assert_called()
        self.memCachedServer.sqliteConnection.commit.assert_called()
        self.memCachedServer.transport.write.assert_called_with(self.SET_SUCCESS)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)

    def testSetKeyDataNoReply(self):
        self.memCachedServer.expectingDataBlock = [b'set', b'capitalOfChina', b'14', b'2400', b'16', b'noreply']
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        cursor = lambda: None
        cursor.execute = MagicMock()
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.setKeyData(b'the data block!!\r\n')
        sqlQueryValues = ('capitalOfChina', '14', '16', 'the data block!!')
        cursor.execute.assert_called_with(self.INSERT_OR_REPLACE_SQL_QUERY, sqlQueryValues)
        self.memCachedServer.sqliteConnection.cursor.assert_called()
        self.memCachedServer.sqliteConnection.commit.assert_called()
        self.memCachedServer.transport.write.assert_not_called()
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)

    def testSetKeyDataStorageError(self):
        self.memCachedServer.expectingDataBlock = [b'set', b'capitalOfChina', b'14', b'2400', b'16']
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        cursor = lambda: None
        cursor.execute = lambda x, y: 1/0
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.setKeyData(b'the data block!!\r\n')
        self.memCachedServer.sqliteConnection.commit.assert_not_called()
        self.memCachedServer.transport.write.assert_called_with(self.SERVER_ERROR_SET_FAILURE)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)

    def testSetKeyDataIncorrectDataBlockLength(self):
        self.memCachedServer.expectingDataBlock = [b'set', b'capitalOfChina', b'14', b'2400', b'16']
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        cursor = lambda: None
        cursor.execute = MagicMock()
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.setKeyData(b'the data block\r\n')
        cursor.execute.assert_not_called()
        self.memCachedServer.sqliteConnection.cursor.assert_not_called()
        self.memCachedServer.sqliteConnection.commit.assert_not_called()
        self.memCachedServer.transport.write.assert_called_with(self.CLIENT_ERROR_FORMATTING_SET_DATA_BLOCK)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)


    def testGetKeyData(self):
        selectQueryString = """ SELECT * FROM keysTable WHERE key IN (?,?,?) """
        self.memCachedServer.transport.write = MagicMock()
        cursor = lambda: None
        cursor.execute = MagicMock()
        cursor.fetchall = MagicMock(return_value=[('manchesterUnited', 1, 7, 'Ronaldo'),('capitalOfChina', 2, 7, 'Beijing'),('biggestOcean', 4, 7, 'Pacific')])
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.getKeyData([b'get', b'manchesterUnited', b'capitalOfChina', b'biggestOcean'])
        sqlQueryValues = ('manchesterUnited', 'capitalOfChina', 'biggestOcean')
        self.memCachedServer.sqliteConnection.cursor.assert_called()
        cursor.execute.assert_called_with(selectQueryString, sqlQueryValues)
        cursor.fetchall.assert_called()
        writeCalls = [
            call(b'VALUE manchesterUnited 1 7\r\n'),
            call(b'Ronaldo\r\n'),
            call(b'VALUE capitalOfChina 2 7\r\n'),
            call(b'Beijing\r\n'),
            call(b'VALUE biggestOcean 4 7\r\n'),
            call(b'Pacific\r\n'),
            call(b'END\r\n')
        ]
        self.assertEqual(self.memCachedServer.transport.write.mock_calls, writeCalls)


    def testGetKeyDataStorageError(self):
        self.memCachedServer.transport.write = MagicMock()
        cursor = lambda: None
        cursor.execute = lambda x, y: 1/0
        cursor.fetchall = MagicMock(return_value=[('manchesterUnited', 1, 7, 'Ronaldo'),('capitalOfChina', 2, 7, 'Beijing'),('biggestOcean', 4, 7, 'Pacific')])
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.getKeyData([b'get', b'manchesterUnited', b'capitalOfChina', b'biggestOcean'])
        self.memCachedServer.sqliteConnection.cursor.assert_called()
        cursor.fetchall.assert_not_called()
        self.memCachedServer.transport.write.assert_called_with(self.SERVER_ERROR_GET_FAILURE)

    def testDeleteKeyDataKeyFound(self):
        deleteQuery = self.DELETE_SQL_QUERY
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        cursor = lambda: None
        cursor.execute = MagicMock()
        cursor.rowcount = 1
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.deleteKeyData([b'delete', b'manchesterUnited'])
        sqlQueryValue = ('manchesterUnited',)
        cursor.execute.assert_called_with(deleteQuery, sqlQueryValue)
        self.memCachedServer.sqliteConnection.commit.assert_called()
        self.memCachedServer.transport.write.assert_called_with(self.DELETE_SUCCESS)

    def testDeleteKeyDataKeyNotFound(self):
        deleteQuery = self.DELETE_SQL_QUERY
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        cursor = lambda: None
        cursor.execute = MagicMock()
        cursor.rowcount = 0
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.deleteKeyData([b'delete', b'manchesterUnited'])
        sqlQueryValue = ('manchesterUnited',)
        cursor.execute.assert_called_with(deleteQuery, sqlQueryValue)
        self.memCachedServer.sqliteConnection.commit.assert_called()
        self.memCachedServer.transport.write.assert_called_with(self.DELETE_NOT_FOUND)

    def testDeleteKeyDataNoReply(self):
        deleteQuery = self.DELETE_SQL_QUERY
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        cursor = lambda: None
        cursor.execute = MagicMock()
        cursor.rowcount = 0
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.deleteKeyData([b'delete', b'manchesterUnited', b'noreply'])
        sqlQueryValue = ('manchesterUnited',)
        cursor.execute.assert_called_with(deleteQuery, sqlQueryValue)
        self.memCachedServer.sqliteConnection.commit.assert_called()
        self.memCachedServer.transport.write.assert_not_called()

    def testDeleteKeyStorageError(self):
        self.memCachedServer.transport.write = MagicMock()
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        cursor = lambda: None
        cursor.execute = lambda x, y: 1/0
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.deleteKeyData([b'delete', b'manchesterUnited', b'noreply'])
        self.memCachedServer.sqliteConnection.cursor.assert_called()
        self.memCachedServer.sqliteConnection.commit.assert_not_called()
        self.memCachedServer.transport.write.assert_called_with(self.SERVER_ERROR_DELETE_FAILURE)
