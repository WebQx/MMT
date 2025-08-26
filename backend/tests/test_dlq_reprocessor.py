import json
from dlq_reprocessor import _handle_message, MAX_REPROCESS_ATTEMPTS
from types import SimpleNamespace
from metrics import (
	reprocessor_attempt_total,
	reprocessor_success_total,
	reprocessor_permanent_failure_total,
)


class DummyChannel:
	def __init__(self):
		self.acks = 0

	def basic_ack(self, delivery_tag):  # noqa: D401, ANN001
		self.acks += 1


class DummyMethod:
	delivery_tag = 1


def test_handle_malformed_message(monkeypatch):
	ch = DummyChannel()
	_handle_message(ch, DummyMethod(), None, b"not-json")
	assert ch.acks == 1
	# counter increment verified indirectly by being callable without error
	assert reprocessor_permanent_failure_total._value.get() >= 1  # type: ignore


def test_handle_permanent_failure(monkeypatch):
	# Message exceeding attempts triggers permanent failure
	ch = DummyChannel()
	body = json.dumps({"_dlq_attempts": MAX_REPROCESS_ATTEMPTS + 1}).encode()
	_handle_message(ch, DummyMethod(), None, body)
	assert ch.acks == 1
	assert reprocessor_permanent_failure_total._value.get() >= 1  # type: ignore

