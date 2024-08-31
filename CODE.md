# Technický popis

Program nepoužívá žádné externí knihovny;
na vykreslování oken je použit modul `Tkinter`,
jehož vzhled závisí na operačním systému.
Celý se nachází v souboru `goapp.py`.

Je užita jednoduchá MCV architektura, tedy rozdělení programu na části
model hry, kontrolor (controller) a pohled (View); každá je samostatnou třídou.
Dále je v kódu definováno několik tříd a funkcí, které jsou popsány níže.
Podrobnější dokumentace všech metod a atributů se nachází v programu (v angličtině).

Na konci se nachází hlavní část spouštící program
s výchozí deskou 9x9 o velikosti políčka 36 v módu Play.

## GoError

Třída výjimek pro účely programu. Má podtřídu
`PlacementError`, která signalizuje nelegální či nemožné položení/vzetí kamene.

## Point

Třída průsečíků desky, na něž lze pokládat kameny.

Obsahuje informaci o tom, kde na desce se nachází, které průsečíky jsou sousední,
a jaký kámen na něm je (je-li nějaký); dále může uchovávat skupinu, jehož je součástí.
Umožňuje nalezení své skupiny, oblasti ohraničené jedním hráčem, v níž je,
a určení, jestli leží v oku nějaké hráčovy skupiny.

## String

Třída souvislých skupin průsečíků (spojených podél linek desky; objekty `Point`).
Buďto je maximální skupinou kamenů jehnoho hráče, nebo
maximální oblastí ohraničenou jedním hráčem.

Obsahuje informaci o tom, jaké má dané skupina svobody; může také zaznamenat, zda je naživu.

## Grid

Třída rozložení kamenů na desce (objektů `Point` v matici).

Umožňuje nalézt bezpodmíněčně živé skupiny na desce.

## Board

Třída stavů desky během hry.

Obsahuje informaci o tom, jak jsou rozloženy kameny (objekt `Grid`),
kolik mají hráči zajatců, kde se nachází ko a kolik předchozích tahů bylo pasováno.
Umožňuje provádění tahů (resp. testování jejich legality), podrobnější hledání živých skupin,
vyhodnocení území hráčů a hledání optimálního tahu algoritmem minmaxu.

## test_repetition

Funkce, která obdrží historii stavů desky a vyhodnotí podle pravidla o dlouhém cyklu,
jestli nedošlo k opakování.

## Goban

Podtřída třídy `Canvas` z modulu `Tkinter`, která slouží k vykreslování desky na obrazovku.
Umožňuje měnit svou velikost a rozměry a vykreslit kameny, ko a území podle objektu Board,
rovněž vykreslit návrhy na nejlepší tah.

## SizeMenu

Menu pro nastavování velikosti a rozměrů desky jako třída.
Obsahuje možnost fixovat čtvercovost desky (ve výchozím nastavení zapnuto).

## ModeMenu

Menu pro nastavování hracího módu a způsobu pokládání kamenů jako třída.
Obsahuje možnost voleb, zda při odebírání kamenů brát zajatce
a zda zachytávat opakování pozice na desce.

## ScoreMenu

Menu pro nastavování komi a vyhodnocování pozice na desce jako třída.

## GameModel

Vnitřní model hry, ve kterém jsou uloženy stavy desky (jako objekty Board).
Umožňuje akce jako vytvoření nové desky, resetování počtu zajatců,
umístění/odebrání kamene, pasování, odvolání akce a vrácení odvolání.

## GameController

Kontroler, který zprostředkovává komunikaci mezi modelem a pohledem a provádí příslušné operace.
Je schopný aktualizovat pohled podle stavu desky a zajatců, vyhodnocovat pozici na desce,
nastavovat, jaký hráč je na tahu, a resetovat historii desek.
Také sleduje, nedošlo-li k opakování pozice nebo dvojímu pasování za sebou.

## GameView

Pohled – grafická realizace programu v Tkinteru, která předává uživatelské vstupy kontroleru.
Vykreslí hlavní okno aplikace s objektem Goban, počty zajatců, ovládacími tlačítky
a instancemi SizeMenu, ModeMenu a ScoreMenu.
