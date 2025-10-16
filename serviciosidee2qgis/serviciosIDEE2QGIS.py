# -*- coding: utf-8 -*-
"""
/***************************************************************************
 serviciosIDEE2QGIS
                                 A QGIS plugin
 Permite cargar a QGIS los servicios de la IDEE a partir del Catálogo CSW
                              -------------------
        begin                : 2025-10-15
        git sha              : $Format:%H$
        copyright            : (C) 2025
        author               : ingenieroGeomatico
        email                : aurearagon@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem, QMessageBox

from qgis.core import QgsRasterLayer, QgsProject
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QListWidgetItem, QDialogButtonBox

from PyQt5.QtWidgets import QPushButton

from .resources import *
from .serviciosIDEE2QGIS_dialog import serviciosIDEE2QGISDialog

import os
import requests
import xml.etree.ElementTree as ET

URL_Catalogo = "https://www.idee.es/segun-tipo-de-servicio"
URL_WMS = (
    "https://www.idee.es/web/idee/segun-tipo-de-servicio?"
    "p_p_id=es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f&"
    "p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&"
    "_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_id=supVisWmsEst&"
    "_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_actionName=cargaTablaSrv"
)

# -----------------------------------------------------------------------------
# Clase principal del plugin
# -----------------------------------------------------------------------------

class serviciosIDEE2QGIS:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'serviciosIDEE2QGIS_{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.actions = []
        self.menu = self.tr(u'&serviciosIDEE2QGIS')
        self.first_start = None

    def tr(self, message):
        return QCoreApplication.translate('serviciosIDEE2QGIS', message)

    def add_action(self, icon_path, text, callback, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        self.iface.addToolBarIcon(action)
        self.iface.addPluginToWebMenu(self.menu, action)
        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = ':/plugins/serviciosIDEE2QGIS/icon.png'
        self.add_action(icon_path, text=self.tr(u'Servicios IDEE'), callback=self.run, parent=self.iface.mainWindow())
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginWebMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        if self.first_start:
            self.first_start = False
            self.dlg = serviciosIDEE2QGISDialog()
            self.dlg.lineEditBuscar.textChanged.connect(self.filtrar_tabla_wms)
            self.cargar_desde_url("WMS")  # llenamos la tabla al abrir

        self.dlg.show()
        self.dlg.raise_()
        self.dlg.exec_()

    # -------------------------------------------------------------------------
    # Método para descargar y rellenar la tabla WMS
    # -------------------------------------------------------------------------
    def cargar_desde_url(self, tab):
        try:
            response = requests.get(URL_WMS)
            response.raise_for_status()
            datos_json = response.json()
            datos_json = datos_json["datos"]["est"]

            if tab == "WMS": 
                tabla = self.dlg.tableWidget_WMS  # tu QTableWidget del tab WMS
            else:
                return
            
            tabla.setRowCount(0)

            for org in datos_json:
                nombre_org = org.get("name", "")
                lista_servicios = org.get("listorg", [])
                for srv in lista_servicios:
                    lista_servicios_2 = srv.get("listserv", [])
                    for srv2 in lista_servicios_2:
                        row = tabla.rowCount()
                        tabla.insertRow(row)

                        #propiedades:
                        nombre = srv2.get("name", "")
                        servicioCap = srv2.get("capa", "")
                        servicio = srv2.get("url", "")

                        # Botón 'Añadir a mapa'
                        btn = QPushButton("Añadir a mapa")
                        tabla.setCellWidget(row, 0, btn)

                        # Conectar el botón a la función con los parámetros capturados
                        btn.clicked.connect(lambda checked, s=servicio, t=tab: self.anadir_a_mapa(s, t))


                        # Rellenar columnas restantes
                        tabla.setItem(row, 1, QTableWidgetItem(nombre_org))  # Organismo
                        nombre = srv2.get("name", "")
                        tabla.setItem(row, 2, QTableWidgetItem(nombre))  # Nombre
                        tabla.setItem(row, 3, QTableWidgetItem(servicioCap))  # URL

        except requests.RequestException as e:
            QMessageBox.warning(self.dlg, "Error", f"No se pudo descargar el JSON de IDEE:\n{e}")
        except ValueError as e:
            QMessageBox.warning(self.dlg, "Error", f"Error al parsear JSON:\n{e}")


    def anadir_a_mapa(self,servicio,tab):
        """
        Función que se ejecuta al pulsar 'Añadir a mapa'.
        Aquí puedes implementar la lógica para añadir la capa WMS a QGIS.
        """

        if tab == "WMS":
            capas = self.obtener_capas_wms(servicio)
            
            if not capas:
                QMessageBox.warning(self.dlg, "Error", "No se encontraron subcapas en el WMS")
                return

            # Abrir diálogo de selección
            dialog = SeleccionarCapasDialog(capas, parent=self.dlg)
            if dialog.exec_():
                capas_elegidas = dialog.capas_seleccionadas()
                for capa in capas_elegidas:
                    uri = f"contextualWMSLegend=0&url={servicio}&layers={capa}&styles=&format=image/png&crs=EPSG:3857"
                    nombre_capa = f"{capa}"  # puedes poner nombre del servicio + capa
                    layer = QgsRasterLayer(uri, nombre_capa, "wms")
                    if layer.isValid():
                        QgsProject.instance().addMapLayer(layer)
                    else:
                        print(f"No se pudo cargar la capa: {nombre_capa}")

                else:
                    return
            
    def obtener_capas_wms(self,url):
        try:
            if "request=" not in url.lower():
                if "?" in url:
                    url_cap = url + "&request=GetCapabilities&service=WMS"
                else:
                    url_cap = url + "?request=GetCapabilities&service=WMS"
            else:
                url_cap = url

            r = requests.get(url_cap)
            r.raise_for_status()
            xml_root = ET.fromstring(r.content)

            # Intentar con namespace
            ns = {"wms": "http://www.opengis.net/wms"}
            capas = [layer.find("wms:Name", ns).text
                    for layer in xml_root.findall(".//wms:Layer/wms:Layer", ns)
                    if layer.find("wms:Name", ns) is not None]

            # Fallback sin namespace
            if not capas:
                capas = [layer.find("Name").text
                        for layer in xml_root.findall(".//Layer/Layer")
                        if layer.find("Name") is not None]
            return capas
        except Exception as e:
            print("Error obteniendo capas WMS:", e)
            return []

    def filtrar_tabla_wms(self):
        texto = self.dlg.lineEditBuscar.text().lower()
        tabla = self.dlg.tableWidget_WMS

        for row in range(tabla.rowCount()):
            # Suponiendo que la descripción está en la columna 2 (Nombre)
            item_descripcion = tabla.item(row, 2)
            if item_descripcion:
                if texto in item_descripcion.text().lower():
                    tabla.setRowHidden(row, False)
                else:
                    tabla.setRowHidden(row, True)

class SeleccionarCapasDialog(QDialog):
    def __init__(self, capas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar capas WMS")
        self.setMinimumWidth(400)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Lista de capas
        self.listWidget = QListWidget()
        self.listWidget.setSelectionMode(QListWidget.MultiSelection)
        for capa in capas:
            item = QListWidgetItem(capa)
            self.listWidget.addItem(item)

        self.layout.addWidget(self.listWidget)

        # Botones OK/Cancel
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

    def capas_seleccionadas(self):
        return [item.text() for item in self.listWidget.selectedItems()]