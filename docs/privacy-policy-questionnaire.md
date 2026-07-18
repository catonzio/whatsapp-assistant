# WhatsApp Assistant — Questionario per la Privacy Policy (GDPR)

> Documento di lavoro: elenco di domande da porre al committente per raccogliere
> tutte le informazioni necessarie a redigere la privacy policy pubblicata su
> [infra/privacy-policy/policies/whatsapp-assistant.md](../../../infra/privacy-policy/policies/whatsapp-assistant.md),
> attualmente un placeholder. Dove la risposta è già ricavabile da
> [requirements.md](./requirements.md) è indicata come "Da requirements.md" —
> va comunque confermata esplicitamente dal committente, non assunta.

## 0. Nota preliminare — la policy è davvero necessaria?

Prima di compilare il questionario, va chiarito un punto legale a monte:

- **Domanda 0.1** — Il bot è ad uso esclusivamente personale/familiare dei due
  coniugi (nessun altro utente, nessuna finalità commerciale)? Se sì, potrebbe
  applicarsi l'esenzione "attività domestica" dell'art. 2(2)(c) GDPR, che
  escluderebbe l'obbligo di una privacy policy in senso stretto.
- **Domanda 0.2** — **Risposta del committente: sì, attività personale, ma la
  policy va comunque fatta.**

  **Nota legale:** l'esenzione "attività domestica" copre solo trattamenti che
  restano in una sfera strettamente privata, senza intervento di terzi. Dal
  momento in cui i messaggi passano da responsabili terzi commerciali (Meta/
  WhatsApp Cloud API, OpenAI, eventualmente Google), l'esenzione
  tipicamente **non si applica più** — va quindi trattata come se il GDPR si
  applicasse pienamente.

  Questo significa: **contenuto completo, forma sintetica.** Vanno inclusi
  tutti gli elementi obbligatori dell'art. 13 GDPR (titolare, finalità e base
  giuridica, destinatari/sub-processor, trasferimenti extra-UE, conservazione,
  diritti dell'interessato, reclamo al Garante) — nessuno va omesso per
  "semplificare". La semplificazione si ottiene invece nel fatto che, dato il
  contesto (un solo interessato esterno, nessun marketing/profilazione/
  vendita dati, pochi sub-processor, nessun minore, nessun cookie/tracking
  web), ogni sezione può restare molto breve: il risultato atteso è una
  policy di circa una pagina, non un documento lungo.

*Si procede quindi a raccogliere i dati per una policy GDPR-compliant ma
sintetica in ogni sezione.*

## 1. Titolare del trattamento (Data Controller)

- **1.1** Nome e cognome completo del titolare (persona fisica) o
  denominazione/ragione sociale (se il servizio è gestito tramite una P.IVA,
  ditta individuale, associazione, ecc.)? De Luca Servizi S.r.l. piva 095 55811000
- **1.2** Natura giuridica: persona fisica privata, libero professionista,
  ditta individuale, società, altro? srl
- **1.3** Indirizzo completo da riportare nella policy (sede legale o
  domicilio, a seconda della natura giuridica)? via genova, 12 ladispoli (rm) 00055
