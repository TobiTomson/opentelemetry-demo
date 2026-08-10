# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


FROM docker.io/library/ruby:4.0.5-alpine3.22@sha256:fae3127404cb61d6897d7eed08e65ec7ccc96ba0542dc7c44712efa9b2ef78f0 AS builder

COPY ./src/email/Gemfile Gemfile
COPY ./src/email/Gemfile.lock Gemfile.lock

# Server-side OpenTelemetry SDK is decoupled from application source: the app
# bundle declares only the OTel API, while the SDK/exporters/auto-instrumentation
# are declared in ./otel and installed into the same shared GEM_HOME here.
COPY ./src/email/otel/Gemfile otel/Gemfile
COPY ./src/email/otel/Gemfile.lock otel/Gemfile.lock

RUN apk update && \
    apk add make gcc musl-dev gcompat && \
    bundle install && \
    BUNDLE_GEMFILE=otel/Gemfile bundle install

FROM docker.io/library/ruby:4.0.5-alpine3.22@sha256:fae3127404cb61d6897d7eed08e65ec7ccc96ba0542dc7c44712efa9b2ef78f0

COPY --from=builder /usr/local/bundle/ /usr/local/bundle/

WORKDIR /email_server

COPY ./src/email/views/ views/

COPY ./src/email/email_server.rb email_server.rb
COPY ./src/email/otel_bootstrap.rb otel_bootstrap.rb

EXPOSE ${EMAIL_PORT}

# Ruby has no vendor-agnostic zero-code auto-instrumentation executable, so the
# SDK is injected by requiring the bootstrap via RUBYOPT before the app starts.
# Running plain `ruby` (not `bundle exec`) lets both the app gems and the
# separately-declared OTel gems resolve from the shared GEM_HOME.
ENV RUBYOPT="-r/email_server/otel_bootstrap.rb"
ENTRYPOINT ["ruby", "email_server.rb"]
