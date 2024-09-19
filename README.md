# GoApp documentation (in Czech)

A simple application for simulating the board game of go. Enables normal game of two players against each other as well as creating any given position and attempting its analysis. The Japanese Rules[^1] are used.

For a school programming course.

## Spuštění

Před spuštěním je nutné mít nainstalovaný Python. Aplikace se spustí příkazem `python goapp.py` v adresáři projektu.

## Rozhraní

### Hrací plocha

Kliknutím na průsečík desky se položí (resp. odebere) kámen (je-li to možné). Tažením je možné položit více kamenů najednou. Barva záleží na tom, kdo je zrovna na tahu, resp. na nastavení. Průsečík, na nějž není možné táhnout v důsledku pravidla ko, je značen prázdným čtverečkem. Některé průsečíky jsou zvýrazněny pro orientaci.

Nad deskou jsou zobrazeny počty zajatců obou hráčů a tlačítko `Reset prisoners`, které je znuluje; tuto akci nelze odvolat. Zobrazovaný počet zajatců nemůže přesáhnout 999.

Pod deskou se nachází tlačíka na pasování (`Pass`), odvolání akce (`Undo`) a navrácení odvolaného stavu (`Redo`). Tytéž akce je rovněž možné provést po řadě stistknutím kláves `p`, `BackSpace` a `r`.

### Postranní menu

#### Parametry desky

Parametry desky se nastavují v postranním menu; je možné upravit počet řádků a sloupců desky a velikost políček. Je-li zaškrtnuté tlačítko `Square`, počet sloupců je automaticky roven počtu řádků. Tlačítko `Resize` změní velikost zobrazení desky. Tlačítko `New Board` vytvoří po ujištění novou desku dle zadaných parametrů; tuto akci nelze odvolat. Je-li požadovaný rozměr příliš velký, zobrazí se chybová hláška.

#### Herní mód

Dále je možno nastavit herní mód.

V režimu `Play` se oba hráči střídají, z prázdné desky začíná černý, a hraje se hra podle pravidel. Možnost `Test Repetition` rozhoduje, jestli hra hlásí opakování stavu desky (hledáno až do začátku momentální hrací sekvence). Nastala-li by taková situace, zobrazí se okno s informací o výsledku podle zajatců a možností buď tah provést, a tím ukončit hrací sekvenci (`OK`), či zrušit (`Cancel`). Pokud by opakování mohlo nastat v následujícím tahu, je dané políčko značeno prázdným kolečkem.

V režimu `Sandbox` je ignorováno pravidlo ko (je však vykreslováno), ukončení hry dvojitým pasem a možné opakování pozice. Lze zde nastavit, zda se hráči střídají v pokládání kamenů (`Alternate`), dává je pouze černý (`Black only`), bílý (`White only`), či jsou kameny odebírány (`Erase`; je-li zaškrtnuto `Take prisoners`, bere se tím zajatec). V případě `Alternate` akce `Undo` a `Redo` mění hráče.

Přepínání mezi módy vždy začíná novou hrací sekvenci, za niž se není možné vrátit pomocí `Undo`. Jestliže byla v režimu `Sandbox` změněna volba na `Alternate` nebo bylo přepnuto z jiné volby než `Alternate` do režimu `Play`, první hraje hráč posledně zvolené barvy, s výjimkou přechodu z `Erase`; pak první táhne černý.

#### Skórování

Nakonec je možné nastavit používanou hodnotu komi (musí být poločíselná) a vyhodnocovat desku.

Tlačítkem `Score` se vyhodnotí živé skupiny obou hráčů, zobrazí se jejich území a skóre. Téhož účinku se dosáhne dvojím pasováním za sebou v režimu `Play` s tím, že se ukončí hrací sekvence. Tlačítkem `Best move` se program pokusí vyhodnotit nejlepší možný tah v dané situaci. Je-li příliš složitá, zobrazí chybovou hlášku; stejně tak, pokud výpočet trvá příliš dlouho. Jinak vykreslí nalezené možnosti nebo napíše pas (byl-li by to nejlepší tah). Poté, co byla pozice jednou vyřešena, je uložena celá optimální variace; provedením jednoho z nejlepších tahů se okamžitě zobrazí pokračování (možná kromě pasu), odvoláním tahu původní řešení. Provedením jiné akce (jiného tahu, přepnutím módu, `Redo`, vytvoření nové desky) se paměť řešení maže.

## Limitace

Program je schopen poznávat jako živé pouze bezpodmíněčně živé skupiny (ani při nekonečně mnoha tazích protihráče nemohou být vzaty) a ty od těchto o 1 tah vzdálené. S ostatními skupinami se pracuje jako mrtvými. Při skórování by proto hráči měli takto své skupiny oživit, ideálně tak, aby se nezměnilo zřejmé území (tj. výměnou za položení zajatce protihráče). Teoreticky to znamená, že klasické seki je skórováno správně a skupiny mrtvé podle pravidel jsou vskutku mrtvé v souladu s japonskými pravidly, nicméně i tak mohou nastat odchylky (a oživení může ztratit body).

