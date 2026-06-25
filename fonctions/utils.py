""" Fonctions diverses utiles pour la GUI de Soundcloud Sync. """

import os
import json
import configparser
from pathlib import Path
import shutil
import requests
import unicodedata

from PyQt6 import QtWidgets, QtGui, QtCore
import soundcloud


CONFIG_PATH = Path(os.getcwd()).resolve() / "config.conf"
VERSION = "1.3"


def fenetre_info(titre, message, window_object=None):
    """ Petite fenetre pour afficher un message. """

    window_message = QtWidgets.QMessageBox(window_object)
    window_message.setText(message)
    window_message.setWindowTitle(titre)
    window_message.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
    window_message.exec() 


def remplacer_caract_spec(chaine):
    """ Nettoie un nom de fichier pour être compatible avec tous les systèmes de fichiers.

        Selon les systèmes d'exploitations, des problèmes de synchronisation peuvent survenir
        à cause des différents codages de caractères.
    """

    dict_caracteres = {"？": "?",
                       ". ": ".",
                       "＊": "*",
                       "＞": ">",
                       "/": "",
                       "⧸": "",
                       "：": ":",
                       "｜": "|",
                       '＂': '"',
                       "ë": 'ë',
                       "＜": "<"}
    chaine = unicodedata.normalize("NFC", chaine)
    for c in dict_caracteres:
        chaine = chaine.replace(c, dict_caracteres[c])

    return chaine


def load_json_file(json_path):
    """" Charger les données de synchronisation depuis le fichier JSON. """

    if Path(json_path).exists():
        try:
            with open(json_path, 'r') as file:
                json_data = json.load(file)
        except FileNotFoundError:
            fenetre_info("Erreur", "Le répertoire de synchronisation est invalide.")
    else:  # Créer le fichier s'il n'existe pas.
        json_data = {
            "musiques": [],
            "albums": [],
            "playlists": [],
            "artistes": [],
            "likes": [],
        }
        with open(json_path, 'w') as file:
            json.dump(json_data, file, indent=4)

    return json_data


def write_json_file(json_path, json_data):
    """ Sauvegarder les données à synchroniser dans le fichier JSON. """

    try:
        with open(json_path, 'w') as file:
            json.dump(json_data, file, indent=4)
    except FileNotFoundError:
        fenetre_info("Erreur", "Le chemin du fichier de synchronisation JSON est invalide.")


def load_local_files(library_path):
    """ Charger dans un dictionnaire l'arborescence du répertoire des musiques téléchargées. """

    nb_total_file = 0
    arborescence = {}
    chemin_bibliotheque = Path(library_path)

    # Parcourir chaque dossier présent dans le répertoire.
    for dossier in chemin_bibliotheque.iterdir():
        if dossier.is_dir():
            if dossier.name == "Musiques":
                arborescence[dossier.name] = []
                for musique in dossier.iterdir():
                    arborescence[dossier.name].append(f"/Musiques/{remplacer_caract_spec(musique.stem)}")
                    nb_total_file += 1
            else:
                arborescence[dossier.name] = {}
                for e in dossier.iterdir():
                    if e.is_dir():
                        arborescence[dossier.name][remplacer_caract_spec(e.name)] = []
                        for fichier in Path(dossier / e).iterdir():
                            path_fichier = f"/{dossier.name}/{remplacer_caract_spec(e.name)}/{remplacer_caract_spec(fichier.stem)}"
                            arborescence[dossier.name][remplacer_caract_spec(e.name)].append(path_fichier)
                            nb_total_file += 1

    return arborescence, nb_total_file


