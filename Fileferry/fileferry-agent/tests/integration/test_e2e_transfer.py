from unittest import TestCase
from src.handlers.transfer_handler import TransferHandler
from src.models.transfer_job import TransferJob

class TestE2ETransfer(TestCase):
    def setUp(self):
        self.transfer_handler = TransferHandler()
        self.transfer_job = TransferJob(source='source_path', destination='destination_path')

    def test_file_transfer(self):
        # Initiate the transfer
        result = self.transfer_handler.initiate_transfer(self.transfer_job)
        self.assertTrue(result['success'], "Transfer should be successful")

        # Check if the file exists at the destination
        file_exists = self.transfer_handler.check_file_exists(self.transfer_job.destination)
        self.assertTrue(file_exists, "File should exist at the destination")

    def test_transfer_completion(self):
        # Complete the transfer
        self.transfer_handler.complete_transfer(self.transfer_job)
        self.assertEqual(self.transfer_job.status, 'completed', "Transfer job status should be completed")

    def tearDown(self):
        # Clean up any resources or reset states if necessary
        self.transfer_handler.cleanup(self.transfer_job)