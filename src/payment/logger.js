// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

const pino = require('pino')

// Plain pino writing to stdout. Log records are exported to OpenTelemetry by the
// container-injected auto-instrumentation (@opentelemetry/instrumentation-pino,
// gated by OTEL_LOGS_EXPORTER), so application source depends only on the OTel API.
const logger = pino({
  mixin() {
    return {
      'service.name': process.env['OTEL_SERVICE_NAME'],
    }
  },
  formatters: {
    level: (label) => {
      return { 'level': label };
    },
  },
});

module.exports = logger;
