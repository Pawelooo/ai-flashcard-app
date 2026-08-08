"""
Management command that mechanically walks every Phase 1 + Phase 2 manual
verification step and reports PASS / FAIL for each one.

Run with:
    uv run python manage.py verify_manual_checks
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from flashcards.models import Card, CardReview, Topic

User = get_user_model()

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []


def check(label, ok):
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {label}")
    results.append((label, ok))


def run_checks():
    client = Client(enforce_csrf_checks=False)

    # ── setup ──────────────────────────────────────────────────────────────
    User.objects.filter(username="_verify_").delete()
    user = User.objects.create_user("_verify_", email="_verify_@example.com", password="v3rify!")

    Topic.objects.filter(slug="_verify_").delete()
    topic = Topic.objects.create(name="Verify Topic", slug="_verify_")
    c1 = Card.objects.create(topic=topic, question="VQ1", answer="VA1")
    c2 = Card.objects.create(topic=topic, question="VQ2", answer="VA2")
    c3 = Card.objects.create(topic=topic, question="VQ3", answer="VA3")

    client.force_login(user)

    # ── 1.2  review button visible after session with missed cards ──────────
    print("\n1.2 - Review button visible when missed cards exist")
    client.post(reverse("flashcards:study_start"), {"topic_id": topic.pk})
    answered = 0
    while True:
        r = client.get(reverse("flashcards:study"))
        if r.status_code != 200:
            break
        cid = r.context["card"].pk
        is_correct = "0" if answered == 0 else "1"
        r = client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": is_correct})
        answered += 1
        if r.status_code == 302 and "results" in r["Location"]:
            break
    r = client.get(reverse("flashcards:study_results"))
    review_url = reverse("flashcards:study_review")
    check("'Powtórz błędne karty' form present", review_url.encode() in r.content)

    # ── 1.3  review session card count = missed count ─────────────────────
    print("\n1.3 - Review session N = missed-card count and shows 'Karta 1 z N'")
    CardReview.objects.filter(user=user).delete()
    now = timezone.now()
    CardReview.objects.create(user=user, card=c1, is_correct=False, reviewed_at=now)
    CardReview.objects.create(user=user, card=c2, is_correct=False, reviewed_at=now)
    CardReview.objects.create(user=user, card=c3, is_correct=True, reviewed_at=now)
    r = client.post(reverse("flashcards:study_review"))
    check("Redirect to study", r.status_code == 302 and "study" in r["Location"])
    session_len = len(client.session["session_cards"])
    check("session_cards length == 2 (missed count)", session_len == 2)
    r = client.get(reverse("flashcards:study"))
    check("'Karta 1 z 2' in study page", b"Karta 1 z 2" in r.content)
    # drain session
    while True:
        r2 = client.get(reverse("flashcards:study"))
        if r2.status_code != 200:
            break
        cid = r2.context["card"].pk
        r2 = client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": "1"})
        if r2.status_code == 302 and "results" in r2["Location"]:
            break

    # ── 1.4  perfect session → review button absent ───────────────────────
    print("\n1.4 - Perfect session hides review button")
    CardReview.objects.filter(user=user).delete()
    client.post(reverse("flashcards:study_start"), {"topic_id": topic.pk})
    while True:
        r = client.get(reverse("flashcards:study"))
        if r.status_code != 200:
            break
        cid = r.context["card"].pk
        r = client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": "1"})
        if r.status_code == 302 and "results" in r["Location"]:
            break
    r = client.get(reverse("flashcards:study_results"))
    check("Review button absent on perfect results", review_url.encode() not in r.content)
    check("Score == total (100%)", r.context["score"] == r.context["total"])

    # ── 1.5  'Ucz się ponownie' absent in review results ─────────────────
    print("\n1.5 - 'Ucz się ponownie' absent after review session")
    CardReview.objects.filter(user=user).delete()
    CardReview.objects.create(user=user, card=c1, is_correct=False, reviewed_at=timezone.now())
    client.post(reverse("flashcards:study_review"))
    r = client.get(reverse("flashcards:study"))
    cid = r.context["card"].pk
    client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": "1"})
    r = client.get(reverse("flashcards:study_results"))
    study_start_url = reverse("flashcards:study_start")
    check("'Ucz się ponownie' form absent", study_start_url.encode() not in r.content)
    check("topic_id is None in context", r.context["topic_id"] is None)

    # ── 1.6  'Wybierz temat' present on both result types ────────────────
    print("\n1.6 - 'Wybierz temat' present on regular AND review results")
    topics_url = reverse("flashcards:topics")

    # regular results: reuse current page (study_results just rendered above)
    CardReview.objects.filter(user=user).delete()
    client.post(reverse("flashcards:study_start"), {"topic_id": topic.pk})
    while True:
        r = client.get(reverse("flashcards:study"))
        if r.status_code != 200:
            break
        cid = r.context["card"].pk
        r = client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": "1"})
        if r.status_code == 302 and "results" in r["Location"]:
            break
    r_reg = client.get(reverse("flashcards:study_results"))
    check("Topics button present on regular results", topics_url.encode() in r_reg.content)

    # review results
    CardReview.objects.filter(user=user).delete()
    CardReview.objects.create(user=user, card=c1, is_correct=False, reviewed_at=timezone.now())
    client.post(reverse("flashcards:study_review"))
    r = client.get(reverse("flashcards:study"))
    cid = r.context["card"].pk
    client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": "1"})
    r_rev = client.get(reverse("flashcards:study_results"))
    check("Topics button present on review results", topics_url.encode() in r_rev.content)

    # ── 2.2  Full E2E cycle ───────────────────────────────────────────────
    print("\n2.2 - Full E2E: session with missed cards -> review -> results")
    CardReview.objects.filter(user=user).delete()
    client.post(reverse("flashcards:study_start"), {"topic_id": topic.pk})
    missed_card_id = None
    answered = 0
    while True:
        r = client.get(reverse("flashcards:study"))
        if r.status_code != 200:
            break
        cid = r.context["card"].pk
        is_correct = "0" if missed_card_id is None else "1"
        if missed_card_id is None:
            missed_card_id = cid
        r = client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": is_correct})
        answered += 1
        if r.status_code == 302 and "results" in r["Location"]:
            break

    r = client.get(reverse("flashcards:study_results"))
    check("Regular results: 1 missed card", len(r.context["missed_cards"]) == 1)
    check("Regular results: review button visible", review_url.encode() in r.content)

    r = client.post(reverse("flashcards:study_review"))
    check("study_review redirects to study", r.status_code == 302 and "study" in r["Location"])
    check("Review session has exactly 1 card", len(client.session["session_cards"]) == 1)

    r = client.get(reverse("flashcards:study"))
    check("Study shows 'Karta 1 z 1'", b"Karta 1 z 1" in r.content)
    check("Review card is the missed card", r.context["card"].pk == missed_card_id)
    cid = r.context["card"].pk
    client.post(reverse("flashcards:study"), {"card_id": cid, "is_correct": "1"})

    r = client.get(reverse("flashcards:study_results"))
    check("Review results: score == 1", r.context["score"] == 1)
    check("Review results: total == 1", r.context["total"] == 1)
    check("Review results: 'Ucz się ponownie' absent", study_start_url.encode() not in r.content)
    check("Review results: 'Wybierz temat' present", topics_url.encode() in r.content)

    # ── teardown ───────────────────────────────────────────────────────────
    User.objects.filter(username="_verify_").delete()
    Topic.objects.filter(slug="_verify_").delete()

    # ── summary ────────────────────────────────────────────────────────────
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"Result: {passed}/{total} checks passed")
    if passed < total:
        print("FAILED checks:")
        for label, ok in results:
            if not ok:
                print(f"  - {label}")
    return passed == total


class Command(BaseCommand):
    help = "Verify all Phase 1 and Phase 2 manual checks"

    def handle(self, *args, **options):
        from django.test.utils import setup_test_environment
        setup_test_environment()
        ok = run_checks()
        import sys
        sys.exit(0 if ok else 1)