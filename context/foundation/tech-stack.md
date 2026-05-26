---
starter_id: django
package_manager: uv
project_name: ai-flashcard-app
hints:
  language_family: python
  team_size: solo
  deployment_target: fly
  ci_provider: github-actions
  ci_default_flow: auto-deploy-on-merge
  bootstrapper_confidence: verified
  path_taken: standard
  quality_override: false
  self_check_answers: null
  has_auth: true
  has_payments: false
  has_realtime: false
  has_ai: true
  has_background_jobs: false
---

## Why this stack

Django is the natural fit for AI Flashcard App: auth, admin panel, ORM, and migrations ship out of the box, directly covering FR-001 (user registration/login) and FR-007 (admin deck management) without third-party assembly. The batteries-included model keeps a 3-week after-hours sprint on schedule — standard CRUD and auth are measured in hours, not days. The leaderboard (FR-005) and session scoring (FR-004) map cleanly to Django's ORM aggregation and queryset API. Fly.io with GitHub Actions provides a proven, low-configuration deployment pipeline for Django + PostgreSQL that a solo developer can wire up in an afternoon.
