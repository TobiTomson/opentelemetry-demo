# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

"""Parity checks for hand-written (API-level) instrumentation.

The SDK for these services is now injected at the container layer rather than
wired into source. The presence/edge suite (test_traces, test_metrics, test_logs)
would still pass if a custom span or metric silently disappeared, because it only
checks that *some* telemetry exists per service. These tests assert the specific
application-authored spans and metrics still flow through the injected SDK.
"""

import os

import pytest
import requests

from conftest import poll_until

# These services are not started in the agentic scope, so skip there.
pytestmark = pytest.mark.skipif(
    os.environ.get("TEST_SCOPE", "minimal") == "agentic",
    reason="custom-instrumentation services are not part of the agentic scope",
)

# service -> span name that application source creates via the OTel API.
CUSTOM_SPANS = {
    "email": "send_email",
    "payment": "charge",
    "recommendation": "get_product_list",
}

# service -> a span attribute the application sets on an auto-instrumented span.
# cart decorates the gRPC server span (Activity.Current) instead of starting its own.
CUSTOM_SPAN_TAGS = {
    "cart": "demo.product.id",
}

# service -> regex matching the custom metric after the OTLP -> Prometheus
# normalization (dots to underscores, counters gain _total, histograms produce
# _bucket/_count/_sum). Confirmed shape: demo.recommendation.requests is queried
# in the repo's Grafana dashboard as demo_recommendation_requests_total.
CUSTOM_METRICS = {
    "email": "demo_notification_confirmations.*",
    "payment": "demo_payment_transactions.*",
    "recommendation": "demo_recommendation_requests.*",
    "cart": "demo_cart_.+_latency.*",
}

# Resource attributes, any one of which proves a resource detector ran under the
# injected SDK. These are populated by detectors, not by OTEL_RESOURCE_ATTRIBUTES.
DETECTOR_RESOURCE_KEYS = frozenset(
    {"host.name", "process.pid", "container.id", "os.type"}
)


def _traces(jaeger_url, service, limit=100):
    resp = requests.get(
        f"{jaeger_url}/jaeger/ui/api/traces",
        params={"service": service, "limit": limit, "lookback": "1h"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


@pytest.mark.parametrize("service,operation", sorted(CUSTOM_SPANS.items()))
def test_custom_span_present(jaeger_url, service, operation):
    """A hand-written span created via the OTel API still reaches Jaeger."""

    def check():
        for trace in _traces(jaeger_url, service):
            for span in trace.get("spans", []):
                if span.get("operationName") == operation:
                    return True
        return False

    poll_until(check, f"custom span '{operation}' for '{service}' in Jaeger")


@pytest.mark.parametrize("service,tag_key", sorted(CUSTOM_SPAN_TAGS.items()))
def test_custom_span_tag_present(jaeger_url, service, tag_key):
    """An application-set span attribute on an auto-instrumented span still reaches Jaeger."""

    def check():
        for trace in _traces(jaeger_url, service):
            for span in trace.get("spans", []):
                if any(tag.get("key") == tag_key for tag in span.get("tags", [])):
                    return True
        return False

    poll_until(check, f"custom span attribute '{tag_key}' for '{service}' in Jaeger")


@pytest.mark.parametrize("service,metric_regex", sorted(CUSTOM_METRICS.items()))
def test_custom_metric_present(prometheus_url, service, metric_regex):
    """A hand-written metric instrument still reaches Prometheus."""

    def check():
        resp = requests.get(
            f"{prometheus_url}/api/v1/query",
            params={"query": f'{{__name__=~"{metric_regex}"}}'},
            timeout=10,
        )
        resp.raise_for_status()
        return len(resp.json().get("data", {}).get("result", [])) > 0

    poll_until(
        check,
        f"custom metric matching /{metric_regex}/ for '{service}' in Prometheus",
    )


def test_frontend_resource_detectors(jaeger_url):
    """The injected register still populates resource attributes via its default
    resource detectors (not set through OTEL_RESOURCE_ATTRIBUTES)."""

    def check():
        for trace in _traces(jaeger_url, "frontend"):
            for process in trace.get("processes", {}).values():
                keys = {tag.get("key") for tag in process.get("tags", [])}
                if keys & DETECTOR_RESOURCE_KEYS:
                    return True
        return False

    poll_until(check, "frontend resource-detector attributes in Jaeger")
