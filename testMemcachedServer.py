import unittest
from memcachedserver import MemcachedServer


class TestMemcachedServer(unittest.TestCase):

    def setUp(self):
        self.memCachedServer = MemcachedServer()

    def testHandleReceivedDataSetFormattingCorrect(self):
        self.assertEqual(self.memCachedServer.expectingDataBlock, False)
        inputMessage = b'set capitalOfChina 14 2400 16\r\n'
        response = self.memCachedServer.handleReceivedData(inputMessage)
        self.assertEqual(self.memCachedServer.expectingDataBlock, True)

    def testSuccessfulSetCommand(self):
        pass

    def testFailedSetCommand(self):
        pass

    def testPoorlyFormattedSetCommand(self):
        pass

    def testSuccessfulGetCommand(self):
        pass

    def testFailedGetCommand(self):
        pass

    def testPoorlyFormattedGetCommand(self):
        pass

    def testSuccessfulDeleteCommand(self):
        pass

    def testFailedDeleteCommand(self):
        pass

    def testPoorlyFormattedDeleteCommand(self):
        pass
