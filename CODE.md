# Technický popis

Program nepoužívá žádné externí knihovny; na vykreslování oken je použit modul `Tkinter`, jehož vzhled závisí na operačním systému. Celý se nachází v souboru `goapp.py`.

Je užita jednoduchá MCV architektura, tedy rozdělení programu na části model hry, kontrolor (controller) a pohled (view); každá je samostatnou třídou. Dále je v kódu definováno několik tříd, které jsou popsány níže. Podrobnější dokumentace všech metod a atributů se nachází v programu (v angličtině).

Na začátku se nachází konstanty pro účely programu.

Na konci se nachází hlavní část spouštící program s výchozí deskou 9 × 9 o velikosti políčka 36 v módu `Play` s komi 6, 5.

## GoError

Třída výjimek pro účely programu. Má podtřídy `PlacementError`, která signalizuje nelegální či nemožné položení/vzetí kamene, a `ComplexityError`, která signalizuje přílišnou složitost výpočtu.

## Point

Třída průsečíků desky, na něž lze pokládat kameny. Obsahuje informaci o tom, kde na desce se nachází, které průsečíky jsou sousední, a jaký kámen na něm je (je-li nějaký); dále může uchovávat skupinu, jehož je součástí. Umožňuje nalezení své skupiny, oblasti ohraničené jedním hráčem, v níž je, a určení, jestli leží v oku nějaké hráčovy skupiny.

## String

Třída souvislých skupin průsečíků (spojených podél linek desky; objekty `Point`). Buďto je maximální skupinou kamenů jehnoho hráče, nebo maximální oblastí ohraničenou jedním hráčem. Obsahuje informaci o tom, jaké má dané skupina svobody; může také zaznamenat, zda je naživu a jaké má oči.

## Grid

Třída rozložení kamenů na desce (objektů `Point` v matici). Umožňuje nalézt bezpodmíněčně živé skupiny na desce (využitím Bensonova algoritmu[^1]) a území obou hráčů.

## Result

Třída výsledků pro vyhledávání řešení pozice. Zaznamenává hodnotu, hloubku a dceřinná řešení pro každý optimální tah (tj. ve výsledku celý strom optimálních sekvenci).

## Board

Třída stavů desky během hry. Pamatuje si již vyřešené pozice ve slovníku. Obsahuje informaci o tom, jak jsou rozloženy kameny (objekt `Grid`), kolik mají hráči zajatců, kde se nachází ko a kolik předchozích tahů bylo pasováno; dále také může uchovávat území hráčů, nerozhodnutou oblast a dceřinné pozice (pro vyhledávání). Umožňuje provádění tahů (resp. testování jejich legality), podrobnější hledání živých skupin, hledání nejlepšího tahu a vyhodnocování podle pravidla o dlouhém cyklum jestli nedošlo k opakování pozice.

### Board.solve

Metoda na hledání optimálního řešení. Definuje několik pomocných funkcí. Postup je z valné části přejatý z programu MIGOS van der Werfa _et al_[^2]. Je použit algoritmus minmaxu (implementovaného jako negamax) s iterativním prohlubováním a alfa-beta ořezáváním. Pro dané vyhledávání se udržuje slovník s prozatímně naleznými řešeními (transpoziční tabulka). Pro malé desky se v malé hloubce vyhledávají také symetrické pozice. Jsou implementovány heuristika killer tahů a heuristika historie. Desky jsou vyhodnocovány heusristickou funkci odměňující nadějnější tahy. Možné tahy jsou omezeny na tahy mimo rozhodnutá území, takže se na deskách průběžně hodnotí život; již takto vyhodnocené jsou ukládány v modelu. Pokud je území bepodmíněčné, běží vyhodnocování ve zkráceném režimu pro zrychlení (nezkouší se život přes _miai_).

## GameModel

Vnitřní model hry, ve kterém jsou uloženy stavy desky (jako objekty `Board`). Umožňuje akce jako vytvoření nové desky, resetování počtu zajatců, umístění/odebrání kamene, pasování, odvolání akce a vrácení odvolání. Testuje, jestli by mohlo dojít k opakování pozice. Uchovává již vyhodnocené desky. Také si pamatuje nalezená řešení desek.

## GameController

Kontroler, který zprostředkovává komunikaci mezi modelem a pohledem a provádí příslušné operace. Je schopný aktualizovat pohled podle stavu desky a zajatců, vyhodnocovat pozici na desce, nastavovat, jaký hráč je na tahu, a resetovat historii desek. Také sleduje, nedošlo-li k opakování pozice nebo dvojímu pasování za sebou.

## Goban

Podtřída třídy `Canvas` z modulu `Tkinter`, která slouží k vykreslování desky na obrazovku. Umožňuje měnit svou velikost a rozměry a vykreslit kameny, ko a území podle objektu `Board`, rovněž po vyřešení vykreslit nejlepší tahy.

## SizeMenu

Menu pro nastavování velikosti a rozměrů desky jako třída. Obsahuje možnost fixovat čtvercovost desky (ve výchozím nastavení zapnuto).

## ModeMenu

Menu pro nastavování hracího módu a způsobu pokládání kamenů jako třída. Obsahuje možnost voleb, zda při odebírání kamenů brát zajatce a zda zachytávat opakování pozice na desce.

## ScoreMenu

Menu pro nastavování komi a vyhodnocování pozice na desce jako třída.

## GameView

Pohled – grafická realizace programu v Tkinteru, která předává uživatelské vstupy kontroleru. Vykreslí hlavní okno aplikace s objektem Goban, počty zajatců, ovládacími tlačítky a instancemi `SizeMenu`, `ModeMenu` a `ScoreMenu`.

 [^1]: BENSON, David B. Life in the game of Go. _Information Sciences_. 1976, vol. 10, no. 2, s. 17–29. ISSN 0020-0255.
 [^2]: VAN DER WERF, Erik C. D.; VAN DEN HERIK, H. Jaap a UITERWIJK, Jos W. H. M. Solving Go on Small Boards. _Journal of the International Computer Games Association_. 2003, vol. 26, no. 2, s. 92–107.