- **1.4** Codice fiscale e/o Partita IVA (se applicabile)? 095 55811000
- **1.5** Email di contatto dedicata per richieste privacy (o va usata
  un'email personale già esistente)? <info@danilocatone.com> o <info@delucaservizi.eu>
- **1.6** È necessario indicare un recapito telefonico o PEC? se non necessario eviterei, altrimenti chiedimela

## 2. Contitolarità tra i due coniugi

- **2.1** Dato che i dati sono condivisi tra i due coniugi (da
  requirements.md, §2), chi è formalmente il "titolare del trattamento" verso
  l'esterno (es. verso Meta/OpenAI)? Uno dei due, entrambi come contitolari
  (art. 26 GDPR), o si considera il secondo coniuge semplicemente come
  "interessato" che ha accettato l'uso condiviso del bot? solo uno dei due, l'altro è interessato
- **2.2** Se contitolarità: esiste (o serve predisporre) un accordo interno
  che definisca i rispettivi ruoli, anche solo in forma sintetica da
  richiamare nella policy? no

## 3. Responsabile della Protezione dei Dati (DPO)

- **3.1** È stato nominato un DPO? (Per un uso di questa scala, tipicamente
  no — confermare che non ricorrono i presupposti dell'art. 37 GDPR, es.
  trattamento su larga scala o categorie particolari di dati come attività
  principale.) no

## 4. Finalità e base giuridica del trattamento

Da requirements.md sono già note le finalità applicative (gestione eventi/
promemoria, catalogazione di informazioni per categorie, liste della spesa e
task condivisi, ricerca di informazioni salvate). Da chiarire la base
giuridica GDPR per ciascuna:

- **4.1** Le finalità sopra elencate si basano su: consenso esplicito
  dell'interessato (il coniuge che usa il bot), esecuzione di un accordo/
  servizio richiesto dall'interessato, legittimo interesse, o altro? accordo verbale tra le parti
- **4.2** Per i promemoria proattivi (requirements.md, §4.1) inviati "di
  iniziativa" del bot: è richiesto un consenso specifico separato, dato che
  comportano l'invio di messaggi non sollecitati? no
- **4.3** Per la geocodifica/verifica tramite tool esterni (es. per capire se
  un nome è un ristorante, requirements.md §4.2): questo comporta l'invio di
  dati (nome del locale, e potenzialmente la città) a un servizio terzo di
  ricerca/geocoding — quale servizio si intende usare (Google Places, OSM/
  Nominatim, altro)? google places, ma eventualmente anche OSM/Nominatim come alternativa open source

## 5. Categorie di dati personali trattati

Confermare/integrare l'elenco (da requirements.md):

- **5.1** Numero di telefono WhatsApp dei due utenti. si
- **5.2** Contenuto dei messaggi testuali inviati al bot si.
- **5.3** Messaggi vocali e relative trascrizioni (via OpenAI). si
- **5.4** Immagini/foto inviate (es. foto di menu, locandine). si
- **5.5** Link condivisi e, se previsto, contenuto estratto dalle pagine
  collegate. si
- **5.6** Informazioni derivate/salvate: eventi, appuntamenti, note su
  ristoranti/film/libri/viaggi, valutazioni, liste della spesa, task. si
- **5.7** Metadati tecnici: timestamp dei messaggi, identificativi interni
  del database, log applicativi/errori. si
- **5.8** C'è altro tipo di dato trattato non elencato sopra (es. posizione
  GPS condivisa via WhatsApp)? no

## 6. Categorie particolari di dati (art. 9 GDPR)

- **6.1** È possibile che nei messaggi liberi vengano menzionati dati
  "particolari" (es. informazioni sulla salute — allergie/intolleranze
  alimentari legate ai ristoranti, dati su stato civile impliciti, ecc.)? Va
  segnalato nella policy che il sistema non è progettato per trattare
  intenzionalmente questi dati, oppure serve un paragrafo dedicato? potrebbe essere possibile, fai la cosa che ritieni più prudente, ma non è intenzionale

## 7. Origine dei dati e modalità di raccolta

- **7.1** Confermare: tutti i dati provengono direttamente e unicamente dagli
  interessati stessi (i due coniugi), tramite i messaggi che inviano al bot —
  nessuna fonte terza. si
- **7.2** Il trattamento è interamente automatizzato (via webhook WhatsApp
  Cloud API → applicazione → LLM → database), senza intervento umano
  manuale sui contenuti, salvo per manutenzione tecnica? si

## 8. Destinatari e responsabili esterni del trattamento (sub-processor)

Da requirements.md risultano già coinvolti almeno questi soggetti terzi. Per
ciascuno serve conferma + eventuale accordo di responsabile del trattamento
(DPA, art. 28 GDPR) già firmato o da firmare:

- **8.1** **Meta/WhatsApp Cloud API** — riceve tutti i messaggi in transito.
  Meta agisce come responsabile o titolare autonomo per alcuni trattamenti
  (es. sicurezza/anti-spam)? È stato accettato/verificato il DPA di Meta per
  Business/WhatsApp Cloud API? si
- **8.2** **OpenAI** — usato per trascrizione vocale (`gpt-4o-transcribe`) e
  potenzialmente come LLM per l'elaborazione del linguaggio. Si usa l'API
  standard OpenAI (che per policy non usa i dati per addestrare i modelli) o
  altro piano? si
