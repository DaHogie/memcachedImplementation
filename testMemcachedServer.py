import unittest
from unittest.mock import MagicMock
from memcachedserver import MemcachedServer
import asyncio
import sqlite3


class TestMemcachedServer(unittest.TestCase):

    # Static variables for response strings
    CLIENT_ERROR_FORMATTING_SET = b'CLIENT_ERROR incorrect # of arguments for set command\r\n'
    CLIENT_ERROR_FORMATTING_SET_NOREPLY = b'CLIENT_ERROR incorrect 6th argument to set command. Expected \'noreply\'\r\n'
    CLIENT_ERROR_FORMATTING_GET = b'CLIENT_ERROR incorrect # of arguments for get command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE = b'CLIENT_ERROR incorrect # of arguments for delete command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE_NOREPLY = b'CLIENT_ERROR incorrect 3rd argument to set command. Expected \'noreply\'\r\n'

    INSERT_OR_REPLACE_SQL_QUERY = """ INSERT OR REPLACE INTO keysTable(key, flags, bytes, dataBlock) VALUES (?, ?, ?, ?) """

    SET_SUCCESS = b'STORED\r\n'

    TIMEOUT = 10

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
        self.memCachedServer.setKeyData(b'the data block\r\n')
        sqlQueryValues = ('capitalOfChina', '14', '16', 'the data block')
        cursor.execute.assert_called_with(self.INSERT_OR_REPLACE_SQL_QUERY, sqlQueryValues)
        self.memCachedServer.sqliteConnection.commit.assert_called()
        self.memCachedServer.transport.write.assert_called_with(self.SET_SUCCESS)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)

    def testSetKeyDataStorageError(self):
        self.memCachedServer.expectingDataBlock = [b'set', b'capitalOfChina', b'14', b'2400', b'16']
        self.memCachedServer.sqliteConnection.commit = MagicMock()
        self.memCachedServer.transport.write = MagicMock()
        cursor = lambda: None
        cursor.execute = lambda x, y: 1/0
        self.memCachedServer.sqliteConnection.cursor = MagicMock(return_value=cursor)
        self.memCachedServer.setKeyData(b'the data block\r\n')
        sqlQueryValues = ('capitalOfChina', '14', '16', 'the data block')
        self.memCachedServer.sqliteConnection.commit.assert_not_called()
        self.memCachedServer.transport.write.assert_called_with(self.memCachedServer.SERVER_ERROR_SET_FAILURE)
        self.assertEqual(self.memCachedServer.expectingDataBlock, None)
