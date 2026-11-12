"""Treść fiszek seedowanych przez `manage.py seed_cards`.

Każdy temat: slug (stabilny klucz), nazwa, ikona, opis i lista par (pytanie, odpowiedź).
Seed jest idempotentny — dopasowuje temat po slugu, a fiszkę po (temat, pytanie),
więc można tu dopisywać kolejne fiszki i ponownie uruchamiać komendę.
"""

TOPICS = [
    {
        "slug": "ai-ml-fundamentals",
        "name": "AI/ML Fundamentals",
        "icon": "🧠",
        "description": "Podstawowe pojęcia uczenia maszynowego: optymalizacja, regularyzacja, generalizacja.",
        "cards": [
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
            (
                "Czym różni się uczenie nadzorowane od nienadzorowanego?",
                "Nadzorowane: model uczy się na danych z etykietami (np. klasyfikacja, regresja). "
                "Nienadzorowane: brak etykiet, model szuka struktury w danych (np. klasteryzacja, "
                "redukcja wymiarowości).",
            ),
            (
                "Co to jest bias-variance trade-off?",
                "Błąd modelu = bias² + wariancja + szum. Wysoki bias → underfitting (model za prosty), "
                "wysoka wariancja → overfitting (model wrażliwy na dane treningowe). Zwiększanie "
                "złożoności obniża bias, ale podnosi wariancję.",
            ),
            (
                "Czym jest learning rate i co się dzieje, gdy jest za duży lub za mały?",
                "Wielkość kroku aktualizacji wag w gradient descent. Za duży — trening oscyluje "
                "lub się rozbiega; za mały — trening jest bardzo wolny i może utknąć w płaskim "
                "obszarze lub minimum lokalnym.",
            ),
            (
                "Czym różni się batch, mini-batch i stochastic gradient descent?",
                "Batch GD liczy gradient na całym zbiorze (stabilny, kosztowny). SGD — na jednym "
                "przykładzie (szybki, zaszumiony). Mini-batch — na małej paczce (np. 32–512), "
                "kompromis stosowany w praktyce.",
            ),
            (
                "Co to jest regularyzacja L1 i L2?",
                "Kara dodawana do funkcji straty za duże wagi. L1 (Lasso) = λ·Σ|w| — zeruje część "
                "wag, daje rzadkie modele i selekcję cech. L2 (Ridge) = λ·Σw² — zmniejsza wagi "
                "równomiernie, nie zeruje ich.",
            ),
            (
                "Po co dzielimy dane na zbiór treningowy, walidacyjny i testowy?",
                "Treningowy — do uczenia wag. Walidacyjny — do doboru hiperparametrów i early "
                "stopping. Testowy — jednorazowa, nieobciążona ocena końcowa modelu na danych, "
                "których model ani my nie „widzieliśmy” podczas strojenia.",
            ),
            (
                "Co to jest k-fold cross-validation?",
                "Dane dzielimy na k części; model trenujemy k razy, za każdym razem inną część "
                "używając jako walidacyjnej. Wynik to średnia z k przebiegów — stabilniejsza "
                "ocena, szczególnie przy małych zbiorach.",
            ),
            (
                "Czym jest funkcja aktywacji i po co jest potrzebna?",
                "Nieliniowa funkcja stosowana do wyjścia neuronu (np. ReLU, sigmoid, tanh). "
                "Bez niej sieć wielowarstwowa byłaby złożeniem przekształceń liniowych, czyli "
                "wciąż modelem liniowym.",
            ),
            (
                "Co to jest early stopping?",
                "Technika regularyzacji: przerywamy trening, gdy strata na zbiorze walidacyjnym "
                "przestaje spadać przez określoną liczbę epok (patience), i przywracamy najlepsze "
                "wagi.",
            ),
            (
                "Co to jest data leakage?",
                "Sytuacja, gdy do treningu przedostaje się informacja niedostępna w momencie "
                "predykcji (np. z danych testowych lub z przyszłości). Daje zawyżone wyniki "
                "offline i słabe działanie w produkcji.",
            ),
            (
                "Czym jest feature scaling i kiedy jest potrzebny?",
                "Sprowadzanie cech do porównywalnej skali: standaryzacja (średnia 0, odchylenie 1) "
                "lub normalizacja min-max do [0, 1]. Ważny dla metod gradientowych, k-NN, SVM "
                "i PCA; drzewa decyzyjne go nie wymagają.",
            ),
            (
                "Co to jest epoka (epoch) w treningu?",
                "Jedno pełne przejście algorytmu uczącego przez cały zbiór treningowy. "
                "Liczba iteracji w epoce = rozmiar zbioru / rozmiar batcha.",
            ),
            (
                "Czym jest funkcja straty (loss function)?",
                "Funkcja mierząca, jak bardzo predykcje modelu odbiegają od prawdziwych wartości. "
                "Trening minimalizuje ją. Przykłady: MSE dla regresji, cross-entropy dla "
                "klasyfikacji.",
            ),
            (
                "Co to jest curse of dimensionality?",
                "Wraz ze wzrostem liczby wymiarów dane stają się rzadkie, odległości między "
                "punktami przestają się różnić, a do pokrycia przestrzeni potrzeba wykładniczo "
                "więcej danych — metody oparte na odległości działają gorzej.",
            ),
            (
                "Czym różni się parametr od hiperparametru?",
                "Parametry (np. wagi, bias) są uczone z danych podczas treningu. Hiperparametry "
                "(np. learning rate, liczba warstw, λ regularyzacji) ustawiamy przed treningiem "
                "i dobieramy na zbiorze walidacyjnym.",
            ),
        ],
    },
    {
        "slug": "classical-ml-algorithms",
        "name": "Klasyczne algorytmy ML",
        "icon": "🌳",
        "description": "Regresja, drzewa, ensemble, SVM, k-NN, klasteryzacja i redukcja wymiarowości.",
        "cards": [
            (
                "Na czym polega regresja liniowa?",
                "Model przewiduje wartość ciągłą jako liniową kombinację cech: y = w·x + b. "
                "Wagi dobiera się najczęściej minimalizując błąd średniokwadratowy (MSE), "
                "np. metodą najmniejszych kwadratów.",
            ),
            (
                "Dlaczego regresja logistyczna to model klasyfikacji, a nie regresji?",
                "Liczy liniową kombinację cech i przepuszcza ją przez funkcję sigmoid, "
                "otrzymując prawdopodobieństwo klasy w [0, 1]. Trenowana jest log-lossem "
                "(binary cross-entropy); decyzję podejmuje się progiem.",
            ),
            (
                "Jak drzewo decyzyjne wybiera podział w węźle?",
                "Sprawdza możliwe podziały cech i wybiera ten, który najbardziej zmniejsza "
                "nieczystość węzłów potomnych — mierzoną indeksem Giniego lub entropią "
                "(information gain); w regresji — wariancją/MSE.",
            ),
            (
                "Czym jest Random Forest?",
                "Ensemble wielu drzew decyzyjnych trenowanych na próbkach bootstrap (bagging), "
                "gdzie w każdym podziale losuje się podzbiór cech. Predykcja to głosowanie lub "
                "średnia — mniejsza wariancja niż pojedyncze drzewo.",
            ),
            (
                "Czym różni się bagging od boostingu?",
                "Bagging trenuje modele równolegle i niezależnie na losowych próbkach, uśrednia "
                "je (redukuje wariancję). Boosting trenuje modele sekwencyjnie — każdy kolejny "
                "poprawia błędy poprzednich (redukuje bias).",
            ),
            (
                "Na czym polega gradient boosting?",
                "Kolejne słabe modele (zwykle płytkie drzewa) dopasowuje się do ujemnego gradientu "
                "funkcji straty (dla MSE — do reszt) poprzedniego ensemble'u i dodaje z małym "
                "współczynnikiem learning rate. Implementacje: XGBoost, LightGBM, CatBoost.",
            ),
            (
                "Jak działa algorytm k-NN?",
                "Dla nowego punktu znajduje k najbliższych przykładów treningowych (np. odległość "
                "euklidesowa) i zwraca większość ich klas lub średnią wartości. Nie ma fazy "
                "treningu (lazy learning), ale predykcja jest kosztowna.",
            ),
            (
                "Na czym polega SVM (Support Vector Machine)?",
                "Szuka hiperpłaszczyzny rozdzielającej klasy z maksymalnym marginesem. Margines "
                "wyznaczają wektory nośne. Parametr C kontroluje kompromis między szerokością "
                "marginesu a błędami klasyfikacji.",
            ),
            (
                "Co to jest kernel trick?",
                "Sposób na nieliniowe granice decyzyjne: zamiast jawnie mapować dane do "
                "wyżej-wymiarowej przestrzeni, liczy się iloczyny skalarne w tej przestrzeni "
                "funkcją jądra (np. RBF, wielomianową). Typowe dla SVM.",
            ),
            (
                "Jak działa algorytm k-means?",
                "Losuje k centroidów, przypisuje każdy punkt do najbliższego centroidu, przelicza "
                "centroidy jako średnie przypisanych punktów i powtarza do zbieżności. Wymaga "
                "podania k i jest wrażliwy na inicjalizację (stąd k-means++).",
            ),
            (
                "Jak dobrać liczbę klastrów k w k-means?",
                "Metoda łokcia (wykres inercji/WCSS od k i szukanie „zgięcia”), współczynnik "
                "sylwetki (silhouette score) lub wiedza domenowa.",
            ),
            (
                "Czym jest DBSCAN i kiedy jest lepszy od k-means?",
                "Klasteryzacja gęstościowa: punkty z co najmniej minPts sąsiadami w promieniu eps "
                "tworzą klastry, pozostałe to szum. Nie wymaga podania k, znajduje klastry "
                "o dowolnym kształcie i wykrywa outliery.",
            ),
            (
                "Co robi PCA (Principal Component Analysis)?",
                "Liniowa redukcja wymiarowości: rzutuje dane na kierunki (składowe główne) "
                "o największej wariancji, ortogonalne do siebie. Wyznacza się je z wektorów "
                "własnych macierzy kowariancji lub przez SVD.",
            ),
            (
                "Czym różni się t-SNE/UMAP od PCA?",
                "PCA jest liniowe i zachowuje globalną wariancję. t-SNE i UMAP są nieliniowe, "
                "zachowują lokalne sąsiedztwo i służą głównie do wizualizacji 2D/3D; odległości "
                "między klastrami na ich wykresach nie są wiarygodne.",
            ),
            (
                "Na czym polega naiwny klasyfikator Bayesa?",
                "Stosuje twierdzenie Bayesa przy „naiwnym” założeniu warunkowej niezależności "
                "cech przy danej klasie. Szybki, dobrze działa przy klasyfikacji tekstu "
                "(np. filtry spamu).",
            ),
            (
                "Jak radzić sobie z niezbalansowanymi klasami?",
                "Oversampling klasy mniejszościowej (np. SMOTE), undersampling większościowej, "
                "wagi klas w funkcji straty, dobór progu decyzyjnego oraz metryki odporne na "
                "nierównowagę (precision/recall, F1, PR-AUC zamiast accuracy).",
            ),
            (
                "Czym jest one-hot encoding?",
                "Zamiana cechy kategorycznej na wektor binarny z jedynką w pozycji danej "
                "kategorii. Unika sztucznego porządku, ale przy dużej liczbie kategorii daje "
                "wiele kolumn — wtedy stosuje się np. target encoding lub embeddingi.",
            ),
            (
                "Jak drzewa i Random Forest mierzą ważność cech?",
                "Impurity-based importance: suma spadków nieczystości uzyskanych dzięki podziałom "
                "po danej cesze. Jest obciążona na rzecz cech o wielu wartościach — alternatywą "
                "jest permutation importance lub SHAP.",
            ),
            (
                "Co to jest grid search i random search?",
                "Metody doboru hiperparametrów. Grid search sprawdza wszystkie kombinacje "
                "z siatki; random search losuje kombinacje — przy tym samym budżecie zwykle "
                "skuteczniejszy. Bardziej zaawansowana: optymalizacja bayesowska (np. Optuna).",
            ),
            (
                "Kiedy wybrać model klasyczny (np. gradient boosting) zamiast sieci neuronowej?",
                "Przy danych tabelarycznych, małych i średnich zbiorach, potrzebie "
                "interpretowalności i szybkiego treningu. Sieci neuronowe przewyższają je "
                "głównie na danych nieustrukturyzowanych (obraz, tekst, audio).",
            ),
        ],
    },
    {
        "slug": "deep-learning",
        "name": "Deep Learning",
        "icon": "🕸️",
        "description": "Sieci neuronowe: architektury, aktywacje, optymalizatory i problemy treningu.",
        "cards": [
            (
                "Czym jest perceptron wielowarstwowy (MLP)?",
                "Sieć złożona z warstwy wejściowej, jednej lub więcej warstw ukrytych i warstwy "
                "wyjściowej, gdzie każdy neuron jest połączony z każdym w kolejnej warstwie "
                "(warstwy w pełni połączone) i stosuje nieliniową aktywację.",
            ),
            (
                "Dlaczego ReLU jest popularniejsze od sigmoid w warstwach ukrytych?",
                "ReLU(x) = max(0, x) jest tanie obliczeniowo i nie nasyca się dla dodatnich "
                "wartości, więc łagodzi problem zanikającego gradientu. Sigmoid nasyca się "
                "na krańcach, dając gradienty bliskie zera.",
            ),
            (
                "Co to jest problem zanikającego i eksplodującego gradientu?",
                "W głębokich sieciach gradienty mnożone przez wiele warstw mogą maleć do zera "
                "(wczesne warstwy się nie uczą) lub rosnąć wykładniczo (niestabilny trening). "
                "Pomagają: ReLU, dobra inicjalizacja, normalizacja, połączenia residualne, "
                "gradient clipping.",
            ),
            (
                "Czym jest problem „martwego ReLU” i jak go uniknąć?",
                "Neuron, którego wejście jest stale ujemne, zawsze zwraca 0 i ma zerowy gradient, "
                "więc przestaje się uczyć. Pomagają Leaky ReLU, ELU, GELU oraz mniejszy "
                "learning rate.",
            ),
            (
                "Do czego służy funkcja softmax?",
                "Zamienia wektor logitów na rozkład prawdopodobieństwa: exp(zᵢ)/Σexp(zⱼ). "
                "Stosowana na wyjściu klasyfikacji wieloklasowej, zwykle razem z cross-entropy.",
            ),
            (
                "Czym jest optymalizator Adam?",
                "Adaptive Moment Estimation — łączy momentum (średnia krocząca gradientów) "
                "i RMSProp (średnia krocząca kwadratów gradientów), dając adaptacyjny learning "
                "rate dla każdego parametru. AdamW dodatkowo poprawnie rozdziela weight decay.",
            ),
            (
                "Co daje momentum w SGD?",
                "Akumuluje wykładniczo ważoną średnią poprzednich gradientów, więc aktualizacje "
                "przyspieszają w spójnych kierunkach i tłumią oscylacje w wąskich dolinach "
                "funkcji straty.",
            ),
            (
                "Jak działa warstwa konwolucyjna w CNN?",
                "Przesuwa po wejściu małe filtry (kernele) o uczonych wagach i liczy iloczyny "
                "skalarne, tworząc mapy cech. Współdzielenie wag i lokalne połączenia dają "
                "mało parametrów i niezmienniczość na przesunięcia.",
            ),
            (
                "Po co w CNN stosuje się pooling?",
                "Zmniejsza rozdzielczość map cech (np. max pooling 2×2), redukując liczbę "
                "obliczeń i parametrów oraz dając odporność na niewielkie przesunięcia.",
            ),
            (
                "Czym są połączenia residualne (skip connections) w ResNet?",
                "Wyjście bloku to F(x) + x — wejście dodawane jest do wyniku warstw. Gradient "
                "płynie bezpośrednio przez skrót, co pozwala trenować sieci o setkach warstw.",
            ),
            (
                "Czym jest RNN i jakie ma ograniczenia?",
                "Sieć rekurencyjna przetwarza sekwencję krok po kroku, przekazując stan ukryty. "
                "Ograniczenia: zanikający gradient (słaba pamięć długoterminowa) i brak "
                "równoległości w czasie.",
            ),
            (
                "Czym LSTM różni się od zwykłej RNN?",
                "Ma komórkę pamięci i bramki (input, forget, output), które sterują przepływem "
                "informacji. Pozwala to zachować zależności długoterminowe i łagodzi zanikający "
                "gradient. Uproszczona wersja to GRU.",
            ),
            (
                "Czym jest transfer learning?",
                "Wykorzystanie modelu wytrenowanego na dużym zbiorze (np. ImageNet) jako punktu "
                "startowego dla nowego zadania — zamraża się część warstw lub dostraja całość. "
                "Wymaga mniej danych i obliczeń.",
            ),
            (
                "Czym jest autoenkoder?",
                "Sieć uczona odtwarzać swoje wejście przez wąskie gardło (enkoder → reprezentacja "
                "ukryta → dekoder). Służy do kompresji, redukcji szumu i detekcji anomalii "
                "(wysoki błąd rekonstrukcji).",
            ),
            (
                "Jak działa GAN (Generative Adversarial Network)?",
                "Dwie sieci rywalizują: generator tworzy fałszywe próbki z szumu, dyskryminator "
                "odróżnia je od prawdziwych. Trening to gra minimax; problemy to niestabilność "
                "i mode collapse.",
            ),
            (
                "Na czym polegają modele dyfuzyjne?",
                "W procesie forward stopniowo dodaje się szum do danych; sieć uczy się procesu "
                "odwrotnego — krok po kroku usuwać szum. Generacja zaczyna od czystego szumu. "
                "Podstawa m.in. Stable Diffusion.",
            ),
            (
                "Dlaczego inicjalizacja wag ma znaczenie? Czym jest Xavier/He?",
                "Złe wagi początkowe powodują zanikające lub eksplodujące aktywacje. Xavier "
                "(Glorot) skaluje wariancję wag do liczby wejść i wyjść (dla tanh/sigmoid), "
                "He — do liczby wejść z czynnikiem 2 (dla ReLU).",
            ),
            (
                "Czym jest learning rate scheduling i warmup?",
                "Zmiana learning rate w trakcie treningu: np. step decay, cosine annealing. "
                "Warmup to stopniowe zwiększanie LR na początku treningu, stabilizujące "
                "pierwsze kroki — standard przy transformerach.",
            ),
            (
                "Czym różni się layer normalization od batch normalization?",
                "BatchNorm normalizuje każdą cechę po przykładach w batchu (zależy od rozmiaru "
                "batcha). LayerNorm normalizuje po cechach w obrębie jednego przykładu — "
                "niezależnie od batcha, dlatego stosuje się ją w transformerach i RNN.",
            ),
            (
                "Co to jest data augmentation?",
                "Sztuczne powiększanie zbioru treningowego przez transformacje zachowujące "
                "etykietę (np. obroty, odbicia, kadrowanie, zmiana jasności dla obrazów). "
                "Działa jak regularyzacja.",
            ),
        ],
    },
    {
        "slug": "nlp-transformers",
        "name": "NLP i Transformery",
        "icon": "🔤",
        "description": "Tokenizacja, embeddingi, mechanizm attention i architektury BERT/GPT.",
        "cards": [
            (
                "Czym jest tokenizacja?",
                "Podział tekstu na jednostki (tokeny), które model zamienia na identyfikatory "
                "ze słownika. Tokenami mogą być słowa, fragmenty słów (subwords) lub znaki/bajty.",
            ),
            (
                "Na czym polega Byte Pair Encoding (BPE)?",
                "Algorytm tokenizacji subword: zaczyna od pojedynczych znaków/bajtów i iteracyjnie "
                "scala najczęściej występujące pary w nowe tokeny, aż do osiągnięcia rozmiaru "
                "słownika. Radzi sobie z rzadkimi i nowymi słowami.",
            ),
            (
                "Jak działa Word2Vec?",
                "Uczy statycznych embeddingów słów na podstawie kontekstu: CBOW przewiduje "
                "słowo z otoczenia, Skip-gram przewiduje otoczenie ze słowa. Słowa w podobnych "
                "kontekstach dostają podobne wektory.",
            ),
            (
                "Czym embeddingi kontekstowe różnią się od statycznych?",
                "Statyczne (Word2Vec, GloVe) dają jeden wektor na słowo. Kontekstowe (BERT, GPT) "
                "zależą od zdania — „zamek” w drzwiach i zamek królewski mają różne wektory.",
            ),
            (
                "Jak działa mechanizm self-attention?",
                "Każdy token tworzy wektory Query, Key i Value. Wagi uwagi to "
                "softmax(Q·Kᵀ/√dₖ), a wyjście to ważona suma wektorów V. Dzięki temu każdy token "
                "może bezpośrednio „patrzeć” na każdy inny.",
            ),
            (
                "Dlaczego w attention dzielimy przez √dₖ?",
                "Iloczyny skalarne rosną z wymiarem dₖ, co wpycha softmax w obszar nasycenia "
                "z bardzo małymi gradientami. Skalowanie utrzymuje wariancję wyników na stałym "
                "poziomie.",
            ),
            (
                "Czym jest multi-head attention?",
                "Kilka równoległych mechanizmów attention z osobnymi projekcjami Q/K/V. Każda "
                "głowa może uchwycić inny rodzaj zależności; wyniki są konkatenowane i rzutowane "
                "liniowo.",
            ),
            (
                "Po co transformerom positional encoding?",
                "Self-attention jest niezależne od kolejności tokenów, więc informację o pozycji "
                "trzeba dodać jawnie — przez sinusoidalne kodowania, uczone embeddingi pozycji "
                "lub metody względne jak RoPE.",
            ),
            (
                "Czym różni się architektura encoder-only, decoder-only i encoder-decoder?",
                "Encoder-only (BERT) — dwukierunkowy, do rozumienia tekstu i klasyfikacji. "
                "Decoder-only (GPT) — autoregresywny, do generowania. Encoder-decoder (T5, "
                "oryginalny Transformer) — do zadań sekwencja→sekwencja, np. tłumaczenia.",
            ),
            (
                "Na czym polega trening BERT-a (Masked Language Modeling)?",
                "Losowe ok. 15% tokenów jest maskowanych, a model przewiduje je na podstawie "
                "kontekstu z obu stron. Oryginalnie dodatkowo Next Sentence Prediction.",
            ),
            (
                "Na czym polega trening modeli GPT (causal language modeling)?",
                "Model przewiduje kolejny token na podstawie wyłącznie poprzednich. Causal mask "
                "w attention blokuje dostęp do przyszłych tokenów.",
            ),
            (
                "Czym jest KV cache?",
                "Przy generowaniu autoregresywnym klucze i wartości (K, V) wcześniejszych tokenów "
                "są zapamiętywane, więc dla nowego tokena liczy się tylko jego Q, K, V. Znacznie "
                "przyspiesza inferencję kosztem pamięci.",
            ),
            (
                "Jaka jest złożoność self-attention względem długości sekwencji?",
                "O(n²) w czasie i pamięci, bo liczy się uwagę każdy-z-każdym. To ogranicza długość "
                "kontekstu; stąd optymalizacje jak FlashAttention, sparse attention czy "
                "sliding window.",
            ),
            (
                "Co to jest perplexity?",
                "Miara jakości modelu językowego: exp ze średniej ujemnej log-wiarygodności "
                "tokenów. Im niższa, tym model lepiej przewiduje tekst; intuicyjnie to "
                "„efektywna liczba wyborów” na token.",
            ),
            (
                "Czym jest TF-IDF?",
                "Ważenie słów w dokumencie: częstość słowa w dokumencie (TF) razy log odwrotnej "
                "częstości dokumentów zawierających to słowo (IDF). Promuje słowa "
                "charakterystyczne, tłumi powszechne.",
            ),
            (
                "Co to jest Named Entity Recognition (NER)?",
                "Zadanie NLP polegające na wykrywaniu i klasyfikowaniu nazw własnych w tekście "
                "(osoby, organizacje, miejsca, daty). Zwykle modelowane jako klasyfikacja "
                "tokenów (np. schemat BIO).",
            ),
            (
                "Jak mierzy się podobieństwo embeddingów?",
                "Najczęściej cosine similarity — cosinus kąta między wektorami, niezależny od ich "
                "długości. Alternatywy: iloczyn skalarny (dla znormalizowanych wektorów równoważny) "
                "i odległość euklidesowa.",
            ),
            (
                "Co to są metryki BLEU i ROUGE?",
                "Metryki porównujące tekst wygenerowany z referencyjnym na podstawie nakładania "
                "się n-gramów. BLEU (precision-oriented) — typowo dla tłumaczeń; ROUGE "
                "(recall-oriented) — dla streszczeń.",
            ),
            (
                "Czym jest cross-attention?",
                "Attention, w którym Query pochodzą z jednej sekwencji (np. dekodera), a Key "
                "i Value z innej (np. wyjścia enkodera). Pozwala dekoderowi korzystać z wejścia "
                "źródłowego.",
            ),
            (
                "Czym jest Mixture of Experts (MoE)?",
                "Architektura, w której warstwa FFN jest zastąpiona wieloma „ekspertami”, a router "
                "wybiera dla każdego tokena tylko kilku. Zwiększa liczbę parametrów bez "
                "proporcjonalnego wzrostu kosztu obliczeń.",
            ),
        ],
    },
    {
        "slug": "llm-prompt-engineering",
        "name": "LLM i Prompt Engineering",
        "icon": "💬",
        "description": "Jak działają i jak się dostraja duże modele językowe, sampling, prompting.",
        "cards": [
            (
                "Czym jest okno kontekstowe (context window) LLM?",
                "Maksymalna liczba tokenów (prompt + odpowiedź), którą model przetwarza naraz. "
                "Wszystko poza nim jest dla modelu niewidoczne; dłuższy kontekst to wyższy koszt "
                "i opóźnienie.",
            ),
            (
                "Co robi parametr temperature?",
                "Skaluje logity przed softmaxem. Niska temperatura (→0) czyni wybór "
                "deterministycznym i zachowawczym; wysoka spłaszcza rozkład, zwiększając "
                "różnorodność i ryzyko błędów.",
            ),
            (
                "Czym jest top-p (nucleus) i top-k sampling?",
                "Top-k losuje tylko spośród k najbardziej prawdopodobnych tokenów. Top-p losuje "
                "z najmniejszego zbioru tokenów, których łączne prawdopodobieństwo ≥ p — "
                "rozmiar zbioru dopasowuje się do pewności modelu.",
            ),
            (
                "Czym różni się zero-shot od few-shot prompting?",
                "Zero-shot: model dostaje tylko instrukcję zadania. Few-shot: prompt zawiera "
                "kilka przykładów wejście→wyjście, które pokazują format i oczekiwane zachowanie "
                "(in-context learning).",
            ),
            (
                "Co to jest chain-of-thought prompting?",
                "Zachęcanie modelu do rozpisania kroków rozumowania przed odpowiedzią (np. "
                "przykładami z rozumowaniem lub poleceniem „pomyśl krok po kroku”). Poprawia "
                "wyniki w zadaniach wieloetapowych, np. matematycznych.",
            ),
            (
                "Czym jest system prompt?",
                "Instrukcja nadrzędna przekazywana modelowi przed rozmową, ustalająca rolę, "
                "zasady, ton i ograniczenia. Ma zwykle wyższy priorytet niż wiadomości "
                "użytkownika.",
            ),
            (
                "Czym jest halucynacja LLM i jak ją ograniczać?",
                "Generowanie pewnie brzmiących, ale nieprawdziwych informacji. Ograniczają ją: "
                "RAG z cytowaniem źródeł, niższa temperatura, pozwolenie modelowi na „nie wiem”, "
                "weryfikacja odpowiedzi i ewaluacje.",
            ),
            (
                "Na czym polega pretraining LLM?",
                "Trening samonadzorowany na ogromnym korpusie tekstu z zadaniem przewidywania "
                "następnego tokena. Model zdobywa wiedzę o języku i świecie, ale jeszcze nie "
                "umie dobrze wykonywać poleceń.",
            ),
            (
                "Czym jest instruction tuning / SFT?",
                "Supervised Fine-Tuning — dostrajanie wytrenowanego modelu na parach "
                "(instrukcja, wzorcowa odpowiedź), by nauczył się wykonywać polecenia "
                "i prowadzić dialog.",
            ),
            (
                "Na czym polega RLHF?",
                "Reinforcement Learning from Human Feedback: ludzie porównują odpowiedzi modelu, "
                "na tych preferencjach trenuje się reward model, a następnie LLM optymalizuje "
                "się (np. PPO) pod wysoką nagrodę z karą KL za odejście od modelu bazowego.",
            ),
            (
                "Czym jest DPO i czym różni się od RLHF?",
                "Direct Preference Optimization uczy model bezpośrednio na parach "
                "(preferowana, odrzucona odpowiedź) prostą stratą klasyfikacyjną — bez osobnego "
                "reward modelu i pętli RL. Prostsze i stabilniejsze.",
            ),
            (
                "Czym jest LoRA?",
                "Low-Rank Adaptation — metoda parameter-efficient fine-tuning: wagi bazowe są "
                "zamrożone, a uczy się małe macierze niskiego rzędu A·B dodawane do wybranych "
                "warstw. Ułamek parametrów i pamięci pełnego fine-tuningu.",
            ),
            (
                "Co to jest QLoRA?",
                "LoRA trenowana na modelu bazowym skwantyzowanym do 4 bitów. Pozwala dostrajać "
                "duże modele na jednej karcie GPU przy niewielkiej utracie jakości.",
            ),
            (
                "Czym jest kwantyzacja modelu?",
                "Zapis wag (i czasem aktywacji) w niższej precyzji, np. int8 lub int4 zamiast "
                "fp16. Zmniejsza zużycie pamięci i przyspiesza inferencję kosztem niewielkiego "
                "spadku dokładności.",
            ),
            (
                "Czym jest prompt injection?",
                "Atak, w którym złośliwe instrukcje ukryte w danych wejściowych (np. w dokumencie "
                "lub stronie WWW) próbują nadpisać instrukcje systemowe modelu. Obrona: "
                "separacja danych od instrukcji, ograniczanie uprawnień narzędzi, walidacja wyjść.",
            ),
            (
                "Jak uzyskać od LLM ustrukturyzowane wyjście (np. JSON)?",
                "Opisać schemat i podać przykład w prompcie, użyć trybu structured output / "
                "JSON schema lub tool calling oferowanego przez API, a wynik zawsze walidować "
                "(np. Pydantic) i ponawiać przy błędzie.",
            ),
            (
                "Czym są scaling laws?",
                "Empiryczne zależności pokazujące, że strata modelu maleje przewidywalnie "
                "(potęgowo) wraz ze wzrostem liczby parametrów, danych i obliczeń. Chinchilla "
                "wskazała optymalne proporcje parametrów do tokenów treningowych.",
            ),
            (
                "Czym jest destylacja wiedzy (knowledge distillation)?",
                "Trening mniejszego modelu-ucznia tak, by naśladował wyjścia (rozkłady "
                "prawdopodobieństwa) większego modelu-nauczyciela. Daje tańszy i szybszy model "
                "o zbliżonej jakości.",
            ),
            (
                "Czym jest prompt caching?",
                "Ponowne wykorzystanie przetworzonego (KV) stałego prefiksu promptu — np. długiego "
                "system promptu lub dokumentu — między zapytaniami. Obniża koszt i czas "
                "odpowiedzi; wymaga, by zmienna część była na końcu promptu.",
            ),
            (
                "Jak ewaluować aplikację opartą o LLM?",
                "Zestaw testowych przypadków (eval set) z oczekiwanymi wynikami, metryki "
                "automatyczne (dokładne dopasowanie, testy jednostkowe na wyjściu), LLM-as-a-judge "
                "z rubryką oraz ocena ludzka; uruchamiane przy każdej zmianie promptu lub modelu.",
            ),
        ],
    },
    {
        "slug": "rag-ai-agents",
        "name": "RAG i agenci AI",
        "icon": "🤖",
        "description": "Retrieval-Augmented Generation, bazy wektorowe, tool calling i agenci.",
        "cards": [
            (
                "Czym jest RAG (Retrieval-Augmented Generation)?",
                "Wzorzec, w którym przed generowaniem odpowiedzi wyszukuje się pasujące fragmenty "
                "z zewnętrznej bazy wiedzy i dołącza do promptu. Daje aktualną, specyficzną "
                "wiedzę i mniej halucynacji bez fine-tuningu.",
            ),
            (
                "Z jakich etapów składa się typowy pipeline RAG?",
                "Indeksowanie: wczytanie dokumentów → chunking → embeddingi → zapis w bazie "
                "wektorowej. Zapytanie: embedding pytania → wyszukanie top-k fragmentów → "
                "(opcjonalnie reranking) → prompt z kontekstem → generacja odpowiedzi.",
            ),
            (
                "Dlaczego chunking ma znaczenie w RAG?",
                "Za duże fragmenty rozmywają znaczenie embeddingu i zużywają kontekst; za małe "
                "tracą kontekst. Stosuje się podział po strukturze dokumentu, rozsądny rozmiar "
                "i overlap między fragmentami.",
            ),
            (
                "Czym jest baza wektorowa?",
                "Baza przechowująca embeddingi z metadanymi i umożliwiająca szybkie "
                "wyszukiwanie najbliższych sąsiadów. Przykłady: pgvector, Qdrant, Weaviate, "
                "Pinecone, Chroma.",
            ),
            (
                "Co to jest ANN i indeks HNSW?",
                "Approximate Nearest Neighbor — przybliżone, ale bardzo szybkie wyszukiwanie "
                "najbliższych wektorów. HNSW to popularny indeks oparty na wielowarstwowym grafie "
                "„małego świata”, dający dobry kompromis szybkości i trafności.",
            ),
            (
                "Czym jest hybrid search?",
                "Połączenie wyszukiwania semantycznego (wektory) z leksykalnym (np. BM25). "
                "Lepiej radzi sobie z nazwami własnymi, kodami i rzadkimi terminami; wyniki "
                "łączy się np. przez Reciprocal Rank Fusion.",
            ),
            (
                "Co robi reranker w RAG?",
                "Model (zwykle cross-encoder) oceniający trafność par (pytanie, fragment) "
                "dokładniej niż wyszukiwanie wektorowe. Stosowany na kilkudziesięciu kandydatach, "
                "by wybrać najlepsze do promptu.",
            ),
            (
                "Czym różni się bi-encoder od cross-encodera?",
                "Bi-encoder koduje pytanie i dokument osobno — wektory dokumentów można "
                "przeliczyć z góry, więc jest szybki. Cross-encoder przetwarza parę razem — "
                "dokładniejszy, ale za wolny na cały korpus.",
            ),
            (
                "Kiedy wybrać RAG, a kiedy fine-tuning?",
                "RAG — gdy model ma korzystać z wiedzy zmiennej, obszernej lub wymagającej "
                "cytowania źródeł. Fine-tuning — gdy trzeba zmienić zachowanie, styl, format "
                "lub nauczyć specyficznego zadania. Często łączy się oba.",
            ),
            (
                "Jak ewaluować system RAG?",
                "Osobno retrieval (recall@k, MRR — czy właściwe fragmenty zostały znalezione) "
                "i generację (faithfulness — czy odpowiedź wynika z kontekstu, answer relevance). "
                "Narzędzia: np. Ragas, LLM-as-a-judge.",
            ),
            (
                "Czym jest tool calling (function calling)?",
                "Mechanizm, w którym model zamiast tekstu zwraca ustrukturyzowane wywołanie "
                "zdefiniowanego narzędzia (nazwa + argumenty wg JSON schema). Aplikacja je "
                "wykonuje i odsyła wynik modelowi.",
            ),
            (
                "Czym jest agent AI?",
                "System, w którym LLM w pętli sam decyduje o kolejnych krokach: planuje, "
                "wywołuje narzędzia, obserwuje wyniki i kontynuuje, aż osiągnie cel lub "
                "warunek stopu.",
            ),
            (
                "Na czym polega wzorzec ReAct?",
                "Reason + Act: model przeplata kroki rozumowania (Thought), działania "
                "(Action — wywołanie narzędzia) i obserwacji wyniku (Observation), aż do "
                "odpowiedzi końcowej.",
            ),
            (
                "Czym jest MCP (Model Context Protocol)?",
                "Otwarty protokół standaryzujący, jak aplikacje AI łączą się z zewnętrznymi "
                "narzędziami i źródłami danych. Serwer MCP udostępnia narzędzia, zasoby "
                "i prompty, które dowolny klient MCP może wykorzystać.",
            ),
            (
                "Jakie są typowe rodzaje pamięci agenta?",
                "Krótkoterminowa — historia rozmowy w oknie kontekstowym (z podsumowywaniem). "
                "Długoterminowa — zewnętrzny magazyn (np. baza wektorowa lub pliki), z którego "
                "agent zapisuje i odczytuje fakty.",
            ),
            (
                "Czym jest workflow, a czym agent w systemach LLM?",
                "Workflow: kroki i kolejność wywołań LLM i narzędzi są z góry zdefiniowane "
                "w kodzie (przewidywalne). Agent: LLM dynamicznie decyduje o krokach "
                "(elastyczny, ale droższy i mniej przewidywalny).",
            ),
            (
                "Jakie zabezpieczenia stosuje się w agentach AI?",
                "Limit iteracji i budżetu, minimalne uprawnienia narzędzi, zatwierdzanie "
                "akcji nieodwracalnych przez człowieka (human-in-the-loop), sandboxing, "
                "walidacja argumentów i logowanie/tracing kroków.",
            ),
            (
                "Czym jest query rewriting / HyDE w RAG?",
                "Przekształcenie pytania przed wyszukiwaniem, by poprawić retrieval. HyDE "
                "(Hypothetical Document Embeddings) generuje hipotetyczną odpowiedź i wyszukuje "
                "po jej embeddingu, bo jest podobniejsza do dokumentów niż samo pytanie.",
            ),
            (
                "Czym jest problem „lost in the middle”?",
                "LLM-y lepiej wykorzystują informacje z początku i końca długiego kontekstu niż "
                "ze środka. W RAG warto ograniczać liczbę fragmentów i umieszczać najważniejsze "
                "na krańcach.",
            ),
            (
                "Czym jest system multi-agentowy?",
                "Architektura z wieloma wyspecjalizowanymi agentami (np. orkiestrator "
                "delegujący podzadania do agentów-wykonawców), które współpracują nad zadaniem. "
                "Daje podział odpowiedzialności i równoległość kosztem złożoności.",
            ),
        ],
    },
    {
        "slug": "model-evaluation-metrics",
        "name": "Ewaluacja modeli i metryki",
        "icon": "📊",
        "description": "Metryki klasyfikacji i regresji, macierz pomyłek, walidacja i testy A/B.",
        "cards": [
            (
                "Co zawiera macierz pomyłek (confusion matrix)?",
                "Dla klasyfikacji binarnej: TP (trafne pozytywne), FP (fałszywe pozytywne), "
                "FN (fałszywe negatywne), TN (trafne negatywne). Wszystkie metryki klasyfikacji "
                "wynikają z tych wartości.",
            ),
            (
                "Dlaczego accuracy bywa myląca?",
                "Przy niezbalansowanych klasach model zawsze przewidujący klasę większościową "
                "osiąga wysoką accuracy (np. 99% przy 1% oszustw), nie wykrywając niczego "
                "istotnego.",
            ),
            (
                "Co to jest F1-score?",
                "Średnia harmoniczna precision i recall: 2·P·R/(P+R). Wysoka tylko wtedy, gdy "
                "obie są wysokie. Fβ pozwala ważyć recall β razy bardziej niż precision.",
            ),
            (
                "Kiedy ważniejszy jest recall, a kiedy precision?",
                "Recall — gdy koszt przeoczenia jest wysoki (diagnostyka chorób, wykrywanie "
                "oszustw). Precision — gdy koszt fałszywego alarmu jest wysoki (filtr spamu "
                "usuwający ważne maile, rekomendacje).",
            ),
            (
                "Czym jest specificity?",
                "TN/(TN+FP) — odsetek rzeczywistych negatywów poprawnie rozpoznanych. "
                "1 − specificity to FPR, oś X krzywej ROC.",
            ),
            (
                "Kiedy PR-AUC jest lepsze od ROC-AUC?",
                "Przy silnie niezbalansowanych danych. ROC-AUC może wyglądać optymistycznie, "
                "bo FPR jest mały przy wielu negatywach; krzywa precision-recall skupia się "
                "na klasie pozytywnej.",
            ),
            (
                "Czym jest micro, macro i weighted averaging metryk?",
                "Macro — średnia metryk liczonych osobno dla każdej klasy (klasy równoważne). "
                "Micro — liczona z sumarycznych TP/FP/FN (dominują liczne klasy). Weighted — "
                "macro ważone liczebnością klas.",
            ),
            (
                "Czym jest log loss (cross-entropy) jako metryka?",
                "−średnia z log prawdopodobieństwa przypisanego prawdziwej klasie. Mocno karze "
                "pewne, ale błędne predykcje i ocenia jakość prawdopodobieństw, a nie tylko "
                "decyzji.",
            ),
            (
                "Czym różnią się MAE, MSE i RMSE?",
                "MAE — średni błąd bezwzględny, odporny na outliery. MSE — średni kwadrat błędu, "
                "mocno karze duże błędy. RMSE = √MSE — w jednostkach zmiennej celu.",
            ),
            (
                "Co mierzy współczynnik R²?",
                "Jaką część wariancji zmiennej celu wyjaśnia model: 1 − SS_res/SS_tot. "
                "1 — idealne dopasowanie, 0 — tyle co przewidywanie średniej, może być ujemny "
                "dla modelu gorszego od średniej.",
            ),
            (
                "Czym jest kalibracja modelu?",
                "Zgodność przewidywanych prawdopodobieństw z rzeczywistymi częstościami (z 70% "
                "pewnych predykcji ok. 70% powinno być trafnych). Sprawdza się wykresem "
                "kalibracji; poprawia Platt scaling lub regresją izotoniczną.",
            ),
            (
                "Jak wybrać próg decyzyjny klasyfikatora?",
                "Domyślne 0.5 rzadko jest optymalne. Próg dobiera się na zbiorze walidacyjnym "
                "według kosztów błędów biznesowych, np. maksymalizując F1 lub wymagając "
                "minimalnego recall.",
            ),
            (
                "Jak poprawnie walidować modele na szeregach czasowych?",
                "Nie mieszać losowo danych — trenować na przeszłości i testować na przyszłości "
                "(time series split / walk-forward validation), aby uniknąć wycieku informacji "
                "z przyszłości.",
            ),
            (
                "Czym jest stratified k-fold?",
                "Wariant k-fold, w którym każdy fold zachowuje proporcje klas z całego zbioru. "
                "Ważne przy niezbalansowanych danych i małych zbiorach.",
            ),
            (
                "Na czym polega test A/B modelu?",
                "Losowy podział ruchu między obecny model (kontrola) i nowy (wariant), porównanie "
                "metryki biznesowej i sprawdzenie istotności statystycznej różnicy przed "
                "pełnym wdrożeniem.",
            ),
            (
                "Czym różnią się metryki offline od online?",
                "Offline liczy się na zbiorze testowym przed wdrożeniem (np. AUC). Online mierzy "
                "rzeczywisty efekt na użytkownikach (np. CTR, konwersja). Poprawa offline nie "
                "gwarantuje poprawy online.",
            ),
            (
                "Jakie metryki stosuje się w systemach rekomendacyjnych i wyszukiwaniu?",
                "Precision@k, Recall@k, MRR (średnia odwrotność pozycji pierwszego trafnego "
                "wyniku), NDCG (uwzględnia stopniowaną trafność i pozycję), MAP.",
            ),
            (
                "Co to jest baseline i po co go ustalać?",
                "Prosty punkt odniesienia — np. przewidywanie klasy większościowej, średniej "
                "lub prosta heurystyka/regresja logistyczna. Pozwala ocenić, czy złożony model "
                "wnosi realną wartość.",
            ),
            (
                "Czym jest analiza błędów (error analysis)?",
                "Ręczny przegląd błędnych predykcji, grupowanie ich w kategorie i szacowanie, "
                "które poprawki (dane, cechy, model) dadzą największy zysk. Często cenniejsze "
                "niż strojenie hiperparametrów.",
            ),
            (
                "Czym jest Cohen's kappa?",
                "Miara zgodności dwóch oceniających (lub modelu z etykietami) skorygowana "
                "o zgodność przypadkową. Używana do oceny jakości etykietowania i przy "
                "niezbalansowanych klasach.",
            ),
        ],
    },
    {
        "slug": "mlops-production",
        "name": "MLOps i wdrażanie modeli",
        "icon": "🚀",
        "description": "Wdrażanie, monitorowanie i utrzymanie modeli ML na produkcji.",
        "cards": [
            (
                "Czym jest MLOps?",
                "Zbiór praktyk łączących ML, DevOps i inżynierię danych, by niezawodnie "
                "trenować, wdrażać, monitorować i aktualizować modele na produkcji — "
                "z automatyzacją i powtarzalnością.",
            ),
            (
                "Czym jest data drift?",
                "Zmiana rozkładu danych wejściowych na produkcji względem danych treningowych "
                "(np. nowi użytkownicy, sezonowość). Wykrywana testami statystycznymi "
                "(KS, PSI) na cechach.",
            ),
            (
                "Czym jest concept drift?",
                "Zmiana zależności między cechami a zmienną celu — te same wejścia oznaczają "
                "teraz co innego (np. nowe schematy oszustw). Wymaga ponownego treningu "
                "na nowych etykietach.",
            ),
            (
                "Czym jest training-serving skew?",
                "Rozbieżność między przetwarzaniem danych podczas treningu a podczas inferencji "
                "(np. inna implementacja cechy). Zapobiega jej współdzielony kod cech "
                "i feature store.",
            ),
            (
                "Czym jest feature store?",
                "Centralny magazyn definicji i wartości cech, serwujący je spójnie do treningu "
                "(offline, z poprawnością point-in-time) i do inferencji (online, niskie "
                "opóźnienie). Przykłady: Feast, Tecton.",
            ),
            (
                "Czym jest model registry?",
                "Repozytorium wersji modeli z metadanymi (metryki, dane, kod, parametry) "
                "i statusem (staging, production). Umożliwia audyt i rollback. Przykład: "
                "MLflow Model Registry.",
            ),
            (
                "Po co śledzić eksperymenty (experiment tracking)?",
                "Aby zapisywać parametry, metryki, wersje kodu i danych oraz artefakty każdego "
                "przebiegu — dla porównania wyników i odtwarzalności. Narzędzia: MLflow, "
                "Weights & Biases.",
            ),
            (
                "Czym różni się inferencja batch od online (real-time)?",
                "Batch — predykcje liczone okresowo dla wielu rekordów i zapisywane (tanie, "
                "opóźnione). Online — predykcja na żądanie przez API z niskim opóźnieniem "
                "(droższe, aktualne).",
            ),
            (
                "Czym jest shadow deployment?",
                "Nowy model dostaje kopię ruchu produkcyjnego i liczy predykcje, ale nie wpływa "
                "na użytkowników. Pozwala porównać go z obecnym modelem bez ryzyka.",
            ),
            (
                "Czym jest canary deployment?",
                "Stopniowe wdrażanie nowego modelu na niewielki procent ruchu, monitorowanie "
                "metryk i zwiększanie udziału, jeśli wszystko działa — z szybkim rollbackiem "
                "w razie problemów.",
            ),
            (
                "Co należy monitorować w modelu na produkcji?",
                "Metryki systemowe (opóźnienie, przepustowość, błędy), rozkłady wejść i wyjść "
                "(drift), jakość predykcji (gdy pojawią się etykiety) oraz metryki biznesowe.",
            ),
            (
                "Czym jest wersjonowanie danych i po co je stosować?",
                "Śledzenie wersji zbiorów danych podobnie jak kodu (np. DVC, lakeFS). Pozwala "
                "odtworzyć dokładnie ten sam trening i powiązać model z danymi, na których "
                "powstał.",
            ),
            (
                "Czym jest CI/CD/CT w kontekście ML?",
                "CI — testy kodu, danych i modelu. CD — automatyczne wdrażanie pipeline'u "
                "i modelu. CT (Continuous Training) — automatyczne ponowne trenowanie "
                "po pojawieniu się nowych danych lub wykryciu driftu.",
            ),
            (
                "Jak testuje się systemy ML?",
                "Testy jednostkowe transformacji cech, walidacja danych (schemat, zakresy — "
                "np. Great Expectations), testy jakości modelu względem progu i baseline'u, "
                "testy behawioralne (niezmienniczość) i testy integracyjne API.",
            ),
            (
                "Jakie są popularne formaty i serwery do serwowania modeli?",
                "Formaty: ONNX, TorchScript, SavedModel, safetensors. Serwery: TorchServe, "
                "Triton Inference Server, BentoML, vLLM (dla LLM). Często opakowane w REST/gRPC "
                "API i kontenery.",
            ),
            (
                "Jak zmniejszyć opóźnienie inferencji modelu?",
                "Kwantyzacja, pruning, destylacja do mniejszego modelu, batching żądań, "
                "kompilacja/optymalizacja (ONNX Runtime, TensorRT), cache wyników i użycie "
                "GPU lub dedykowanego sprzętu.",
            ),
            (
                "Czym jest feedback loop w systemach ML?",
                "Sytuacja, gdy predykcje modelu wpływają na dane, na których będzie trenowany "
                "(np. rekomendacje kształtują kliknięcia). Może utrwalać biasy — przeciwdziała "
                "się eksploracją i losowymi próbkami kontrolnymi.",
            ),
            (
                "Dlaczego konteneryzacja (Docker) jest ważna dla modeli ML?",
                "Zamyka model, kod i dokładne wersje zależności w powtarzalnym obrazie, który "
                "działa tak samo lokalnie, w CI i na produkcji, i łatwo się skaluje "
                "(np. w Kubernetes).",
            ),
            (
                "Czym jest wyjaśnialność modeli (SHAP, LIME)?",
                "Metody tłumaczące predykcje. SHAP przypisuje każdej cesze wkład w konkretną "
                "predykcję na bazie wartości Shapleya. LIME dopasowuje lokalny prosty model "
                "wokół wyjaśnianego przykładu.",
            ),
            (
                "Na czym polega rollback modelu i dlaczego trzeba go zaplanować?",
                "Powrót do poprzedniej wersji modelu, gdy nowa psuje metryki. Wymaga "
                "wersjonowania modeli i cech, zachowania kompatybilności API i szybkiego "
                "przełączania (np. przez model registry lub feature flag).",
            ),
        ],
    },
]