- **8.3** **Google (Gemini Flash Lite)** o altro provider LLM economico
  menzionato come opzione (requirements.md §5): quale verrà effettivamente
  usato in produzione? non lo so ancora, faro dei test
- **8.4** Servizio di geocoding/ricerca ristoranti (vedi 4.3), se previsto.
- **8.5** Provider di hosting: il server è del committente (self-hosted, come
  indicato) — è ospitato fisicamente in Italia/UE (es. a casa, in un
  datacenter italiano) o altrove? in italia a casa mia
- **8.6** C'è un servizio di backup esterno (cloud storage per i backup del
  database Postgres)? Se sì, quale e dove. no
- **8.7** Ci sono altri sub-processor non elencati (es. servizio di
  monitoring/logging esterno, servizio email transazionale)? no

## 9. Trasferimento dati verso paesi extra-UE

Meta, OpenAI e Google sono società statunitensi:

- **9.1** Per ciascuno dei fornitori sopra: aderiscono all'EU-US Data Privacy
  Framework, o il trasferimento si basa su Clausole Contrattuali Standard
  (SCC)? (Da verificare nei rispettivi termini/DPA — utile per la sezione
  "trasferimenti extra-UE" della policy.)

  **Nota AI:** Meta, OpenAI e Google risultano attualmente aderenti
  all'EU-U.S. Data Privacy Framework (verificabile in qualsiasi momento su
  dataprivacyframework.gov, elenco pubblico e ufficiale); in aggiunta
  applicano comunque Clausole Contrattuali Standard nei propri DPA
  enterprise. Nella policy useremo questa formulazione, con l'avvertenza che
  le certificazioni vanno riverificate periodicamente perché possono
  cambiare. Prima della pubblicazione definitiva andrebbe fatto un controllo
  puntuale sull'elenco ufficiale aggiornato.

## 10. Conservazione dei dati (retention)

- **10.1** Per quanto tempo vengono conservati i messaggi grezzi (testo,
  audio, trascrizioni) dopo l'elaborazione — cancellati subito dopo aver
  estratto l'informazione utile, o conservati indefinitamente? i messaggi grezzi rimangono nel db di google adk tra le sessions. posso prevedere di cancellarli dopo un certo periodo, più che altro per poter far continuare la conversazione. Se cancellassi subito i messaggi, non avrei la history

  **Deciso:** 90 giorni (il committente ha indicato che andrebbe bene anche
  un valore inferiore, ma 90 giorni è confermato come periodo da usare).
- **10.2** Per quanto tempo vengono conservati gli elementi salvati (eventi,
  note, liste) — indefinitamente fino a cancellazione manuale da parte
  dell'utente, o esiste una scadenza automatica? indefinitamente fino a cancellazione manuale da parte dell'utente
- **10.3** Esiste già (o va prevista) una funzionalità per l'utente per
  richiedere la cancellazione di un singolo elemento o di tutti i propri
  dati? no, ma posso prevederla
- **10.4** I log applicativi/di sistema (es. per debug) per quanto tempo
  vengono conservati? dipende, generalmente pochi giorni, ma posso prevedere di cancellarli automaticamente dopo un certo periodo. definiamolo insieme

  **Nota AI (proposta):** **14 giorni**, cancellazione automatica (es. log
  rotation). È un valore standard per log applicativi/di debug: sufficiente
  per diagnosticare problemi recenti, senza accumulare a lungo dati che
  includono numeri di telefono e contenuti dei messaggi (vedi anche §12.2).
  Stesso periodo può valere anche per il log temporaneo dei messaggi da
  numeri non autorizzati.

## 11. Sicurezza e misure tecniche/organizzative

- **11.1** Il traffico è cifrato end-to-end/in transito (HTTPS/TLS per le
  chiamate API, connessione al DB)? Il database Postgres è cifrato a riposo? si
- **11.2** Chi ha accesso amministrativo diretto al server/database (solo il
  committente in quanto sviluppatore)? Ci sono altre persone con accesso
  (es. altri sviluppatori, hosting provider)? solo il committente
- **11.3** Vengono effettuati backup del database? Con quale frequenza e per
  quanto tempo vengono conservati? no, ma posso prevederli. dammi suggerimenti su frequenza e retention

  **Nota AI (proposta):** backup automatico giornaliero del database,
  mantenendo gli ultimi 7 giorni + le ultime 4 copie settimanali (~1 mese a
  rotazione), cifrati, sullo stesso server o su un disco separato in loco
  (non serve offsite, dato che non è previsto storage esterno). Se vuoi una
  rete di sicurezza più lunga, aggiungi una copia mensile conservata 6 mesi.
  Questo va poi riportato nella policy con il periodo di conservazione
  effettivo scelto.

