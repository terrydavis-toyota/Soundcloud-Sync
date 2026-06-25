""" Fonctions relatives à la synchronisation et au téléchargement des musiques. """

import os
import requests
from pathlib import Path

import soundcloud
import yt_dlp
import music_tag
from PyQt6 import QtCore

from fonctions import utils


class SyncElementThread(QtCore.QThread):
    """ Classe pour lancer la fonction sync_element dans un Thread avec QThread. """

    sync_finished = QtCore.pyqtSignal(object)

    def __init__(self, window_object, library_path, sc_object, url, parent=None):
        super().__init__(parent)
        self.library_path = library_path
        self.sc_object = sc_object
        self.url = url
        self.window_object = window_object

    def run(self):
        try:
            sync_element(self.window_object, self.library_path,
                         self.sc_object, self.url)
        except (FileNotFoundError, TypeError):
            pass
        self.sync_finished.emit(None)


class SyncAllThread(QtCore.QThread):
    """ Classe pour lancer la fonction sync_all dans un Thread avec QThread. """

    sync_finished = QtCore.pyqtSignal(object)

    def __init__(self, window_object, json_path, sc_object, parent=None):
        super().__init__(parent)
        self.json_path = json_path
        self.sc_object = sc_object
        self.window_object = window_object

    def run(self):
        try:
            sync_all(self.window_object, self.json_path, self.sc_object)
        except (FileNotFoundError, TypeError):
            pass
        self.sync_finished.emit(None)


def sync_all(window_object, json_path, sc_object):
    """ Synchroniser l'ensemble du répertoire local avec les éléments distant dans le fichier json. """

    json_content = utils.load_json_file(json_path)
    library_path = Path(json_path).parent
    for musique_id in range(len(json_content["musiques"])):  # Synchroniser chaque musique individuelle.
        sync_element(window_object, library_path, sc_object, json_content["musiques"][musique_id])
    for playlist_id in range(len(json_content["playlists"])):  # Synchroniser chaque playliste.
        sync_element(window_object, library_path, sc_object,
                     json_content["playlists"][playlist_id])
    for album_id in range(len(json_content["albums"])):  # Synchroniser chaque album.
        sync_element(window_object, library_path, sc_object,
                     json_content["albums"][album_id])
    for artiste_id in range(len(json_content["artistes"])):  # Synchroniser les sons de chaque artiste.
        sync_element(window_object, library_path, sc_object,
                     json_content["artistes"][artiste_id])
    for user_id in range(len(json_content["likes"])):  # Synchroniser les listes de likes d'utilisateurs.
        sync_element(window_object, library_path, sc_object,
                     json_content["likes"][user_id])


