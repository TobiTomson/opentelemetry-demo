# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# https://mcr.microsoft.com/v2/dotnet/sdk/tags/list
FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:10.0.300@sha256:c0790639332692a0d56cdd81ed581cfd24d040d9839764c138994866df89a3b6 AS builder
ARG TARGETARCH

WORKDIR /usr/src/app/

COPY ./src/cart/ ./
COPY ./pb/ ./pb/

RUN dotnet restore ./src/cart.csproj -r linux-$TARGETARCH

# Framework-dependent publish (UseAppHost=false) so the app runs as
# `dotnet cart.dll` under the injected .NET auto-instrumentation. The
# OpenTelemetry.AutoInstrumentation package publishes instrument.sh and the CLR
# profiler assets into the output; the SDK is not wired into application source.
RUN dotnet publish ./src/cart.csproj -r linux-$TARGETARCH --no-restore -o /cart /p:UseAppHost=false

# -----------------------------------------------------------------------------

# https://mcr.microsoft.com/v2/dotnet/aspnet/tags/list
FROM ghcr.io/grpc-ecosystem/grpc-health-probe:v0.4.52@sha256:0303b506a288d544ed99fef17a55c8c5ce872f498f643c396b532b3595089ac9 AS grpc-health-probe

FROM mcr.microsoft.com/dotnet/aspnet:10.0.10@sha256:1fa23fc4872d95fd71c2833ebe65d7e84a43b2d51a31d119516852f13d9505a7

WORKDIR /usr/src/app/
COPY --from=builder /cart/ ./
COPY --from=grpc-health-probe /ko-app/grpc-health-probe /bin/grpc_health_probe

USER root
RUN mkdir -p "/var/log/opentelemetry/dotnet" && \
    chown app "/var/log/opentelemetry/dotnet" && \
    chown app "/usr/src/app/instrument.sh" && \
    chmod +x "/usr/src/app/instrument.sh"
USER app

ENV DOTNET_HOSTBUILDER__RELOADCONFIGONCHANGE=false
ENV OTEL_DOTNET_AUTO_TRACES_ADDITIONAL_SOURCES=OpenTelemetry.Demo.Cart
ENV OTEL_DOTNET_AUTO_METRICS_ADDITIONAL_SOURCES=OpenTelemetry.Demo.Cart,OpenFeature

EXPOSE ${CART_PORT}
ENTRYPOINT [ "./instrument.sh", "dotnet", "cart.dll" ]
