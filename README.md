# Soundcloud Sync

> **Téléchargez et synchronisez** vos musiques, playlists, albums et artistes SoundCloud **localement** sur votre PC.

![screen](ressources/screen1.png)


## Fonctionnement et options

- **Téléchargez tous les titres d'une playlist ou d'un autre type de contenu en un clique.**
- Fichiers téléchargés dans **la meilleure qualité disponible** :
  - **160 kb/s (OPUS)** avec un compte gratuit.
  - **258 kb/s (AAC)** avec un compte Premium.
- Conserve les **métadonnées** : titre, artiste, album, genre, artwork (pochette), date de sortie.
- Synchronise les contenus :
  - Les **nouveaux titres** ajoutés à une playlist/album sont téléchargés.
  - Les **titres supprimés** des playlists peuvent être **supprimés localement** (option activée par défaut, modifiable dans les paramètres).
- Prend en charge la **conversion en MP3** (nécessite `ffmpeg`).

### Types de contenus pris en charge
- **Musique** : `https://soundcloud.com/nerz303/les-free-party`
- **Playlist** : `https://soundcloud.com/kurtdklg/sets/tribe`
- **Album** : `https://soundcloud.com/saphirelefleur/sets/houellebecq-soumission`
- **Artiste** : `https://soundcloud.com/bertha_official`
- **Titres aimés** : `https://soundcloud.com/matekasm/likes`


## Installation

Vous avez besoin de `Python 3.9` minimum: https://www.python.org/downloads/

FFMPEG est aussi requis.

Avec Windows, le plus simple est d'utiliser WINGET (https://aka.ms/getwinget): Dans le terminal, entrez

    winget install ffmpeg

Sur macOS: `brew install ffmpeg`.

Sur Linux, utilisez votre gestionnaire de paquet.

Pour installer les dépendances Python, entrez cette commande dans le terminal depuis le répertoire du projet:

    python -m pip install -r requirements.txt

Pour lancer le programme:

    python "SoundCloud sync.py"


## Paramètres

*Vous pouvez modifier ces paramètres en ouvrant la fenêtre de configuration depuis l'onglet Actions.*

![screen](ressources/screen2.png)

#### Token Soundcloud
Ne partagez jamais votre Token à quiconque. Il permet de se connecter à votre compte.

Pour l'obtenir:
1. Connectez-vous à soundcloud.com
2. Ouvrez les outils de développement (F12 ou Ctrl+Shift+I)
3. Allez dans l’onglet Application > Cookies
4. Copiez la valeur du cookie oauth_token

#### Répertoire de synchronisation
Vous devez spécifier le chemin du répertoire dans lequel seront téléchargées les musiques.
Choisissez un dossier vide, par exemple `Musiques/Soundcloud/`
Chaque répertoir est indépendant et contient un fichier JSON avec tous les liens SoundCloud ajoutés.


## Notes

Si l'installation des dépendances du requirements.txt échoue avec une version récente de Python, essayez d'utiliser `Python 3.9`.

Il n'est pas possible de télécharger deux musiques avec le même titre dans la même playlist.

Désactiver les services de synchronisation de fichier comme OneDrive et ne pas convertir les fichiers au format MP3
sont des moyens d'accélérer le téléchargement des contenus.

Certains bugs liés au format des noms de fichiers peuvent affecter l'affichage du status de synchronisation d'un élément.
Voir les caractères interdits dans les noms de fichier Windows.