def sync_element(window_object, library_path, sc_object, json_element):
    """ Synchroniser le contenu distant au répertoire local. """

    if json_element[0] in window_object.lien_en_synchro:
        return
    window_object.lien_en_synchro.append(json_element[0])
    window_object.label_status_general.setText("Synchronisation en cours...")
    tracklist = []  # Liste des sons dans le lien soundcloud distant, composée de sous listes [url, titre].
    content = sc_object.resolve(json_element[0])
    ligne_element = utils.trouver_ligne_url(window_object, json_element[0][8:])
    utils.definir_status_element(window_object, ligne_element,
                                 f"Démarrage de la synchronisation...", "orange")
    try:
        if isinstance(content, soundcloud.Track):  # Si c'est un son unique.
            path = Path(json_element[1].replace("/", os.sep)).parent
            library_path = Path(f"{library_path}{os.sep}{path}{os.sep}")
            library_path.parent.mkdir(parents=True, exist_ok=True)
            tracklist.append([content.permalink_url, content.title])
        elif isinstance(content, soundcloud.AlbumPlaylist) and content.is_album:  # Si c'est un album.
            library_path = Path(f"{library_path}{json_element[1].replace('/', os.sep)}{os.sep}")
            library_path.mkdir(parents=True, exist_ok=True)
            for track in content.tracks:
                resolved_track = sc_object.get_track(track.id)
                tracklist.append([resolved_track.permalink_url, resolved_track.title])
        elif isinstance(content, soundcloud.AlbumPlaylist) and not content.is_album:  # Si c'est une playliste.
            library_path = Path(f"{library_path}{json_element[1].replace('/', os.sep)}{os.sep}")
            library_path.mkdir(parents=True, exist_ok=True)
            for track in content.tracks:
                resolved_track = sc_object.get_track(track.id)
                tracklist.append([resolved_track.permalink_url, resolved_track.title])
        elif isinstance(content, soundcloud.User):  # Si c'est un utilisateur soundcloud.
            library_path = Path(f"{library_path}{json_element[1].replace('/', os.sep)}{os.sep}")
            library_path.mkdir(parents=True, exist_ok=True)
            if json_element[0].endswith("likes"):
                for track in sc_object.get_user_likes(content.id):
                    if isinstance(track, soundcloud.TrackLike):
                        resolved_track = sc_object.get_track(track.track.id)
                        tracklist.append([resolved_track.permalink_url,
                                          resolved_track.title])
            else:
                for track in sc_object.get_user_tracks(content.id):
                    resolved_track = sc_object.get_track(track.id)
                    tracklist.append([resolved_track.permalink_url,
                                      resolved_track.title])

        # Lister toutes les musiques deja téléchargées.
        list_musiques_telechargees = []
        for fichier in library_path.iterdir():
            if fichier.is_file():
                list_musiques_telechargees.append(utils.remplacer_caract_spec(fichier.stem))
        # Pour chaque titre soundcloud distant.
        for track in tracklist:
            ligne_element = utils.trouver_ligne_url(window_object, json_element[0][8:])
            # Afficher le nombre de fichiers téléchargés et le nombre de fichiers dans la liste soundcloud.
            nb_fichiers = sum(1 for element in library_path.iterdir() if element.is_file())
            utils.definir_status_element(window_object, ligne_element,
                                         f"Synchronisation en cours... ({nb_fichiers}/{len(tracklist)})", "orange")
            if not utils.remplacer_caract_spec(track[1]) in list_musiques_telechargees:  # Si la musique n'est pas deja téléchargée.
                try:
                    # Télécharger le son de la liste tracklist.
                    download_track(window_object, track, str(library_path),
                                  sc_object.auth_token)
                except PermissionError as e:
                    pass

        # Si l'option de suppression des fichiers intrus est activé.
        if not window_object.bloquer_suppression_action.isChecked():
            #if isinstance(content, soundcloud.AlbumPlaylist):  # Si l'élément est un album ou une playlist.
            tracks_title = [utils.remplacer_caract_spec(title[1]) for title in tracklist]  # Liste des noms de musiques distants.
            for file_path in library_path.iterdir():  # Parcourir les fichiers locaux.
                if file_path.is_file():
                    # Si le nom du fichier n'est pas dans la liste des noms de musiques à synchroniser.
                    if utils.remplacer_caract_spec(file_path.stem) not in tracks_title:
                        print(f"Suppression de '{file_path.stem}' qui n'existe pas dans la playliste.")
                        try:
                            file_path.unlink()  # Supprimer le fichier local.
                        except PermissionError:
                            print("Erreur lors de la suppression d'un fichier: Permissions manquantes.")

        # Afficher le nombre de fichiers téléchargés et le nombre de fichiers dans la liste soundcloud.
        nb_fichiers = sum(1 for element in library_path.iterdir() if element.is_file())
        utils.definir_status_element(window_object, ligne_element,
                                     f"{nb_fichiers}/{len(tracklist)} musiques téléchargées", "green")

    except Exception as e:  # Echec de la synchronisation de l'élément.
        utils.definir_status_element(window_object, ligne_element,f"Erreur", "red")
        print(f"Erreur: Synchronisation impossible. {e}")

    # Supprimer le numéro de ligne de l'élément synchronisé de la liste des éléments en cours de syncro.
    window_object.lien_en_synchro.remove(json_element[0])
    if not window_object.lien_en_synchro:
        window_object.label_status_general.setText("")


def download_track(window_object, track, path, auth_token):
    """ Télécharge une musique et ajoute les métadonnées. """

    # yt-dlp paramètres.
    ydl_opts = {
        'outtmpl': f'{path}{os.sep}%(title)s.%(ext)s',
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'username': "oauth",
        'password': auth_token
    }
    if window_object.convert_mp3_action.isChecked():
        ydl_opts["postprocessors"] = [{  # Convertir le fichier en mp3.
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }]

    try:
        # Télécharger la musique avec yt-dlp.
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(track[0], download=True)

        # Ajouter les métadonnées au fichier.
        f = music_tag.load_file(result["requested_downloads"][0]["filepath"])
        f['title'] = result["title"]
        if result["artists"]:
            for artist in result["artists"]:
                f.append_tag('artist', artist)
        else:
            f.append_tag('artist', result["uploader"])
        if result["genres"]:
            for genre in result["genres"]:
                f.append_tag('genre', genre)
        f["artwork"] = requests.get(result["thumbnails"][-1]["url"]).content
        f.save()
    except Exception as e:
        print(f"Erreur lors du téléchargement de {track[1]}: {e}")
