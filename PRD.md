# Product Requirements Document: ReqStudio

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-03-24  
**PM:** TBD  
**Source Brief:** product-brief.md  

---

## 1. Product Overview

ReqStudio is a browser-based AI-powered requirements elicitation platform. It translates domain expertise into professional software requirements artifacts through guided multi-agent AI sessions. The platform is designed for business analysts with no software development background, providing BMAD-inspired methodology through an accessible graphical interface.

---

## 2. Goals and Success Criteria

### Business Goals
- Democratize professional requirements elicitation for non-technical domain specialists
- Create a scalable SaaS platform with per-session AI cost below $0.50
- Establish a workflow that produces BMAD-compatible artifacts for downstream development pipelines

### User Goals
- Conduct a complete requirements session without prior methodology knowledge
- Generate professional, structured documents ready for developer handoff
- Resume sessions across multiple working sessions without losing progress

### Non-Goals (MVP)
- Architecture or system design guidance
- Implementation stories for development
- User authentication or cloud storage
- Direct API integrations with Jira, Notion, Linear

---

## 3. User Personas

### Persona 1: The Domain Specialist Analyst
- **Profile:** 5–15 years of experience in a specific business domain (healthcare, finance, logistics, education, etc.)
- **Tech comfort:** High with general SaaS tools; zero with IDEs, CLIs, or developer tooling
- **Pain point:** Knows exactly what the system should do but cannot communicate it in developer-ready format
- **Goal:** Produce a PRD and user stories her team can hand off to a development agency

### Persona 2: The Solo Product Manager
- **Profile:** PM at an early-stage startup; wears multiple hats
- **Tech comfort:** Moderate; familiar with Jira, Notion, Figma
- **Pain point:** No BA resource; needs structured requirements fast without a full methodology course
- **Goal:** Generate a solid PRD in one working session that investors and developers both understand

---

## 4. Functional Requirements

### FR-01: Project Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01.1 | User can create a new project with a name and domain description | Must Have |
| FR-01.2 | User can view a list of existing projects with status and last modified date | Must Have |
| FR-01.3 | User can open and resume any existing project from any phase | Must Have |
| FR-01.4 | User can delete a project | Must Have |
| FR-01.5 | Projects persist in local storage between browser sessions | Must Have |
| FR-01.6 | Project data structure includes `userId` and `collaborators` fields as placeholders for V2 auth | Should Have |

### FR-02: Guided Briefing (Phase 1)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-02.1 | System presents structured questions to capture project vision, stakeholders, and constraints | Must Have |
| FR-02.2 | Questions adapt based on previous answers (conversational, not a static form) | Must Have |
| FR-02.3 | User can edit any previous answer before finalizing the brief | Must Have |
| FR-02.4 | System generates a structured `product-brief.md` upon briefing completion | Must Have |
| FR-02.5 | User can review and approve the brief before proceeding | Must Have |
| FR-02.6 | User can request regeneration of the brief with different emphasis | Should Have |

### FR-03: PRD Construction (Phase 2)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-03.1 | PRD is built section by section, not all at once | Must Have |
| FR-03.2 | Each PRD section requires user confirmation before proceeding to the next | Must Have |
| FR-03.3 | User can request revision of any section without restarting the entire PRD | Must Have |
| FR-03.4 | PRD sections include: Overview, Personas, Functional Requirements, Non-Functional Requirements, Epics, User Stories with Acceptance Criteria | Must Have |
| FR-03.5 | User stories follow the format: `As a [persona], I want to [action] so that [benefit]` | Must Have |
| FR-03.6 | Each user story includes at least 3 acceptance criteria in Given/When/Then format | Must Have |
| FR-03.7 | System generates a complete `PRD.md` upon section completion | Must Have |

### FR-04: Party Mode — Multi-Agent Panel (Phase 3)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-04.1 | Party Mode presents 4 AI agents: Business Analyst, Product Owner, End User, Domain Specialist | Must Have |
| FR-04.2 | Each agent reviews the current artifacts and contributes perspective in character | Must Have |
| FR-04.3 | Agents can disagree with each other and with the user's requirements | Must Have |
| FR-04.4 | User can direct a question to a specific agent | Must Have |
| FR-04.5 | Party Mode session produces a list of identified gaps and open questions | Must Have |
| FR-04.6 | User can accept, reject, or defer each gap identified by agents | Must Have |
| FR-04.7 | Accepted gaps trigger targeted refinement of the relevant PRD section | Must Have |
| FR-04.8 | Party Mode is optional — user can skip and proceed to export | Should Have |

