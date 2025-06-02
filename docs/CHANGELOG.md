# Historia zmian (Changelog)

Wszystkie znaczące zmiany w projekcie będą dokumentowane w tym pliku.

Format jest oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/).
Na projekcie stosowane jest [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.11.0] - 2025-05-26

### Dodano w wersji 1.11.0

- Kompleksowy system zarządzania obrazami w bibliotece
  - Nowe polecenie `optimize_library_images` do optymalizacji i zarządzania obrazami bibliotecznymi
  - Nowe polecenie `ensure_unique_image_filenames` do zapewnienia unikalnych i spójnych nazw plików obrazów
  - Nowe polecenie `verify_image_references` do weryfikacji i naprawy uszkodzonych referencji obrazów
  - Nowe polecenie `fix_specific_books` do naprawy konkretnych książek z nieprawidłowymi tytułami i brakującymi obrazami
- Nowe polecenie `cleanup_book_templates` do porządkowania szablonów i zapewnienia spójności nazewnictwa
  - Automatyczne wykrywanie i usuwanie duplikatów szablonów
  - Przenoszenie szablonów do właściwych katalogów
  - Tworzenie kopii zapasowych przed usunięciem plików
- Nowe polecenie `fix_book_data` do naprawy problemów z danymi książek
  - Naprawianie brakujących kategorii/gatunków książek
  - Usuwanie zduplikowanych autorów i zastępowanie "Unknown Author" prawdziwymi autorami
  - Naprawianie nieprawidłowych opisów książek (np. ISBN jako opis)
  - Konfigurowalny system korekcji danych oparty na plikach JSON
- Nowy model `Category` do lepszej organizacji książek
  - Automatyczna migracja gatunków z pola JSON do relacji many-to-many
  - Generowanie slugów dla łatwiejszego filtrowania i adresowania URL
  - Integracja z istniejącym systemem wyświetlania książek
- Nowe polecenie `fix_publisher_author_data` do naprawy danych wydawców i autorów
  - Naprawianie nieprawidłowych opisów wydawców (np. dane CSV w opisie)
  - Dodawanie profesjonalnych biografii dla autorów
  - Usuwanie pozostałych wpisów "Unknown Author"
  - Konfigurowalny system korekcji danych oparty na plikach JSON

### Ulepszenia w wersji 1.11.0

- Usprawniony system generowania obrazów AI
  - Zoptymalizowane wymiary obrazów (512x768 dla okładek książek, 512x512 dla zdjęć autorów/logo wydawców)
  - Ulepszone prompte dla generowania obrazów z bardziej szczegółowymi wskazówkami
  - Zmniejszone rozmiary plików obrazów przy zachowaniu jakości
- Uporządkowana struktura szablonów dla lepszej organizacji i wydajności
  - Usunięto nieużywane i zduplikowane szablony
  - Zapewniono spójne nazewnictwo plików szablonów
  - Poprawiono lokalizację szablonów testowych
- Usprawniony system kategoryzacji książek
  - Migracja z pola JSON na relacyjny model kategorii
  - Automatyczne tworzenie kategorii na podstawie istniejących gatunków
  - Wsadowe przetwarzanie danych dla lepszej wydajności
- Ulepszone dane bibliograficzne i wydawnicze
  - Profesjonalne biografie dla wszystkich autorów
  - Szczegółowe opisy wydawnictw z danymi kontaktowymi
  - Polskie nazwy kategorii dla lepszej integracji z systemem filtrowania

### Poprawki błędów w wersji 1.11.0

- Usunięto duplikaty książek w bazie danych z zachowaniem powiązanych recenzji i danych
- Naprawiono nieprawidłowe tytuły książek (zamieniono numery ISBN na właściwe tytuły)
- Poprawiono nazwy plików obrazów, aby zapewnić unikalność i spójność
- Naprawiono problemy z brakującymi obrazami dla książek z serii "Flu"
- Rozwiązano problem z nieprawidłową lokalizacją szablonu `test_images.html`
- Usunięto zduplikowane pliki szablonów z niespójnymi nazwami (`.new`, `.fixed`, itp.)
- Naprawiono 18 książek z nieprawidłowymi opisami (ISBN jako opis)
- Poprawiono problem zduplikowanych autorów w książkach
- Zastąpiono "Unknown Author" prawdziwymi autorami (np. Dan Brown dla "Kod Leonarda da Vinci", Gina Kolata dla "Flu")
- Dodano brakujące gatunki do książek
- Rozwiązano problem wyświetlania kategorii książek w szablonach
- Naprawiono problem z wydajnością przy przetwarzaniu dużej liczby książek
- Usunięto dane CSV z opisów wydawców i zastąpiono je profesjonalnymi opisami
- Naprawiono puste lub generyczne biografie autorów
- Usunięto wszystkie pozostałe wpisy "Unknown Author" (3) i zastąpiono je właściwymi autorami
- Poprawiono problem z filtrowaniem książek po kategoriach dzięki polskim nazwom kategorii
- Naprawiono filtrowanie książek według gatunków
  - Dodano nowe polecenie `fix_book_genres` do standaryzacji gatunków książek
  - Usprawniono logikę filtrowania dla obsługi różnych formatów danych w polu JSONField
  - Zaktualizowano wszystkie książki, aby używały standardowych identyfikatorów gatunków
  - Zapewniono zgodność między gatunkami książek a listą filtrów w interfejsie użytkownika