## 12. Controllo di accesso — whitelist dei numeri

Da requirements.md (§2): proposta whitelist dei due numeri autorizzati,
lato applicazione, con rifiuto/ignoranza dei messaggi da numeri non presenti.

- **12.1** Confermare che questo meccanismo è (o sarà) effettivamente
  implementato prima del rilascio della policy — la policy non dovrebbe
  descrivere una misura di sicurezza non ancora attiva. per ora lo devo ancora implementare, ma per poter fare i primi test ho bisogno della privacy policy

  **Deciso (rischio accettato dal committente):** la policy descriverà la
  whitelist come misura attiva; il committente ha scelto di pubblicarla così
  e implementarla subito dopo, assumendosi il rischio di un breve
  disallineamento tra quanto dichiarato e quanto realmente attivo. Consiglio
  comunque di implementarla il prima possibile, idealmente prima di ricevere
  messaggi reali da numeri diversi da quelli dei due coniugi.
- **12.2** Cosa succede tecnicamente ai messaggi ricevuti da numeri non in
  whitelist: vengono scartati senza essere salvati, o comunque loggati per
  motivi di sicurezza/debug (anche solo temporaneamente)? Questo va precisato
  perché anche uno scarto "silenzioso" implica un trattamento minimo (numero
  mittente) da dichiarare. li vorrei tenere per analisi di sicurezza/debug, ma non li salverei nel db, solo in un log temporaneo

  **Nota AI:** questo è un trattamento minimo lecito su base di legittimo
  interesse (art. 6.1.f GDPR — sicurezza del sistema), da dichiarare in
  policy in una riga, con lo stesso periodo di conservazione breve proposto
  al §10.4 (14 giorni).

## 13. Diritti dell'interessato

- **13.1** Confermare il canale con cui l'interessato (l'altro coniuge, o in
  futuro terzi) può esercitare i diritti GDPR (accesso, rettifica,
  cancellazione, portabilità, opposizione, limitazione) — stessa email di
  cui al punto 1.5? si
- **13.2** Va indicato nella policy anche il diritto di proporre reclamo al
  Garante per la protezione dei dati personali (obbligatorio per legge,
  indipendentemente dalla risposta del committente — verrà incluso di
  default). includilo

## 14. Minori

- **14.1** Confermare che il servizio non è destinato a minori e non li
  riguarda in alcun modo (utenti previsti: solo i due coniugi adulti). in futuro potrebbe essere usato anche dai nostri figli, ma ti parlo comunque di almeno altri 10 anni quindi per ora non lo prevedere

## 15. Processi decisionali automatizzati / Intelligenza Artificiale

- **15.1** L'uso di un LLM per interpretare i messaggi, inferire categorie e
  decidere quando inviare un promemoria proattivo costituisce una forma di
  elaborazione automatizzata dei dati. Va menzionato esplicitamente nella
  policy come "trattamento automatizzato senza processo decisionale con
  effetti legali significativi sull'interessato" (di norma sufficiente per
  questo caso d'uso, ma da confermare che non si prevedono usi che
  producano effetti significativi, es. decisioni finanziarie/legali). ragiona bene sulla frase che userai, è importante che non dia adito a interpretazioni errate, ma allo stesso tempo non sia troppo lunga e complessa. Non deve essere un paragrafo lungo, ma qualche frase chiara e concisa

  **Nota AI — testo proposto per la policy:**

  > "Alcune funzionalità (organizzazione delle informazioni in categorie,
  > individuazione di promemoria) sono supportate da modelli di intelligenza
  > artificiale (LLM). Si tratta di un'elaborazione automatizzata che non
  > comporta decisioni con effetti giuridici o comunque significativi sugli
  > utenti: il sistema si limita a organizzare e restituire le informazioni
  > che gli utenti stessi hanno fornito."

  Due frasi, tono neutro, esclude esplicitamente l'ambito dell'art. 22 GDPR
  senza usare gergo legale eccessivo. Fammi sapere se va bene così.