def verification_parametres():
    """ Vérifie la validité des paramètres. """

    json_path, sc_object = True, True
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    # Vérifier le fichier de configuration.
    if not "GLOBAL" in config:
        fenetre_info("Erreur", "Le fichier de configuration est introuvable:\n"
                                     f"{CONFIG_PATH}")
    if not config["GLOBAL"]["LOCAL_PATH"] or not Path(config["GLOBAL"]["LOCAL_PATH"]).exists():
        json_path = False
    if config["GLOBAL"]["TOKEN"]:
        sc_object = soundcloud.SoundCloud(auth_token=config["GLOBAL"]["TOKEN"])
        try:
            assert sc_object.is_auth_token_valid()
        except AssertionError:
            sc_object = False
    else:
        sc_object = False

    return json_path, sc_object


def recuperer_parametres():
    """ Charger les paramètres. """

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    json_path = config["GLOBAL"]["LOCAL_PATH"] + os.sep + config["GLOBAL"]["SYNCONF_FILE"]
    json_data = load_json_file(json_path)
    sc_object = soundcloud.SoundCloud(auth_token=config["GLOBAL"]["TOKEN"])

    return config, json_path, json_data, sc_object


def trouver_ligne_url(object_window, url):
    """ Obtenir le numéro de ligne de la table des éléments à synchroniser avec l'URL. """

    for row in range(object_window.table_elements.rowCount()):
        item = object_window.table_elements.item(row, 1)
        if item.text() == url:
            return row
    return None


def definir_status_element(object_window, ligne, texte, couleur):
    """ Définir le status d'un élément dans le tableau affiché. """

    status = QtWidgets.QTableWidgetItem(texte)
    status.setForeground(QtGui.QColor(couleur))
    object_window.table_elements.setItem(ligne, 2, status)


def _get_total_tracks(sc_object, element, type_element):
    """Retourne le nombre total de titres pour un élément donné (album, playlist, artiste, likes)."""

    resolve = sc_object.resolve(element[0])
    if type_element in ("albums", "playlists"):
        return len(resolve.tracks)
    elif type_element == "artistes":
        return resolve.track_count
    elif type_element == "likes":
        return sum(
            1 for like in sc_object.get_user_likes(resolve.id)
            if isinstance(like, soundcloud.TrackLike)
        )


def actualiser_interface(object_window):
    """ Actualise les éléments affichés dans le tableau.
        - Met à jour les labels (nombre de fichiers, compte utilisateur).
        - Recharge et affiche les données depuis le JSON, les fichiers locaux et les liens distants.
    """

    # Récupération des données.
    try:
        config, json_path, json_data, sc_object = recuperer_parametres()
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(f"Connexion impossible: {e}")
    arborescence, nb_total_file = load_local_files(config["GLOBAL"]["LOCAL_PATH"])
    # Mise à jour des labels de la barre de status.
    object_window.label_nb_fichiers.setText(f"Nombre de fichiers téléchargés: {nb_total_file}")
    object_window.label_compte.setText(f"Connecté avec le compte de {sc_object.get_me().username}")

    object_window.table_elements.setRowCount(0)  # Supprimer toutes les lignes affichées.
    # Ajout des elements dans le tableau affiché.
    categories = ["musiques", "albums", "playlists", "artistes", "likes"]
    for categorie in categories:
        for element in json_data[categorie]:
            ajouter_ligne_interface(object_window, element, categorie, arborescence, sc_object)


