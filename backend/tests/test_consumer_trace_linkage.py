import json
import os
import sys
import threading
import time
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import inject, extract
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Import consumer callback logic - assume it's encapsulated in openemr_consumer module
import openemr_consumer  # type: ignore

# We'll simulate publish, then directly invoke consumer callback with properties containing headers.

class DummyProps:
    def __init__(self, headers):
        self.headers = headers

class DummyMethod:
    def __init__(self):
        self.delivery_tag = 1

class DummyChannel:
    def basic_ack(self, delivery_tag):
        pass

span_exporter = InMemorySpanExporter()
provider = TracerProvider(resource=Resource.create({"service.name": "test"}))
provider.add_span_processor(SimpleSpanProcessor(span_exporter))
trace.set_tracer_provider(provider)

def test_consumer_parent_span_linkage(monkeypatch):
    tracer = trace.get_tracer(__name__)

    # Monkeypatch ack and any external calls inside consumer (FHIR, DB) to no-op quickly
    monkeypatch.setattr('openemr_consumer._check_duplicate', lambda *a, **k: False, raising=False)
    monkeypatch.setattr('openemr_consumer.store_transcript', lambda **k: 1, raising=False)
    monkeypatch.setattr('openemr_consumer.extract_entities', lambda text: type('E',(),{'to_dict':lambda self: {}})(), raising=False)
    monkeypatch.setattr('openemr_consumer.summarize_text', lambda text: 'summary', raising=False)
    monkeypatch.setattr('openemr_consumer.store_transcript_payload', lambda **k: None, raising=False)

    # Capture spans
    with tracer.start_as_current_span("publish-root") as parent_span:
        carrier: Dict[str, str] = {}
        inject(carrier)
        # Build message like publisher would
        body = json.dumps({"transcript_id": "abc123", "text": "hello", "filename": "f.wav"}).encode()
        props = DummyProps(headers=carrier)
        method = DummyMethod()
        ch = DummyChannel()
        # directly invoke consumer callback
        openemr_consumer.callback(ch, method, properties=props, body=body)  # type: ignore

    spans = span_exporter.get_finished_spans()
    # find consume span
    consume_spans = [s for s in spans if s.name == 'consume_message']
    assert consume_spans, 'consume_message span not found'
    consume_span = consume_spans[-1]
    # Its trace id should match publish parent span trace id
    assert consume_span.context.trace_id == parent_span.get_span_context().trace_id
    # And it should not be the same span id
    assert consume_span.context.span_id != parent_span.get_span_context().span_id
