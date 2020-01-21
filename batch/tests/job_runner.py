import uuid


class DummyJobRunner:
    def run(self, *args, **kwargs):
        return uuid.uuid4().hex
