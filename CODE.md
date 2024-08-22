# Technický popis

Program nepoužívá žádné externí knihovny;
na vykreslování oken je použit modul Tkinter,
jehož vzhled závisí na operačním systému.

Je užita jednoduchá MCV architektura, tedy rozdělení programu na části
model hry, kontrolor (controller) a pohled (View); každá je samostatnou třídou.
Dále je v kódu definováno několik tříd a funkcí, které jsou popsány níže.
Podrobnější dokumentace všech metod a atributů se nachází v programu (v angličtině).

Na konci se nachází hlavní část spouštící program
s výchozí deskou 9x9 o velikosti políčka 36 v módu Play.

## GoError

Třída výjimek pro účely programu. Má podtřídy
`PlacementError`, která signalizuje nelegální či nemožné položení/vzetí kamene,
a `ActionError`, která signalizuje, že kýženou akci nelze ve hře provést.

## Point

Třída průsečíků desky, na něž lze pokládat kameny.
Obsahuje informaci o tom, které průsečíky jsou sousední.

## String

Třída maximálních souvislých skupin kamenů (spojených podél linek desky).
Obsahuje informaci o tom, má-li daná skupina nějakou svobodu.

## create_grid

Funkce, která vytvoří prázdnou desku daných rozměrů. Prvky desky jsou objekty Point.

## find_string

Funkce, která na na zadané desce k danému kamenu vrátí jeho skupinu.

## Board

Třída stavů desky během hry. Obsahuje informaci o tom, jak jsou rozloženy kameny (objekty Point),
kde se nachází ko a jestli předchozí tah byl pas.
Umožňuje provádění tahů (resp. testování jejich legality).

## Goban

Podtřída třídy Canvas z modulu Tkinter, která slouží k vykreslování desky na obrazovku.
Umožňuje měnit svou velikost a rozměry a vykreslit kameny a ko podle objektu Board.

## SizeMenu

Menu pro nastavování velikosti a rozměrů desky jako třída.
Obsahuje možnost fixovat čtvercovost desky (ve výchozím nastavení zapnuto).

## ModeMenu

Menu pro nastavování hracího módu a způsobu pokládání kamenů jako třída.
Obsahuje možnost volby, zda detekovat opakování pozice na desce.

## GameModel

Vnitřní model hry, ve kterém jsou uloženy stavy desky (jako objekty Board).
Umožňuje akce jako vytvoření nové desky, resetování počtu zajatců,
umístění/odebrání kamene, pasování, odvolání akce a vrácení odvolání.

## GameController

Kontroler, který zprostředkovává komunikaci mezi modelem a pohledem a provádí příslušné operace.
Je schopný aktualizovat pohled podle stavu desky a zajatců,
nastavovat, jaký hráč je na tahu, a resetovat historii desek.
Také sleduje, nedošlo-li k opakování pozice nebo dvojímu pasování za sebou.

## GameView

Pohled -- grafická realizace programu v Tkinteru, která předává uživatelské vstupy kontroleru.
Vykreslí hlavní okno aplikace s objektem Goban, počty zajatců, ovládacími tlačítky
a instancemi SizeMenu a ModeMenu.
