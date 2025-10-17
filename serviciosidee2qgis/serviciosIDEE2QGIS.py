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
from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis.PyQt.QtWidgets import QProgressDialog

from qgis.core import QgsRasterLayer, QgsProject


from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QHeaderView, QAbstractItemView, QPushButton,
)
from .resources import *
from .serviciosIDEE2QGIS_dialog import serviciosIDEE2QGISDialog

import os
import time
import requests
import xml.etree.ElementTree as ET


URL_Catalogo = "https://www.idee.es/segun-tipo-de-servicio"
URL_WMS_est = (
    "https://www.idee.es/web/idee/segun-tipo-de-servicio?"
    "p_p_id=es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f&"
    "p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&"
    "_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_id=supVisWmsEst&"
    "_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_actionName=cargaTablaSrv"
)
URL_WMS_aut = (
    "https://www.idee.es/web/idee/segun-tipo-de-servicio?p_p_id=es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_id=supVisWmsAut&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_actionName=cargaTablaSrv"
)
URL_WMS_loc = (
    "https://www.idee.es/web/idee/segun-tipo-de-servicio?p_p_id=es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_id=supVisWmsLoc&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_actionName=cargaTablaSrv"
)
URL_WMS_pve= (
    "https://www.idee.es/web/idee/segun-tipo-de-servicio?p_p_id=es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_id=supVisWmsPV&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_actionName=cargaTablaSrv"    
)
URL_WMTS = (
    "https://www.idee.es/web/idee/segun-tipo-de-servicio?p_p_id=es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_id=sup-vis-wmts&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_actionName=cargaTablaSrv"
)
URL_XYZ= (
    "https://www.idee.es/web/idee/segun-tipo-de-servicio?p_p_id=es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_id=sup-vis-rts&_es_igncnig_dirserv72_DirectorioServiciosPortlet_INSTANCE_YZFuNrhnVi4f_actionName=cargaTablaSrv"
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
            # 💡 Aquí conectamos los filtros
            self.dlg.lineEditBuscar_WMS.textChanged.connect(self.filtrar_tabla_wms)
            self.dlg.lineEditBuscar_WMTS.textChanged.connect(self.filtrar_tabla_wmts)
            self.dlg.lineEditBuscar_XYZ.textChanged.connect(self.filtrar_tabla_xyz)
            self.dlg.show()  # Abrir el diálogo inmediatamente

            # Crear ProgressDialog
            self.progress = QProgressDialog("Cargando servicios IDEE...", "Cancelar", 0, 0, self.dlg)
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.show()

            # Lanzar threads para obtener listado de servicios
            self.worker_wms = CargarServiciosWorker("WMS", [URL_WMS_est, URL_WMS_aut, URL_WMS_loc, URL_WMS_pve])
            self.worker_wms.resultado.connect(self.rellenar_tabla)
            self.worker_wms.start()

            self.worker_wmts = CargarServiciosWorker("WMTS", [URL_WMTS])
            self.worker_wmts.resultado.connect(self.rellenar_tabla)
            self.worker_wmts.start()

            self.worker_xyz = CargarServiciosWorker("TMSXYZ", [URL_XYZ])
            self.worker_xyz.resultado.connect(self.rellenar_tabla)
            self.worker_xyz.start()


        else:
            self.dlg.show()

    
    def rellenar_tabla(self, tab, datos_json):

        if tab == "WMS":
            tabla = self.dlg.tableWidget_WMS

        elif tab == "WMTS":
            tabla = self.dlg.tableWidget_WMTS

        elif tab == "TMSXYZ":
            tabla = self.dlg.tableWidget_XYZ

        else:
            return

        tabla.setRowCount(0)

        for nodo in datos_json:
            for org in nodo:
                nombre_org = org.get("name", "")
                lista_servicios = org.get("listorg", org.get("listserv", []))

                for srv in lista_servicios:
                    lista_servicios_2 = srv.get("listserv", [])
                    lista_Servicios_2_nodos = srv.get("listsuborg", [])
                    capa_2 = srv.get("capa", [])

                    def rellenarFila(item, nomOrg):
                        row = tabla.rowCount()
                        tabla.insertRow(row)
                        nombre = item.get("name", "")
                        servicioCap = item.get("capa", "")
                        servicio = item.get("url", "")
                        btn = QPushButton("Añadir a mapa")
                        obj={
                            "nombre": nombre,
                            "capa": servicioCap,
                            "url": servicio
                        }
                        tabla.setCellWidget(row, 0, btn)
                        btn.clicked.connect(lambda checked, s=servicio, t=tab: self.anadir_a_mapa(s, t, obj))
                        tabla.setItem(row, 1, QTableWidgetItem(nomOrg))
                        tabla.setItem(row, 2, QTableWidgetItem(nombre))
                        tabla.setItem(row, 3, QTableWidgetItem(servicioCap))

                    if capa_2:
                        rellenarFila(srv, nombre_org)
                    elif lista_servicios_2:
                        if srv.get("name"):
                            nombre_org = srv.get("name", "")
                        for srv2 in lista_servicios_2:
                            rellenarFila(srv2, nombre_org)
                    elif lista_Servicios_2_nodos:
                        for srv2 in lista_Servicios_2_nodos:
                            lista_servicios_3 = srv2.get("listserv", [])
                            if srv2.get("name"):
                                nombre_org = srv2.get("name", "")
                            for srv3 in lista_servicios_3:
                                rellenarFila(srv3, nombre_org)

        # Cerrar el progress si ambos workers han terminado
        if ((not self.worker_xyz.isRunning()) and 
            (not self.worker_wms.isRunning()) and 
            (not self.worker_wmts.isRunning())):
            self.progress.close()


    # -------------------------------------------------------------------------
    # Método para descargar y rellenar la tabla
    # -------------------------------------------------------------------------

    def anadir_a_mapa(self, servicio, tab, obj):
        """
        Función que se ejecuta al pulsar 'Añadir a mapa'.
        Aquí se abre el diálogo de selección de capas WMS y se cargan al mapa.
        """

        if tab == "WMS":
            progress = QProgressDialog("Buscando capas en el WMS...", "Cancelar", 0, 0, self.dlg)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            self.worker = CargarCapasWMSWorker(servicio)
            self.worker.terminado.connect(lambda capas: self._on_capas_cargadas_WMS(capas,servicio, progress))
            self.worker.error.connect(lambda e: (progress.close(), QMessageBox.warning(self.dlg, "Error", e)))            
            self.worker.start()

        elif tab == "WMTS":
            progress = QProgressDialog("Buscando capas en el WMTS...", "Cancelar", 0, 0, self.dlg)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

            self.worker = CargarCapasWMTSWorker(servicio)
            self.worker.terminado.connect(lambda capas: self._on_capas_cargadas_WMTS(capas,servicio, progress))
            self.worker.error.connect(lambda e: (progress.close(), QMessageBox.warning(self.dlg, "Error", e)))            
            self.worker.start()
        
        elif tab == "TMSXYZ":
            self._on_capas_cargadas_XYZ(obj, servicio)


        else:
            return

    def _on_capas_cargadas_WMS(self, capas, servicio, progress):
        """Se llama cuando el worker ha terminado de obtener las capas WMS"""
        progress.close()  # cerrar el diálogo de espera

        if not capas:
            QMessageBox.warning(self.dlg, "Error", "No se encontraron subcapas en el WMS")
            return

        # Abrir diálogo de selección
        dialog = SeleccionarCapasDialog_WMS(capas, parent=self.dlg)
        if dialog.exec_():
            capas_elegidas = dialog.capas_seleccionadas()
            for capa in capas_elegidas:
                print(capa)
                uri = (
                    f"contextualWMSLegend=0&url={servicio}"
                    f"&layers={capa['name']}&styles=&format={capa['format']}&crs=EPSG:3857"
                )
                nombre_capa = capa['name']
                layer = QgsRasterLayer(uri, nombre_capa, "wms")
                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                else:
                    print(f"No se pudo cargar la capa: {nombre_capa}")

    def filtrar_tabla_wms(self):
        """Filtra la tabla de WMS por texto en las columnas Organismo y Nombre."""
        texto = self.dlg.lineEditBuscar_WMS.text().lower()
        tabla = self.dlg.tableWidget_WMS

        for row in range(tabla.rowCount()):
            item_org = tabla.item(row, 1)   # columna Organismo
            item_nombre = tabla.item(row, 2)  # columna Nombre / Descripción

            texto_org = item_org.text().lower() if item_org else ""
            texto_nombre = item_nombre.text().lower() if item_nombre else ""

            # Mostrar fila si el texto aparece en alguna de las dos columnas
            visible = (texto in texto_org) or (texto in texto_nombre)
            tabla.setRowHidden(row, not visible)
    
    def _on_capas_cargadas_WMTS(self, capas, servicio, progress):
        """Se llama cuando el worker ha terminado de obtener las capas WMTS"""
        progress.close()  # cerrar el diálogo de espera

        if not capas:
            QMessageBox.warning(self.dlg, "Error", "No se encontraron capas en el WMTS")
            return

        # Abrir diálogo de selección
        dialog = SeleccionarCapasDialog_WMTS(capas, parent=self.dlg)
        if dialog.exec_():
            capas_elegidas = dialog.capas_seleccionadas()
            for capa in capas_elegidas:
                url_base = servicio.split("?")[0]  # quitar parámetros GetCapabilities

                uri = (
                    f"crs=EPSG:3857"
                    f"&dpiMode=7"
                    f"&format={capa['format']}"
                    f"&layers={capa['identifier']}"
                    f"&styles=default"
                    f"&tileMatrixSet=GoogleMapsCompatible"
                    f"&tilePixelRatio=0"
                    f"&url={url_base}"
                )

                layer = QgsRasterLayer(uri, f"{capa['identifier']} ({capa['format']})", "wms")

                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                else:
                    print(f"No se pudo cargar la capa: {capa}")

    def filtrar_tabla_wmts(self):
        """Filtra la tabla de WMTS por texto en las columnas Organismo y Nombre."""
        texto = self.dlg.lineEditBuscar_WMTS.text().lower()
        tabla = self.dlg.tableWidget_WMTS

        for row in range(tabla.rowCount()):
            item_org = tabla.item(row, 1)   # columna Organismo
            item_nombre = tabla.item(row, 2)  # columna Nombre / Descripción

            texto_org = item_org.text().lower() if item_org else ""
            texto_nombre = item_nombre.text().lower() if item_nombre else ""

            visible = (texto in texto_org) or (texto in texto_nombre)
            tabla.setRowHidden(row, not visible)


    def _on_capas_cargadas_XYZ(self, obj, servicio):
        """
        Se llama cuando el worker ha terminado de obtener las capas XYZ.
        Carga la capa XYZ en QGIS.
        """

        if not obj:
            QMessageBox.warning(self.dlg, "Error", "No se encontraron capas en el servicio XYZ")
            return

        # Asegurarnos de tener la URL base sin parámetros
        url_base = servicio.split("?")[0]

        # La plantilla de URL XYZ debe tener {z}, {x}, {y} o {-y}
        # Si el servicio no la tiene, la añadimos
        if "{z}" not in url_base:
            if not url_base.endswith("/"):
                url_base += "/"
            url_base += "{z}/{x}/{y}.png"

        # Construcción del URI para QGIS
        uri = (
            f"http-header:referer="
            f"&type=xyz"
            f"&url={url_base}"
            f"&zmax=19"
            f"&zmin=0"
        )

        layer_name = obj.get("nombre") or "Capa XYZ"

        layer = QgsRasterLayer(uri, layer_name, "wms")

        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
        else:
            QMessageBox.warning(self.dlg, "Error", f"No se pudo cargar la capa XYZ:\n{layer_name}")
            print(f"No se pudo cargar la capa: {obj}")


    def filtrar_tabla_xyz(self):
        """Filtra la tabla de TMS por texto en las columnas Organismo y Nombre."""
        texto = self.dlg.lineEditBuscar_XYZ.text().lower()
        tabla = self.dlg.tableWidget_XYZ

        for row in range(tabla.rowCount()):
            item_org = tabla.item(row, 1)   # columna Organismo
            item_nombre = tabla.item(row, 2)  # columna Nombre / Descripción

            texto_org = item_org.text().lower() if item_org else ""
            texto_nombre = item_nombre.text().lower() if item_nombre else ""

            visible = (texto in texto_org) or (texto in texto_nombre)
            tabla.setRowHidden(row, not visible)



class SeleccionarCapasDialog_WMS(QDialog):
    def __init__(self, capas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar capas WMS")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tabla de capas
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Identificador", "Título", "formato", "Descripción"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 250)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 300)

        # Llenar tabla
        self.table.setRowCount(len(capas))
        for row, capa in enumerate(capas):
            nombre = capa.get("name", "")
            titulo = capa.get("title", "")
            formato = capa.get("format", "")
            descripcion = capa.get("abstract", "")
            self.table.setItem(row, 0, QTableWidgetItem(nombre))
            self.table.setItem(row, 1, QTableWidgetItem(titulo))
            self.table.setItem(row, 2, QTableWidgetItem(formato))
            self.table.setItem(row, 3, QTableWidgetItem(descripcion))

        layout.addWidget(self.table)

        # Botones OK / Cancelar
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def capas_seleccionadas(self):
        """Devuelve lista con los 'name' de las capas seleccionadas"""
        capas = []
        for item in self.table.selectionModel().selectedRows():
            row = item.row()
            nombre = self.table.item(row, 0).text()
            formato = self.table.item(row, 2).text()
            obj = {
                "name": nombre,
                "format": formato
            }
            capas.append(obj)
        return capas

class SeleccionarCapasDialog_WMTS(QDialog):
    def __init__(self, capas, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar capas WMTS")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tabla de capas
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Identificador", "Título", "formato", "Descripción"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 250)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 300)

        # Llenar tabla
        self.table.setRowCount(len(capas))
        for row, capa in enumerate(capas):
            identifier = capa.get("identifier", "")
            titulo = capa.get("title", "")
            format = capa.get("format", "")
            descripcion = capa.get("abstract", "")
            self.table.setItem(row, 0, QTableWidgetItem(identifier))
            self.table.setItem(row, 1, QTableWidgetItem(titulo))
            self.table.setItem(row, 2, QTableWidgetItem(format))
            self.table.setItem(row, 3, QTableWidgetItem(descripcion))

        layout.addWidget(self.table)

        # Botones OK / Cancelar
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def capas_seleccionadas(self):
        """Devuelve lista con los 'identifier' de las capas seleccionadas"""
        capas = []
        for item in self.table.selectionModel().selectedRows():
            row = item.row()
            identifier = self.table.item(row, 0).text()
            format = self.table.item(row, 2).text()
            obj={
                "identifier": identifier,
                "format":format
            }
            capas.append(obj)
        return capas


class CargarServiciosWorker(QThread):
    resultado = pyqtSignal(str, object)  # tab, datos_json

    def __init__(self, tab, urls):
        super().__init__()
        self.tab = tab
        self.urls = urls  # lista de URLs a descargar

    def run(self):
        datos_completos = []
        for url in self.urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                datos_json_r = response.json()
                if self.tab == "WMS":
                    datos_tab = [
                        datos_json_r["datos"].get("est", []),
                        datos_json_r["datos"].get("aut", []),
                        datos_json_r["datos"].get("loc", []),
                        datos_json_r["datos"].get("pve", []),
                    ]
                elif self.tab == "WMTS":
                    datos_tab = [
                        datos_json_r["datos"].get("est", []),
                        datos_json_r["datos"].get("aut", []),
                        datos_json_r["datos"].get("loc", []),
                        datos_json_r["datos"].get("pve", []),
                    ]
                elif self.tab == "TMSXYZ":
                    datos_tab = [
                        datos_json_r["datos"].get("est", []),
                        datos_json_r["datos"].get("aut", []),
                        datos_json_r["datos"].get("loc", []),
                        datos_json_r["datos"].get("pve", []),
                    ]
                else:
                    pass

                datos_completos.extend(datos_tab)

            except Exception as e:
                print(f"Error descargando {url}: {e}")

        self.resultado.emit(self.tab, datos_completos)

class CargarCapasWMSWorker(QThread):
    terminado = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, servicio):
        super().__init__()
        self.servicio = servicio

    def run(self):
        try:
            capas = self.obtener_capas_wms(self.servicio)
            self.terminado.emit(capas)
        except Exception as e:
            self.error.emit(str(e))
    
    def obtener_capas_wms(self, servicio):
        """
        Obtiene las capas disponibles en un servicio WMS mediante su GetCapabilities.
        Devuelve una lista de diccionarios:
        [{'name':..., 'title':..., 'abstract':..., 'format':...}, ...]
        Cada capa se repite si tiene varios formatos de salida.
        """
        url = servicio
        if not url.lower().startswith("http"):
            return []

        params = {"SERVICE": "WMS", "REQUEST": "GetCapabilities"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        ns = {
            "wms": "http://www.opengis.net/wms"
        }

        # Obtener los formatos disponibles a nivel global (GetMap)
        global_formats = root.findall(".//wms:Capability/wms:Request/wms:GetMap/wms:Format", ns)
        formatos_globales = [f.text for f in global_formats if f.text] or ["image/png"]

        capas = []
        for layer in root.findall(".//wms:Layer", ns):
            name_el = layer.find("wms:Name", ns)
            title_el = layer.find("wms:Title", ns)
            abstract_el = layer.find("wms:Abstract", ns)

            if name_el is not None:
                # Buscar formatos específicos de la capa (si existen)
                layer_formats = layer.findall("wms:Format", ns)
                formatos = [f.text for f in layer_formats if f.text] or formatos_globales

                # Crear un registro por cada formato
                for fmt in formatos:
                    capas.append({
                        "name": name_el.text or "",
                        "title": title_el.text if title_el is not None else "",
                        "abstract": abstract_el.text if abstract_el is not None else "",
                        "format": fmt
                    })

        return capas

class CargarCapasWMTSWorker(QThread):
    terminado = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, servicio):
        super().__init__()
        self.servicio = servicio

    def run(self):
        try:
            capas = self.obtener_capas_wmts(self.servicio)
            self.terminado.emit(capas)
        except Exception as e:
            self.error.emit(str(e))
    
    def obtener_capas_wmts(self, servicio):
        """
        Obtiene las capas disponibles en un servicio WMTS mediante su GetCapabilities.
        Devuelve una lista de diccionarios: [{'identifier':..., 'title':..., 'abstract':..., 'format':...}, ...]
        Cada capa se repite si tiene varios formatos de salida.
        """
        url = servicio
        if not url.lower().startswith("http"):
            return []

        params = {"SERVICE": "WMTS", "REQUEST": "GetCapabilities"}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            QMessageBox.warning(self.dlg, "Error", f"No se pudo acceder al WMTS:\n{e}")
            return []

        root = ET.fromstring(response.content)
        ns = {
            "wmts": "http://www.opengis.net/wmts/1.0",
            "ows": "http://www.opengis.net/ows/1.1",
        }

        capas = []
        for layer in root.findall(".//wmts:Layer", ns):
            identifier_el = layer.find("ows:Identifier", ns)
            title_el = layer.find("ows:Title", ns)
            abstract_el = layer.find("ows:Abstract", ns)

            if identifier_el is not None:
                # Buscar formatos disponibles
                formats = layer.findall("wmts:Format", ns)
                if not formats:
                    # Si no hay formatos, añadir un registro vacío
                    capas.append({
                        "identifier": identifier_el.text or "",
                        "title": title_el.text if title_el is not None else "",
                        "abstract": abstract_el.text if abstract_el is not None else "",
                        "format": ""
                    })
                else:
                    for fmt in formats:
                        capas.append({
                            "identifier": identifier_el.text or "",
                            "title": title_el.text if title_el is not None else "",
                            "abstract": abstract_el.text if abstract_el is not None else "",
                            "format": fmt.text or ""
                        })
        return capas


