# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


FROM docker.io/library/node:26.4.0-slim@sha256:a1d9d671994fc2d26e297ac56b4b1522a8bc7fa71c43b14cd1b1fe6c5116f7dc AS builder

WORKDIR /usr/src/app/

COPY ./src/payment/package.json package.json
COPY ./src/payment/package-lock.json package-lock.json

RUN npm ci --omit=dev

# Server-side OpenTelemetry SDK is decoupled from application source: it is
# declared in src/payment/otel and installed here, then merged into the app's
# node_modules so a single @opentelemetry/api instance is shared. Swapping OTel
# distributions is a change to this manifest/image, not to application code.
COPY ./src/payment/otel/package.json ./src/payment/otel/package-lock.json otel/
# The otel tree is authoritative on merge (clobber) so the injected SDK stays
# internally consistent (payment's app tree also pulls OTel packages via
# pino-opentelemetry-transport, so no-clobber would leave a mismatched SDK). The
# guard then fails the build if the merge changed the app-visible version of a
# package the app imports directly (a single shared @opentelemetry/api and
# @grpc/grpc-js), catching future drift loudly.
RUN cd otel && npm ci --omit=dev && cp -r node_modules/. /usr/src/app/node_modules/ && \
    for pkg in @opentelemetry/api @grpc/grpc-js; do \
      exp=$(node -p "require('/usr/src/app/package.json').dependencies['$pkg']"); \
      got=$(node -p "require('/usr/src/app/node_modules/$pkg/package.json').version"); \
      test "$exp" = "$got" || { echo "ERROR: $pkg is $got after merge, app pins $exp"; exit 1; }; \
    done

# -----------------------------------------------------------------------------

FROM gcr.io/distroless/nodejs22-debian12:nonroot@sha256:13593b7570658e8477de39e2f4a1dd25db2f836d68a0ba771251572d23bb4f8e

WORKDIR /usr/src/app/

COPY --from=builder /usr/src/app/node_modules/ node_modules/

COPY ./pb/demo.proto demo.proto

COPY ./src/payment/charge.js charge.js
COPY ./src/payment/index.js index.js
COPY ./src/payment/logger.js logger.js

EXPOSE ${PAYMENT_PORT}

ENV NODE_OPTIONS="--require @opentelemetry/auto-instrumentations-node/register"

CMD ["index.js"]
