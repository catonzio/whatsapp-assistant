# WhatsApp Assistant — Documento di Requisiti e Funzionalità

> Documento di riferimento per lo sviluppo futuro. Riflette le risposte raccolte
> direttamente dal committente (17/07/2026). I punti non ancora decisi in modo
> definitivo sono segnalati esplicitamente come "da validare".

## 1. Obiettivo del progetto

Realizzare un assistente agentico personale, accessibile via WhatsApp, che aiuti
una coppia a tenere traccia di eventi, appuntamenti, promemoria e informazioni di
vita quotidiana (ristoranti, film, libri, viaggi, ecc.), permettendo di salvare e
recuperare queste informazioni in modo rapido e naturale, semplicemente scrivendo
o parlando al bot.

Il sistema sarà self-hosted sul server già a disposizione (Docker + Traefik, vedi
[compose.yaml](../compose.yaml)).

## 2. Utenti e accesso

- **Utenti previsti:** solo i due coniugi, senza previsione attuale di estendere
  ad altre persone.
- **Modello dati:** tutti i dati (eventi, note, categorie, promemoria, liste) sono
  **condivisi** tra i due utenti — non esiste uno spazio privato separato.
- **Autenticazione / controllo accessi:** non è stato definito un meccanismo
  formale. *Proposta da validare:* whitelist dei due numeri WhatsApp autorizzati
  lato applicazione — il bot ignora/rifiuta messaggi da numeri non presenti in
  whitelist. Non fare affidamento solo sulla segretezza del numero del bot.

## 3. Canale di messaggistica

- **Canale principale:** WhatsApp Cloud API ufficiale (Meta), già parzialmente
  implementata in [api/webhook.py](../src/whatsapp_assistant/api/webhook.py).
- Il codice per **WAHA** (libreria non ufficiale, già presente in
  [api/waha.py](../src/whatsapp_assistant/api/waha.py)) va **mantenuto nel
  repository** come alternativa/backup, ma non è la base per lo sviluppo attuale.
- **Tipi di messaggio da gestire:**
  - Testo libero
  - Messaggi vocali (già supportata la trascrizione via OpenAI)
  - Immagini/foto
  - Link (es. link a un ristorante, un film, un articolo)

### 3.1 Vincolo tecnico WhatsApp — finestra delle 24 ore

La WhatsApp Cloud API consente risposte "gratuite" solo entro 24 ore dall'ultimo
messaggio ricevuto dall'utente. Per inviare un messaggio **di iniziativa** del
bot (es. un promemoria proattivo al mattino di un appuntamento) è necessario un
**message template pre-approvato da Meta**, il cui utilizzo può avere un costo
oltre una soglia gratuita mensile.

## 4. Funzionalità principali

### 4.1 Gestione di eventi, appuntamenti e promemoria

- Il bot deve poter registrare eventi, appuntamenti e promemoria a partire da
  messaggi in linguaggio naturale.
- **Promemoria proattivi:** desiderati (il bot deve poter scrivere per primo per
  ricordare un evento), **a condizione che il costo mensile complessivo resti
  sotto il budget definito** (vedi §6). Se il costo dei template WhatsApp
  necessari per i promemoria proattivi supera il budget, il sistema deve
  degradare a modalità "solo su richiesta" (il bot risponde solo quando
  interpellato, nessun messaggio spontaneo).
- *Da validare:* gestione della ricorrenza degli eventi (es. eventi annuali,
  settimanali), fuso orario, anticipo con cui inviare il promemoria.

### 4.2 Catalogazione intelligente di informazioni per categorie

- Le informazioni salvate (ristoranti, film, libri, viaggi, canzoni, ecc.) devono
  essere organizzate in **categorie**.
- Le categorie possono essere:
  - **create liberamente dall'utente**, oppure
  - **inferite/inventate autonomamente dall'agente** in base al contenuto del
    messaggio.
- Logica di inferenza richiesta esplicitamente dal committente:
  - Se esistono già categorie come "viaggi" o "canzoni" e l'utente scrive il
    nome di un luogo, l'agente deve capire dal contesto/categorie esistenti che
    si tratta probabilmente di un viaggio.
  - Se l'utente invia il nome di un ristorante, l'agente deve poter
    **verificare tramite un tool** (es. ricerca/geocoding) che si tratti
    effettivamente di un ristorante, e in tal caso creare autonomamente una
    nuova categoria "ristoranti" se non esiste ancora.
