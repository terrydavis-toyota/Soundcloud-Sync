""" Fenetre de configuration des paramètres de Soundcloud Sync. """

import configparser
import os
from pathlib import Path

from PyQt6 import QtWidgets, QtGui, QtCore
import soundcloud

from fonctions import utils


config = configparser.ConfigParser()
config.read(utils.CONFIG_PATH)


class ConfigApp(QtWidgets.QWidget):
    """ Fenetre de configuration des paramètres de Soundcloud Sync. """

    config_closed = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration de Soundcloud Sync")
        self.setWindowIcon(QtGui.QIcon(f"ressources{os.sep}logo.png"))
        self.setGeometry(0, 0, 500, 400)

        self.init_ui()

    def init_ui(self):
        layout_principal = QtWidgets.QVBoxLayout()

        titre_label = QtWidgets.QLabel("Configuration des paramètres")
        titre_label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Weight.DemiBold))
        titre_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titre_label)

        layout_input1_vertical = QtWidgets.QVBoxLayout()
        layout_input1_vertical.setSpacing(1)
        label_layout1 = QtWidgets.QLabel("Token d'authentification Soundcloud")
        layout_input1_vertical.addWidget(label_layout1)

        layout_input1_horizontal = QtWidgets.QHBoxLayout()
        self.input1 = QtWidgets.QLineEdit()
        if config["GLOBAL"]["TOKEN"]:
            self.input1.setText(config["GLOBAL"]["TOKEN"])
        layout_input1_horizontal.addWidget(self.input1)

        layout_input1_vertical.addLayout(layout_input1_horizontal)
        layout_principal.addLayout(layout_input1_vertical)

        layout_principal.addItem(QtWidgets.QSpacerItem(40, 40))

        layout_input2_vertical = QtWidgets.QVBoxLayout()
        label_layout2 = QtWidgets.QLabel("Répertoire local contenant les musiques à synchroniser")
        layout_input2_vertical.addWidget(label_layout2)

        layout_input2_horizontal = QtWidgets.QHBoxLayout()
        self.input2 = QtWidgets.QLineEdit()
        self.input2.setReadOnly(True)
        if config["GLOBAL"]["LOCAL_PATH"]:
            self.input2.setText(config["GLOBAL"]["LOCAL_PATH"])
        bouton2 = QtWidgets.QPushButton("Parcourir")
        bouton2.setFixedSize(QtCore.QSize(100, 30))
        bouton2.clicked.connect(self.parcourir_repertoire)
        layout_input2_horizontal.addWidget(bouton2)
        layout_input2_horizontal.addWidget(self.input2)

        layout_input2_vertical.addLayout(layout_input2_horizontal)
        layout_principal.addLayout(layout_input2_vertical)

        aide_label = QtWidgets.QLabel(
            "<a href='https://github.com/terrydavis-toyota/Soundcloud-Sync/tree/main?tab=readme-ov-file#param%C3%A8tres'>Cliquez ici si vous avez besoin d'aide</a>")
        aide_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        aide_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        aide_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
        aide_label.setOpenExternalLinks(True)
        layout_principal.addWidget(aide_label)

        boutton_valider = QtWidgets.QPushButton("Confirmer")
        boutton_valider.clicked.connect(lambda: valider_config(self, self.input1.text(), self.input2.text()))
        layout_principal.addWidget(boutton_valider)

        self.setLayout(layout_principal)


    def parcourir_repertoire(self):
        """ Ouvre une fenetre système pour sélectionner le répertoire cible. """

        folder_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,"Sélectionner un dossier","",
            QtWidgets.QFileDialog.Option.ShowDirsOnly)
        self.input2.setText(folder_path)


    def closeEvent(self, event):
        self.config_closed.emit()
        super().closeEvent(event)


def valider_config(self, token, path):
    """ Vérifier la validité des informations. """

    if token and path:
        # Vérifier le token soundcloud.
        sc_object = soundcloud.SoundCloud(auth_token=token)
        try:
            assert sc_object.is_auth_token_valid()
            config['GLOBAL']['TOKEN'] = token
            with open(utils.CONFIG_PATH, 'w') as configfile:
                config.write(configfile)
        except AssertionError:
            utils.fenetre_info("Erreur", "Le token est invalide.")
            return

        # Vérifier le répertoire choisi
        json_path = Path(path) / config["GLOBAL"]["SYNCONF_FILE"]
        if not json_path.exists():
            json_data = {
                "musiques": [],
                "albums": [],
                "playlists": [],
                "artistes": [],
                "likes": []
            }
            utils.write_json_file(json_path, json_data)
        config['GLOBAL']['LOCAL_PATH'] = path
        with open(utils.CONFIG_PATH, 'w') as configfile:
            config.write(configfile)
        self.close()
    else:
        utils.fenetre_info("Erreur", "Tout les paramètres ne sont pas définis.")
        return