## [1.10.0] - 2025-05-26

### Ulepszenia interfejsu w 1.10.0

- Kompleksowa poprawa paginacji we wszystkich szablonach
  - Dodano `{{ request.path }}` do wszystkich linków paginacji, aby zachować kontekst strony
  - Zachowano wszystkie parametry zapytania (filtry, opcje sortowania) podczas nawigacji między stronami
  - Poprawiono warunek wyświetlania kontrolek paginacji, aby pojawiały się tylko wtedy, gdy jest więcej niż jedna strona

### Poprawki błędów w wersji 1.10.0

- Naprawiono funkcjonalność "Zgłoś błąd" dla książek, autorów i wydawców
  - Połączono przyciski "Zgłoś błąd" z odpowiednimi modalami do zgłaszania problemów
  - Zaimplementowano spójny mechanizm zgłaszania problemów dla wszystkich typów encji
  - Zaktualizowano JavaScript do obsługi zgłoszeń błędów dla wszystkich typów encji
- Naprawiono wyświetlanie dostępności książek na stronach szczegółów wydawcy i autora
  - Zaktualizowano logikę dostępności książek, aby używać `available_copies` zamiast `available`
  - Zapewniono poprawne wyświetlanie książek jako "Dostępna" lub "Niedostępna" na podstawie liczby dostępnych egzemplarzy
- Naprawiono zepsute linki do obrazów dla powiązanych wydawców

## [1.9.0] - 2025-05-25

### Dodano w wersji 1.9.0

- Reorganizacja struktury projektu dla lepszej organizacji kodu
  - Utworzono katalog `library/ai_utils` dla plików związanych z generowaniem obrazów AI
  - Utworzono katalog `library/utils` dla narzędzi pomocniczych
  - Utworzono katalog `library/ui_images` dla plików związanych z generowaniem obrazów UI
  - Utworzono katalog `scripts` dla skryptów narzędziowych
- Zaktualizowano ścieżki URL w szablonach (usunięto prefiks 'library:')
- Zaktualizowano ścieżki do plików AI w module `ai_signals.py`
- Zaktualizowano dokumentację projektu
  - Dodano szczegółowy plan rozwoju projektu w `docs/development-roadmap.md`
  - Zaktualizowano README.md o informacje o testach i strukturze projektu
  - Zaktualizowano CHANGELOG.md o informacje o najnowszych zmianach

### Usunięto w wersji 1.9.0

- Usunięto niepotrzebne pliki i katalogi
  - Usunięto katalog `test_images`
  - Usunięto katalog `outputs`
  - Usunięto katalog `zad_galeria` (stara konfiguracja projektu)
  - Usunięto katalog `staticfiles` (pliki generowane automatycznie)

### Poprawki błędów w wersji 1.9.0

- Naprawiono problemy z ścieżkami do plików AI po reorganizacji struktury projektu
- Poprawiono importy w modułach po przeniesieniu plików do nowych katalogów

## [1.8.0] - 2025-05-25

### Dodano w wersji 1.8.0

- Kompleksowy zestaw testów dla całego projektu
  - Testy modeli (Book, Author, Publisher, BookLoan, BookReservation, Review, LateFee, LibrarySettings)
  - Testy widoków (podstawowe, wypożyczenia, recenzje, opłaty za opóźnienia)
  - Testy sygnałów AI do generowania obrazów
  - Testy tłumaczeń i lokalizacji
  - Testy end-to-end dla kompletnych przepływów użytkownika
- Testy generowania zdjęć profilowych użytkowników
- Testy generowania obrazów UI dla biblioteki
- Dokumentacja testów w README.md

### Ulepszenia interfejsu w 1.8.0

- Przeprojektowano nagłówek, aby był bardziej profesjonalny i spójny
- Ulepszono wygląd przycisków logowania i rejestracji
- Zoptymalizowano układ elementów nawigacyjnych
- Poprawiono styl i formatowanie menu rozwijanego

### Poprawki błędów w 1.8.0

