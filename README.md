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

---

## Résumé du script `001_top_crypto_snapshot.py`

Ce script interroge l’API CoinGecko afin d’extraire, à la date d’exécution, les `N` cryptomonnaies ayant la plus grande capitalisation boursière. Le résultat est sauvegardé dans un fichier JSON intitulé `YYMMDD_top_crypto_history.json` et stocké dans le dossier `crypto_data/market_data/`. Exécuté régulièrement, il constitue une série de snapshots quotidiens exploitables pour l’analyse de l’évolution du marché crypto. **Note : seule la market cap est utilisée comme critère de classement.**
