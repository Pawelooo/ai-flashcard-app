---
project: AI Flashcard App
version: 1
status: draft
created: 2026-05-26
updated: 2026-05-26
prd_version: 1
main_goal: speed
top_blocker: decisions
---

# Roadmap: AI Flashcard App

> Derived from `context/foundation/prd.md` (v1) + auto-researched codebase baseline.
> Edit-in-place; archive when superseded.
> Slices below are listed in dependency order. The "At a glance" table is the index.

## Vision recap

Working developers preparing for AI/ML job interviews have no clear, structured study path through AI concepts. The AI Flashcard App addresses this by offering a topic-based deck experience: pick a topic, flip through flashcards, self-score each card, and see your session score — with a leaderboard that shows how your cumulative performance compares to other learners. The product's differentiator is a curated, sequenced path built for developers who already have a technical foundation but need structured review, not another scattered tutorial.

## North star

**S-01: Kompletna sesja nauki** — the smallest end-to-end flow (log in → pick a topic → flip through the deck → see session score) whose successful delivery proves the product's core hypothesis and satisfies the primary success criterion in `prd.md`.

> "North star" here means the single smallest vertical slice — crossing all layers from the database to the UI — that, if shipped and working, proves the product's core hypothesis: that a structured, topic-based flashcard session with self-scoring gives developers a meaningfully better interview preparation path than scattered resources. It is placed as early in the ordering as its prerequisites allow, because everything else — leaderboard, spaced repetition, AI-seeded content — is irrelevant if this slice does not work.

## At a glance

| ID   | Change ID                | Outcome (user can …)                                          | Prerequisites | PRD refs                             | Status   |
|------|--------------------------|---------------------------------------------------------------|---------------|--------------------------------------|----------|
| F-01 | dev-tooling-baseline     | (foundation) ruff + .env.example in place                     | —             | —                                    | ready    |
| F-02 | topic-deck-model         | (foundation) Topic model exists; Card linked to Topic         | —             | FR-002, FR-007                       | ready    |
| S-01 | complete-study-session   | pick a topic, flip deck, mark cards correct/incorrect, see score | F-01, F-02 | FR-001, FR-002, FR-003, FR-004, US-01 | proposed |
| S-03 | admin-ai-deck-seeding    | (admin) create AI-seeded topic decks                          | F-01, F-02    | FR-007                               | blocked  |
| S-02 | leaderboard              | view ranking of all users by cumulative correct answers       | S-01          | FR-005                               | proposed |
| S-04 | spaced-repetition-review | review cards marked incorrect in a prior session              | S-01          | FR-006                               | proposed |

## Streams

Navigation aid — groups items that share a Prerequisites chain. Canonical ordering lives in the dependency graph below; this table is the proposed reading order across parallel tracks.

| Stream | Theme                | Chain                          | Note                                                                    |
|--------|----------------------|--------------------------------|-------------------------------------------------------------------------|
| A      | Tooling + study loop | `F-01` → `S-01` → `S-02`      | Main must-have path for `speed` goal; S-01 also requires F-02 (joins B) |
| B      | Topic model + admin  | `F-02` → `S-03` (blocked)     | F-02 is also a prerequisite for S-01 in Stream A                        |
| C      | Spaced repetition    | `S-04`                         | Nice-to-have; branches from S-01, parallel with S-02                    |

## Baseline

What's already in place as of 2026-05-26 (auto-researched + user-confirmed).
Foundations below assume these are present and do NOT re-scaffold them.

- **Frontend:** present — Django templates fully wired; `base.html`, `home.html`, `study.html`, `card_list.html`, `card_form.html`, `stats/dashboard.html`, login/register templates; all views render HTML end-to-end
- **Backend / API:** present — Django 6.0.5; `flashcards` and `stats` apps registered; views for study, card_list, card_create, stats dashboard, home, healthz; services layer (`compute_study_stats`); URL routing complete
- **Data:** partial — `Card` + `CardReview` models with migrations; `seed_cards` management command (10 AI/ML cards); no `Topic` model (required by FR-002, FR-007)
- **Auth:** present — Django built-in auth fully wired; register/login/logout views + templates; `login_required` decorators applied throughout; `LOGIN_REDIRECT_URL` configured
- **Deploy / infra:** partial — `Dockerfile` (Python 3.14, uv, placeholder `SECRET_KEY`) + `fly.toml` (healthcheck at `/healthz/`, `auto_stop_machines = off`, release migration command) present; GitHub Actions CI/CD absent
- **Observability:** absent — Django default stdout logging only; no error tracking, no metrics

