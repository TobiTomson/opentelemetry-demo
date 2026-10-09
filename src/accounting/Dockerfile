# Copyright The OpenTelemetry Authors
# SPDX-License-Identifier: Apache-2.0

FROM ghcr.io/open-telemetry/opentelemetry-operator/autoinstrumentation-dotnet:1.17.0@sha256:642e740b926ce7a736d674df40f7d9796451b9b018130e5dbeb2d4dd5a0f9323 AS otelagent

# -----------------------------------------------------------------------------

FROM --platform=${BUILDPLATFORM} mcr.microsoft.com/dotnet/sdk:10.0.401@sha256:35d40304542c8689331f8cab17c65926cdf48fe711e289321d71924b230a7d29 AS builder
ARG TARGETARCH
ARG BUILD_CONFIGURATION=Release
WORKDIR /src
COPY ["/src/accounting/", "Accounting/"]
COPY ["/pb/demo.proto", "Accounting/src/protos/demo.proto"]
RUN dotnet restore "./Accounting/Accounting.csproj" -r linux-$TARGETARCH
WORKDIR "/src/Accounting"

RUN dotnet build "./Accounting.csproj" -r linux-$TARGETARCH -c $BUILD_CONFIGURATION -o /app/build

# -----------------------------------------------------------------------------

FROM builder AS publish
ARG TARGETARCH
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "./Accounting.csproj" -r linux-$TARGETARCH -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

# -----------------------------------------------------------------------------

FROM mcr.microsoft.com/dotnet/aspnet:10.0.12@sha256:2d584d8147faddb0d678c5748d47953e5b8e18621ed4fb7049a91381d9d7746f
WORKDIR /app
COPY --from=publish /app/publish .

# Path and env var values match what the OpenTelemetry Operator injects, so a
# statically built image and an operator-injected pod behave identically.
# Changing either breaks that equivalence. The profiler path is the glibc one
# because this base image is Debian; the agent image is multi-arch, so its
# linux/ directory always holds the native library for the target platform.
COPY --from=otelagent /autoinstrumentation /otel-auto-instrumentation-dotnet

ENV CORECLR_ENABLE_PROFILING=1 \
    CORECLR_PROFILER={918728DD-259F-4A6A-AC2B-B85E1B658318} \
    CORECLR_PROFILER_PATH=/otel-auto-instrumentation-dotnet/linux/OpenTelemetry.AutoInstrumentation.Native.so \
    DOTNET_STARTUP_HOOKS=/otel-auto-instrumentation-dotnet/net/OpenTelemetry.AutoInstrumentation.StartupHook.dll \
    DOTNET_ADDITIONAL_DEPS=/otel-auto-instrumentation-dotnet/AdditionalDeps \
    DOTNET_SHARED_STORE=/otel-auto-instrumentation-dotnet/store \
    OTEL_DOTNET_AUTO_HOME=/otel-auto-instrumentation-dotnet

ENV OTEL_DOTNET_AUTO_TRACES_ADDITIONAL_SOURCES=Accounting.Consumer

USER app

ENTRYPOINT ["dotnet", "Accounting.dll"]
