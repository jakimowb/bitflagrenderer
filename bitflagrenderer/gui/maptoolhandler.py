from bitflagrenderer.core.utils import BITFLAG_DATA_TYPES
from qgis.PyQt.QtCore import pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsRasterLayer, QgsRasterDataProvider, QgsCoordinateReferenceSystem, QgsPointXY
from qgis.gui import QgsAbstractMapToolHandler, QgsMapTool, QgsMapToolEmitPoint, QgsMapCanvas, \
    QgsVertexMarker, QgsMapMouseEvent


class BitFlagMapTool(QgsMapToolEmitPoint):
    """
    A QgsMapTool to collect SpatialPoints
    """
    bitFlagRequest = pyqtSignal(QgsCoordinateReferenceSystem, QgsPointXY)

    def __init__(self, canvas: QgsMapCanvas):
        """
        :param canvas: QgsMapCanvas
        :param showCrosshair: bool, if True (default), a crosshair appears for some milliseconds to highlight
            the selected location
        """
        QgsMapToolEmitPoint.__init__(self, canvas)
        self.marker = QgsVertexMarker(self.canvas())

        color = QColor('red')
        self.mButtons = [Qt.LeftButton]
        self.marker.setColor(color)
        self.marker.setPenWidth(3)
        self.marker.setIconSize(5)
        self.marker.setIconType(QgsVertexMarker.ICON_CROSS)  # or ICON_CROSS, ICON_X

    def flags(self) -> QgsMapTool.Flags:
        return QgsMapTool.ShowContextMenu

    def canvasPressEvent(self, e):
        assert isinstance(e, QgsMapMouseEvent)
        if e.button() in self.mButtons:
            coordinate = self.toMapCoordinates(e.pos())
            self.marker.setCenter(coordinate)

    def canvasReleaseEvent(self, e):

        if e.button() in self.mButtons:
            pixelPoint = e.pixelPoint()
            crs = self.canvas().mapSettings().destinationCrs()
            self.marker.hide()
            coordinates: QgsPointXY = self.toMapCoordinates(pixelPoint)
            self.bitFlagRequest[QgsCoordinateReferenceSystem, QgsPointXY].emit(crs, coordinates)

    def hideRubberband(self):
        """
        Hides the rubberband
        """
        self.rubberband.reset()


class BitFlagMapToolHandler(QgsAbstractMapToolHandler):
    def __init__(self, tool, action: QAction):
        super().__init__(tool, action)

    def isCompatibleWithLayer(self, layer, context: QgsAbstractMapToolHandler.Context):
        # this tool can only be activated when an editable vector layer is selected
        if isinstance(layer, QgsRasterLayer) and layer.isValid():
            dp: QgsRasterDataProvider = layer.dataProvider()
            return dp.dataType(1) in BITFLAG_DATA_TYPES.keys()
        else:
            return False