- Per ogni elemento salvato, il sistema deve poter registrare almeno: nome,
  categoria, recensione/note testuali, punteggio/valutazione, e recuperarli in
  un secondo momento.
- *Da validare:* elenco preciso dei campi per categoria (es. un ristorante avrà
  campi diversi da un libro?), gestione di duplicati/aggiornamenti di un
  elemento già salvato.

### 4.3 Recupero delle informazioni

- Il recupero avviene tramite **domande in linguaggio naturale** rivolte al bot
  (es. "che ristoranti abbiamo salvato a Roma?"), senza necessità di comandi
  specifici o riepiloghi automatici (non richiesti).

### 4.4 Liste della spesa e task condivisi

- Il sistema deve supportare la gestione di **liste della spesa** condivise.
- Il sistema deve supportare **task/attività condivise** tra i due utenti.
- *Da validare:* struttura delle liste (checklist con spunta, cancellazione
  automatica alla conferma d'acquisto, ecc.), gestione priorità/scadenze dei
  task.

### 4.5 Gestione input multimediali

- **Vocali:** già supportata la trascrizione (OpenAI, `gpt-4o-transcribe`).
- **Immagini:** da gestire (nuovo requisito). *Da validare:* uso previsto (es.
  estrarre testo/OCR da una foto di un menu o locandina, analisi visiva tramite
  modello multimodale per identificare un piatto/locale, o semplice allegato
  associato a una nota).
- **Link:** da gestire (nuovo requisito). *Da validare:* se richiesto solo il
  salvataggio del link o anche l'estrazione automatica di informazioni dalla
  pagina collegata (scraping/preview).

## 5. Architettura tecnica (stato attuale e vincoli)

- **Linguaggio/stack:** Python, FastAPI (`uv` come package manager), già in uso
  nel repository.
- **Canale WhatsApp:** WhatsApp Cloud API ufficiale (Meta) come base; mantenere
  il modulo WAHA esistente senza rimuoverlo.
- **Persistenza dati:** database **PostgreSQL**, da containerizzare insieme al
  servizio applicativo (nessun costo di hosting aggiuntivo previsto, il DB gira
  sullo stesso server).
- **Modello LLM:** aperto a modelli economici (es. Gemini Flash Lite o
  equivalenti) purché sufficienti al task, per contenere i costi entro il
  budget.
- **Hosting:** server già disponibile del committente, dietro reverse proxy
  Traefik (vedi [compose.yaml](../compose.yaml)); nessun costo di hosting da
  considerare nel budget mensile.

## 6. Requisiti non funzionali

- **Lingua:** italiano come lingua principale di interazione del bot.
- **Budget mensile complessivo:** deve restare **sotto i 10 €/mese**, includendo
  tutti i costi variabili (chiamate LLM, eventuali message template WhatsApp a
  pagamento per i promemoria proattivi). Non sono inclusi costi di hosting
  (server già disponibile).
- **Privacy/sicurezza:** richiesta una qualche forma di controllo accessi (vedi
  §2); da definire nel dettaglio in fase di design tecnico.
- **Disponibilità/affidabilità:** nessun requisito specifico dichiarato al
  momento — *da validare* (es. tempo massimo di risposta, tolleranza a downtime).

## 7. Punti aperti da chiarire prima/in fase di design tecnico

1. Meccanismo di autenticazione/whitelist dei numeri autorizzati.
2. Gestione della ricorrenza e del fuso orario per eventi e promemoria.
3. Comportamento esatto in caso di superamento del budget mensile (chi/come
   viene notificato, come si torna alla modalità "solo su richiesta").
4. Campi specifici da salvare per ciascuna categoria di elemento.
5. Gestione di duplicati o aggiornamenti di elementi già salvati.
6. Utilizzo previsto per immagini (OCR, analisi visiva, semplice allegato).
7. Comportamento per i link (solo salvataggio vs. estrazione automatica di
   informazioni dalla pagina).
8. Struttura di liste della spesa e task condivisi (stati, scadenze, priorità).
9. Requisiti di disponibilità/affidabilità del servizio.