### FR-05: Advanced Elicitation (Phase 4)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-05.1 | After any artifact is generated, system offers Advanced Elicitation | Must Have |
| FR-05.2 | System suggests 5 relevant elicitation methods based on current artifact content | Must Have |
| FR-05.3 | Available methods include: Pre-mortem, Red Team, Stakeholder Mapping, Socratic Questioning, First Principles, Inversion, Constraint Removal, Analogical Reasoning | Must Have |
| FR-05.4 | User selects one method; system applies it to the artifact and presents findings | Must Have |
| FR-05.5 | User can accept or discard findings and repeat with a different method | Must Have |
| FR-05.6 | Each elicitation round is saved to session history | Should Have |

### FR-06: Artifact Export (Phase 5)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-06.1 | User can export `product-brief.md` as a downloadable Markdown file | Must Have |
| FR-06.2 | User can export `PRD.md` as a downloadable Markdown file | Must Have |
| FR-06.3 | User can export `user-stories.md` as a downloadable Markdown file | Must Have |
| FR-06.4 | User can export `glossary.md` as a downloadable Markdown file | Should Have |
| FR-06.5 | All exports use consistent Markdown structure compatible with BMAD input format | Must Have |
| FR-06.6 | Artifacts are internally stored as structured JSON objects to enable future format translation | Must Have |
| FR-06.7 | Export module is designed as a pluggable adapter pattern to support future Jira/Notion integration | Should Have |
| FR-06.8 | User can export all artifacts as a single ZIP bundle | Could Have |

---

## 5. Non-Functional Requirements

### NFR-01: Performance
| ID | Requirement |
|----|-------------|
| NFR-01.1 | AI agent responses must begin streaming within 3 seconds of user submission |
| NFR-01.2 | Local project save/load operations must complete within 500ms |
| NFR-01.3 | Application initial load time must be under 2 seconds on a standard broadband connection |

### NFR-02: Usability
| ID | Requirement |
|----|-------------|
| NFR-02.1 | A user with no requirements methodology training must be able to complete a full session without external help |
| NFR-02.2 | All UI labels, prompts, and agent messages must be in plain language — no technical jargon unless defined inline |
| NFR-02.3 | Application must be fully usable on desktop browsers (Chrome, Firefox, Safari, Edge) |
| NFR-02.4 | Application must be responsive and functional on tablet-sized screens (768px+) |

### NFR-03: Reliability
| ID | Requirement |
|----|-------------|
| NFR-03.1 | Session state must be saved automatically after every user interaction — no data loss on browser refresh |
| NFR-03.2 | API call failures must display a clear, non-technical error message with a retry option |
| NFR-03.3 | Application must handle API timeout gracefully without corrupting session state |

### NFR-04: Extensibility
| ID | Requirement |
|----|-------------|
| NFR-04.1 | Storage layer must be abstracted behind an interface (`StorageAdapter`) to allow swap from localStorage to cloud backend without UI changes |
| NFR-04.2 | Export layer must be abstracted behind an interface (`ExportAdapter`) to allow addition of Jira/Notion connectors in V2 |
| NFR-04.3 | Agent configuration (personas, system prompts) must be externalized in a data structure, not hardcoded in components |
| NFR-04.4 | Authentication hooks (`userId`, `collaborators`) must be present in data schemas even if not functional in MVP |

### NFR-05: Security
| ID | Requirement |
|----|-------------|
| NFR-05.1 | No user data or API keys are transmitted to any third-party service other than Anthropic API |
| NFR-05.2 | All API calls use HTTPS |
| NFR-05.3 | Local storage data does not contain sensitive PII beyond project names and descriptions |

---

## 6. Data Schema

### Project Object
```json
{
  "projectId": "uuid-v4",
  "userId": "placeholder",
  "name": "string",
  "domain": "string",
  "status": "briefing | prd | party | elicitation | complete",
  "createdAt": "ISO-8601",
  "updatedAt": "ISO-8601",
  "collaborators": [],
  "sessions": [
    {
      "sessionId": "uuid-v4",
      "phase": "briefing | prd | party | elicitation",
      "startedAt": "ISO-8601",
      "completedAt": "ISO-8601 | null",
      "messages": [
        {
          "role": "user | assistant",
          "agentId": "analyst | po | enduser | domain | system",
          "content": "string",
          "timestamp": "ISO-8601"
        }
      ]
    }
  ],
  "artifacts": {
    "brief": {
      "markdown": "string",
      "json": {},
      "version": 1,
      "lastUpdated": "ISO-8601"
    },
    "prd": {
      "markdown": "string",
      "json": {},
      "version": 1,
      "lastUpdated": "ISO-8601"
    },
    "userStories": {
      "markdown": "string",
      "json": [],
      "version": 1,
      "lastUpdated": "ISO-8601"
    },
    "glossary": {
      "markdown": "string",
      "json": {},
      "version": 1,
      "lastUpdated": "ISO-8601"
    }
  },
  "exportHistory": [
    {
      "exportedAt": "ISO-8601",
      "format": "markdown | json",
      "artifacts": ["brief", "prd", "userStories"]
    }
  ]
}
```