## 16. Violazioni dei dati (data breach)

- **16.1** Esiste già una procedura interna, anche minima, per rilevare e
  notificare un'eventuale violazione dei dati (es. accesso non autorizzato al
  server)? Se no, va almeno prevista una modalità con cui il committente
  informerebbe l'altro coniuge in caso di incidente. No, ma posso prevederla. In caso di incidente informerei l'altro coniuge via WhatsApp o a voce, ma non so se sia sufficiente per legge. Dammi indicazioni su come fare

  **Nota AI:** la legge (art. 33-34 GDPR) distingue due obblighi separati,
  entrambi scattano solo se la violazione comporta un rischio per i diritti
  e le libertà delle persone coinvolte:
  1. **Notifica al Garante** entro 72 ore dalla scoperta — è una procedura
     formale online (garanteprivacy.it), non basta avvisare a voce; se il
     rischio è concreto va fatta comunque, indipendentemente da cosa dici al
     coniuge.
  2. **Notifica all'interessato** (il coniuge, se il rischio è elevato) —
     qui la legge non impone un canale specifico: WhatsApp o a voce vanno
     bene *purché* avvenga senza ingiustificato ritardo e comunichi cosa è
     successo, le probabili conseguenze e le misure adottate. Consiglio però
     di lasciarne traccia scritta anche minima (un messaggio di follow-up,
     un'email a te stesso con data e contenuto) per poter dimostrare, in
     caso di controllo, di aver rispettato l'obbligo (principio di
     accountability, art. 5(2)).

  Per la policy basta una clausola generica standard (vedi checklist §19);
  la procedura interna dettagliata sopra non va necessariamente pubblicata.

## 17. Validità, modifiche e versioning della policy

- **17.1** Data di prima pubblicazione della policy da indicare.

  **Deciso:** 18 luglio 2026.
- **17.2** Con quale modalità l'altro coniuge verrà informato in caso di
  modifiche sostanziali alla policy (es. semplice notifica via WhatsApp dal
  bot stesso)? a voce

## 18. Altre informazioni

- **18.1** Lingua/e in cui va redatta la policy (italiano, come da
  requirements.md §6 — confermare se serve anche una versione inglese). sia in italiano che in inglese, ma la versione ufficiale è quella italiana
- **18.2** C'è un nome/brand con cui il bot si presenta agli utenti (da usare
  come riferimento nella policy invece di "WhatsApp Assistant")? per ora ChatAssistant, ma proponimi dei nomi alternativi, se vuoi. Non deve essere un nome commerciale, ma qualcosa di più friendly e simpatico, che dia l'idea di un assistente personale (tipo Jarvis, ma non Jarvis)

  **Nota AI — proposte:** ho evitato nomi di assistenti già noti/commerciali
  (Siri, Alexa, Cortana, Jarvis...) per non generare confusione o problemi di
  marchio, puntando su nomi brevi, amichevoli, facili da dire a voce:
  - **Bric** — corto, simpatico, richiama "bricconcello"/qualcosa di vivace.
  - **Nino** — nome proprio caldo e familiare, suona come un vero assistente di casa.
  - **Filo** — evoca il "filo conduttore" che tiene insieme le informazioni.
  - **Bussola** — idea di orientamento/aiuto a ritrovare le cose salvate.
  - **Pico** — corto, easy da pronunciare, neutro e amichevole.

  **Deciso:** Nino (per ora — valore facilmente cambiabile in futuro,
  essendo usato solo come riferimento testuale nella policy e nei messaggi
  del bot).
- **18.3** URL definitivo su cui la policy sarà pubblicata (verosimilmente
  `https://<host>/privacy-policy/whatsapp-assistant.html`, da confermare) da
  linkare eventualmente nel primo messaggio di benvenuto del bot. si, confermo che sarà pubblicata su `https://danilocatone.com/privacy-policy/whatsapp-assistant.html`

## 19. Checklist — contenuti obbligatori della policy finale

Punti ancora aperti da confermare prima della stesura definitiva (vedi note
AI nelle rispettive sezioni): email di contatto (§1.5), numero/nome del
servizio (§18.2), periodo di conservazione della cronologia grezza (§10.1),
data di pubblicazione (§17.1). Tutto il resto è confermato o coperto da una
raccomandazione di default. Sotto, l'elenco di ciò che la policy finale deve
contenere, sezione per sezione:

