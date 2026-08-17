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

# Both bundles install into the shared GEM_HOME and the app runs via plain `ruby`,
# which activates the highest installed version of any gem. Fail the build if a
# gem shared by the app and otel bundles resolved to more than one version, so
# future drift between the two lockfiles is caught here instead of silently
# picking a version that differs from a lockfile.
RUN for g in opentelemetry-api google-protobuf; do \
      n=$(gem list -e "$g" 2>/dev/null \
          | sed -n "s/^$g (\(.*\))/\1/p" \
          | tr ',' '\n' \
          | awk '{print $1}' \
          | sort -u | grep -c .); \
      if [ "$n" -ne 1 ]; then \
        echo "ERROR: $g has $n versions installed in GEM_HOME (expected 1)"; \
        gem list -e "$g"; \
        exit 1; \
      fi; \
    done

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
