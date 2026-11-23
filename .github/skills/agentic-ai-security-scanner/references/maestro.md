---
title: "MAESTRO local review guide"
source: "https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro"
publisher: "Cloud Security Alliance"
kind: "Original review guide, not a copy of the source"
updated: "2026-11-23"
---

# MAESTRO review guide

Use the CSA's MAESTRO framework to model assets, actors, boundaries and attack
paths across seven layers, and examine interactions between layers:

1. Foundation models: model access, inputs, outputs, and model supply chain.
2. Data operations: sources, training and retrieval data, integrity and access.
3. Agent frameworks: orchestration, tools, memory, identity, and permissions.
4. Deployment and infrastructure: services, networks, hosts and isolation.
5. Evaluation and observability: telemetry, detection, testing and response.
6. Security and compliance: policy enforcement, governance and audit.
7. Agent ecosystem: interoperability, third-party agents and dependencies.

For each plausible threat, identify the affected layer, entry point, trust
boundary, impact and existing controls. A code review cannot establish the safety
of infrastructure or processes not available to the reviewer.

Source: [Cloud Security Alliance, Agentic AI Threat Modeling Framework: MAESTRO](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro).
CSA's website terms restrict automated retrieval; this guide is manually maintained.
