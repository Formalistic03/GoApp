# GoApp

## Documentation (in Czech)

### Spuštění

Před spuštěním je nutné mít nainstalovaný Python.
Aplikace se spustí příkazem `python goapp.py` v adresáři projektu.

### Rozhraní

#### Hrací plocha

Kliknutím na průsečík desky se položí (resp. odebere) kámen (je-li to možné).
Barva záleží na tom, kdo je zrovna na tahu, resp. na nastavení.
Průsečík, na nějž není možné táhnout v důsledku pravidla ko,
je značen prázdným čtverečkem.

Nad deskou jsou zobrazeny počty zajatců obou hráčů
a tlačítko `Reset prisoners`, které je znuluje; tuto akci nelze odvolat.

Pod deskou se nachází tlačíka na pasování (`Pass`),
odvolání akce (`Undo`) a navrácení odvolaného stavu (`Redo`).

#### Postranní menu

Parametry desky se nastavují v postranním menu;
je možné upravit počet řádků a sloupců desky a velikost políček.
Je-li zaškrtnuté tlačítko `Square`, počet sloupců je automaticky roven počtu řádků.
Tlačítko `Resize` změní velikost zobrazení desky.
Tlačítko `New Board` vytvoří po ujištění novou desku dle zadaných parametrů;
tuto akci nelze odvolat.

Dále je možno nastavit herní mód.

V režimu `Play` se oba hráči střídají, z prázdné desky začíná černý,
a hraje se hra podle pravidel.
Možnost `Test Repetition` rozhoduje, jestli hra hlásí opakování stavu desky
(hledáno až do začátku momentální hrací sekvence).
Nastala-li by taková situace, zobrazí se okno s informací o výsledku podle zajatců
a možností buď tah provést (`OK`) či zrušit (`Cancel`).

V režimu `Sandbox` je ignorováno pravidlo ko (je však vykreslováno),
ukončení hry dvojitým pasem a možné opakování pozice.
Lze zde nastavit, zda se hráči střídají v pokládání kamenů (`Alternate`),
dává je pouze černý (`Black only`), bílý (`White only`),
či jsou kameny odebírány (`Erase`; to nemění zajatce).
V případě `Alternate` akce `Undo` a `Redo` mění hráče.

Přepínání mezi módy vždy začíná novou hrací sekvenci,
za niž se není možné vrátit pomocí `Undo`.
Jestliže byla v režimu `Sandbox` změněna volba na `Alternate`
nebo bylo přepnuto z jiné volby než `Alternate` do režimu `Play`,
první hraje hráč posledně zvolené barvy, s výjimkou přechodu z `Erase`;
pak první táhne černý.

### Stručná pravidla Go
