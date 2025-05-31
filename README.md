# Installation de l'environnement virtuel

Pour préparer un espace Python propre au projet :

1. Place-toi à la racine du dépôt.
2. Crée un environnement virtuel :
   ```bash
   python -m venv .venv
   ```
3. Active-le :
   * macOS / Linux : `source .venv/bin/activate`
   * Windows : `.venv\Scripts\Activate`
4. Mets `pip` à jour :
   ```bash
   python -m pip install --upgrade pip
   ```
5. Installe la dépendance du projet :
   ```bash
   pip install requests
   ```
6. Gèle l’état des paquets pour partage ou CI :
   ```bash
   pip freeze > requirements.txt
   ```

## Résumé du script `001_top_crypto_marketcap.py`

Ce script interroge l’API CoinGecko afin d’extraire, à la date d’exécution, les `N` cryptomonnaies ayant la plus grande capitalisation boursière. Le résultat est sauvegardé dans un fichier JSON intitulé `YYMMDD_top_crypto_history.json` et stocké dans le dossier `data/market_analysis/`. Exécuté régulièrement, il constitue une série de snapshots quotidiens exploitables pour l’analyse de l’évolution du marché crypto. **Note : seule la market cap est utilisée comme critère de classement.**

## Résumé du script `002_plot_marketcap.py`

Script Python permettant visualiser les données du fichier JSON produit par 001_top_crypto_marketcap.py sous forme de treemap (surface proportionnelle à la market cap).

## Résumé du script 003_get_crypto_data.py

Télécharge l’historique de prix (chandeliers) pour **une seule paire Binance** (ex. : BTCUSDC) et enregistre toutes les colonnes de l’endpoint `/klines` (12 valeurs)
au format Parquet dans `data/crypto_data/`.

## Résumé du script 004_in_data_perm.py
Generate *N* permutations of a single OHLC parquet file (plus original).

Méthode : 
1. Le script lit le fichier OHLC d’origine et convertit les prix en logarithmes pour travailler avec des additions plutôt que des multiplications.
2. Chaque barre est décomposée en quatre « briques » : le gap d’ouverture (différence C₍t-1₎ → Oₜ) et les variations internes O → H, O → L, O → C.
3. Toutes les briques après `START_INDEX` sont placées dans quatre tableaux NumPy sans rien changer à leurs valeurs.
4. On tire deux permutations : l’une mélange les gaps d’ouverture, l’autre mélange conjointement les triplets (high, low, close) pour préserver la cohérence H ≥ C ≥ L d’une même barre.
5. En reconstruisant barre par barre, on ajoute le gap à la clôture précédente pour obtenir la nouvelle ouverture, puis on ajoute les variations internes pour le high, le low et la clôture.
6. Les prix logarithmiques ainsi recalculés sont re-convertis en prix normaux via l’exponentielle, donnant une série de prix complètement ré-ordonnés.
7. Comme aucune valeur numérique n’est modifiée, les distributions globales (moyenne, écart-type, skewness, etc.) des rendements et des variations intra-barre demeurent strictement identiques à celles du fichier d’origine.
8. Seul l’ordre temporel est détruit : autocorrélations, clustering de volatilité ou tendances disparaissent, ce qui crée un “monde parallèle” statistiquement équivalent mais chronologiquement différent.
9. Le script génère autant de permutations que demandé, plus une copie de l’original, et range chaque jeu de données dans un sous-dossier nommé d’après le fichier source (ex. `data/in_data_perm/btcusdc_1d/`).
10. Cette approche permet de tester des stratégies ou des modèles sur des séries qui gardent les mêmes propriétés de premier ordre que le marché réel tout en éliminant les patterns temporels.


## Résumé du script 008_simple_EMA_strategy_test.py

Premier test de stratégie sur le crossover EMA 12/26 sur le btc 1d



