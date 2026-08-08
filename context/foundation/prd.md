---
project: AI Flashcard App
version: 1
status: draft
created: 2026-05-19
context_type: greenfield
product_type: web-app
target_scale:
  users: small
  qps: "# TODO: qps — see Open Questions"
  data_volume: "# TODO: data_volume — see Open Questions"
timeline_budget:
  mvp_weeks: 3
  hard_deadline: null
  after_hours_only: true
---

## Vision & Problem Statement

Working developers preparing for AI/ML job interviews have no clear study path through AI concepts. The moment of pain hits when they sit down to prepare — they find concepts scattered across papers, courses, and documentation with no structured sequence. The cost is wasted time jumping between resources and arriving at an interview uncertain about whether they've covered what matters.

# TODO: insight paragraph — see Open Questions

## User & Persona

**Primary persona:** Any developer brushing up on AI — they may already work in software (or even adjacent AI roles) but need structured review of AI concepts before a job interview. They have a developer's background and can handle technical depth; what they lack is a curated, sequenced path.

## Success Criteria

### Primary
- User can open the app, log in, pick an AI topic, study a deck of flashcards, and receive a score that accurately reflects which cards they marked correct. This flow working end-to-end = the product works.

### Secondary
- Spaced repetition — the app resurfaces cards the user got wrong in a prior session, automatically prioritizing weak spots.
- 75% of cards in production decks are AI-generated (adoption signal).
- 75% of AI-generated cards are completed without being abandoned mid-session (quality signal).

### Guardrails
- Score accuracy: the final score must reflect the user's actual answers. A wrong score breaks the only feedback loop the app provides.

## User Stories

### US-01: Study session (primary path)

- **Given** a logged-in developer on the home screen,
- **When** they select an AI topic and complete a deck of flashcards,
- **Then** they see a score that accurately reflects how many cards they marked correct.

## Functional Requirements

### Authentication

- FR-001: User can register and log in to the app. Priority: must-have
  > Socratic: Counter-argument considered: "Auth adds weeks of work — a local profile would prove the concept faster." Resolution: kept; login is required for the ranking feature to function.

### Topic Discovery

- FR-002: User can see available AI topics on the home screen and select one to study. Priority: must-have
  > Socratic: Counter-argument accepted: "A dedicated browse screen is overkill for 3–5 topics at launch — list them directly on the home screen." Resolution: FR updated to reflect a simple home-screen list rather than a separate browse view.

### Study Session

- FR-003: User can flip through flashcards and mark each as correct or incorrect during a session. Priority: must-have
  > Socratic: Counter-argument noted: "Self-marking is subjective — multiple choice would give objective scoring and better simulate interview conditions." Resolution: kept as self-mark for v1; multiple choice format is a candidate upgrade for v2.

- FR-004: User can see their score at the end of a study session. Priority: must-have
  > Socratic: No counter-argument; stands as written.

### Rankings

- FR-005: User can view a ranking of all students ordered by score. Priority: must-have
  > Socratic: Counter-argument noted: "With few early users the leaderboard will be empty and useless." Resolution: kept; leaderboard is part of the product vision and adoption metric.

### Review

- FR-006: User can review cards they got wrong in a prior session. Priority: nice-to-have
  > Socratic: No counter-argument; stands as written.

### Admin

- FR-007: Admin can create topic decks seeded with AI-generated flashcard content. Priority: must-have
  > Socratic: No counter-argument; admin seeding is the content supply mechanism for the entire product.

## Non-Functional Requirements

- The app runs in a web browser (desktop); no native mobile app required for v1.
- User-perceived response time for card transitions and score display must be under 2 seconds.

## Business Logic

The app ranks users by their cumulative total of correct answers across all study sessions. A session score is the count of cards the user marked correct. Correct answers from spaced-repetition review sessions count equally toward the lifetime total. The leaderboard orders all users by this lifetime total, descending.

## Access Control

Users log in via email/password or OAuth. Regular users have equal access to study features; no separate named admin role exists. Admin content-seeding access (FR-007) is granted via Django's built-in `is_superuser` flag on an otherwise-regular account — see Open Questions #3 for the resolution. Progress and deck state are persisted per account across devices.

## Non-Goals

- No native mobile app (iOS/Android) — web browser only for v1.
- No custom AI model — admin deck seeding uses an existing third-party AI API; no custom ML training.
- No team or group study features — individual study sessions only; no shared decks or collaborative modes in v1.

## Open Questions

1. **What is the insight paragraph for Vision & Problem Statement?** What does this product understand about the problem that existing resources (YouTube tutorials, scattered docs, bootcamps) do not address? — Owner: user. Block: no (PRD is functional without it, but weaker for pitching).
2. **What are the qps and data_volume estimates for target_scale?** Downstream stack selection can proceed with small/small defaults, but explicit values anchor NFR targets better. — Owner: user. Block: no.
3. ~~**Admin role vs. flat user model — contradiction to resolve.**~~ **RESOLVED (2026-08-08):** Django's built-in `is_superuser` flag is the canonical admin-role mechanism for FR-007. No new role model or separate admin table. Rationale: the Django admin panel already registers `Card`/`CardReview` (`flashcards/admin.py`) and a superuser can already create cards manually through it; the only remaining work for S-03 is an AI-seeding action or management command layered on top of that existing access. This unblocks roadmap item S-03 (`admin-ai-deck-seeding`).
4. **US-01 acceptance criteria incomplete.** Only a Given/When/Then block exists; no formal acceptance criteria checklist was captured. What are the edge cases — empty deck, connection failure mid-session, score display precision, duplicate session submissions? — Owner: user. Block: no (enough to start; completeness matters before implementation begins).
