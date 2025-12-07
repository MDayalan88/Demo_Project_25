class TransferJob:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
        self.status = "Pending"

    def start(self):
        self.status = "In Progress"

    def complete(self):
        self.status = "Completed"

    def fail(self):
        self.status = "Failed"