- [ ] **Titolare**: De Luca Servizi S.r.l., P.IVA 09555811000, via Genova 12,
      00055 Ladispoli (RM); email di contatto per richieste privacy (§1.5)
- [ ] Precisazione sintetica che il Servizio è usato da due coniugi: uno
      opera per conto del Titolare, l'altro è "interessato" (§2.1)
- [ ] **Finalità del trattamento**: gestione di eventi/promemoria,
      catalogazione di informazioni per categorie, liste della spesa e task
      condivisi, recupero di informazioni salvate (§4)
- [ ] **Base giuridica**: consenso libero e informato (art. 6.1.a GDPR),
      prestato tramite l'uso volontario del Servizio dopo l'informativa (§4.1)
- [ ] **Categorie di dati trattati**: numero di telefono, testo dei
      messaggi, messaggi vocali e trascrizioni, immagini, link condivisi,
      informazioni derivate/salvate (eventi, note, valutazioni, liste),
      metadati tecnici (§5)
- [ ] Clausola su **categorie particolari di dati** (art. 9): non raccolte
      intenzionalmente, possibile presenza incidentale nei messaggi liberi,
      nessuna analisi mirata (§6.1)
- [ ] Dichiarazione che i dati provengono **direttamente dagli interessati**,
      nessuna fonte terza (§7)
- [ ] **Destinatari/sub-responsabili**: Meta (WhatsApp Cloud API), OpenAI
      (trascrizione/LLM), eventualmente Google (Gemini, in valutazione),
      servizi di geocodifica/verifica luoghi (Google Places o alternative
      open source) (§8)
- [ ] **Trasferimenti extra-UE**: adesione dei fornitori al Data Privacy
      Framework UE-USA e/o Clausole Contrattuali Standard, con nota di
      verifica periodica (§9)
- [ ] **Periodi di conservazione**:
  - [ ] cronologia grezza dei messaggi/sessioni: periodo definito, non
        indefinito (proposta: 90 giorni) (§10.1)
  - [ ] informazioni salvate (eventi, note, liste): fino a cancellazione
        manuale dell'utente (§10.2)
  - [ ] log applicativi e log di sicurezza (numeri non in whitelist):
        periodo breve e definito (proposta: 14 giorni) (§10.4, §12.2)
- [ ] **Misure di sicurezza**: cifratura in transito e a riposo, accesso
      amministrativo limitato al solo titolare, controllo di accesso tramite
      whitelist dei numeri autorizzati — *da implementare prima che la
      policy dichiari questa misura come attiva* (§11, §12.1)
- [ ] **Diritti dell'interessato**: accesso, rettifica, cancellazione,
      limitazione, opposizione, portabilità + diritto di reclamo al Garante
      Privacy (§13)
- [ ] Dichiarazione che il **Servizio non è rivolto a minori** (§14)
- [ ] Paragrafo breve su **elaborazione automatizzata/IA**, testo già
      proposto al §15.1, che esclude effetti giuridici significativi (art. 22
      GDPR)
- [ ] Clausola generica su **gestione delle violazioni dei dati** (notifica al
      Garante entro i termini di legge se sussiste rischio, notifica agli
      interessati se il rischio è elevato) (§16.1)
- [ ] **Data di ultimo aggiornamento** e modalità di comunicazione di
      modifiche sostanziali (§17)
- [ ] **Doppia versione linguistica** IT (ufficiale) + EN, con nota che in
      caso di discrepanza prevale la versione italiana (§18.1)
- [ ] **Nome del servizio** usato in modo coerente in tutto il testo (§18.2)
- [ ] URL di pubblicazione:
      `https://danilocatone.com/privacy-policy/whatsapp-assistant.html`
      (§18.3)

## Come procedere

Una volta confermati i punti ancora aperti, aggiornare
[whatsapp-assistant.md](../../../infra/privacy-policy/policies/whatsapp-assistant.md)
sostituendo il placeholder con il testo completo della policy, seguendo la
checklist del §19 (titolare, finalità e basi giuridiche, categorie di dati,
destinatari/sub-responsabili, trasferimenti extra-UE, conservazione,
sicurezza, diritti dell'interessato, minori, IA, violazioni dei dati,
modifiche alla policy), e la sua versione inglese.
