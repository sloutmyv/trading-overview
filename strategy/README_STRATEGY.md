## Glossaire détaillé des métriques de backtest

### Période analysée

- Start : Horodatage de la première bougie (candle) incluse dans le backtest. Il fixe le point de départ de toutes les statistiques.
- End : Horodatage de la dernière bougie testée.
- Duration : Période couverte (End – Start). Utile pour replacer les résultats dans leur contexte temporel (par ex. savoir si la stratégie a traversé un marché haussier ou baissier).

### Capital & frais

- Equity Final ($) : Valeur du portefeuille à la dernière barre après prise en compte des frais et de la valeur de la position ouverte éventuelle.
- Equity Peak ($) : Plus haut niveau d’equity atteint au cours du backtest – sert de référence pour le drawdown max.
- Commissions ($) : Somme totale payée en frais de transaction (commissions, slippage simulé, etc.).
- Exposure Time (%) : Pourcentage du temps où la stratégie est investie par rapport à la durée totale. Mesure la « fréquence d’exposition » au risque de marché.

### Performance brute

- Return (%) : Performance globale -> (Equity_Fin / Equity_Init – 1) × 100.
- Buy & Hold Return (%) : Rendement qu’aurait fourni l’achat initial de l’actif et sa conservation jusqu’à la fin (comparaison passive vs. active).
- Return (Ann.) (%) : Rendement annualisé en extrapolant le Return sur 365 jours -> ((1 + Return)^(365/Duration_days) – 1) × 100.
- CAGR (%) : Taux de croissance annuel composé. Reflète la croissance lissée année après année. Méthodologie équivalente au Return (Ann.) mais généralement préférée pour plus d’un an de données.
- Volatility (Ann.) (%) : Écart-type annualisé des rendements quotidiens ; quantifie l’« amplitude » moyenne des variations.

### Ratios ajustés au risque

- Sharpe Ratio : (Return (Ann.) – Rf) / Volatility (Ann.), où Rf est le taux sans risque (souvent ≈ 0 dans Backtesting.py). Plus il est haut, meilleur est le rendement par unité de volatilité.
- Sortino Ratio : Variante du Sharpe. On divise par la seule volatilité baissière (écart-type des rendements < 0). Récompense les stratégies à pertes rares mais à forte volatilité haussière.
- Calmar Ratio : CAGR / Max. Drawdown. Mesure combien d’alpha annuel on obtient par point de drawdown.
- Alpha (%) : Sur- ou sous-performance annuelle relative à un bench (Buy & Hold ici). Approximée dans Backtesting.py ; > 0 % indique de la valeur ajoutée.
- Beta : Sensibilité du portefeuille aux variations du bench ; ≈ 1 : suit le marché, < 1 : moins volatile, > 1 : amplifie les mouvements.

### Drawdowns

- Max. Drawdown (%) : Plus forte perte relative depuis un pic d’equity jusqu’au creux suivant. Indicateur clé du risque psychologique et financier.
- Avg. Drawdown (%) : Moyenne arithmétique de tous les drawdowns mesurés.
- Max. Drawdown Duration : Nombre de jours entre le sommet précédant le drawdown et la récupération complète (nouveau sommet).
- Avg. Drawdown Duration : Durée moyenne de tous les épisodes de drawdown.

### Statistiques de trading

- Trades : Nombre total d’ordres « round-trip » (entrée + sortie).
- Win Rate (%) : Part des trades clôturés avec un gain net.
- Best Trade (%) : Rendement du trade le plus profitable.
- Worst Trade (%) : Rendement du trade le plus perdant.
- Avg. Trade (%) : Moyenne arithmétique des rendements de chaque trade.
- Max. Trade Duration : Durée du trade ouvert le plus longtemps.
- Avg. Trade Duration : Durée moyenne de détention d’une position.
- Profit Factor : (Somme_Gains / Somme_Pertes) sur l’ensemble des trades. > 1 signifie stratégie globalement rentable.
- Expectancy (%) : Gain/perte moyen espéré par trade, tenant compte de la win-rate et du ratio gains/pertes.
- SQN : System Quality Number de Van Tharp : √n × (Avg_Trade / Std_Dev_Trades). > 2 : très bon ; > 3 : excellent.
- Kelly Criterion : Fraction optimale du capital à risquer sur chaque trade pour maximiser la croissance logarithmique (théorique, sans contrainte).

## Processus en quatre étapes pour développer et valider des stratégies de trading, applicable notamment aux stratégies basées sur les prix.

1. Excellence dans l'échantillon (In-sample excellence) : Cette étape consiste à optimiser la stratégie sur des données historiques et à évaluer si les résultats obtenus sont excellents et ne présentent pas de surajustement évident.
2. Test de permutation Monte Carlo dans l'échantillon (In-sample Monte Carlo permutation test) vise à déterminer si l'excellente performance dans l'échantillon est due à des schémas intrinsèques des données ou à un biais d'exploration des données (data mining bias). Il s'agit de générer des permutations des données de prix qui conservent les propriétés statistiques mais suppriment les schémas légitimes, puis d'optimiser la stratégie sur ces ensembles de données permutées. Une valeur P est calculée pour évaluer la probabilité que les résultats réels soient dus au biais d'exploration des données. Une valeur P inférieure à 1% est considérée comme un succès.
3. Test hors échantillon progressif (Walk-forward test) consiste à optimiser la stratégie sur des données historiques, puis à la tester sur de nouvelles données non vues, simulant ainsi le trading en conditions réelles. 
4. Test de permutation Monte Carlo hors échantillon progressif (Walk-forward Monte Carlo permutation test) évalue si des résultats satisfaisants en mode hors échantillon progressif sont dus à de véritables schémas ou simplement à la chance. Il consiste à permuter les données après la première phase d'entraînement et à évaluer la performance de la stratégie sur ces permutations. Une valeur P d'environ 5% est acceptable pour une année de données, tandis que 1% est préférable pour deux années ou plus.

Développer un script Python pour backtester une stratégie de trading en utilisant un processus en quatre étapes :
1. Optimisation des paramètres de la stratégie sur un ensemble de données historiques (in-sample) pour atteindre une performance 'excellente' tout en évitant le surajustement.
2. Réalisation d'un test de permutation Monte Carlo sur les résultats in-sample pour valider que la performance n'est pas due au hasard ou au data mining (objectif P-value < 1%).
3. Mise en œuvre d'un test hors échantillon progressif (walk-forward) où la stratégie est optimisée sur une fenêtre de données historiques glissante et testée sur la période suivante.
4. Exécution d'un test de permutation Monte Carlo sur les résultats du test hors échantillon progressif pour confirmer la robustesse de la stratégie (objectif P-value < 5% pour 1 an de données, < 1% pour 2 ans ou plus).

Une stratégie surajustée affichera des résultats exceptionnels (par exemple, des profits élevés, un faible drawdown) lorsqu'elle est testée sur les données historiques utilisées pour la construire et l'optimiser. Cela donne une fausse impression de sa robustesse. Une stratégie surajustée manque de capacité à généraliser ses règles à des conditions de marché différentes de celles de son ensemble d'entraînement. Elle n'a pas appris les principes fondamentaux et robustes du marché, mais plutôt les particularités d'un ensemble de données spécifique.