## Foundations

### F-01: Dev tooling baseline

- **Outcome:** (foundation) ruff linter/formatter configured in `pyproject.toml`; `.env.example` added at project root documenting required environment variables.
- **Change ID:** dev-tooling-baseline
- **PRD refs:** —
- **Unlocks:** S-01, S-02, S-03, S-04 — establishes the code quality baseline and secure environment config documentation that all subsequent slices depend on; without `.env.example`, agent implementations may hardcode `SECRET_KEY` or `DATABASE_URL` variants
- **Prerequisites:** —
- **Parallel with:** F-02
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Without ruff, each slice introduces inconsistent formatting that accumulates as noise in diffs. Without `.env.example`, environment variable assumptions are implicit. Both are under 5 minutes to configure; risk is in skipping and paying later across every slice.
- **Status:** ready

### F-02: Topic/deck data model

- **Outcome:** (foundation) `Topic` model exists (name, slug); `Card` has a ForeignKey to `Topic`; migration created and applied; `seed_cards` command updated to assign the 10 existing cards to an "AI/ML Fundamentals" topic.
- **Change ID:** topic-deck-model
- **PRD refs:** FR-002, FR-007
- **Unlocks:** S-01 (topic selection on the home screen requires topics in the database), S-03 (admin deck seeding must target a specific `Topic`)
- **Prerequisites:** —
- **Parallel with:** F-01
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Simple Django model addition. The only design lock-in risk: if cards ever need to belong to multiple topics, a FK is too narrow and a ManyToMany would be required. For MVP (each card belongs to one topic), FK is correct and the simplest path per the `speed` goal.
- **Status:** ready

## Slices

### S-01: Kompletna sesja nauki

