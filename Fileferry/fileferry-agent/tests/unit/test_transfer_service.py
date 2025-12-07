from unittest import TestCase
from src.services.transfer_service import TransferService

class TestTransferService(TestCase):
    def setUp(self):
        self.transfer_service = TransferService()

    def test_start_transfer_job(self):
        # Test starting a transfer job
        job = self.transfer_service.start_transfer_job(source='source_path', destination='destination_path')
        self.assertIsNotNone(job)
        self.assertEqual(job.source, 'source_path')
        self.assertEqual(job.destination, 'destination_path')

    def test_monitor_transfer_job(self):
        # Test monitoring a transfer job
        job = self.transfer_service.start_transfer_job(source='source_path', destination='destination_path')
        self.transfer_service.monitor_transfer_job(job.id)
        self.assertIn(job.status, ['in_progress', 'completed', 'failed'])

    def test_transfer_job_failure(self):
        # Test handling of a failed transfer job
        job = self.transfer_service.start_transfer_job(source='invalid_path', destination='destination_path')
        self.transfer_service.monitor_transfer_job(job.id)
        self.assertEqual(job.status, 'failed')

    def tearDown(self):
        # Clean up any resources if necessary
        pass