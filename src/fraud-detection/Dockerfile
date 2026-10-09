# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


FROM ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-java:2.31.1@sha256:6f70427eee0ddfaaa861632eadf2d1c9ba03f4daa30e68ae352eac269e9caf7e AS otelagent

# -----------------------------------------------------------------------------

FROM --platform=${BUILDPLATFORM} docker.io/library/gradle:9.7.1-jdk17@sha256:853c26f1712d8c97e8d312d3a628e237c53a6c6beecd1fab6f8fc808a741ce8b AS builder

WORKDIR /usr/src/app/

COPY ./src/fraud-detection/ ./
COPY ./pb/ ./src/main/proto/

RUN gradle shadowJar

# -----------------------------------------------------------------------------

FROM gcr.io/distroless/java17-debian12:nonroot@sha256:06484c2a9dcc9070aeafbc0fe752cb9f73bc0cea5c311f6a516e9010061998ad

WORKDIR /usr/src/app/

# The destination path and the JAVA_TOOL_OPTIONS value below are byte-for-byte
# what the OpenTelemetry Operator injects, so a statically built image and an
# operator-injected pod behave identically. Changing either breaks that
# equivalence.
#
# COUPLING: the Operator's Java mount path is per-container since operator
# v0.131.0 - /otel-auto-instrumentation-java-<containerName>. The demo Helm
# chart renders `containers: - name: {{ .name }}` from the component key, so
# this path hard-codes the Kubernetes container name "fraud-detection". If that
# component is ever renamed in the chart, this path must be renamed with it.
COPY --from=otelagent /javaagent.jar /otel-auto-instrumentation-java-fraud-detection/javaagent.jar
ENV JAVA_TOOL_OPTIONS=" -javaagent:/otel-auto-instrumentation-java-fraud-detection/javaagent.jar"

# The heap cap deliberately lives outside JAVA_TOOL_OPTIONS: the Operator *sets*
# that variable in the PodSpec rather than appending to it, and a Dockerfile ENV
# is invisible to its mutating webhook, so anything co-located there is silently
# dropped in Kubernetes.
ENV JDK_JAVA_OPTIONS="-Xmx180m"

COPY --from=builder /usr/src/app/build/libs/fraud-detection-1.0-all.jar fraud-detection-1.0-all.jar

ENTRYPOINT [ "java", "-jar", "fraud-detection-1.0-all.jar" ]