- Naprawiono wyświetlanie obrazów okładek książek i zdjęć autorów
- Poprawiono ścieżki do obrazów w szablonach (book_covers/ → covers/)
- Usunięto angielskie teksty z opisów książek i autorów
- Przetłumaczono tytuły książek na język polski

## [1.7.0] - 2025-05-25

### Dodano w wersji 1.7.0

- Pełna lokalizacja interfejsu na język polski
- Zoptymalizowany nagłówek z konsolidacją opcji użytkownika w jednym menu
- Sekcje w menu użytkownika z nagłówkami dla lepszej organizacji
- Ikony dla wszystkich opcji menu dla lepszej czytelności

### Ulepszenia interfejsu w 1.7.0

- Przeprojektowano nagłówek, aby był bardziej profesjonalny i spójny
- Ulepszono wygląd przycisków logowania i rejestracji
- Zoptymalizowano układ elementów nawigacyjnych
- Poprawiono styl i formatowanie menu rozwijanego

### Poprawki błędów w 1.7.0

- Naprawiono wyświetlanie obrazów okładek książek i zdjęć autorów
- Poprawiono ścieżki do obrazów w szablonach (book_covers/ → covers/)
- Usunięto angielskie teksty z opisów książek i autorów
- Przetłumaczono tytuły książek na język polski

## [1.6.0] - 2025-05-25

### Dodano w wersji 1.6.0

- Nowoczesny interfejs użytkownika z naturą inspirowaną paletą kolorów
- Ulepszony nagłówek i stopka z intuicyjną nawigacją
- Nowe style kart książek i autorów z efektami hover i płynnymi przejściami
- Responsywny design dostosowany do wszystkich urządzeń
- Zmienne CSS dla spójnej palety kolorów w całej aplikacji

### Ulepszenia interfejsu w 1.6.0

- Usunięto zależność od django-crispy-forms i crispy-bootstrap5
- Zaktualizowano dokumentację projektu, dodając informacje o nowym interfejsie
- Zastosowano domyślne renderowanie formularzy Django zamiast crispy-forms
- Ulepszono wizualne aspekty formularzy i przycisków
- Zoptymalizowano style CSS dla lepszej wydajności

### Poprawki błędów w 1.6.0

- Rozwiązano problem z brakującym modułem crispy_forms
- Poprawiono ścieżki do obrazów w szablonach

## [1.5.0] - 2025-05-25

### Dodano - Generowanie obrazów AI

- Zaawansowany system generowania obrazów dla książek, autorów i wydawców
- Integracja z modelem Flux AI do tworzenia realistycznych grafik
- Moduł `generate_images.py` do podstawowego generowania obrazów
- Moduł `advanced_image_generator.py` do zaawansowanego generowania obrazów z AI
- Moduł `flux_wrapper.py` do bezpiecznej integracji z Flux AI
- Mechanizm automatycznego fallbacku do podstawowego generatora w przypadku problemów z zależnościami AI
- Skrypty testowe do weryfikacji generowania obrazów
- Generowanie wykresów statystycznych (historia wypożyczeń, popularne książki, aktywność użytkowników, rozkład gatunków)

### Zmieniono - Dokumentacja i modele

- Zaktualizowano dokumentację projektu, dodając informacje o systemie generowania obrazów
- Rozszerzono modele `Book`, `Author` i `Publisher` o pola do przechowywania ścieżek do wygenerowanych obrazów

## [1.4.0] - 2025-05-25

### Dodano - Raporty i Statystyki

- System raportów i statystyk bibliotecznych
- Model `Report` do przechowywania raportów z różnych kategorii
- Model `Dashboard` do tworzenia konfigurowalnych pulpitów z widgetami
- Model `DashboardWidget` do prezentacji danych w formie wykresów i tabel
- Model `ReportExport` do śledzenia eksportów raportów
- Funkcje generowania raportów dla różnych typów danych (wypożyczenia, popularne książki, przychody, itp.)
- Możliwość eksportu raportów do formatów CSV, Excel i JSON
- Interaktywne dashboardy z odświeżanymi automatycznie widgetami
- Panel administracyjny do zarządzania raportami i dashboardami

### Zmieniono - Interfejs i Dokumentacja

- Dodano link do systemu raportów w menu administratora
- Zaktualizowano dokumentację projektu, dodając informacje o systemie raportów i statystyk
- Skonfigurowano email backend do wyświetlania wiadomości w konsoli podczas rozwoju

## [1.3.0] - 2025-05-25

### Dodano - System Opłat