Technická seki v důsledku japonských pravidel kvůli neutrálním bodům mezi jinak samostatně žijícími skupinami nejsou brána v úvahu, což je v souladu s běžnou praxí. Rovněž nejsou aplikována pravidla o obnovení hry a prohře obou hráčů.

Při hledání optimálního tahu jsou zkoušeny všechny možné tahy mimo území, nerozhodnutých bodů musí tedy být řádově jednotky. Hledání může trvat několik minut. Bude řádově rychlejší, pokud jsou na začátku území ohraničená bezpodmíněčně živými skupinami. Nejsou uvažovány tahy do území hráčů, přičemž by někdy užitečné být mohly, například kdyby bylo možné vytvořit živou skupinu, ohrozit skupinu protihráče nebo jako ko hrozbu; stejně tak program nemusí správně vyhodnotit, pokud nějaký tah zvnějšku ohrozí život skupiny. Jinak je výsledek zcela správný, až na velice vzácný případ, kdy by byl optimální výsledek remíza opakováním pozice.

## Stručná pravidla Go[^1]

_Go_ je hra na desce s vyznačenou mřížkou (standardními rozměry jsou 9 × 9, 13 × 13 a 19 × 19). Dva hráči, černý a bílý, se střídají v tazích; každý tah buďto položí kámen své barvy na prázdný průsečík, nebo pasují bez akce. Začíná černý.

_Skupinou_ kamenů se rozumí maximální souvislá množina kamenů jedné barvy (kameny bereme za spojené, pokud leží na sousedních průsečících). _Svobodami_ skupiny se rozumí prázdné průsečíky sousedící s nějakým kamenem skupiny. Pro tah položením kamene platí následující:
- Pokud po tahu hráče ztratí nějaká skupina protihráče všechny své svobody, jsou kameny této skupiny odstraněny z desky a daný hráč si je bere jako své zajatce.
- Tah je zakázáno provést, pokud neměla skupina právě zahraného kamene žádné svobody (po odstranění případných zajatců).
- Tah je rovněž zakázáno provést, pokud by po něm rozložení kamenů na dece bylo stejné jako před posledním tahem (toto se nazývá pravidlo _ko_).

Hra končí dvěma pasy za sebou. Poté je vyhodnocena pozice. Skupina se nazývá _živá_, pokud by ji protihráč (začínaje) při optimální hře obou hráčů nemohl vzít[^2] (typicky tak, že má dvě _oči_ – prostory, které protihráč nemůže zaplnit); v opačném případě se nazývá _mrtvá_. Oblasti průsečíků pouze s mrtvými skupinami jednoho hráče ohraničené pouze živými skupinami druhého hráče (alespoň nějakou) se nazývají _území_ druhého hráče[^2]. Hráči si z území odstraní mrtvé kameny protihráče a vezmou je jako zajatce. Konečně počet bodů hráče je počet součet počtu průsečíků v jeho území a počtu jeho zajatců. Hráč s větším počtem bodů vyhrává.

Během hry se může stát, že se na desce vyskytne _dlouhý cyklus_, tedy že se zopakuje pozice (daná rozložením kamenů), která se již naskytla[^3]. V takovém případě se spočte, který hráč od posledního výskytu pozice získal větší počet zajatců; hra předčasně končí a tento hráč vyhrává. Pokud jsou na tom hráči stejně, hra končí bez výsledku.

Jako kompenzace výhody prvního hráče nebo jako handicap se hrává s tzv. _komi_; jedná se o hodnotu, která je při určování výsledku přičtena ke skóre bílého (při japonských pravidlech na standardních deskách 6, 5).

[^1]: NIHON KIIN; KANSAI KIIN; DAVIES, J. a CANO, J., HANSEN, F. (ed.). _The Japanese Rules of Go_. Online. 1989. Dostupné z: http://www-2.cs.cmu.edu/wjh/go/rules/Japanese.html. [cit. 2024-09-19].

[^2]: Přesná definice života a území je složitější a závisí na zvolených pravidlech, pokud ji vůbec poskytují. Pro účely tohoto programu rozdíly nejsou tolik podstatné; poznamenejme snad jen, že není brána v potaz situace _seki_, kdy skupiny dvou hráčů žijí vzájemně tak, že ani jedna strana nedovede žít bezpodmíněčně či vzít druhou.

[^3]: Rovněž co se dlouhých cyklů týče se různá pravidla liší. Při hraní je to v programu možno ignorovat, při vyhodnocování se program uvedeným pravidlem řídí. Tento postup však odpovídá duchu japonských pravidel[^4].

[^4]: JASIEK, Robert. _Commentary on the Japanese 1989 Rules._ Online. 2007. Dostupné z: http://home.snafu.de/~jasiek/j1989c.html. [cit. 2024-09-19].
