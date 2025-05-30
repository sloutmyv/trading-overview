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

## Résumé du script `001_top_crypto_snapshot.py`

Ce script interroge l’API CoinGecko afin d’extraire, à la date d’exécution, les `N` cryptomonnaies ayant la plus grande capitalisation boursière. Le résultat est sauvegardé dans un fichier JSON intitulé `YYMMDD_top_crypto_history.json` et stocké dans le dossier `crypto_data/market_data/`. Exécuté régulièrement, il constitue une série de snapshots quotidiens exploitables pour l’analyse de l’évolution du marché crypto. **Note : seule la market cap est utilisée comme critère de classement.**

## Résumé du script `002_plot_marketcap.py`

Ce script charge un fichier JSON produit par le script 001 et affiche un graphique de type treemap représentant la répartition des capitalisations boursières des principales cryptomonnaies. Chaque surface est proportionnelle à la market cap de l’actif. Le script est conçu pour être utilisé dans un notebook ou directement depuis un script Python avec la fonction `plot_marketcap()`.

## Résumé du script `003_top_stocks_marketcap.py`

Ce script interroge l’API **Financial Modeling Prep** afin d’extraire les `N` entreprises cotées ayant la plus grande capitalisation boursière (NASDAQ et NYSE). Le résultat est sauvegardé dans un fichier JSON intitulé `YYMMDD_top_stock_history.json` et stocké dans le dossier `stock_data/market_data/`.  
**Note : le classement est ordonné localement par market cap décroissante à partir des données extraites.**

## Résumé du script `004_plot_stock_marketcap.py`

Ce script lit un fichier JSON généré par `003_top_stocks_marketcap.py` et produit une visualisation **treemap** des capitalisations boursières à la date indiquée.  
Une légende, située sous le graphique, fait correspondre les symboles boursiers aux noms complets des entreprises.

## Résumé du script 005_get_crypto_data.py

Ce script interroge l’API Binance pour télécharger les chandeliers historiques (prix, volumes) des 3 plus grandes cryptomonnaies du dernier snapshot top_crypto_history.json (paire en USDC).
Les données sont stockées en .parquet dans crypto_data/pair_data/, et consolidées automatiquement si des données existent déjà.

## Résumé du script 006_preview_crypto_data.py

Ce script lance un dashboard Streamlit permettant de visualiser de manière interactive les fichiers .parquet des données crypto.
Le graphique affiche les chandeliers (OHLC) et les volumes colorés (en rouge ou vert) selon l’évolution du prix. L’utilisateur peut filtrer dynamiquement la plage de temps via un calendrier.


## Résumé du script 007_get_stock_data.py

Extraction des stocks 

## Résumé du script 008_simple_EMA_strategy_test.py

première stratégie sur le crossover des EMA sur le btc 1d pour test



