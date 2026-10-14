from django.core.management.base import BaseCommand
from flashcards.models import Card, Topic

# Seed data for AI/ML flashcards used in interview preparation

CARDS = [
    (
        "Co to jest gradient descent?",
        "Algorytm optymalizacji iteracyjnie aktualizujący parametry modelu w kierunku "
        "przeciwnym do gradientu funkcji straty, minimalizując jej wartość.",
    ),
    (
        "Czym różni się overfitting od underfitting?",
        "Overfitting: model zbyt dobrze dopasowany do danych treningowych, słabo "
        "generalizuje. Underfitting: model zbyt prosty, nie uchwytuje wzorców nawet "
        "w danych treningowych.",
    ),
    (
        "Co to jest backpropagation?",
        "Algorytm trenowania sieci neuronowych — oblicza gradienty funkcji straty "
        "względem wag metodą łańcuchową (chain rule), propagując błąd od warstwy "
        "wyjściowej do wejściowej.",
    ),
    (
        "Co to jest dropout w sieciach neuronowych?",
        "Technika regularyzacji losowo wyłączająca neurony (z prawdopodobieństwem p) "
        "podczas treningu, zapobiegając overfittingowi i wymuszając uczenie "
        "niezależnych cech.",
    ),
    (
        "Czym jest transformer w uczeniu maszynowym?",
        "Architektura sieci neuronowej oparta na mechanizmie self-attention, bez "
        "rekurencji. Podstawa modeli językowych (BERT, GPT). Przetwarza sekwencje "
        "równolegle, co umożliwia efektywne skalowanie.",
    ),
    (
        "Co oznacza skrót LLM?",
        "Large Language Model — duży model językowy trenowany na ogromnych zbiorach "
        "tekstów do przewidywania kolejnych tokenów. Przykłady: GPT-4, Claude, Llama.",
    ),
    (
        "Co to jest precision i recall?",
        "Precision = TP/(TP+FP) — ile z przewidzianych pozytywnych jest naprawdę "
        "pozytywnych. Recall = TP/(TP+FN) — ile z rzeczywistych pozytywnych model "
        "wykrył. Często są w konflikcie (trade-off).",
    ),
    (
        "Co to jest embedding w kontekście NLP?",
        "Reprezentacja słów lub tokenów jako wektorów liczb rzeczywistych w przestrzeni "
        "o niskiej wymiarowości, gdzie podobne semantycznie słowa mają bliskie wektory.",
    ),
    (
        "Czym jest batch normalization?",
        "Technika normalizująca aktywacje warstwy po każdym mini-batchu (średnia=0, "
        "odchylenie=1), przyspieszająca trening i zmniejszająca czułość na "
        "inicjalizację wag.",
    ),
    (
        "Co to jest ROC-AUC?",
        "ROC: krzywa Receiver Operating Characteristic (TPR vs FPR dla różnych progów). "
        "AUC: pole pod tą krzywą — im bliżej 1, tym lepszy klasyfikator. "
        "AUC=0.5 oznacza losowe zgadywanie.",
    ),
]


class Command(BaseCommand):
    help = "Seed the database with example AI/ML flashcards"

    def handle(self, *args, **options):
        if Card.objects.exists():
            self.stdout.write(self.style.WARNING("Fiszki już istnieją, pomijam."))
            return

        topic, _ = Topic.objects.get_or_create(
            slug='ai-ml-fundamentals',
            defaults={'name': 'AI/ML Fundamentals'},
        )
        cards = [Card(topic=topic, question=q, answer=a) for q, a in CARDS]
        Card.objects.bulk_create(cards)
        self.stdout.write(self.style.SUCCESS(f"Dodano {len(cards)} fiszek do tematu '{topic.name}'."))