def ajouter_ligne_interface(object_window, element, type_element, arborescence, sc_object):
    """ Ajouter une ligne au tableau avec: Le nom, le lien et le status de synchronisation de l'élément. """

    # Configuration selon le type.
    if type_element == "musiques":
        arborescence_key = "Musiques"
    else:
        arborescence_key = type_element.capitalize()

    # Insertion de la ligne dans le tableau.
    row_position = object_window.table_elements.rowCount()
    object_window.table_elements.insertRow(row_position)
    object_window.table_elements.setItem(row_position, 1, QtWidgets.QTableWidgetItem(element[0][8:]))
    object_window.table_elements.setItem(row_position, 0, QtWidgets.QTableWidgetItem(element[1]))

    # Statut de synchronisation.
    if element[0] in object_window.lien_en_synchro:
        definir_status_element(object_window, row_position, "synchronisation en cours...", "orange")
        return
    # Pour les musiques seules, pas besoin de resolve.
    if type_element == "musiques":
        is_downloaded = element[1] in arborescence[arborescence_key]
        status = "Musique téléchargée" if is_downloaded else "Musique non téléchargée"
        color = "green" if is_downloaded else "red"
        definir_status_element(object_window, row_position, status, color)
        return
    # Pour les autres types de contenu:
    try:  # Essayer d'obtenir le nombre de titres dans le contenu.
        total_tracks = _get_total_tracks(sc_object, element, type_element)
    except AttributeError:
        definir_status_element(object_window, row_position, "Lien invalide", "red")
        return
    if str(Path(element[1]).name) not in arborescence[arborescence_key]:  # Aucun titre n'est téléchargé.
        definir_status_element(object_window, row_position, f"0/{total_tracks} musiques téléchargées", "red")
    else:  # Une partie est téléchargée.
        downloaded = len(arborescence[arborescence_key][str(Path(element[1]).name)])
        status = f"{downloaded}/{total_tracks} musiques téléchargées"
        color = "green" if downloaded == total_tracks else "orange"
        definir_status_element(object_window, row_position, status, color)


class ActualiserAffichage(QtCore.QThread):
    """ Classe pour lancer la fonction actualiser_interface dans un Thread avec QThread. """

    sync_finished = QtCore.pyqtSignal(object)

    def __init__(self, window_object, parent=None):
        super().__init__(parent)
        self.window_object = window_object

    def run(self):
        actualiser_interface(self.window_object)
        self.sync_finished.emit(None)


def supprimer_element(object_window, index, json_path):
    """ Supprimer un élément. """

    url = object_window.table_elements.item(index, 1).text()
    object_window.table_elements.removeRow(index)
    json_content = load_json_file(json_path)

    for cat in json_content:
        cat_id = 0
        for element in json_content[cat]:
            if element[0].endswith(url):
                # Si l'option de supression des fichiers locaux est activée.
                if object_window.remove_local_action.isChecked():
                    # Suppréssion du fichier ou du dossier local.
                    config = configparser.ConfigParser()
                    config.read(CONFIG_PATH)
                    path_to_remove = Path(config["GLOBAL"]["LOCAL_PATH"]) / Path(
                        json_content[cat][cat_id][1][1:])
                    if path_to_remove.is_dir():
                        shutil.rmtree(path_to_remove)
                    else:
                        for fichier in path_to_remove.parent.iterdir():
                            if fichier.is_file() and fichier.stem == path_to_remove.name:
                                fichier.unlink()
                                break

                del json_content[cat][cat_id]  # Suppression de l'élément dans le fichier JSON.
                break
            cat_id += 1

    write_json_file(json_path, json_content)


def supprimer_tout_elements(object_window, json_path):
    """ Vider la liste des éléments à synchroniser après confirmation. """

    # Créer une boite de dialogue pour demander confirmation avant de supprimer tout les éléments.
    boite_dialogue = QtWidgets.QMessageBox()
    boite_dialogue.setWindowTitle("Confirmation")
    boite_dialogue.setText("Êtes-vous sûr de vouloir supprimer tous les éléments à synchroniser ?")
    bouton_oui = boite_dialogue.addButton("Oui", QtWidgets.QMessageBox.ButtonRole.AcceptRole)
    boite_dialogue.addButton("Non", QtWidgets.QMessageBox.ButtonRole.RejectRole)
    boite_dialogue.exec()
    if boite_dialogue.clickedButton() == bouton_oui:
        Path(json_path).unlink()  # Suppréssion du fichier JSON.
        object_window.table_elements.setRowCount(0)  # Vider la table des éléments affichée.
    else:
        pass


def modifier_parametre_config(cle, valeur):
    """ Modifie une valeur booléenne dans le fichier de configuration. """

    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    config["GLOBAL"][cle] = str(valeur)
    with open(CONFIG_PATH, 'w') as configfile:
        config.write(configfile)
