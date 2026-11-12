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
    {
        "slug": "responsible-ai-safety",
        "name": "Etyka, bezpieczeństwo i odpowiedzialne AI",
        "icon": "🛡️",
        "description": "Bias i fairness, bezpieczeństwo LLM, prywatność oraz regulacje (AI Act).",
        "cards": [
            (
                "Jakie są główne źródła biasu w modelach ML?",
                "Bias w danych (niereprezentatywna próba, historyczne uprzedzenia), bias etykiet "
                "(subiektywni anotatorzy), bias pomiaru (cechy będące proxy dla wrażliwych "
                "atrybutów) oraz bias wynikający z wdrożenia i pętli sprzężenia zwrotnego.",
            ),
            (
                "Czym jest demographic parity?",
                "Kryterium fairness: odsetek pozytywnych decyzji modelu powinien być taki sam "
                "w każdej grupie (np. płci), niezależnie od rzeczywistych etykiet.",
            ),
            (
                "Czym jest equalized odds?",
                "Kryterium fairness wymagające równych wartości TPR i FPR we wszystkich grupach — "
                "model ma popełniać podobne błędy niezależnie od przynależności do grupy. "
                "Słabsza wersja (equal opportunity) wymaga tylko równego TPR.",
            ),
            (
                "Dlaczego usunięcie atrybutu wrażliwego (np. płci) nie gwarantuje fairness?",
                "Inne cechy mogą być jego silnymi proxy (np. kod pocztowy, imię, historia "
                "zakupów), więc model nadal może dyskryminować pośrednio. Fairness trzeba "
                "mierzyć, a nie zakładać.",
            ),
            (
                "Czy różne kryteria fairness można spełnić jednocześnie?",
                "Zwykle nie. Gdy częstość klasy pozytywnej różni się między grupami, kalibracja "
                "i equalized odds są matematycznie niemożliwe do jednoczesnego spełnienia "
                "(poza trywialnymi przypadkami) — trzeba świadomie wybrać kryterium.",
            ),
            (
                "Czym jest jailbreak modelu językowego?",
                "Technika omijania zabezpieczeń modelu (np. odgrywanie ról, hipotetyczne "
                "scenariusze, kodowanie treści), by skłonić go do wygenerowania treści, których "
                "odmówiłby w normalnych warunkach.",
            ),
            (
                "Czym różni się jailbreak od prompt injection?",
                "Jailbreak to użytkownik próbujący obejść zasady modelu. Prompt injection to "
                "złośliwe instrukcje wstrzyknięte przez dane z zewnętrznego źródła (dokument, "
                "strona, wynik narzędzia), które przejmują kontrolę nad aplikacją użytkownika.",
            ),
            (
                "Czym jest red teaming w kontekście AI?",
                "Celowe, systematyczne atakowanie modelu przez zespół (ludzi lub inne modele) "
                "w poszukiwaniu szkodliwych zachowań, luk i obejść zabezpieczeń przed "
                "wdrożeniem i w trakcie jego działania.",
            ),
            (
                "Jakie kategorie ryzyka wprowadza unijny AI Act?",
                "Ryzyko niedopuszczalne (zakazane, np. social scoring), wysokie (ścisłe wymagania, "
                "np. rekrutacja, kredyty, medycyna), ograniczone (obowiązki przejrzystości, "
                "np. chatboty, deepfake'i) i minimalne (bez dodatkowych wymogów).",
            ),
            (
                "Jakie obowiązki AI Act nakłada na modele ogólnego przeznaczenia (GPAI)?",
                "Dokumentację techniczną, informacje dla podmiotów budujących na modelu, politykę "
                "zgodności z prawem autorskim i podsumowanie danych treningowych. Modele "
                "z ryzykiem systemowym mają dodatkowo ewaluacje, red teaming i raportowanie "
                "incydentów.",
            ),
            (
                "Czym jest differential privacy?",
                "Formalna gwarancja, że wynik analizy lub modelu prawie się nie zmieni po dodaniu "
                "lub usunięciu danych jednej osoby. Osiąga się ją przez kontrolowane dodawanie "
                "szumu (np. DP-SGD); parametr ε określa poziom prywatności.",
            ),
            (
                "Czym jest membership inference attack?",
                "Atak, w którym na podstawie odpowiedzi modelu ustala się, czy konkretny rekord "
                "był w danych treningowych. Szczególnie skuteczny wobec przeuczonych modeli; "
                "chroni przed nim m.in. differential privacy.",
            ),
            (
                "Czym jest memoryzacja danych treningowych w LLM i dlaczego to problem?",
                "Model potrafi odtworzyć dosłowne fragmenty danych treningowych — w tym dane "
                "osobowe, sekrety czy treści chronione prawem autorskim. Ograniczają ją "
                "deduplikacja danych, filtrowanie PII i filtry wyjścia.",
            ),
            (
                "Czym jest federated learning?",
                "Trening modelu na wielu urządzeniach lub w wielu instytucjach bez przesyłania "
                "surowych danych — do serwera trafiają tylko aktualizacje modelu, które są "
                "agregowane (np. FedAvg).",
            ),
            (
                "Czym jest data poisoning?",
                "Atak polegający na wprowadzeniu spreparowanych przykładów do danych "
                "treningowych, by pogorszyć model lub ukryć w nim backdoor aktywowany "
                "konkretnym wyzwalaczem.",
            ),
            (
                "Czym są adversarial examples?",
                "Wejścia z niewielkimi, często niezauważalnymi dla człowieka zmianami, które "
                "powodują błędną predykcję modelu (np. FGSM dodaje perturbację w kierunku znaku "
                "gradientu). Obrona: adversarial training.",
            ),
            (
                "Czym jest alignment modelu AI?",
                "Dopasowanie zachowania modelu do intencji i wartości ludzi — by był pomocny, "
                "szczery i nieszkodliwy. Techniki: RLHF, DPO, Constitutional AI, ewaluacje "
                "bezpieczeństwa.",
            ),
            (
                "Na czym polega Constitutional AI?",
                "Metoda alignmentu, w której model krytykuje i poprawia własne odpowiedzi według "
                "spisanego zestawu zasad („konstytucji”), a preferencje do treningu generuje AI "
                "zamiast ludzi (RLAIF).",
            ),
            (
                "Czym są model cards i datasheets for datasets?",
                "Ustandaryzowana dokumentacja: model card opisuje przeznaczenie modelu, dane, "
                "metryki (także w podziale na grupy) i ograniczenia; datasheet opisuje "
                "pochodzenie, skład i sposób zbierania zbioru danych.",
            ),
            (
                "Czym są guardrails w aplikacjach LLM?",
                "Warstwy kontroli wokół modelu: filtrowanie wejścia (np. wykrywanie prompt "
                "injection, PII) i wyjścia (moderacja treści, walidacja formatu, sprawdzanie "
                "faktów), ograniczenia tematyczne i uprawnień narzędzi.",
            ),
        ],
    },
    {
        "slug": "llm-inference-optimization",
        "name": "Inferencja i optymalizacja LLM",
        "icon": "⚡",
        "description": "Serwowanie LLM: batching, KV cache, kwantyzacja, dekodowanie i koszty.",
        "cards": [
            (
                "Czym różnią się fazy prefill i decode w inferencji LLM?",
                "Prefill przetwarza cały prompt równolegle i buduje KV cache — jest ograniczony "
                "mocą obliczeniową (compute-bound). Decode generuje tokeny pojedynczo — jest "
                "ograniczony przepustowością pamięci (memory-bound).",
            ),
            (
                "Co to jest TTFT i TPOT?",
                "TTFT (Time To First Token) — czas do pojawienia się pierwszego tokena, zależy "
                "głównie od prefillu. TPOT (Time Per Output Token) — średni czas generowania "
                "każdego kolejnego tokena; razem wyznaczają odczuwalne opóźnienie.",
            ),
            (
                "Dlaczego generowanie tokenów jest memory-bound?",
                "Dla każdego nowego tokena trzeba wczytać z pamięci GPU wszystkie wagi modelu "
                "i KV cache, a obliczeń na bajt jest mało. Wąskim gardłem jest przepustowość "
                "pamięci (HBM), a nie FLOPS.",
            ),
            (
                "Jak oszacować rozmiar KV cache?",
                "2 (K i V) × liczba warstw × liczba głów KV × wymiar głowy × długość sekwencji "
                "× batch × bajty na wartość. Rośnie liniowo z długością kontekstu i rozmiarem "
                "batcha — często zajmuje więcej pamięci niż wagi.",
            ),
            (
                "Czym jest PagedAttention (vLLM)?",
                "Zarządzanie KV cache w blokach o stałym rozmiarze, jak strony pamięci "
                "wirtualnej w systemie operacyjnym. Eliminuje fragmentację i rezerwowanie "
                "pamięci na zapas, pozwala współdzielić prefiksy i obsłużyć większy batch.",
            ),
            (
                "Czym jest continuous batching?",
                "Batching na poziomie iteracji: nowe żądania dołączają do batcha, a zakończone "
                "go opuszczają po każdym kroku dekodowania, zamiast czekać na zakończenie "
                "najdłuższej sekwencji. Znacznie zwiększa przepustowość serwera.",
            ),
            (
                "Na czym polega speculative decoding?",
                "Mały, szybki model (draft) proponuje kilka kolejnych tokenów, a duży model "
                "weryfikuje je w jednym równoległym przebiegu i akceptuje zgodne. Przyspiesza "
                "generowanie bez zmiany rozkładu wyjścia dużego modelu.",
            ),
            (
                "Co optymalizuje FlashAttention?",
                "Liczy attention blokami (tiling) w szybkiej pamięci SRAM GPU, bez zapisywania "
                "pełnej macierzy n×n do HBM. Wynik jest dokładny, a zużycie pamięci liniowe "
                "i obliczenia znacznie szybsze.",
            ),
            (
                "Czym są Multi-Query Attention (MQA) i Grouped-Query Attention (GQA)?",
                "Warianty attention, w których wiele głów Query współdzieli głowy Key/Value: "
                "MQA — jedną dla wszystkich, GQA — jedną na grupę. Zmniejszają KV cache "
                "i przyspieszają dekodowanie przy niewielkiej stracie jakości.",
            ),
            (
                "Czym różnią się kwantyzacje GPTQ, AWQ i GGUF?",
                "GPTQ — kwantyzacja wag po treningu minimalizująca błąd warstwa po warstwie. "
                "AWQ — chroni wagi istotne dla dużych aktywacji. GGUF — format plików llama.cpp "
                "z różnymi poziomami kwantyzacji, popularny do inferencji na CPU i lokalnie.",
            ),
            (
                "Ile pamięci GPU potrzeba na wagi modelu 70B?",
                "Liczba parametrów × bajty na parametr: ok. 140 GB w FP16/BF16, ok. 70 GB "
                "w INT8 i ok. 35 GB w INT4 — plus pamięć na KV cache i aktywacje.",
            ),
            (
                "Czym jest tensor parallelism, a czym pipeline parallelism?",
                "Tensor parallelism dzieli pojedyncze macierze warstwy między GPU (wymaga szybkiej "
                "komunikacji, np. NVLink). Pipeline parallelism przydziela różne warstwy różnym "
                "GPU i przesyła między nimi aktywacje.",
            ),
            (
                "Czym jest prefix caching?",
                "Ponowne wykorzystanie KV cache dla wspólnego początku promptów (np. system "
                "promptu, few-shotów, dokumentu) między żądaniami. Skraca prefill i TTFT oraz "
                "obniża koszt; wymaga stałego prefiksu na początku promptu.",
            ),
            (
                "Czym jest greedy decoding i beam search?",
                "Greedy wybiera w każdym kroku najbardziej prawdopodobny token. Beam search "
                "utrzymuje k najlepszych częściowych sekwencji. Oba są deterministyczne; "
                "w czatach częściej używa się samplingu (temperature, top-p).",
            ),
            (
                "Czym jest constrained decoding?",
                "Ograniczanie dozwolonych tokenów w każdym kroku generowania, tak by wyjście "
                "spełniało gramatykę lub JSON schema (maskowanie logitów). Gwarantuje poprawny "
                "format struktury.",
            ),
            (
                "Od czego zależy koszt wywołania API LLM i jak go obniżyć?",
                "Od liczby tokenów wejściowych i wyjściowych (wyjściowe są zwykle droższe) "
                "oraz wybranego modelu. Obniżają go: krótsze prompty, prompt caching, mniejszy "
                "model do prostych zadań (routing), limit długości odpowiedzi i batch API.",
            ),
            (
                "Czym jest model routing / cascading?",
                "Kierowanie zapytań do tańszego, mniejszego modelu, a do droższego tylko gdy "
                "zadanie jest trudne lub mały model nie jest pewny odpowiedzi. Obniża koszt "
                "i opóźnienie przy podobnej jakości.",
            ),
            (
                "Czym jest throughput a latency w serwowaniu LLM i jak się do siebie mają?",
                "Throughput — liczba tokenów lub żądań na sekundę dla całego serwera; latency — "
                "czas odpowiedzi dla pojedynczego żądania. Większy batch zwiększa throughput, "
                "ale zwykle wydłuża latency.",
            ),
            (
                "Czym jest sliding window attention?",
                "Każdy token zwraca uwagę tylko na ostatnie w tokenów zamiast na całą sekwencję. "
                "Koszt rośnie liniowo z długością, a KV cache jest ograniczony do okna; "
                "informacja z dalszej przeszłości przepływa przez kolejne warstwy.",
            ),
            (
                "Czym jest streaming odpowiedzi LLM i po co go stosować?",
                "Wysyłanie tokenów klientowi na bieżąco (np. przez Server-Sent Events) zamiast "
                "czekać na całą odpowiedź. Nie skraca całkowitego czasu generowania, ale "
                "radykalnie poprawia odczuwalną szybkość (liczy się TTFT).",
            ),
        ],
    },
    {
        "slug": "ai-history",
        "name": "Historia i kamienie milowe AI",
        "icon": "📜",
        "description": "Od testu Turinga i perceptronu do transformerów i ChatGPT.",
        "cards": [
            (
                "Czym jest test Turinga i kiedy został zaproponowany?",
                "Zaproponowany przez Alana Turinga w 1950 r. w artykule „Computing Machinery and "
                "Intelligence”: maszyna przechodzi test, jeśli w rozmowie tekstowej sędzia nie "
                "potrafi jej odróżnić od człowieka („gra w naśladownictwo”).",
            ),
            (
                "Kiedy i gdzie narodził się termin „sztuczna inteligencja”?",
                "Na konferencji w Dartmouth w 1956 r., zorganizowanej m.in. przez Johna "
                "McCarthy'ego, Marvina Minsky'ego, Claude'a Shannona i Nathaniela Rochestera. "
                "Uważa się ją za początek AI jako dziedziny nauki.",
            ),
            (
                "Kto stworzył perceptron i dlaczego był ważny?",
                "Frank Rosenblatt w 1958 r. Był to pierwszy model sztucznego neuronu, który "
                "uczył się wag z danych — prekursor współczesnych sieci neuronowych.",
            ),
            (
                "Jakie ograniczenie perceptronu wykazali Minsky i Papert?",
                "W książce „Perceptrons” (1969) pokazali, że jednowarstwowy perceptron nie "
                "rozwiąże problemów nieseparowalnych liniowo, np. XOR. Przyczyniło się to do "
                "spadku zainteresowania sieciami neuronowymi.",
            ),
            (
                "Czym były „zimy AI”?",
                "Okresy cięć finansowania i spadku zainteresowania AI po niespełnionych "
                "obietnicach: pierwsza w latach 70. (m.in. po raporcie Lighthilla, 1973), "
                "druga pod koniec lat 80. po załamaniu rynku systemów eksperckich.",
            ),
            (
                "Czym była ELIZA?",
                "Program Josepha Weizenbauma z 1966 r. symulujący psychoterapeutę za pomocą "
                "prostych reguł dopasowywania wzorców. Ludzie przypisywali mu zrozumienie — "
                "stąd „efekt ELIZY”.",
            ),
            (
                "Czym były systemy eksperckie?",
                "Popularne w latach 70.–80. systemy oparte na regułach „jeśli–to” spisanych przez "
                "ekspertów (np. MYCIN — diagnoza infekcji, XCON — konfiguracja komputerów). "
                "Trudne w utrzymaniu i nieuczące się z danych.",
            ),
            (
                "Kto spopularyzował backpropagation w sieciach neuronowych?",
                "Rumelhart, Hinton i Williams w artykule z 1986 r. w „Nature”. Pokazali, że "
                "wielowarstwowe sieci trenowane propagacją wsteczną uczą się użytecznych "
                "reprezentacji wewnętrznych.",
            ),
            (
                "Czym był LeNet?",
                "Konwolucyjna sieć neuronowa Yanna LeCuna (od 1989 r., LeNet-5 w 1998 r.) do "
                "rozpoznawania odręcznych cyfr, używana m.in. do odczytu czeków. Wzorzec dla "
                "późniejszych CNN.",
            ),
            (
                "Co osiągnął Deep Blue?",
                "Komputer szachowy IBM, który w 1997 r. wygrał mecz z mistrzem świata Garrim "
                "Kasparowem. Opierał się na przeszukiwaniu drzewa gry i specjalizowanym "
                "sprzęcie, a nie na uczeniu maszynowym.",
            ),
            (
                "Kiedy i przez kogo zaproponowano LSTM?",
                "Sepp Hochreiter i Jürgen Schmidhuber w 1997 r. LSTM rozwiązywało problem "
                "zanikającego gradientu w RNN i przez lata było standardem w przetwarzaniu "
                "sekwencji (mowa, tłumaczenia).",
            ),
            (
                "Dlaczego AlexNet (2012) uważa się za przełom?",
                "Sieć Krizhevsky'ego, Sutskevera i Hintona wygrała konkurs ImageNet z ogromną "
                "przewagą (błąd top-5 ok. 15% vs ok. 26%). Pokazała siłę głębokich CNN trenowanych "
                "na GPU i zapoczątkowała boom deep learningu.",
            ),
            (
                "Co wniosły Word2Vec (2013) i GAN (2014)?",
                "Word2Vec (Mikolov i in., Google) spopularyzował gęste embeddingi słów. GAN "
                "(Ian Goodfellow i in.) wprowadził generowanie danych przez rywalizację "
                "generatora i dyskryminatora.",
            ),
            (
                "Co osiągnął AlphaGo?",
                "Program DeepMind, który w 2016 r. pokonał Lee Sedola 4:1 w go — grze uważanej "
                "za zbyt złożoną dla komputerów. Łączył sieci neuronowe, uczenie ze wzmocnieniem "
                "i Monte Carlo Tree Search.",
            ),
            (
                "Dlaczego artykuł „Attention Is All You Need” jest tak ważny?",
                "Opublikowany w 2017 r. przez zespół Google wprowadził architekturę Transformer "
                "opartą wyłącznie na attention. Stała się ona podstawą BERT-a, GPT i niemal "
                "wszystkich współczesnych LLM.",
            ),
            (
                "Czym wyróżniał się BERT (2018)?",
                "Model Google z dwukierunkowym enkoderem Transformer, pretrenowany zadaniem "
                "Masked Language Modeling. Spopularyzował schemat pretraining + fine-tuning "
                "i pobił rekordy w wielu benchmarkach NLP.",
            ),
            (
                "Co pokazał GPT-3 (2020)?",
                "Model OpenAI ze 175 mld parametrów pokazał, że skalowanie daje zdolność "
                "in-context learning — wykonywania nowych zadań na podstawie kilku przykładów "
                "w prompcie, bez dostrajania.",
            ),
            (
                "Kiedy pojawił się ChatGPT i dlaczego był przełomowy?",
                "30 listopada 2022 r. Model GPT-3.5 dostrojony instrukcjami i RLHF, udostępniony "
                "jako darmowy czat, w kilka tygodni zdobył dziesiątki milionów użytkowników "
                "i zapoczątkował masowe zainteresowanie generatywną AI.",
            ),
            (
                "Co osiągnął AlphaFold?",
                "System DeepMind, który w 2020 r. (CASP14) przewidywał strukturę 3D białek "
                "z dokładnością bliską metodom eksperymentalnym. Jego twórcy (Hassabis, Jumper) "
                "otrzymali w 2024 r. Nagrodę Nobla z chemii.",
            ),
            (
                "Kogo nazywa się „ojcami chrzestnymi deep learningu”?",
                "Geoffreya Hintona, Yanna LeCuna i Yoshuę Bengio — laureatów Nagrody Turinga "
                "za 2018 r. Hinton otrzymał też (z Johnem Hopfieldem) Nagrodę Nobla z fizyki "
                "w 2024 r.",
            ),
        ],
    },
    {
        "slug": "python",
        "name": "Python",
        "icon": "🐍",
        "description": "Język Python na rozmowy techniczne: typy, iteratory, dekoratory, GIL, async.",
        "cards": [
            (
                "Czym różnią się typy mutowalne od niemutowalnych w Pythonie?",
                "Niemutowalnych (int, float, str, tuple, frozenset, bytes) nie da się zmienić "
                "po utworzeniu — „zmiana” tworzy nowy obiekt. Mutowalne (list, dict, set) "
                "można modyfikować w miejscu. Tylko obiekty hashowalne mogą być kluczami dict.",
            ),
            (
                "Dlaczego mutowalny argument domyślny (np. def f(x=[])) to błąd?",
                "Wartość domyślna jest tworzona raz, przy definicji funkcji, i współdzielona "
                "między wywołaniami — lista „pamięta” poprzednie dodania. Poprawnie: "
                "def f(x=None): x = [] if x is None else x.",
            ),
            (
                "Czym różni się == od is?",
                "== porównuje wartości (wywołuje __eq__), is sprawdza tożsamość — czy to ten sam "
                "obiekt w pamięci. is stosuje się do singletonów, np. x is None.",
            ),
            (
                "Czym jest list comprehension a generator expression?",
                "[x*x for x in data] tworzy od razu całą listę w pamięci. (x*x for x in data) "
                "tworzy leniwy generator, który produkuje wartości na żądanie — oszczędza "
                "pamięć przy dużych danych, ale można go przejść tylko raz.",
            ),
            (
                "Czym jest generator i słowo kluczowe yield?",
                "Funkcja z yield zwraca generator — iterator, który wstrzymuje wykonanie przy "
                "każdym yield i wznawia je przy następnym next(). Pozwala leniwie przetwarzać "
                "strumienie danych bez ładowania ich w całości.",
            ),
            (
                "Czym jest dekorator?",
                "Funkcja przyjmująca funkcję i zwracająca nową (zwykle opakowującą) funkcję. "
                "@dec nad def f to skrót dla f = dec(f). Używany do logowania, cache'owania, "
                "autoryzacji; functools.wraps zachowuje nazwę i docstring.",
            ),
            (
                "Czym jest GIL?",
                "Global Interpreter Lock w CPythonie — w danej chwili tylko jeden wątek wykonuje "
                "bajtkod Pythona. Wątki pomagają przy I/O, ale nie przyspieszają obliczeń CPU — "
                "do tego multiprocessing lub biblioteki w C (NumPy). Python 3.13+ ma "
                "eksperymentalny build bez GIL.",
            ),
            (
                "Kiedy użyć threading, multiprocessing, a kiedy asyncio?",
                "threading — zadania I/O-bound z blokującymi bibliotekami. multiprocessing — "
                "zadania CPU-bound (omija GIL osobnymi procesami). asyncio — bardzo wiele "
                "współbieżnych operacji I/O (np. zapytań sieciowych) w jednym wątku.",
            ),
            (
                "Jak działają async i await?",
                "async def tworzy korutynę; await zawiesza ją do czasu zakończenia operacji, "
                "oddając sterowanie pętli zdarzeń, która w tym czasie wykonuje inne korutyny. "
                "asyncio.gather uruchamia wiele korutyn współbieżnie.",
            ),
            (
                "Czym jest context manager i instrukcja with?",
                "Obiekt z metodami __enter__ i __exit__, który gwarantuje sprzątanie zasobów "
                "(zamknięcie pliku, zwolnienie blokady) nawet przy wyjątku. Łatwo go napisać "
                "dekoratorem @contextlib.contextmanager.",
            ),
            (
                "Czym różnią się *args i **kwargs?",
                "*args zbiera nadmiarowe argumenty pozycyjne w krotkę, **kwargs — nazwane "
                "argumenty w słownik. Przy wywołaniu * i ** rozpakowują sekwencję lub słownik "
                "na argumenty.",
            ),
            (
                "Czym różni się kopia płytka od głębokiej?",
                "copy.copy() tworzy nowy obiekt zewnętrzny, ale współdzieli obiekty zagnieżdżone. "
                "copy.deepcopy() rekurencyjnie kopiuje wszystko — zmiana zagnieżdżonej listy "
                "w kopii nie wpływa na oryginał.",
            ),
            (
                "Jaka jest złożoność operacji na list, dict i set?",
                "list: dostęp po indeksie i append O(1), wyszukiwanie (in) i wstawianie na "
                "początek O(n). dict i set: wyszukiwanie, dodawanie i usuwanie średnio O(1) "
                "dzięki tablicy haszującej.",
            ),
            (
                "Czym jest dataclass?",
                "Dekorator @dataclass automatycznie generuje __init__, __repr__ i __eq__ na "
                "podstawie adnotowanych pól. frozen=True czyni instancje niemutowalnymi, "
                "slots=True oszczędza pamięć.",
            ),
            (
                "Do czego służą type hints w Pythonie?",
                "Adnotacje typów (def f(x: int) -> str) nie są sprawdzane w czasie wykonania, "
                "ale umożliwiają statyczną analizę (mypy, pyright), lepsze podpowiedzi w IDE "
                "i walidację w bibliotekach jak Pydantic czy FastAPI.",
            ),
            (
                "Czym jest MRO i jak działa super()?",
                "Method Resolution Order — kolejność przeszukiwania klas przy wielokrotnym "
                "dziedziczeniu, wyznaczana algorytmem C3 (podgląd: Klasa.__mro__). super() "
                "wywołuje metodę następnej klasy w MRO, nie koniecznie bezpośredniego rodzica.",
            ),
            (
                "Czym jest reguła LEGB?",
                "Kolejność wyszukiwania nazw: Local (funkcja), Enclosing (funkcje zewnętrzne), "
                "Global (moduł), Built-in. Do przypisania zmiennej z zewnętrznego zakresu "
                "służą nonlocal i global.",
            ),
            (
                "Czym jest closure (domknięcie)?",
                "Funkcja wewnętrzna, która pamięta zmienne z zakresu funkcji zewnętrznej nawet "
                "po jej zakończeniu. Podstawa dekoratorów i fabryk funkcji.",
            ),
            (
                "Jak zarządzać pamięcią w Pythonie — jak działa garbage collection?",
                "CPython używa zliczania referencji (obiekt usuwany, gdy licznik spada do zera) "
                "oraz cyklicznego garbage collectora z pokoleniami do wykrywania cykli "
                "referencji.",
            ),
            (
                "Po co używać wirtualnych środowisk i jak to robić?",
                "Izolują zależności projektów, by różne wersje pakietów nie kolidowały. "
                "Narzędzia: venv + pip, a nowocześniej uv lub Poetry z plikiem pyproject.toml "
                "i lockfile'em dla powtarzalnych instalacji.",
            ),
        ],
    },
    {
        "slug": "docker",
        "name": "Docker",
        "icon": "🐳",
        "description": "Kontenery, obrazy, Dockerfile, sieci, wolumeny i Docker Compose.",
        "cards": [
            (
                "Czym różni się kontener od maszyny wirtualnej?",
                "Kontener współdzieli jądro systemu hosta i izoluje procesy (namespaces, "
                "cgroups) — jest lekki i startuje w sekundy. Maszyna wirtualna emuluje cały "
                "sprzęt i ma własny system operacyjny z jądrem — cięższa, ale silniej izolowana.",
            ),
            (
                "Czym różni się obraz od kontenera?",
                "Obraz to niezmienny szablon (warstwy systemu plików + metadane). Kontener to "
                "uruchomiona instancja obrazu z dodatkową zapisywalną warstwą. Z jednego obrazu "
                "można uruchomić wiele kontenerów.",
            ),
            (
                "Jak działają warstwy obrazu Dockera?",
                "Każda instrukcja Dockerfile (RUN, COPY, ADD) tworzy warstwę. Warstwy są "
                "cache'owane i współdzielone między obrazami; zmiana jednej unieważnia cache "
                "wszystkich kolejnych.",
            ),
            (
                "Jak uporządkować Dockerfile, by dobrze wykorzystać cache?",
                "Rzadko zmieniające się kroki na początku: najpierw skopiuj plik zależności "
                "(np. pyproject.toml, package.json) i zainstaluj zależności, dopiero potem "
                "kopiuj kod aplikacji — zmiana kodu nie przebuduje wtedy zależności.",
            ),
            (
                "Czym różni się CMD od ENTRYPOINT?",
                "ENTRYPOINT definiuje stały program uruchamiany w kontenerze. CMD podaje "
                "domyślne argumenty (lub domyślną komendę), które można nadpisać w docker run. "
                "Często łączy się je: ENTRYPOINT [\"python\"] + CMD [\"app.py\"].",
            ),
            (
                "Czym różni się COPY od ADD?",
                "COPY tylko kopiuje pliki z kontekstu budowania. ADD dodatkowo rozpakowuje "
                "lokalne archiwa tar i potrafi pobrać plik z URL. Zalecane jest COPY, chyba że "
                "potrzebujesz tych funkcji.",
            ),
            (
                "Czym jest multi-stage build?",
                "Dockerfile z wieloma etapami FROM: w pierwszym budujesz aplikację "
                "(kompilatory, narzędzia), a do finalnego, lekkiego obrazu kopiujesz tylko "
                "wynikowe artefakty. Mniejszy obraz i mniejsza powierzchnia ataku.",
            ),
            (
                "Jak zmniejszyć rozmiar obrazu Dockera?",
                "Mała baza (slim, alpine, distroless), multi-stage build, łączenie poleceń RUN "
                "i czyszczenie cache menedżera pakietów w tej samej warstwie, plik "
                ".dockerignore i instalowanie tylko zależności produkcyjnych.",
            ),
            (
                "Do czego służy plik .dockerignore?",
                "Wyklucza pliki z kontekstu budowania (np. .git, node_modules, .venv, sekrety). "
                "Przyspiesza budowanie, zmniejsza obraz i zapobiega przypadkowemu wrzuceniu "
                "wrażliwych danych.",
            ),
            (
                "Czym różnią się volume, bind mount i tmpfs?",
                "Volume — zarządzany przez Dockera magazyn danych przetrwający usunięcie "
                "kontenera. Bind mount — zamontowany konkretny katalog hosta (wygodny w dev). "
                "tmpfs — dane tylko w pamięci RAM, znikają po zatrzymaniu.",
            ),
            (
                "Dlaczego dane nie powinny być przechowywane w warstwie kontenera?",
                "Zapisywalna warstwa kontenera znika wraz z jego usunięciem i nie jest "
                "współdzielona. Trwałe dane (np. bazy danych) należy trzymać w wolumenach.",
            ),
            (
                "Jakie są podstawowe sterowniki sieci w Dockerze?",
                "bridge (domyślny — prywatna sieć na hoście, kontenery w sieci użytkownika widzą "
                "się po nazwach), host (kontener używa sieci hosta bez izolacji), none (brak "
                "sieci), overlay (sieć między wieloma hostami, np. w Swarm).",
            ),
            (
                "Co oznacza -p 8080:80 w docker run?",
                "Publikuje port: ruch na porcie 8080 hosta jest przekierowywany na port 80 "
                "wewnątrz kontenera. Kolejność to HOST:KONTENER.",
            ),
            (
                "Czym jest Docker Compose?",
                "Narzędzie do definiowania i uruchamiania aplikacji wielokontenerowych z pliku "
                "YAML (usługi, sieci, wolumeny, zmienne). docker compose up uruchamia cały "
                "stos, np. aplikację + bazę danych + Redis.",
            ),
            (
                "Czy depends_on w Compose czeka, aż baza danych będzie gotowa?",
                "Domyślnie nie — czeka tylko na uruchomienie kontenera. Aby czekać na gotowość, "
                "trzeba zdefiniować healthcheck i użyć depends_on z condition: "
                "service_healthy (lub logikę ponawiania w aplikacji).",
            ),
            (
                "Dlaczego nie uruchamiać procesu w kontenerze jako root?",
                "Root w kontenerze to ten sam UID 0 co na hoście; przy ucieczce z kontenera "
                "lub błędnej konfiguracji daje szerokie uprawnienia. Należy utworzyć "
                "nieuprzywilejowanego użytkownika i przełączyć się instrukcją USER.",
            ),
            (
                "Jak bezpiecznie przekazywać sekrety do kontenera?",
                "Nie wpisywać ich w Dockerfile ani nie kopiować do obrazu (zostają w warstwach "
                "i historii). Używać zmiennych środowiskowych z zewnętrznego źródła, Docker/"
                "Kubernetes secrets lub BuildKit --secret przy budowaniu.",
            ),
            (
                "Czym jest HEALTHCHECK w Dockerfile?",
                "Polecenie okresowo sprawdzające, czy aplikacja w kontenerze działa poprawnie "
                "(np. curl na endpoint /health). Status healthy/unhealthy wykorzystują "
                "orkiestratory i Compose.",
            ),
            (
                "Czym jest rejestr obrazów i tag?",
                "Rejestr (Docker Hub, GHCR, ECR) przechowuje i udostępnia obrazy. Tag oznacza "
                "wersję obrazu (np. app:1.4.2). Tag latest jest zmienny — na produkcji lepiej "
                "używać konkretnych wersji lub digestów.",
            ),
            (
                "Jakie komendy pomagają debugować działający kontener?",
                "docker logs (wyjście procesu), docker exec -it <kontener> sh (wejście do "
                "środka), docker inspect (konfiguracja, sieć, wolumeny), docker stats (zużycie "
                "zasobów), docker ps -a (status i kod wyjścia).",
            ),
        ],
    },
    {
        "slug": "aws",
        "name": "AWS",
        "icon": "☁️",
        "description": "Podstawowe usługi Amazon Web Services: obliczenia, dane, sieć, IAM i ML.",
        "cards": [
            (
                "Czym różni się region od strefy dostępności (Availability Zone)?",
                "Region to obszar geograficzny (np. eu-central-1, Frankfurt) z kilkoma "
                "odizolowanymi centrami danych — strefami dostępności (AZ). Rozmieszczenie "
                "zasobów w wielu AZ daje wysoką dostępność.",
            ),
            (
                "Czym jest model współdzielonej odpowiedzialności (shared responsibility)?",
                "AWS odpowiada za bezpieczeństwo chmury (sprzęt, centra danych, infrastrukturę). "
                "Klient odpowiada za bezpieczeństwo w chmurze (dane, konfigurację IAM, "
                "system operacyjny EC2, reguły sieci, szyfrowanie).",
            ),
            (
                "Czym jest IAM i z czego się składa?",
                "Identity and Access Management — zarządzanie dostępem. Elementy: użytkownicy, "
                "grupy, role (tymczasowe uprawnienia dla usług i osób) oraz polityki JSON "
                "określające dozwolone akcje na zasobach.",
            ),
            (
                "Czym jest zasada najmniejszych uprawnień (least privilege)?",
                "Nadawanie tożsamości tylko tych uprawnień, które są niezbędne do jej zadania. "
                "W AWS: wąskie polityki IAM, role zamiast stałych kluczy dostępu i unikanie "
                "używania konta root.",
            ),
            (
                "Dlaczego dla aplikacji na EC2 lepsza jest rola IAM niż klucze dostępu?",
                "Rola dostarcza automatycznie rotowane, tymczasowe poświadczenia przez metadane "
                "instancji. Klucze zapisane w kodzie lub konfiguracji mogą wyciec i nie "
                "wygasają same.",
            ),
            (
                "Czym jest EC2?",
                "Elastic Compute Cloud — wirtualne serwery w chmurze. Wybiera się typ instancji "
                "(CPU, RAM, GPU), obraz systemu (AMI), sieć i dyski (EBS). Modele cenowe: "
                "On-Demand, Reserved/Savings Plans, Spot.",
            ),
            (
                "Czym są instancje Spot i kiedy ich używać?",
                "Niewykorzystana pojemność EC2 dużo taniej (nawet do 90%), ale AWS może je "
                "odebrać z 2-minutowym ostrzeżeniem. Dobre do zadań odpornych na przerwanie: "
                "batch, trening ML z checkpointami, CI.",
            ),
            (
                "Czym jest S3 i jakie ma klasy przechowywania?",
                "Simple Storage Service — magazyn obiektów (pliki w bucketach) o bardzo wysokiej "
                "trwałości. Klasy: Standard, Intelligent-Tiering, Standard-IA, One Zone-IA, "
                "Glacier (archiwum, tańsze, wolniejszy dostęp). Lifecycle policies przenoszą "
                "dane między klasami.",
            ),
            (
                "Jak zabezpieczyć bucket S3?",
                "Włączone Block Public Access, polityki bucketu i IAM z minimalnymi "
                "uprawnieniami, szyfrowanie (SSE-S3/SSE-KMS), wersjonowanie, logowanie dostępu "
                "i presigned URL do tymczasowego udostępniania plików.",
            ),
            (
                "Czym jest AWS Lambda?",
                "Usługa serverless uruchamiająca funkcje w odpowiedzi na zdarzenia (HTTP przez "
                "API Gateway, S3, SQS). Płaci się za liczbę wywołań i czas wykonania; limit "
                "czasu to 15 minut. Wadą bywa cold start.",
            ),
            (
                "Czym jest cold start w AWS Lambda?",
                "Opóźnienie przy pierwszym wywołaniu (lub po bezczynności), gdy AWS musi "
                "utworzyć nowe środowisko i załadować kod. Łagodzą go mniejsze paczki, lżejsze "
                "runtime'y i Provisioned Concurrency.",
            ),
            (
                "Czym jest VPC i czym różni się podsieć publiczna od prywatnej?",
                "Virtual Private Cloud — izolowana sieć w AWS. Podsieć publiczna ma trasę do "
                "Internet Gateway (np. load balancery). Prywatna nie ma — zasoby (np. bazy) "
                "wychodzą do internetu przez NAT Gateway, a z zewnątrz nie są osiągalne.",
            ),
            (
                "Czym różnią się Security Groups od Network ACL?",
                "Security Group działa na poziomie instancji, jest stanowa (ruch powrotny "
                "dozwolony automatycznie) i ma tylko reguły allow. NACL działa na poziomie "
                "podsieci, jest bezstanowa i ma reguły allow oraz deny.",
            ),
            (
                "Czym różnią się RDS i DynamoDB?",
                "RDS — zarządzane relacyjne bazy SQL (PostgreSQL, MySQL, Aurora) z backupami "
                "i replikami. DynamoDB — zarządzana baza NoSQL klucz-wartość/dokumentowa, "
                "serverless, z przewidywalnie niskim opóźnieniem przy dużej skali.",
            ),
            (
                "Czym jest Multi-AZ w RDS, a czym read replica?",
                "Multi-AZ to synchroniczna kopia zapasowa w innej AZ z automatycznym failoverem — "
                "dla wysokiej dostępności. Read replica to asynchroniczna kopia do odciążenia "
                "odczytów — dla skalowania.",
            ),
            (
                "Czym różnią się SQS i SNS?",
                "SQS to kolejka wiadomości (pull) — jeden konsument przetwarza wiadomość, "
                "buforuje i rozprzęga usługi. SNS to pub/sub (push) — jedna wiadomość trafia "
                "do wielu subskrybentów. Często łączy się je we wzorzec fan-out.",
            ),
            (
                "Czym są ECS, EKS i Fargate?",
                "ECS — natywny orkiestrator kontenerów AWS. EKS — zarządzany Kubernetes. "
                "Fargate — tryb serverless dla ECS/EKS, w którym nie zarządzasz serwerami, "
                "tylko definiujesz CPU i pamięć zadania.",
            ),
            (
                "Czym jest CloudWatch?",
                "Usługa monitoringu AWS: metryki zasobów i aplikacji, logi (CloudWatch Logs), "
                "alarmy wyzwalające powiadomienia lub autoskalowanie oraz dashboardy.",
            ),
            (
                "Czym jest SageMaker, a czym Bedrock?",
                "SageMaker — platforma do budowania, trenowania i wdrażania własnych modeli ML "
                "(notebooki, joby treningowe, endpointy). Bedrock — serverless dostęp przez API "
                "do gotowych modeli fundamentowych (m.in. Claude, Llama) z opcją RAG i agentów.",
            ),
            (
                "Czym jest Infrastructure as Code w AWS?",
                "Definiowanie infrastruktury w plikach wersjonowanych w repozytorium zamiast "
                "klikania w konsoli. Narzędzia: CloudFormation (natywny, YAML/JSON), AWS CDK "
                "(w językach programowania), Terraform (wielochmurowy).",
            ),
        ],
    },
    {
        "slug": "kubernetes",
        "name": "Kubernetes",
        "icon": "☸️",
        "description": "Orkiestracja kontenerów: pody, deploymenty, serwisy, konfiguracja i skalowanie.",
        "cards": [
            (
                "Czym jest Kubernetes?",
                "Platforma do orkiestracji kontenerów: automatyzuje wdrażanie, skalowanie, "
                "self-healing i zarządzanie siecią aplikacji kontenerowych na klastrze maszyn. "
                "Działa deklaratywnie — opisujesz stan docelowy w YAML.",
            ),
            (
                "Z jakich elementów składa się control plane?",
                "kube-apiserver (punkt wejścia API), etcd (magazyn stanu klastra), "
                "kube-scheduler (przydziela pody do węzłów) oraz kube-controller-manager "
                "(pętle kontrolne doprowadzające stan do docelowego).",
            ),
            (
                "Co działa na każdym węźle roboczym (worker node)?",
                "kubelet (uruchamia i pilnuje podów zgodnie ze specyfikacją), container runtime "
                "(np. containerd) oraz kube-proxy (reguły sieciowe dla Service).",
            ),
            (
                "Czym jest Pod?",
                "Najmniejsza jednostka wdrożeniowa — jeden lub kilka kontenerów współdzielących "
                "adres IP, sieć i wolumeny. Pody są efemeryczne; zwykle nie tworzy się ich "
                "ręcznie, tylko przez Deployment.",
            ),
            (
                "Czym jest Deployment?",
                "Obiekt zarządzający bezstanową aplikacją: utrzymuje zadaną liczbę replik "
                "podów (przez ReplicaSet), wykonuje rolling update i umożliwia rollback "
                "(kubectl rollout undo).",
            ),
            (
                "Na czym polega rolling update?",
                "Stopniowa wymiana podów starej wersji na nową — tak, by część replik zawsze "
                "obsługiwała ruch. Tempo kontrolują maxSurge i maxUnavailable, a gotowość "
                "nowych podów — readiness probe.",
            ),
            (
                "Czym jest Service i jakie są jego typy?",
                "Stały adres i load balancing dla zmiennego zestawu podów wybranych etykietami. "
                "Typy: ClusterIP (tylko wewnątrz klastra), NodePort (port na każdym węźle), "
                "LoadBalancer (zewnętrzny balancer chmury), ExternalName (alias DNS).",
            ),
            (
                "Czym jest Ingress?",
                "Obiekt definiujący reguły routingu HTTP/HTTPS z zewnątrz do serwisów "
                "(po hoście i ścieżce), z obsługą TLS. Wymaga działającego Ingress Controllera "
                "(np. NGINX, Traefik). Nowszą alternatywą jest Gateway API.",
            ),
            (
                "Czym różni się ConfigMap od Secret?",
                "ConfigMap przechowuje niewrażliwą konfigurację, Secret — dane wrażliwe "
                "(hasła, tokeny). Oba można wstrzyknąć jako zmienne środowiskowe lub pliki. "
                "Secret jest domyślnie tylko zakodowany base64, nie zaszyfrowany.",
            ),
            (
                "Czym różnią się liveness, readiness i startup probe?",
                "Liveness — czy kontener żyje; po porażce jest restartowany. Readiness — czy pod "
                "jest gotowy na ruch; jeśli nie, znika z endpointów Service. Startup — "
                "wstrzymuje pozostałe sondy, dopóki wolno startująca aplikacja się nie uruchomi.",
            ),
            (
                "Czym są requests i limits zasobów?",
                "Requests — gwarantowana ilość CPU/pamięci, na podstawie której scheduler "
                "wybiera węzeł. Limits — górna granica: przekroczenie CPU powoduje throttling, "
                "przekroczenie pamięci — zabicie kontenera (OOMKilled).",
            ),
            (
                "Czym jest Horizontal Pod Autoscaler (HPA)?",
                "Automatycznie zmienia liczbę replik Deploymentu na podstawie metryk (np. "
                "zużycia CPU względem requests albo metryk własnych). Wymaga metrics-server. "
                "Dodawanie węzłów to zadanie Cluster Autoscalera.",
            ),
            (
                "Czym jest StatefulSet i kiedy go używać zamiast Deploymentu?",
                "Dla aplikacji stanowych (bazy danych, Kafka): pody mają stabilne nazwy "
                "(app-0, app-1), uporządkowane uruchamianie i własne trwałe wolumeny "
                "(volumeClaimTemplates).",
            ),
            (
                "Czym są DaemonSet, Job i CronJob?",
                "DaemonSet uruchamia po jednym podzie na każdym (lub wybranym) węźle — np. "
                "agenty logów i monitoringu. Job wykonuje zadanie do skutku, CronJob — "
                "cyklicznie według harmonogramu.",
            ),
            (
                "Czym są PersistentVolume i PersistentVolumeClaim?",
                "PV to zasób dyskowy w klastrze. PVC to żądanie aplikacji o pamięć określonego "
                "rozmiaru i trybu dostępu. StorageClass pozwala tworzyć PV dynamicznie "
                "(np. dysk EBS) w odpowiedzi na PVC.",
            ),
            (
                "Czym jest Namespace?",
                "Logiczny podział klastra na izolowane przestrzenie nazw (np. dev, staging, "
                "zespoły). Pozwala stosować osobne uprawnienia RBAC, limity zasobów "
                "(ResourceQuota) i polityki sieciowe.",
            ),
            (
                "Co oznacza status CrashLoopBackOff i jak go debugować?",
                "Kontener wielokrotnie startuje i się wywraca, a Kubernetes wydłuża odstępy "
                "między restartami. Debugowanie: kubectl logs <pod> --previous, kubectl describe "
                "pod (zdarzenia, kod wyjścia, OOMKilled), sprawdzenie konfiguracji i sond.",
            ),
            (
                "Czym jest RBAC w Kubernetes?",
                "Role-Based Access Control: Role/ClusterRole definiują dozwolone akcje "
                "na zasobach, a RoleBinding/ClusterRoleBinding przypisują je użytkownikom, "
                "grupom lub ServiceAccountom.",
            ),
            (
                "Czym jest Helm?",
                "Menedżer pakietów dla Kubernetes. Chart to szablon manifestów z parametrami "
                "(values.yaml), co ułatwia instalację, wersjonowanie, aktualizację i rollback "
                "aplikacji.",
            ),
            (
                "Czym są labels i selectors?",
                "Etykiety to pary klucz-wartość przypisane do obiektów (np. app: api). "
                "Selektory wybierają obiekty po etykietach — tak Service i Deployment wiedzą, "
                "którymi podami zarządzają.",
            ),
        ],
    },
    {
        "slug": "javascript",
        "name": "JavaScript",
        "icon": "🟨",
        "description": "JavaScript na rozmowy: zakresy, domknięcia, this, event loop, async i ES6+.",
        "cards": [
            (
                "Czym różnią się var, let i const?",
                "var ma zasięg funkcyjny i jest hoistowany z wartością undefined. let i const "
                "mają zasięg blokowy i leżą w temporal dead zone do deklaracji. const "
                "uniemożliwia ponowne przypisanie, ale obiekt nadal można modyfikować.",
            ),
            (
                "Czym jest hoisting?",
                "Przenoszenie deklaracji na początek zakresu w fazie kompilacji. Deklaracje "
                "funkcji są hoistowane w całości, var — jako undefined, a let/const/class "
                "są hoistowane, ale niedostępne przed deklaracją (TDZ, ReferenceError).",
            ),
            (
                "Czym różni się == od ===?",
                "== porównuje z niejawną konwersją typów (np. 0 == '0' jest true). === porównuje "
                "bez konwersji — wartość i typ muszą być równe. W praktyce używa się ===.",
            ),
            (
                "Czym jest closure w JavaScripcie?",
                "Funkcja zachowująca dostęp do zmiennych z zakresu, w którym została "
                "zdefiniowana, nawet po zakończeniu funkcji zewnętrznej. Używane do "
                "enkapsulacji stanu, fabryk funkcji i obsługi zdarzeń.",
            ),
            (
                "Od czego zależy wartość this?",
                "Od sposobu wywołania: metoda obiektu — obiekt; zwykłe wywołanie — undefined "
                "(strict mode) lub globalThis; new — nowy obiekt; call/apply/bind — wskazany "
                "obiekt. Funkcje strzałkowe nie mają własnego this — dziedziczą je z otoczenia.",
            ),
            (
                "Czym różnią się call, apply i bind?",
                "call i apply wywołują funkcję od razu z podanym this — call przyjmuje argumenty "
                "po przecinku, apply jako tablicę. bind zwraca nową funkcję z trwale ustawionym "
                "this (i opcjonalnie argumentami).",
            ),
            (
                "Jak działa event loop?",
                "JavaScript wykonuje kod w jednym wątku. Po opróżnieniu call stacku event loop "
                "najpierw wykonuje wszystkie mikrozadania (Promise, queueMicrotask), potem "
                "jedno makrozadanie (setTimeout, zdarzenia I/O) i powtarza cykl.",
            ),
            (
                "Co wypisze: setTimeout(() => log('A'), 0); Promise.resolve().then(() => log('B')); log('C')?",
                "C, B, A. Kod synchroniczny wykonuje się najpierw, potem mikrozadania (then), "
                "a dopiero na końcu makrozadania (setTimeout), nawet z opóźnieniem 0.",
            ),
            (
                "Czym jest Promise i jakie ma stany?",
                "Obiekt reprezentujący przyszły wynik operacji asynchronicznej. Stany: pending, "
                "fulfilled (resolve) i rejected (reject). Wynik obsługuje się przez then/catch/"
                "finally lub await.",
            ),
            (
                "Czym różnią się Promise.all, allSettled, race i any?",
                "all — czeka na wszystkie, odrzuca przy pierwszym błędzie. allSettled — czeka "
                "na wszystkie i zwraca status każdej. race — wynik pierwszej zakończonej "
                "(sukces lub błąd). any — pierwszy sukces, błąd tylko gdy wszystkie zawiodą.",
            ),
            (
                "Jak działa async/await i jak obsługiwać błędy?",
                "async funkcja zawsze zwraca Promise; await wstrzymuje ją do rozwiązania "
                "obietnicy bez blokowania wątku. Błędy łapie się try/catch. Niezależne operacje "
                "warto uruchamiać równolegle przez Promise.all zamiast kolejnych await.",
            ),
            (
                "Czym jest dziedziczenie prototypowe?",
                "Każdy obiekt ma ukryte łącze [[Prototype]] do innego obiektu; przy braku "
                "właściwości wyszukiwanie idzie w górę łańcucha prototypów. Składnia class "
                "jest cukrem syntaktycznym nad tym mechanizmem.",
            ),
            (
                "Czym różnią się funkcje strzałkowe od zwykłych?",
                "Nie mają własnego this, arguments ani super (biorą je z otoczenia), nie mogą "
                "być konstruktorami (new) i mają krótszą składnię. Nie nadają się na metody "
                "obiektów korzystające z this.",
            ),
            (
                "Jakie są typy prymitywne w JavaScripcie?",
                "string, number, bigint, boolean, undefined, null i symbol. Wszystko inne to "
                "obiekty (w tym tablice i funkcje). Uwaga: typeof null zwraca 'object' "
                "(historyczny błąd).",
            ),
            (
                "Czym różnią się null i undefined?",
                "undefined oznacza, że wartość nie została przypisana (np. brak argumentu, "
                "brak właściwości). null to celowo ustawiony „brak wartości”. null == undefined "
                "jest true, ale null === undefined — false.",
            ),
            (
                "Czym są operatory ?. i ???",
                "Optional chaining (a?.b) zwraca undefined zamiast rzucić błąd, gdy a jest "
                "null/undefined. Nullish coalescing (a ?? b) zwraca b tylko gdy a jest "
                "null/undefined — w przeciwieństwie do ||, które reaguje też na 0 i ''.",
            ),
            (
                "Czym są destrukturyzacja oraz operatory spread i rest?",
                "Destrukturyzacja wyciąga wartości: const {a, b} = obj; const [x, y] = arr. "
                "Spread (...) rozkłada tablicę lub obiekt (kopie, łączenie), rest (...) zbiera "
                "pozostałe elementy lub argumenty w tablicę lub obiekt.",
            ),
            (
                "Czym różnią się debounce i throttle?",
                "Debounce wywołuje funkcję dopiero po ustaniu zdarzeń przez zadany czas "
                "(np. wyszukiwanie po skończeniu pisania). Throttle wywołuje ją najwyżej raz "
                "na dany przedział czasu (np. obsługa scrolla).",
            ),
            (
                "Czym jest event delegation?",
                "Podpięcie jednego listenera na elemencie nadrzędnym zamiast na wielu dzieciach — "
                "dzięki propagacji (bubbling) zdarzeń; cel rozpoznaje się przez event.target. "
                "Działa też dla elementów dodanych później.",
            ),
            (
                "Czym różnią się moduły ES (import/export) od CommonJS (require)?",
                "ES Modules są standardem języka, ładowane statycznie (umożliwiają tree-shaking) "
                "i asynchronicznie, działają w przeglądarce i Node. CommonJS (require/"
                "module.exports) to starszy, synchroniczny system modułów Node.js.",
            ),
        ],
    },
]
