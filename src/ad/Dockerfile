# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0


FROM ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-java:2.31.1@sha256:6f70427eee0ddfaaa861632eadf2d1c9ba03f4daa30e68ae352eac269e9caf7e AS otelagent

# -----------------------------------------------------------------------------

FROM --platform=${BUILDPLATFORM} docker.io/library/eclipse-temurin:24.0.2_12-jdk@sha256:7493205ffe6caa8074fa8a06a276bb1c5ac41d3dd0fd43a0db66d7f776e80b3e AS builder
WORKDIR /usr/src/app/

COPY ./src/ad/gradlew* ./src/ad/settings.gradle* ./src/ad/build.gradle ./
COPY ./src/ad/gradle ./gradle

RUN chmod +x ./gradlew
RUN ./gradlew
RUN ./gradlew downloadRepos

COPY ./src/ad/ ./
COPY ./pb/ ./proto
RUN chmod +x ./gradlew
RUN ./gradlew installDist -PprotoSourceDir=./proto

# -----------------------------------------------------------------------------

FROM docker.io/library/eclipse-temurin:24.0.2_12-jre@sha256:8cb2387a28af84cf0db0948d9c67d4480192f4e567027a3963f145d218e8b4f2

WORKDIR /usr/src/app/

COPY --from=builder /usr/src/app/ ./

# The path and the JAVA_TOOL_OPTIONS value below match byte-for-byte what the
# OpenTelemetry Operator injects, so a statically built image and an
# operator-injected pod behave identically. Changing either breaks that
# equivalence. The Operator scopes the Java agent path per container name, so
# the "-ad" suffix has to be baked in here: the demo Helm chart renders
# "containers: - name: {{ .name }}" from the component key, which makes "ad"
# deterministic, but it does couple this Dockerfile to a Kubernetes name.
COPY --from=otelagent /javaagent.jar /otel-auto-instrumentation-java-ad/javaagent.jar
ENV JAVA_TOOL_OPTIONS=" -javaagent:/otel-auto-instrumentation-java-ad/javaagent.jar"

# The heap cap must stay out of JAVA_TOOL_OPTIONS: the Operator overwrites that
# variable wholesale (a Dockerfile ENV is invisible to its webhook), which would
# silently discard the cap in Kubernetes. JDK_JAVA_OPTIONS is read by the java
# launcher and never touched by the Operator, and a percentage lets the JVM size
# itself from whatever cgroup memory limit it is given. 200/300 keeps exact
# parity with the previous -Xmx200m under the 300Mi limit both compose and the
# Helm chart set, so non-heap headroom is unchanged.
ENV JDK_JAVA_OPTIONS="-XX:MaxRAMPercentage=66.666666"

ARG AD_PORT=9555
ARG AD_PROMETHEUS_PORT=9465
EXPOSE ${AD_PORT}
EXPOSE ${AD_PROMETHEUS_PORT}
ENTRYPOINT [ "./build/install/opentelemetry-demo-ad/bin/Ad" ]
