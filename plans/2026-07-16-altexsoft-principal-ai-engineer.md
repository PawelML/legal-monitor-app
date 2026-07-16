# AltexSoft — Principal AI Engineer

**Źródło:** treść ogłoszenia przekazana ręcznie, bez linku<br>
**Zapisano:** 2026-07-16<br>
**Model pracy:** zdalnie

## Najważniejsze wymagania dotyczące podejścia do kodu

| Obszar | Wymaganie z ogłoszenia | Co warto umieć pokazać w praktyce |
| --- | --- | --- |
| Architektura i jakość | Głębokie doświadczenie w projektowaniu systemów, testach, refaktoryzacji i code review; zdolność samodzielnej korekty kodu wygenerowanego przez AI | Przykład złożonej zmiany od decyzji architektonicznej po testy, przegląd ryzyk i refaktoryzację; umiejętność wskazania konkretnych błędów lub nieprawdziwych założeń agenta. |
| AI-first delivery | Produkcyjne dostarczanie oprogramowania przede wszystkim z użyciem narzędzi agentowych | Powtarzalny workflow pokazujący podział pracy między człowieka i agenta, artefakty z realizacji oraz mierzalną kontrolę jakości przed wdrożeniem. |
| Narzędzia agentowe | Biegłość w Claude Code, Cursor lub odpowiednikach, także w trybach planowania i agentowym | Demonstracja celowego doboru narzędzia do małej poprawki, większego refaktoru i budowy funkcji; czytelne prompty, kontekst repozytorium i ograniczenia zadania. |
| Specyfikacja i kontekst | Specification-driven development oraz context engineering: problem i projekt są zdefiniowane przed uruchomieniem agenta | Krótki spec/ADR z zakresem, ograniczeniami, modelem danych, kryteriami akceptacji i planem testów, przekazany agentowi jako źródło prawdy. |
| Agentic TDD | Testy i specyfikacja prowadzą pracę agenta, a jakość powstaje w procesie, nie dopiero na końcu | Najpierw kryteria akceptacji i testy przypadków pozytywnych oraz brzegowych, następnie generacja implementacji, uruchomienie kontroli i ręczna ocena wyniku. |
| AI-first code review | Automatyczna/rzeczowa weryfikacja zmian agentowych przed review człowieka | Checklist lub etap review obejmujący zgodność ze specyfikacją, testy, bezpieczeństwo, regresje, zależności i wielkość diffu; mały, zrozumiały PR dla recenzenta. |
| Frameworki SDLC | BMAD, OpenSpec i Superpowers; świadomy wybór procesu dla brownfield/greenfield, skali, pokrycia SDLC i budżetu | Porównanie lekkiego i rozbudowanego procesu oraz uzasadnienie wyboru dla konkretnego projektu, z uwzględnieniem kosztu tokenów. |
| Ekonomia agentów | Aktywne zarządzanie zużyciem tokenów i kosztem pracy agentowej | Budżet dla zadania, ograniczanie kontekstu, etapowanie pracy, wybór modelu oraz ocena kosztu względem wartości i ryzyka zmiany. |
| Przywództwo techniczne | Kształtowanie AI-native SDLC, mentoring, komunikacja z klientem i pełna odpowiedzialność za wynik | Przełożenie niejasnego celu biznesowego na zakres, decyzje i kryteria sukcesu; jasne wyjaśnienie kompromisów osobom technicznym i nietechnicznym. |
| Środowisko pracy | Chmura oraz angielski C1 | Przykład wdrożonego systemu i omówienie decyzji technicznych po angielsku; w ofercie nie wskazano konkretnego dostawcy chmury. |

## Wniosek: oczekiwany standard pracy

To nie jest stanowisko „promptującego programisty”, lecz principal-level
ownership nad dostarczaniem produktu z AI jako narzędziem wykonawczym. Najlepszym
dowodem kompetencji będzie publiczny lub dobrze opisany case study: od niejasnego
problemu biznesowego, przez specyfikację i decyzje architektoniczne, po testy,
kontrolę jakości kodu agentowego, wdrożenie oraz koszt wykonania. Kluczowa jest
umiejętność zatrzymania agenta tam, gdzie potrzebny jest osąd człowieka.

## Priorytety nauki wynikające z tej oferty

1. **Powtarzalny spec-driven workflow dla agentów** — przygotować szablon specyfikacji zawierający zakres, kryteria akceptacji, ograniczenia, ryzyka, plan testów i granice autonomii agenta; użyć go w realnej zmianie brownfield.
2. **Agentic TDD i review generated code** — zbudować bramkę jakości: testy przed implementacją, lint/type check, testy regresji oraz checklistę ręcznej weryfikacji halucynowanych API, błędów logicznych i bezpieczeństwa.
3. **BMAD i OpenSpec w praktyce** — przejść dokumentację obu podejść i wykonać po jednym małym zadaniu, porównując koszt, liczbę iteracji i jakość artefaktów; traktować je jako preferowane, nie obowiązkowe, bo są tylko „mile widziane”.
4. **Ekonomia pracy agentowej** — rejestrować dla kilku zadań model, użyty kontekst, tokeny/koszt, czas człowieka i wynik; wyciągnąć zasady ograniczania kosztów bez obniżania jakości.
5. **Case study AI-native delivery** — opisać po angielsku wybraną funkcję od specyfikacji do wdrożenia, wraz z przykładami decyzji, błędów złapanych w review i sposobem mentoringu zespołu.
6. **Angielski zawodowy na poziomie C1** — ćwiczyć prowadzenie technicznego discovery, uzasadnianie decyzji architektonicznych i pisemne podsumowania dla klienta; profil deklaruje obecnie B2, podczas gdy oferta wymaga C1.

## Co już jest szczególnie trafne dla obecnego profilu

- Profil potwierdza intensywne użycie Claude Code, Codex i także Cursor w AI-powered dev workflows, a także budowę produkcyjnych agentów tool-calling oraz autonomicznego WatchdogAgent.
- W DigitFactory kandydat samodzielnie prowadził pełny cykl: architekturę, backend, frontend, dane, AI, wdrożenie i utrzymanie; w PRO realizował wymagania biznesowe od projektu po produkcję i runbooki.
- Potwierdzone są praktyki jakościowe: pytest, pytest-asyncio, Ruff, Mypy strict, Vitest, React Testing Library i weryfikacja przeglądarkowa przez Playwright.
- Profil obejmuje projektowanie agentów, MCP, human approval flows, source evidence, agent timelines oraz prompt/version fingerprinting — to dobra baza do pokazania kontrolowanego użycia agentów.
- Potwierdzone są Docker/Docker Compose, VPS, CI/CD oraz AWS (EC2, S3, Lambda, EMR, DocumentDB), co częściowo pokrywa ogólne wymaganie chmurowe.

## Pytania do weryfikacji przy kolejnych ofertach

- Czy AI-first delivery oznacza w firmie obowiązkowy workflow i konkretne metryki, czy przede wszystkim indywidualny styl pracy inżyniera?
- Jakie konkretne praktyki, artefakty i narzędzia składają się w AltexSoft na BMAD, OpenSpec i „Superpowers”?
- Jaki jest zakres odpowiedzialności principal engineer za architekturę, security, review i mentoring na projektach klienta?
- Czy koszty tokenów są mierzone per projekt, zespół czy zadanie oraz jakie są akceptowane budżety?
- Czy angielski C1 jest weryfikowany przez codzienną pracę z klientem, rozmowę techniczną czy formalny certyfikat?
