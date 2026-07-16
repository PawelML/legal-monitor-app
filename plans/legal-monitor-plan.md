# Plan: Monitor zmian prawnych dla firm (nazwa robocza: "PrawoRadar")

Data: 2026-07-16 · Status: zatwierdzona koncepcja, przed implementacją

## 1. Koncepcja

Darmowa usługa e-mailowa: firma podaje NIP + e-mail, system buduje jej profil
(PKD z rejestrów publicznych + kilka pytań doprecyzowujących), a potem
automatycznie pilnuje Dziennika Ustaw, Monitora Polskiego i procesu
legislacyjnego Sejmu. Gdy pojawia się zmiana dotycząca profilu firmy —
użytkownik dostaje alert/digest: co się zmienia, kogo dotyczy, od kiedy, co
trzeba zrobić.

Problem źródłowy zaobserwowany w PRO: przepisy dotyczące fragmentu działalności
zmieniają się, nikt tego nie pilnuje, firma dowiaduje się po fakcie.
PRO = pierwszy realny użytkownik (pilot).

**Framing produktu: monitoring i wczesne ostrzeganie, NIE porada prawna.**
Ta granica musi być widoczna w każdym miejscu komunikacji (stopka maila,
strona, README).

### Cele portfolio (dlaczego ten projekt, obok DigitFactory)

Projekt ma domykać luki, których nie pokrywa DigitFactory:

1. **Orkiestracja multi-agentowa** — kilku wyspecjalizowanych agentów
   (watcher → klasyfikator → streszczacz → digest), nie jeden agent z 25
   narzędziami.
2. **Eval harness od dnia 1** — golden set, precision/recall, regresje po
   zmianie promptu. Publicznie widoczny w repo.
3. **Realni użytkownicy + dobro publiczne** — darmowe, po polsku, publiczne
   strony z analizami aktów.
4. **Ekonomia tokenów jako constraint** — sekcja kosztów w README z realnymi
   liczbami.
5. **AI-native delivery jako dowód kompetencji principal-level** — każda
   większa zmiana przechodzi od krótkiej specyfikacji przez testy i review
   kodu agentowego do mierzalnego wdrożenia. Repo pokazuje nie tylko produkt,
   lecz także kontrolowany proces jego budowy.

## 2. Zweryfikowane źródła danych (2026-07-16)

| Źródło | Endpoint | Status | Uwagi |
| --- | --- | --- | --- |
| ELI API Sejmu (DU + MP) | `api.sejm.gov.pl/eli` | ✅ działa, bez klucza | Metadane: status, `entryIntoForce`, keywords, `references` (co uchyla/zmienia, podstawa prawna). Tekst: PDF zawsze, HTML dla części. Polling po `changeDate`. |
| Proces legislacyjny | `api.sejm.gov.pl/sejm/term{N}/processes` | ✅ działa, bez klucza | Projekty ustaw + przebieg + druki + linki ELI. Wczesne ostrzeganie przed publikacją w DU. |
| KRS | `api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}` | ✅ działa, bez klucza | Pełny odpis JSON; dział 3 = komplet PKD z opisami. Pokrywa spółki. |
| CEIDG | `dane.biznes.gov.pl/api/ceidg/v3` | ⚠️ wymaga darmowego JWT | Rejestracja przez biznes.gov.pl. Potrzebne dla JDG. Do załatwienia raz. |
| GUS REGON BIR1.1 | `wyszukiwarkaregon.stat.gov.pl` | ⚠️ SOAP + klucz | Jedno API na spółki i JDG, ale więcej tarcia. Odłożone — KRS+CEIDG wystarczą na MVP. |
| RCL (projekty rządowe) | `legislacja.rcl.gov.pl` | ❌ brak API (WAF) | Tylko scraping, kruche. **Poza MVP** — Sejm API łapie projekty na etapie sejmowym. Faza 2, jeśli będzie potrzeba. |

Skala: DU+MP ≈ 2–3 tys. pozycji/rok (~5–10 dziennie). Koszt analizy LLM —
grosze miesięcznie, niezależny od liczby użytkowników.

## 3. Architektura

Trzy oddzielne pętle + cienki web. Zasada ekonomiczna: **drogi krok (LLM)
wykonywany raz na akt; krok per-firma jest tani (matching tagów/embeddingów)**
— dzięki temu darmowy tier nie skaluje kosztów z liczbą użytkowników.

