import json
import os
import sys
from opentelemetry import trace
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # ensure backend root in path
from rabbitmq_utils import send_to_rabbitmq  # noqa: E402

# This is a lightweight test that ensures publish embeds trace headers and consume extracts them.
# It assumes the consumer callback is instrumented; here we focus on injection path only (unit-level).

def test_trace_context_injection_headers(monkeypatch):
    captured_headers = {}
    def fake_basic_publish(channel, exchange, routing_key, body, properties, mandatory=False):  # signature mimic
        return True
    # Intercept inject to capture carrier
    def fake_inject(carrier):
        nonlocal captured_headers
        # simulate real injector by adding a traceparent with current span context
        from opentelemetry import trace as _t
        ctx = _t.get_current_span().get_span_context()
        trace_id_hex = f"{ctx.trace_id:032x}"
        span_id_hex = f"{ctx.span_id:016x}"
        carrier['traceparent'] = f"00-{trace_id_hex}-{span_id_hex}-01"
        captured_headers = carrier.copy()
        return carrier
        return True
    # Monkeypatch pika BlockingConnection channel.basic_publish indirectly.
    class DummyChannel:
        def queue_declare(self, queue, durable=True):
            return True
        def basic_publish(self, exchange, routing_key, body, properties, mandatory=False):
            return fake_basic_publish(self, exchange, routing_key, body, properties)
    class DummyConnection:
        def channel(self):
            return DummyChannel()
        def close(self):
            return True
    class DummyParams: ...
    # Patch pika objects referenced inside rabbitmq_utils
    monkeypatch.setattr('pika.BlockingConnection', lambda params: DummyConnection())
    monkeypatch.setattr('pika.URLParameters', lambda url: 'dummy')
    monkeypatch.setattr('rabbitmq_utils.inject', fake_inject)
    class DummyProps:
        def __init__(self, delivery_mode=2, headers=None):
            self.delivery_mode = delivery_mode
            self.headers = headers or {}
    monkeypatch.setattr('pika.BasicProperties', DummyProps)

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("test-publish-span") as span:
        send_to_rabbitmq("test_queue", {"foo": "bar"})
        assert captured_headers, "Headers should be captured"
        # W3C traceparent should exist
        assert 'traceparent' in captured_headers
        traceparent = captured_headers['traceparent']
        # Format: version-traceid-spanid-flags
        parts = traceparent.split('-')
        assert len(parts) == 4
        injected_trace_id = parts[1]
        assert span.get_span_context().trace_id == int(injected_trace_id, 16)
