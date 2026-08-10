# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

# Container-injected OpenTelemetry SDK bootstrap for the email service.
#
# This file is loaded via RUBYOPT (-r) before email_server.rb, so the SDK,
# exporters and auto-instrumentation are wired up here rather than in
# application source. The gems it requires are declared in otel/Gemfile and
# installed at container build time. Swapping OpenTelemetry distributions is a
# change to this file / the image, not to application code.
#
# Sinatra is required first so the auto-instrumentation can patch it when
# OpenTelemetry::SDK.configure installs the instrumentation.

require "sinatra/base"

require "opentelemetry/sdk"
require "opentelemetry-logs-sdk"
require "opentelemetry-metrics-sdk"
require "opentelemetry/exporter/otlp"
require "opentelemetry-exporter-otlp-logs"
require "opentelemetry-exporter-otlp-metrics"
require "opentelemetry/instrumentation/sinatra"

OpenTelemetry::SDK.configure do |c|
  c.use "OpenTelemetry::Instrumentation::Sinatra"
end

otlp_metric_exporter = OpenTelemetry::Exporter::OTLP::Metrics::MetricsExporter.new
OpenTelemetry.meter_provider.add_metric_reader(otlp_metric_exporter)
