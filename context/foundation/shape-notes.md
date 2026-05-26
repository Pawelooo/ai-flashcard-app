---
project: AI Flashcard App
context_type: greenfield
updated: 2026-05-18
checkpoint:
  current_phase: 8
  phases_completed: [1, 2, 3, 4, 5, 6, 7]
  frs_drafted: 7
  quality_check_status: accepted
  timeline_budget:
    mvp_weeks: 3
    after_hours_only: true
    hard_deadline: null
product_type: web-app
target_scale:
  users: small
  quality_check_status: accepted
---

## Functional Requirements

- FR-001: User can register and log in to the app. Priority: must-have
  > Socrates: Counter-argument considered: "Auth adds weeks of work — a local profile would prove the concept faster." Resolution: kept; login is required for the ranking feature to function.

- FR-002: User can see available AI topics on the home screen and select one to study. Priority: must-have
  > Socrates: Counter-argument accepted: "A dedicated browse screen is overkill for 3–5 topics at launch — list them directly on the home screen." Resolution: FR updated to reflect a simple home-screen list rather than a separate browse view.

- FR-003: User can flip through flashcards and mark each as correct or incorrect during a session. Priority: must-have
  > Socrates: Counter-argument noted: "Self-marking is subjective — multiple choice would give objective scoring and better simulate interview conditions." Resolution: kept as self-mark for v1; multiple choice format is a candidate upgrade for v2.

- FR-004: User can see their score at the end of a study session. Priority: must-have
  > Socrates: No counter-argument; stands as written.

- FR-005: User can view a ranking of all students ordered by score. Priority: must-have
  > Socrates: Counter-argument noted: "With few early users the leaderboard will be empty and useless." Resolution: kept; leaderboard is part of the product vision and adoption metric.

- FR-006: User can review cards they got wrong in a prior session. Priority: nice-to-have
  > Socrates: No counter-argument; stands as written.

- FR-007: Admin can create topic decks seeded with AI-generated flashcard content. Priority: must-have
  > Socrates: No counter-argument; admin seeding is the content supply mechanism for the entire product.

## Non-Goals

- No native mobile app (iOS/Android) — web browser only for v1.
- No custom AI model — admin deck seeding uses an existing third-party AI API; no custom ML training.
- No team or group study features — individual study sessions only; no shared decks or collaborative modes in v1.

## Business Logic

The app ranks users by their cumulative total of correct answers across all study sessions. A session score is the count of cards the user marked correct. Correct answers from spaced-repetition review sessions count equally toward the lifetime total. The leaderboard orders all users by this lifetime total, descending.

## Non-Functional Requirements

- The app runs in a web browser (desktop); no native mobile app required for v1.
- User-perceived response time for card transitions and score display must be under 2 seconds.

## User Stories

### US-01: Study session (primary path)
**Given** a logged-in developer on the home screen,
**When** they select an AI topic and complete a deck of flashcards,
**Then** they see a score that accurately reflects how many cards they marked correct.

## Vision & Problem Statement

Working developers preparing for AI/ML job interviews have no clear study path through AI concepts. The moment of pain hits when they sit down to prepare — they find concepts scattered across papers, courses, and documentation with no structured sequence. The cost is wasted time jumping between resources and arriving at an interview uncertain about whether they've covered what matters.

## User & Persona

**Primary persona:** Any developer brushing up on AI — they may already work in software (or even adjacent AI roles) but need structured review of AI concepts before a job interview. They have a developer's background and can handle technical depth; what they lack is a curated, sequenced path.

## Success Criteria

### Primary
User can open the app, log in, pick an AI topic, study a deck of flashcards, and receive a score that accurately reflects which cards they marked correct. This flow working end-to-end = the product works.

### Secondary
- Spaced repetition — the app resurfaces cards the user got wrong in a prior session, automatically prioritizing weak spots.
- 75% of cards in production decks are AI-generated (adoption signal).
- 75% of AI-generated cards are completed without being abandoned mid-session (quality signal).

### Guardrails
Score accuracy: the final score must reflect the user's actual answers. A wrong score breaks the only feedback loop the app provides.

## Access Control

Users log in via email/password or OAuth. Flat user model — all users have equal access; no admin or role separation. Progress and deck state are persisted per account across devices.
