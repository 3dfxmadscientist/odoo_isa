��    r      �  �   <      �	     �	     �	     �	  
   �	     �	     �	  
   �	  
   
  	   
     
     ,
     ;
     H
  
   V
     a
     j
      x
  "   �
      �
     �
     �
          *     F     Z     k     �     �     �     �     �     �     �     �     �          (     8     U  	   m     w     �     �     �     �     �  :   �  *   �  >        \     e     k  
   p     {     �     �  _   �                              #  �   1     �     �     �  
   �     �                    %     -     >     T     f     w  
   �  	   �     �     �     �  @   �  !   �          '     8     >     M     Z     u     �     �  	   �     �     �     �     �     �  0      :   1  f   l  U   �  9   )  8   c  �  �  7   �     �     �  
   �  	          �       �     �     �  	   �     �       	   	  
     	        (     8     H     Z  	   h  	   r     |     �  %   �  !   �     �     
     (     ?     ^     u     �     �     �     �     �                !  	   (     2     I     a     r     �  	   �     �     �     �     �     �     �  S   �  )   J  P   t     �     �     �  	   �     �     �       ]        z     �     �     �     �     �  d   �          $     -     5  
   C     N     V  	   f     p     y     �     �     �     �     �  	   �     �     �  	   �  :      !   ;     ]     n     �     �     �     �     �  #   �                    *     A     M     \  5   n  W   �  v   �  p   s  A   �  E   &   d   l   C   �   )   !     ?!     U!  	   a!     k!                  !   p   J   `   T   ;   m   &   ^   C   b   5   ]   _   :   k   ?   3   >   <                         \   l      B       =      2   H      1   P   g   N   W   
      S      Q       %              6          )       G           o   M               e   f   X   Y   n       +   L             Z      R      V   j   7       q   4       E   *      [   h   O       F   "   D      A      -      c       i              9               K       	   r   ,      a                     @       (         U   d           .          $   '   I       8       #      0   /                                01 - Not to be billed 02 - To be billed 03 - Billed Activities April August Bill Month Bill State Bill Year Billable Hours Billable hours Billing Date Billing Hours Categories Category Category Line Category of Closing Project Form Category of Closing Project Search Category of Closing Project Tree Category of Project Form Category of Project Search Category of Project Tree Category of closing project Category of project Category of task Category of task Form Category of task Search Category of task Tree Causal Closure Close Description Closed Notes Closing Categories Code Contract Contract Line Number Contract Modify Date Contract Number Contract line of Isa project Contract of Isa project Contracts Contracts Line Date December Description Duplicate Work Error ! Error ! Task end-date must be greater then task start-date Error ! You cannot create recursive tasks. Error! project start-date must be lower then project end-date. February Field File Filters... Group By... Hours Hours worked for partners If confirmed the record will be saved once and then you will be able to change anyway. Confirm? January July June March May Month billing Non si puo' chiudere il progetto perche' lo stato del lavoro "%s" non e' "cancellato" o "terminato".' %task.name))
                raise osv.except_osv(_('Warning ! Not Billing November October Open Notes PTF code Partner Planned Hours Program Project Project Contract Project Contract Line Project Task Work Project_contract Projects References September Spent Hours State billing Task The chosen company is not in the allowed companies for this user The project '%s' has been closed. Ticket Required Ticket reference Today Transfer as400 Type of work Type of work activity Form Type of work activity Search Type of work activity Tree User Warning ! Work activity Tree Work description Works Works Search Year billing You can not have two users with the same login ! You cannot close a project with billing hours not correct. You cannot close a project with category "85 - Assistenza presso clienti" without select contract line You cannot close a project with name strting with "HR_" without closing informations. You cannot close a project with projec manager HelpBoard. You cannot close an activity with responsible HelpBoard. You cannot close this project,because the project_task "%s" state is not "cancelled" or "done".' %task.name))
        return True



    def onchange_contract(self, cr, uid, ids, context=None):
        #import pdb;pdb.set_trace()
        #if newstate == "01":
        #    return {'value':{'billing_month': 0, 'billing_year': 0}}
        #act_day = time.gmtime()[2]
        #act_month = time.gmtime()[1]
        #act_year = time.gmtime()[0]
        act_date = time.strftime('%Y-%m-%d %H:%M:%S You cannot open an activity with responsible HelpBoard. You must select billing state. included package hours project_id res.users unknown Project-Id-Version: PACKAGE VERSION
Report-Msgid-Bugs-To: support@openerp.com
POT-Creation-Date: 2012-09-10 07:21+0000
PO-Revision-Date: 2012-09-10 09:22+0100
Last-Translator: Loris Turchetti <l.turchetti@isa.it>
Language-Team: LANGUAGE <LL@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: it
Plural-Forms: nplurals=2; plural=(n != 1);
X-Generator: Pootle 2.1.6
 01 - Da non fatturare 02 - Da fatturare 03 - Fatturato Attività Aprile Agosto Mese Fatt Stato Fatt Anno Fatt Ore fatturabili Ore fatturabili Data Fatturazione Ore fatturate Categorie Categoria Righe Categoria Categoria di chiusura progetti Categoria di chiusura progetti Search Categoria di chiusura di progetti Categoria dei progetti Categoria dei progetti Search Categoria dei progetti Categorie di chiusura progetti Categoria dei progetti Categoria di attività Categoria di attività Categoria di attività Search Categoria di attività Causale di Chiusra Descrizione Chiusura Note Chiusura Categorie Chiusura Codice Contratto Numero Linea Contratto Data Modifica Contratto Numero Contratto Righe contratto dei progetti Contratti dei progetti isa Contratti Righe Contratto Data Dicembre Descrizione Duplica Lavoro Errore ! Errore ! La data finale della mansione deve essere  più vecchia di quella iniziale Errore! Non puoi creare lavori ricorsivi. Errore! La data di inizio del progetto deve essere antecedente alla data di fine Febbraio Campo File Filtri... Raggruppa per... Ore effettuate Ore Lavorate per cliente Se confermato il record sarà salvato subito e poi si potrà comunque modificare. Confermare? Gennaio Luglio Giugno Marzo Maggio Mese fatturazione Non si puo' chiudere il progetto perche' lo stato del lavoro "%s" non e' "cancellato" o "terminato". Non Fatturabile Novembre Ottobre Note Apertura Codice PTF Partner Ore Pianificate Programma Progetto Contratto progetto Righe Contratto Lavori Contratto_progetto Progetti Riferimenti Settembre Ore impiegate Stato fatturazione Attività La società scelta non è tra quelle consentite all'utente Il progetto '%s' è stato chiuso. Ticket Richiesto Riferimento ticket Oggi Trasferito as400 Tipologia del lavoro Tipologia del lavoro Tipologia del lavoro Search Tipologia del lavoro dell'attività Utente Attenzione ! Tipologia del lavoro Descrizione del lavoro Lavorazioni Ricerca Lavori Anno fatturazione Non si possono avere due utenti con lo stesso login ! Non si può chiudere un progetto senza aver indicato correttamente le ore da fatturare. Non si può chiudere un progetto che ha categoria "85 - Assistenza presso clienti" senza indicare la riga di contratto Non si può chiudere un progetto che inizia con la stringa  "HR_" senza inserire le informazioni della chiusura. Non si può chiudere un progetto che ha projec manager HelpBoard. Non si può chiudere un'attività che ha come responsabile HelpBoard. Non si puo' chiudere il progetto perche' lo stato del lavoro "%s" non e' "cancellato" o "terminato". Non si può aprire un'attività che ha come responsabile HelpBoard. Deve essere scelto lo stato fatturazione. Incluso pacchetto ore id_progetto res.users sconosciuto 