---

## 7. Agent Definitions

### Agent: Business Analyst (Ana)
- **Role:** Ensures requirements are complete, unambiguous, and testable
- **Perspective:** Methodology and documentation quality
- **Typical challenges:** "This requirement is too vague to test. What does 'fast' mean exactly?"

### Agent: Product Owner (Pedro)
- **Role:** Challenges scope and business value
- **Perspective:** ROI, prioritization, user value
- **Typical challenges:** "Is this truly a must-have for launch, or are we over-engineering scope?"

### Agent: End User (Úrsula)
- **Role:** Represents the actual user experience
- **Perspective:** Usability, pain points, real-world usage patterns
- **Typical challenges:** "A real user would never understand this flow. What happens if they make a mistake here?"

### Agent: Domain Specialist (Configured per project)
- **Role:** Applies deep domain knowledge to validate business rules
- **Perspective:** Domain-specific constraints, regulations, and nuances
- **Typical challenges:** "This rule doesn't account for the exception case common in this industry."

---

## 8. User Flow

```
START
  │
  ▼
[Create / Open Project]
  │
  ▼
[Phase 1: Guided Briefing]
  │  ← AI asks structured questions
  │  ← User answers conversationally
  │  ← Brief generated and approved
  ▼
[Phase 2: PRD Construction]
  │  ← Section by section
  │  ← User confirms each section
  │  ← PRD assembled progressively
  ▼
[Phase 3: Party Mode] (optional)
  │  ← All agents review artifacts
  │  ← Gaps identified and listed
  │  ← User accepts/rejects/defers gaps
  │  ← Accepted gaps trigger PRD refinement
  ▼
[Phase 4: Advanced Elicitation] (optional, repeatable)
  │  ← System suggests 5 methods
  │  ← User selects one
  │  ← Method applied, findings shown
  │  ← User accepts or discards
  ▼
[Phase 5: Export]
  │  ← Select artifacts to export
  │  ← Download as Markdown files
  ▼
END (project saved, resumable)
```

---

## 9. Epics

### Epic 1: Project Foundation
Setup, navigation, and project lifecycle management.
- E1-S1: Create new project with name and domain
- E1-S2: List and open existing projects
- E1-S3: Delete project with confirmation
- E1-S4: Auto-save on every interaction

### Epic 2: Guided Briefing
AI-guided session to produce `product-brief.md`.
- E2-S1: Adaptive question flow for vision capture
- E2-S2: Stakeholder and constraint identification
- E2-S3: Brief generation and approval workflow
- E2-S4: Brief revision without session restart

### Epic 3: PRD Construction
Progressive, section-by-section PRD creation.
- E3-S1: Section navigation and confirmation UI
- E3-S2: Functional requirements generation
- E3-S3: Non-functional requirements generation
- E3-S4: User story generation with acceptance criteria
- E3-S5: Section revision workflow

### Epic 4: Party Mode
Multi-agent requirements review panel.
- E4-S1: Agent panel UI with distinct personas
- E4-S2: Sequential agent commentary on artifacts
- E4-S3: Gap identification and acceptance workflow
- E4-S4: Targeted PRD refinement from accepted gaps

### Epic 5: Advanced Elicitation
Structured reasoning refinement for any artifact.
- E5-S1: Method suggestion engine
- E5-S2: Method application and findings display
- E5-S3: Accept/discard/repeat workflow

### Epic 6: Export
Artifact download and format management.
- E6-S1: Individual artifact Markdown export
- E6-S2: Internal JSON structure for all artifacts
- E6-S3: Export history tracking
- E6-S4: ZIP bundle export (all artifacts)

---

## 10. Out of Scope (Future Versions)

| Feature | Target Version |
|---------|----------------|
| User authentication and accounts | V2 |
| Cloud project storage and sync | V2 |
| Team collaboration and sharing | V2 |
| Jira direct integration | V2 |
| Notion direct integration | V2 |
| Architecture phase support | V2 |
| Custom agent configuration per user | V3 |
| Domain-specific templates (healthcare, finance) | V3 |
| Enterprise SSO | V3 |
| API for third-party integrations | V3 |

---

## 11. Implementation Readiness Checklist

Before handing to architecture/development:

- [ ] Open questions from product-brief.md resolved
- [ ] Agent personas reviewed and approved
- [ ] Data schema validated by technical lead
- [ ] Export format validated against Jira/Notion Markdown import specs
- [ ] StorageAdapter interface defined
- [ ] ExportAdapter interface defined
- [ ] UX spec created (ux-spec.md) — *triggers `bmad-create-ux-design` workflow*

---

*Next step: Run `bmad-create-ux-design` to produce `ux-spec.md`, then `bmad-create-architecture` for technical decisions.*