```
┌─ Pętla 1: INGEST + ANALIZA (cron 1×dziennie, jedyne drogie LLM) ─────────┐
│ ELI (DU/MP) + Sejm processes → nowe/zmienione akty → ekstrakcja tekstu   │
│ → agent-analityk: streszczenie po ludzku, działy PKD, tagi przekrojowe,  │
│   kto ma obowiązek, od kiedy, waga zmiany → zapis wersjonowany + embeddingi │
└──────────────────────────────────────────────────────────────────────────┘
┌─ Pętla 2: MATCHING + WYSYŁKA (cron, tanie/zero LLM) ─────────────────────┐
│ analizy × profile firm (PKD/tagi/embeddingi, próg istotności)            │
│ → digest tygodniowy e-mail + alert natychmiastowy dla zmian ważnych      │
└──────────────────────────────────────────────────────────────────────────┘
┌─ Pętla 3: ONBOARDING (interaktywna, jedyna z agentem "na żywo") ─────────┐
│ NIP + e-mail → KRS/CEIDG → szkic profilu do zatwierdzenia                │
│ → 2–4 pytania doprecyzowujące generowane z PKD (checkboxy, nie wolny tekst) │
│ → podgląd obszarów alertów → magic link (double opt-in)                  │
│ → RETROSPEKTYWA: dopasowane zmiany z ostatnich 12 mies. od razu po       │
│   rejestracji (kluczowy moment "wow")                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

### Decyzje architektoniczne (z uzasadnieniem — materiał do README)

- **Produkt e-mail-first, web celowo cienki.** Wartość dostarcza digest;
  użytkownik nie ma powodu wracać na stronę. Brak dashboardu to decyzja,
  nie brak.
- **Onboarding = wizard, nie czat.** Przewidywalne koszty, brak prompt
  injection od anonimów, lepsza konwersja. Agent pracuje pod spodem
  (szkic profilu, generowanie pytań), UI pozostaje deterministyczne.
- **Magic link zamiast haseł.** E-mail i tak jest tożsamością (tam trafia
  produkt); załatwia double opt-in; zero tabel haseł.
- **Baza analiz = główny aktyw.** Przechowujemy metadane ELI, wyekstrahowany
  tekst (cache do re-analizy lepszym promptem), wersjonowaną analizę LLM
  (z zapisem promptu/modelu — wzorzec z `offer_evaluations` w CV_builder)
  i embeddingi. Samych PDF-ów nie trzymamy (ELI jest trwałym źródłem).
- **RAG-czat nad bazą: świadomie POZA MVP** (koszty per-user, ryzyko "porady
  prawnej"). Baza jest na to gotowa od dnia 1 — zapisać w README jako
  odroczoną decyzję.
- **AI wspiera implementację, ale nie zastępuje odpowiedzialności.** Dla
  większej zmiany najpierw powstaje spec i test plan, potem mały,
  reviewowalny diff. Człowiek zatwierdza decyzje o architekturze, migracjach,
  zmianach taksonomii/promptu oraz uruchomieniu wysyłki do użytkowników.

### Stack

- Backend: **FastAPI** (async) + **PostgreSQL + pgvector**.
- Frontend: **Jinja2 + HTMX**, server-side. Bez Reacta — świadomy minimalizm
  (React już pokazany w DigitFactory).
- Joby: APScheduler / cron w kontenerze. Bez Celery/Redis na MVP.
- E-mail: Resend lub Amazon SES; własna domena + SPF/DKIM (digest o prawie
  nie może wpadać do spamu).
- LLM: tani model do filtra wstępnego ("czy akt w ogóle dotyczy firm?"),
  mocniejszy tylko do pełnej analizy aktów, które przeszły filtr.
- Deploy: Docker Compose na VPS (wzorzec z DigitFactory).
- Strony publiczne: render statyczny z bazy analiz, serwowany przez
  FastAPI/nginx (SEO + dobro publiczne, zero kosztów krańcowych).
- Jakość: pytest + pytest-asyncio, Ruff, Mypy strict, testy kontraktowe API;
  Playwright dla krytycznych ścieżek onboardingowych. Jedna komenda lokalna i
  CI uruchamiają ten sam zestaw bramek.
- Obserwowalność: strukturalne logi, metryki jobów i dostaw e-maili oraz
  alertowanie o nieudanym/niekompletnym ingestcie i wysyłce.

## 4. Model danych (szkic)

- `acts` — klucz ELI (`DU/2026/946`), tytuł, typ, status, daty (ogłoszenie,
  wejście w życie), keywords, `references` (JSON), `change_date` (polling),
  surowy tekst po ekstrakcji.
- `act_analyses` — FK do `acts`; wersjonowane: streszczenie PL, działy PKD,
  tagi przekrojowe (słownik: zatrudnienie, VAT, e-commerce, żywność,
  transport, ochrona danych, …), obowiązki, `effective_from`, waga (1–5),
  `prompt_version`, `model`, embedding (pgvector).
- `legislative_processes` — projekty z Sejm API: etap, druki, powiązane ELI.
- `companies` — NIP, nazwa, forma prawna, źródło (KRS/CEIDG), kody PKD,
  odpowiedzi na pytania doprecyzowujące, profil tekstowy + embedding.
- `users` — e-mail (verified_at = double opt-in), magic-link tokeny,
  preferencje częstotliwości; relacja do `companies`.
- `matches` — akt×firma: score, powód dopasowania (które PKD/tagi),
  status wysyłki.
- `deliveries` — log wysłanych digestów/alertów.
- `job_runs` — uruchomienie ingestu, analizy, matchingu lub wysyłki: status,
  liczby wejść/wyjść, retry, błąd i czas trwania; baza dla dashboardu
  operacyjnego i alertów.
- `eval_golden` — akt×profil testowy: oczekiwane dopasowanie (bool + tagi),
  źródło labelki (ręczna).

## 5. Eval harness i testy jakości (od dnia 1, publiczne w repo)

1. Golden set: ~100 historycznych aktów z DU otagowanych ręcznie względem
   3–4 profili (PRO + fikcyjne: sklep eko-żywność online, firma transportowa,
   software house).
2. Metryki: precision/recall klasyfikacji "dotyczy/nie dotyczy" per profil +
   trafność tagów. **False negative = metryka biznesowa** ("firma dowiedziała
   się po fakcie") — recall ważniejszy niż precision, ale precision poniżej
   progu = spam = wypisy.
3. Komenda `make eval` (albo `python -m evals.run`): re-analiza golden setu
   bieżącym promptem → raport diff vs poprzedni wynik. Uruchamiana przy
   każdej zmianie promptu (docelowo w CI).
4. Wyniki evali commitowane do repo (katalog `evals/results/`) — publiczna
   historia jakości.
5. Oprócz evali LLM utrzymujemy testy kontraktowe odpowiedzi ELI/KRS/CEIDG,
   próbki regresyjne ekstrakcji PDF oraz testy integracyjne przepływu
   `akt → analiza → match → delivery`.
6. Joby są testowane na powtórne uruchomienie (idempotencja), zmianę danych u
   źródła, błąd częściowy i retry. Niedostarczenie istotnego alertu jest
   krytyczną regresją produktu.
7. Zmiana promptu, modelu, taksonomii lub progu matchingu wymaga raportu diff
   evali i ręcznej decyzji: zaakceptować, poprawić albo wycofać zmianę.

## 6. AI-native delivery workflow

Lekki proces spec-driven jest częścią MVP, nie biurokracją obok niego. Nie
wdrażamy pełnego BMAD/OpenSpec dla każdej drobnej poprawki; stosujemy ich
zasady proporcjonalnie do ryzyka i wielkości zmiany.

### Artefakty i granice autonomii

- **Mała poprawka:** ticket/opis, kryterium akceptacji, test regresji i mały
  diff.
- **Funkcja lub zmiana przekrojowa:** `docs/specs/<nazwa>.md` z problemem,
  zakresem i poza zakresem, ograniczeniami, modelem danych/API, ryzykami,
  kryteriami akceptacji i planem testów.
- **Decyzja trudna do odwrócenia:** krótki ADR z kontekstem, rozważonymi
  opcjami, decyzją i konsekwencjami (np. provider e-mail, format analizy,
  polityka retencji).
- Agent może implementować wyłącznie wobec zatwierdzonej specyfikacji i
  istniejących ograniczeń repo. Nie samodzielnie zmienia granic produktu,
  polityki danych, architektury, zależności produkcyjnych, schematu migracji
  ani progów wpływających na alerty użytkowników.

### Pętla realizacji zmiany

1. Człowiek definiuje problem, kryteria akceptacji, ryzyka i budżet zadania.
2. Najpierw powstają lub są aktualizowane testy przypadków pozytywnych,
   brzegowych i regresyjnych; dopiero potem implementacja.
3. Agent wykonuje ograniczony zakres pracy, a autor weryfikuje jego założenia
   (zwłaszcza API zewnętrzne, bezpieczeństwo i reguły biznesowe).
4. Przed merge'em obowiązkowo przechodzą: formatowanie/lint, type check,
   testy jednostkowe i integracyjne oraz odpowiednie evale i testy e2e.
5. Review zawiera checklistę: zgodność ze specem, testy, bezpieczeństwo i
   dane osobowe, regresje, retry/idempotencja, zależności, migracje i
   zrozumiałość/rozmiar diffu. Dla zmian o wysokim ryzyku — ręczny test na
   danych kontrolnych przed produkcją.

### Ekonomia pracy agentowej

- README rozdziela koszt działania produktu od kosztu jego budowy z AI.
- Dla reprezentatywnych zmian zapisujemy w dokumentacyjnym work logu: model,
  rozmiar kontekstu, tokeny/koszt, czas człowieka, liczbę iteracji i wynik
  review. Nie jest to tabela ani funkcja produktu.
- Budżet i głębokość procesu są proporcjonalne do ryzyka: mała poprawka ma
  krótki kontekst i test regresji; ingest, e-mail, RODO, migracje i matching
  wymagają pełnego specu oraz rozszerzonej bramki jakości.

## 7. Fazy budowy

**Faza -1 — kontrakt dostarczania (krótki start):** struktura `docs/specs/`
i `docs/adr/`, szablon specu/ADR, `CONTRIBUTING.md` z workflowem agentowym i
checklistą review, komendy quality (`lint`, `typecheck`, `test`, `eval`) oraz
minimalne CI. Ustalić warunki ręcznego approvalu oraz sposób kalibracji progów
LLM/matchingu w Fazie 1, gdy będzie golden set. Weryfikacja: przykładowa mała
zmiana przechodzi pełną pętlę od specu do CI.

**Faza 0 — fundament (weekend):** nowe publiczne repo, Docker Compose
(Postgres+pgvector, app), szkielet FastAPI, migracje (alembic), klient ELI,
ingest DU/MP do `acts`, `job_runs`, logi i metryki jobów. Weryfikacja: baza
wypełnia się aktami z lipca 2026, a ponowne uruchomienie ingestu nie tworzy
duplikatów i zgłasza błąd źródła.

**Faza 1 — analiza + evals (tydz. 1–2):** ekstrakcja tekstu z PDF, agent-analityk
ze schematem JSON + walidacją, taksonomia tagów, golden set v1 (min. 50 aktów),
`make eval`, próbki regresyjne PDF i iteracja promptu do sensownego
recall/precision. Każda zmiana promptu/modelu ma raport diff i ręczny review.
To jest merytoryczne serce — nie skracać.

**Faza 2 — profil + matching (tydz. 2–3):** klient KRS (CEIDG gdy będzie
token), NIP→profil, matching PKD/tagi/embeddingi z progiem, kontrakty API,
testy idempotencji i retrospektywa 12 mies. dla profilu PRO — **pierwszy test
na żywym użytkowniku: czy retrospektywa dla PRO jest trafna?** To jest
go/no-go jakościowe; zmiana progów wymaga pełnego eval diffu.

**Faza 3 — e-mail + onboarding (tydz. 3–4):** wizard (NIP→szkic→pytania→
podgląd), magic link + double opt-in, szablon digestu, wysyłka (Resend/SES),
stopka: wypisz się / usuń konto / "to nie porada prawna". Testy e2e obejmują
potwierdzenie e-maila, wypisanie, usunięcie konta i brak podwójnej dostawy;
uruchomienie produkcyjnej wysyłki następuje po ręcznym approvalu.

**Faza 4 — publiczne uruchomienie (tydz. 4–5):** strony publiczne analiz
(SEO), landing, polityka prywatności + endpoint usunięcia danych (RODO),
deploy na VPS, monitoring/alerty operacyjne, README EN z architekturą,
decyzjami ADR, workflowem AI-native, sekcją kosztów produktu i pracy
agentowej oraz wynikami evali. Onboarding PRO jako pilota.

**Faza 5 — po MVP (backlog):** proces legislacyjny w digestach ("projekt po
1. czytaniu dotyczy Twojej branży"), CEIDG/REGON, RCL (scraping), RAG-czat,
monitoring przetargów/grantów tym samym silnikiem (generalizacja wzorca).

## 8. RODO / zgodność (element wiarygodności projektu)

- Przechowujemy NIP (dla JDG = dane osobowe) + e-mail → polityka prywatności,
  double opt-in, link wypisania w każdym mailu, endpoint "usuń konto i dane".
- Retencja: konto nieaktywne/niepotwierdzone usuwane po X dniach.
- Opisać własny compliance w README — w produkcie do monitoringu compliance
  to feature, nie formalność.

## 9. Otwarte decyzje

- [ ] Nazwa + domena (robocza: PrawoRadar; sprawdzić dostępność domeny).
- [ ] Provider e-mail: Resend vs SES (progi darmowe, deliverability).
- [ ] Modele LLM: który do filtra, który do analizy (zbadać koszt/jakość na
      golden secie — to samo w sobie jest materiałem do README).
- [ ] Ekstrakcja PDF: tekst lokalnie (pdfplumber/poppler) vs PDF prosto do
      modelu — porównać jakość na 10 aktach.
- [ ] Język repo/README: angielski (portfolio) przy polskim produkcie —
      rekomendacja: README EN, treści produktu PL.
- [ ] Progi jakościowe: minimalny recall/precision, maksymalna dopuszczalna
      regresja i warunki blokujące zmianę promptu lub matchingu.
- [ ] Zestaw bramek CI i proporcjonalny proces: utrzymać lekki własny workflow
      czy po jednym eksperymencie porównać go z BMAD/OpenSpec pod kątem kosztu,
      liczby iteracji i jakości artefaktów.