- **Outcome:** User can select a topic from the home screen, flip through that topic's full deck of cards one at a time, mark each card correct or incorrect, and see their session score (X out of N correct) on a results screen at the end of the deck.
- **Change ID:** complete-study-session
- **PRD refs:** FR-001, FR-002, FR-003, FR-004, US-01
- **Prerequisites:** F-01, F-02
- **Parallel with:** S-03 (once S-03 unblocks; both depend only on F-01 + F-02)
- **Blockers:** —
- **Unknowns:**
  - Session model design — should a `StudySession` model track start/end of a deck run, or should the score be computed on-the-fly from `CardReview` records within a time window? — Owner: user/team. Block: no (can decide during `/10x-plan`; both approaches deliver the user-visible outcome).
  - US-01 acceptance criteria incomplete — edge cases not specified: empty deck, mid-session connection failure, score display precision, duplicate session submissions (PRD Open Question #4) — Owner: user. Block: no (enough to start; details matter before implementation ends).
- **Risk:** The current study view shows one random card at a time with no session boundary and no end screen. The transition to "session with a defined deck, ordered progression, and a results screen" is the largest design change in this slice. Scoped correctly it is still straightforward, but the session abstraction — what constitutes one session, when it ends — must be decided before the view is rewritten.
- **Status:** proposed

### S-03: Admin — seeding decków z AI

- **Outcome:** Admin can create a new topic deck and seed it with AI-generated flashcard content using a third-party AI API, either through the Django admin interface or a dedicated management command.
- **Change ID:** admin-ai-deck-seeding
- **PRD refs:** FR-007
- **Prerequisites:** F-01, F-02
- **Parallel with:** S-01 (once unblocked)
- **Blockers:** —
- **Unknowns:**
  - Admin role model — which is canonical: a separate named admin role, Django's built-in `is_staff`/`is_superuser`, or out-of-app seeding via management command only? (PRD Open Question #3) — Owner: user. Block: yes.
- **Risk:** Blocked until the admin role decision is made. The lowest-effort resolution is Django's built-in `is_superuser` — the Django admin panel already has `Card` and `CardReview` registered (`flashcards/admin.py`), so a superuser can already create cards manually; the only addition would be an AI-seeding action or command. Resolving the question takes minutes; not resolving it blocks the entire content-supply mechanism for the product.
- **Status:** blocked

### S-02: Tablica liderów

- **Outcome:** User can view a rankings page that lists all registered users ordered by their cumulative total of correct answers across all study sessions, descending.
- **Change ID:** leaderboard
- **PRD refs:** FR-005
- **Prerequisites:** S-01
- **Parallel with:** S-04
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Low technical risk. The leaderboard is an aggregate query on `CardReview` data that already exists after S-01 ships. Business logic is fully specified in the PRD: cumulative correct answers, all session types count equally. The only edge case is an empty leaderboard at launch (few early users) — PRD acknowledged this and kept the feature.
- **Status:** proposed

### S-04: Powtórki słabych kart

- **Outcome:** User can start a "review" session that automatically surfaces cards they marked incorrect in a previous session, prioritizing weak spots.
- **Change ID:** spaced-repetition-review
- **PRD refs:** FR-006
- **Prerequisites:** S-01
- **Parallel with:** S-02
- **Blockers:** —
- **Unknowns:**
  - Spaced repetition algorithm scope — is v1 "show wrong cards from last session" or a full SRS algorithm (e.g. SM-2)? PRD secondary success criterion says "resurfaces cards the user got wrong in a prior session, automatically prioritizing weak spots." — Owner: user. Block: no (the minimal reading — wrong cards from last session — is implementable first; full SRS is a progressive enhancement).
- **Risk:** FR-006 is nice-to-have; sequenced after S-02 to protect the must-have path. Secondary success criterion treats it as an adoption signal, so it is not purely cosmetic — but it is the last item in the must-have → nice-to-have order and should not delay the `speed` goal.
- **Status:** proposed

## Backlog Handoff

| Roadmap ID | Change ID                | Suggested issue title                                 | Ready for `/10x-plan` | Notes                                               |
|------------|--------------------------|-------------------------------------------------------|-----------------------|-----------------------------------------------------|
| F-01       | dev-tooling-baseline     | Add ruff formatter and .env.example to project        | yes                   | Quick setup (< 5 min); do before or during F-02     |
| F-02       | topic-deck-model         | Add Topic model; link Card to Topic; update seed data | yes                   | Run parallel to F-01                                |
| S-01       | complete-study-session   | Implement end-to-end study session with score screen  | no                    | Needs F-01 + F-02 done first                        |
| S-03       | admin-ai-deck-seeding    | Admin: AI-seeded topic deck creation                  | no                    | Blocked — resolve Open Question #3 first            |
| S-02       | leaderboard              | Implement user leaderboard by cumulative score        | no                    | Needs S-01 done first                               |
| S-04       | spaced-repetition-review | Implement spaced repetition review session            | no                    | Nice-to-have; needs S-01; parallel with S-02        |

## Open Roadmap Questions

1. **Admin role — which model is canonical?** Separate named admin role, Django's built-in `is_staff`/`is_superuser`, or out-of-app seeding via management command only? — Owner: user. Block: S-03 (FR-007 is unplannable until resolved; lowest-effort resolution is `is_superuser` since Django admin is already wired).
2. **CI/CD pipeline timing** — When to set up GitHub Actions auto-deploy to Fly.io (per `ci_default_flow: auto-deploy-on-merge` in `tech-stack.md`)? — Owner: user. Block: no (manual `fly deploy` works now; CI/CD reduces friction but is not required for the MVP sprint).
3. **US-01 acceptance criteria edge cases** — Empty deck, mid-session connection failure, score display precision, duplicate session submissions — not defined in PRD (Open Question #4). — Owner: user. Block: no (sufficient to start planning S-01; matters before implementation ends).

## Parked

- **Native mobile app (iOS/Android)** — Why parked: PRD §Non-Goals — web browser only for v1.
- **Custom AI model / ML training** — Why parked: PRD §Non-Goals — use existing third-party AI API for deck seeding; no custom ML training.
- **Team/group study features** — Why parked: PRD §Non-Goals — individual sessions only; no shared decks or collaborative modes in v1.
- **Observability stack (Sentry, structured logging, metrics)** — Why parked: no PRD NFR requires it at MVP; stdout logging via `fly logs` is sufficient for solo MVP operation. Add post-launch when there are users to monitor.
- **CI/CD auto-deploy pipeline** — Why parked: manual `fly deploy` is sufficient for the MVP sprint; set up once the must-have path is stable and deploys become frequent.
- **Insight paragraph (Vision & Problem Statement)** — Why parked: PRD Open Question #1, Block: no; not required for roadmap or implementation.

## Done

(Empty on first generation. `/10x-archive` appends entries here — and flips that item's `Status` to `done` — when a change whose `Change ID` matches a roadmap item is archived.)