- System opłat za przetrzymanie książek
- Model `LibrarySettings` do przechowywania globalnych ustawień biblioteki
- Model `LateFee` do śledzenia opłat za przetrzymanie
- Automatyczne naliczanie opłat za przetrzymanie książek
- Panel zarządzania opłatami dla administratorów
- Możliwość opłacania kar online przez użytkowników
- System wniosków o umorzenie opłat
- Rozbudowany interfejs administratora do zarządzania opłatami
- Statystyki opłat (oczekujące, opłacone, umorzone)

### Zmieniono

- Rozszerzono model BookLoan o pole `late_fee_paid` i metody do obliczania opłat
- Zaktualizowano interfejs administratora dla wypożyczeń, dodając informacje o opłatach
- Dodano nowe widoki i szablony do zarządzania opłatami
- Zaktualizowano dokumentację projektu, dodając informacje o systemie opłat

## [1.2.0] - 2025-05-25

### Dodano

- System recenzji książek umożliwiający użytkownikom ocenianie i komentowanie książek
- Model `Review` do przechowywania recenzji użytkowników
- Formularze do dodawania, edycji i usuwania recenzji
- Panel moderacji recenzji w interfejsie administratora
- Wyświetlanie średniej oceny i liczby recenzji na stronie szczegółów książki
- Zakładkę "Recenzje" na stronie szczegółów książki z listą recenzji i formularzem dodawania nowej recenzji
- Graficzną reprezentację ocen w postaci gwiazdek
- Wykres rozkładu ocen dla każdej książki
- Walidację zapobiegającą dodaniu wielu recenzji przez jednego użytkownika

### Zmieniono

- Zaktualizowano szablon book_detail_tabs.html, dodając zakładkę z recenzjami
- Rozszerzono model Book o metody do obliczania średniej oceny i liczby recenzji
- Zaktualizowano dokumentację projektu, dodając informacje o systemie recenzji

## [1.1.0] - 2025-05-20

### Naprawiono

- Poprawiono system filtrowania książek w widoku book_list
- Naprawiono błąd związany z filtrowaniem po gatunkach w bazie SQLite
- Poprawiono szablon book_detail.html, rozwiązując problem z niezamkniętymi tagami
- Zaktualizowano linki w szablonach author_detail.html i publisher_detail.html
- Zaimplementowano funkcjonalne filtry w szablonie book_list.html
- Dodano możliwość sortowania książek według tytułu i daty publikacji
- Naprawiono wyświetlanie imion autorów w sekcji "Polecani autorzy"
- Poprawiono gramatykę polską przy wyświetlaniu liczby książek autorów (książka/książki/książek)

### Zmieniono

- Ulepszono interfejs użytkownika dla filtrowania książek
- Zoptymalizowano zapytania do bazy danych w widoku book_list
- Poprawiono wygląd kart autorów w sekcji "Polecani autorzy"

## [Nadchodzące zmiany] - YYYY-MM-DD

### Nadchodzące zmiany

- Nowe funkcjonalności, które zostaną dodane w następnej wersji

### Planowane zmiany

- Istniejące funkcjonalności, które zostaną zmodyfikowane

### Planowane usunięcia

- Funkcjonalności, które zostaną usunięte

### Planowane poprawki

- Błędy, które zostaną naprawione

## [1.0.0] - 2024-03-15

### Nowe funkcjonalności

- Podstawowa struktura projektu Django
- Modele dla książek, autorów, wydawnictw i wypożyczeń
- System uwierzytelniania użytkowników z różnymi rolami
- Panel administracyjny do zarządzania zasobami biblioteki
- System rezerwacji książek
- Moduł recenzji i oceniania książek
- System powiadomień email
- Dokumentacja projektu w pliku README.md

### Zmieniono - Struktura projektu

- Przekształcono oryginalną galerię zdjęć w system zarządzania biblioteką
- Zaktualizowano modele danych do obsługi systemu bibliotecznego
- Zmodernizowano interfejs użytkownika

## [0.1.0] - 2024-01-10

### Inicjalne funkcjonalności

- Utworzenie projektu Django
- Podstawowa konfiguracja środowiska deweloperskiego
- Plik README z opisem projektu
- Plik .gitignore dla Pythona i Django
- Wymagania projektu w pliku requirements.txt

---

## Wzór zapisu zmian

Każda zmiana powinna być dokumentowana w odpowiedniej sekcji według typu zmiany.

### Kategorie zmian

- **Dodano** - dla nowych funkcjonalności
- **Zmieniono** - dla zmian w istniejących funkcjonalnościach
- **Przestarzałe** - dla funkcjonalności oznaczonych do usunięcia w przyszłych wersjach
- **Usunięto** - dla usuniętych funkcjonalności
- **Naprawiono** - dla poprawionych błędów
- **Zabezpieczono** - w celu poinformowania o poprawkach bezpieczeństwa
