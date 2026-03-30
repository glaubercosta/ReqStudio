# Product Brief: ReqStudio

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-03-24  
**Author:** Product Discovery Session  

---

## Executive Summary

ReqStudio is a web-based AI-powered requirements elicitation platform designed for business analysts and domain specialists with no software development background. Inspired by the BMAD Method workflow, ReqStudio guides users through structured requirements gathering sessions using multi-agent AI conversations, advanced elicitation techniques, and professional artifact generation — all within an accessible graphical interface that requires zero technical knowledge to operate.

---

## Problem Statement

Business analysts and domain specialists possess deep knowledge of their problem space but lack the structured methodology to translate that knowledge into software requirements artifacts. Existing solutions force a binary choice:

- **IDE-integrated tools** (like BMAD in VS Code) — powerful but inaccessible to non-technical users
- **Generic AI chat** (ChatGPT, Claude.ai) — accessible but unstructured, producing inconsistent outputs
- **Specialized requirements tools** (Jira, Visure, Jama) — expensive, complex, and not AI-native

No current solution combines **guided AI methodology + accessible GUI + structured exportable artifacts** in a single product.

---

## Vision

A platform where any domain specialist — regardless of technical background — can conduct a professional-grade requirements elicitation session, guided by AI agents that challenge, refine, and document their ideas, producing artifacts ready for immediate use in development pipelines.

> "The analyst brings the domain knowledge. ReqStudio brings the methodology."

---

## Target Users

### Primary User
**Domain-specialist business analyst** — Deep expertise in a specific business domain (healthcare, finance, logistics, etc.), comfortable with general technology (email, SaaS tools, web browsers), zero knowledge of software requirements methodology or development practices.

### Secondary Users
- **Product Managers** who need structured requirements documentation
- **Consultants** managing requirements for multiple clients across different domains
- **Startups** without dedicated BA staff who need professional requirements output

### Out of Scope (V1)
- Software developers (served by BMAD directly)
- System architects
- QA engineers

---

## Core Value Proposition

1. **Methodology without the learning curve** — BMAD-inspired workflow made accessible through guided UX
2. **Multi-agent perspective** — Multiple AI personas challenge requirements from different angles, surfacing gaps the analyst would miss
3. **Professional artifacts out of the box** — Structured, consistent documents ready for Jira, Notion, Confluence, or direct BMAD input
4. **Domain agnostic** — Works for any business domain; the user defines the context
5. **Resumable sessions** — Projects persist across sessions; analysts can pause and return

---

## Key Features (MVP)

### 1. Guided Briefing
Structured conversation that captures project vision, stakeholders, constraints, and success criteria. Produces `product-brief.md`.

### 2. Progressive PRD Construction
Section-by-section Product Requirements Document built through AI-guided questions with user confirmation at each step. Produces `PRD.md`.

### 3. Party Mode — Multi-Agent Panel
Multiple AI agents (Business Analyst, Product Owner, End User, Domain Specialist) simultaneously review and challenge the requirements, each from their unique perspective. Produces refined requirements with documented rationale.

### 4. Advanced Elicitation
Post-generation refinement using structured reasoning methods (Pre-mortem, Red Team, Stakeholder Mapping, Socratic Questioning, First Principles, etc.). User selects method; AI applies it to the current artifact.

### 5. Artifact Export
All generated documents exported as structured Markdown files, designed to be compatible with BMAD input format and importable into Notion, Confluence, and future integrations (Jira, Linear).

### 6. Session Persistence
Projects saved locally (MVP) with full resumption capability. Architecture supports future cloud persistence and multi-user collaboration.

---

## Features Explicitly Excluded (MVP)

- User authentication and accounts
- Cloud storage and sync
- Jira / Linear / Notion direct integration (export only)
- Architecture phase (system design, tech stack decisions)
- Implementation stories for development agents
- Team collaboration features
- Billing and subscription management

---

## Success Metrics

| Metric | Target (90 days post-launch) |
|--------|------------------------------|
| Sessions completed end-to-end | > 50 |
| Artifacts exported per session | ≥ 2 |
| User-reported "ready to use in dev pipeline" | > 70% |
| Session resumption rate | > 40% |
| Time to first artifact | < 20 minutes |

---

## Constraints

- **Technical:** MVP runs entirely in-browser as a React artifact; no backend infrastructure required
- **API:** Uses Anthropic Claude API (Sonnet model); estimated cost ~$0.32 per full session
- **Scope:** Requirements elicitation only — no architecture, no implementation
- **Platform:** claude.ai Artifact environment (MVP); standalone web app (V2)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API costs exceed projections at scale | Medium | High | Implement prompt caching in V2; monitor token usage per session |
| Users skip Party Mode (perceived as slow) | Medium | Medium | Make Party Mode optional but visually compelling |
| Artifacts not compatible with target tools | Low | High | Validate Markdown output against Jira/Notion import specs before launch |
| Non-technical users confused by artifact formats | Medium | Medium | Add in-app preview and explanation of each artifact type |

---

## Roadmap Overview

### MVP (Current Scope)
In-browser React application with guided briefing, PRD construction, Party Mode, Advanced Elicitation, and Markdown export. Local session persistence.

### V2 — Platform
Standalone web application with user authentication, cloud project storage, team collaboration, and direct export to Jira and Notion.

### V3 — Ecosystem
Custom agent configuration, domain-specific templates, API for third-party integrations, and enterprise SSO.

---

## Open Questions

1. Should the MVP support multiple projects simultaneously, or one active project at a time?
2. What is the preferred export format for initial integrations — pure Markdown or structured JSON?
3. Should Party Mode agents be fixed (4 personas) or configurable by the user per project?
4. Is there a target domain (e.g., healthcare, fintech) for early adopter validation, or fully generic from day one?

---

*This document feeds directly into `PRD.md` via the BMAD `bmad-create-prd` workflow.*
