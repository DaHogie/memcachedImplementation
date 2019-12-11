import unittest
from unittest.mock import MagicMock
from memcachedserver import MemcachedServer


class TestMemcachedServer(unittest.TestCase):

    # Static variables for response strings
    CLIENT_ERROR_FORMATTING_SET = b'CLIENT_ERROR incorrect # of arguments for set command\r\n'
    CLIENT_ERROR_FORMATTING_SET_NOREPLY = b'CLIENT_ERROR incorrect 6th argument to set command. Expected \'noreply\'\r\n'
    CLIENT_ERROR_FORMATTING_GET = b'CLIENT_ERROR incorrect # of arguments for get command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE = b'CLIENT_ERROR incorrect # of arguments for delete command\r\n'
    CLIENT_ERROR_FORMATTING_DELETE_NOREPLY = b'CLIENT_ERROR incorrect 3rd argument to set command. Expected \'noreply\'\r\n'

    def setUp(self):
        self.memCachedServer = MemcachedServer()
        self.memCachedServer.transport = lambda: None
        self.memCachedServer.transport.write = lambda y: None

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
