import sys
import traceback
import logging
import weakref
from collections import namedtuple

try:
    from PySide import QtGui, QtCore
    from PySide.QtGui import *
    from PySide.QtCore import *
    import shiboken
except:
    from PySide2 import QtGui, QtCore, QtWidgets
    from PySide2.QtGui import *
    from PySide2.QtCore import *
    from PySide2.QtWidgets import *
    import shiboken2 as shiboken

app = QtWidgets.QApplication.instance()
STANDALONE = False
if not app:
    STANDALONE = True
    app = QtWidgets.QApplication(sys.argv)

MAYA_AVAILABLE = False
try:
    import pymel.core as pm
    import maya.cmds as cmds
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaUI as mui
    MAYA_AVAILABLE = True
except Exception as e:
    traceback.print_exc()

MAYA_HEADLESS = False
if 'mayapy.exe' in sys.executable:
    MAYA_HEADLESS = True


class DependListModel(QtCore.QAbstractListModel):
    MAYA_NODE = QtCore.Qt.UserRole + 1

    def __init__(self, node_list, parent=None):
        super(DependListModel, self).__init__(parent)
        self.__node_list = node_list

    def invisibleRootItem(self):
        return self.__node_list

    def rowCount(self, parent):
        return len(self.__node_list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    def itemFromIndex(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node is not None:
                return node
        return self.invisibleRootItem()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        node = self.__node_list[index.row()]
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return str(node.nodeName())
            elif index.column() == 1:
                return node.startFrame.get()
            elif index.column() == 2:
                return node.startFrame.get()
            elif index.column() == 3:
                if role == QtCore.Qt.DisplayRole:
                    return str(node.currentCamera.get())
                if role == QtCore.Qt.EditRole:
                    return sorted(cmds.ls(type='camera')).index(str(node.currentCamera.get().nodeName()))
        if role == QtCore.Qt.ToolTipRole:
            return str(repr(node))
        if role == DependListModel.MAYA_NODE:
            return node

    def flags(self, index):
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        status = False
        node = self.__node_list[index.row()]
        if role == QtCore.Qt.EditRole:
            try:
                if index.column() == 0:
                    node.rename(value)
                elif index.column() == 1:
                    node.startFrame.set(value)
                elif index.column() == 2:
                    node.endFrame.set(value)
                elif index.column() == 3:
                    cameras = sorted(cmds.ls(type='camera'))
                    print value, cameras[value]
                    camera = pm.PyNode(cameras[value])
                    node.currentCamera.connect(camera)
                status = True
            except Exception as e:
                print e.message
                status = False
        return status

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        success = False
        end = position + rows - 1
        self.beginRemoveRows(parent, position, end)
        for row in range(rows):
            node = self.__node_list.pop(position + row)
            pm.delete(node)
            success = True
        self.endRemoveRows()
        return success


class ComboBoxDelegate(QtWidgets.QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent, itemlist=None):
        super(ComboBoxDelegate, self).__init__(parent)
        self.item_list = itemlist or []

    def currentIndexChanged(self):
        self.commitData.emit(self.sender())

    def createEditor(self, parent, option, index):
        combo = QtWidgets.QComboBox(parent)
        self.item_list = index.model().data(index, QtCore.Qt.EditRole)
        current = index.model().data(index, QtCore.Qt.DisplayRole)
        combo.addItems(self.item_list)
        item = combo.model().findItems(current, QtCore.Qt.MatchExactly, 0)
        if len(item):
            combo.setCurrentIndex(item[0].index().row())
        combo.currentIndexChanged.connect(self.currentIndexChanged)
        return combo

    def setModelData(self, combo, model, index):
        combo_index = combo.currentIndex()
        text = self.item_list[combo_index]
        model.setData(index, text)


class DependTableModel(QtCore.QAbstractTableModel):
    MAYA_NODE = QtCore.Qt.UserRole + 1

    def __init__(self, node_list, parent=None):
        super(DependTableModel, self).__init__(parent)
        self.__node_list = node_list

    def invisibleRootItem(self):
        return self.__node_list

    def rowCount(self, parent):
        return len(self.__node_list)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        node = self.__node_list[index.row()]
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return str(node.nodeName())
            elif index.column() == 1:
                return node.startFrame.get()
            elif index.column() == 2:
                return node.startFrame.get()
            elif index.column() == 3:
                if role == QtCore.Qt.EditRole:
                    return cmds.ls(type='camera')
                else:
                    if cmds.objExists('%s.currentCamera' % node.nodeName()):
                         connection = cmds.connectionInfo('%s.currentCamera' % node.nodeName(), sourceFromDestination=True)
                         if connection:
                             return connection.split('.')[:-1][0]
        if role == QtCore.Qt.ToolTipRole:
            return str(repr(node))
        if role == DependTableModel.MAYA_NODE:
            return node

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        status = False
        node = self.__node_list[index.row()]
        if role == QtCore.Qt.EditRole:
            try:
                if index.column() == 0:
                    node.rename(value)
                elif index.column() == 1:
                    node.startFrame.set(value)
                elif index.column() == 2:
                    node.endFrame.set(value)
                elif index.column() == 3:
                    cmds.shot(node.nodeName(), e=True, cc=value)
                status = True
            except Exception as e:
                print e.message
                status = False
        return status

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        success = False
        end = position + rows - 1
        self.beginRemoveRows(parent, position, end)
        for row in range(rows):
            node = self.__node_list.pop(position + row)
            pm.delete(node)
            success = True
        self.endRemoveRows()
        return success

    def flags(self, index):
        if not index.isValid():
            return 0
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable


class AttributeEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AttributeEditor, self).__init__(parent)
        form_layout = QtWidgets.QFormLayout(self)
        self.setLayout(form_layout)

        object_type_lbl = QtWidgets.QLabel(self)
        object_type_lbl.setText('Name')
        self.object_name_txt = QtWidgets.QLineEdit(self)
        form_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, object_type_lbl)
        form_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.object_name_txt)

        start_frame_lbl = QtWidgets.QLabel(self)
        start_frame_lbl.setText('Start Frame')
        self.start_frame = QtWidgets.QLineEdit(self)
        form_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, start_frame_lbl)
        form_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.start_frame)

        end_frame_lbl = QtWidgets.QLabel(self)
        end_frame_lbl.setText('End Frame')
        self.end_frame = QtWidgets.QLineEdit(self)
        form_layout.setWidget(2, QtWidgets.QFormLayout.LabelRole, end_frame_lbl)
        form_layout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.end_frame)

        camera_lbl = QtWidgets.QLabel(self)
        camera_lbl.setText('Camera')
        self.camera_combo = QtWidgets.QComboBox(self)
        for camera in sorted(cmds.ls(type='camera')):
            self.camera_combo.addItem(camera)
        form_layout.setWidget(3, QtWidgets.QFormLayout.LabelRole, camera_lbl)
        form_layout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.camera_combo)


class SequencerWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(SequencerWidget, self).__init__(parent)
        self.splitter = QtWidgets.QSplitter(self)

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        self.ae_view = AttributeEditor(self)

        self.dgnodes = [n for n in pm.ls(type='shot')]
        # self.list_model = DependListModel(self.dgnodes, parent=self)
        self.dependency_model = DependTableModel(self.dgnodes, parent=parent)
        self.selection_model = QtCore.QItemSelectionModel(self.dependency_model)

        self.list_view = QtWidgets.QListView(self)
        self.table_view = QtWidgets.QTableView(self)
        
        self.list_view.setModel(self.dependency_model)
        self.table_view.setModel(self.dependency_model)
        
        self.table_view.setSelectionModel(self.selection_model)
        self.list_view.setSelectionModel(self.selection_model)
        self.table_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        self.cameras = cmds.ls(type='camera')
        self.cameras_delegate = ComboBoxDelegate(self.table_view, self.cameras)
        self.table_view.setItemDelegateForColumn(3, self.cameras_delegate)

        self.data_mapper = QtWidgets.QDataWidgetMapper()
        self.data_mapper.setSubmitPolicy(QtWidgets.QDataWidgetMapper.AutoSubmit)
        self.data_mapper.setModel(self.dependency_model)
        self.data_mapper.addMapping(self.ae_view.object_name_txt, 0, 'text')
        self.data_mapper.addMapping(self.ae_view.start_frame, 1, 'text')
        self.data_mapper.addMapping(self.ae_view.end_frame, 2, 'text')
        self.data_mapper.addMapping(self.ae_view.camera_combo, 3, "currentText")

        self.splitter.addWidget(self.list_view)
        self.splitter.addWidget(self.table_view)
        self.splitter.addWidget(self.ae_view)
        self.splitter.setStretchFactor(0, 0)

        self.setCentralWidget(self.splitter)

        self.setWindowTitle("Camera Sequencer")
        self.resize(800, 500)

        self.table_view.clicked.connect(self.set_ae_view)

    def set_ae_view(self, index):
        if index.isValid():
            node = self.dependency_model.invisibleRootItem()[index.row()]
            idx = self.ae_view.camera_combo.findText(str(cmds.shot(node.nodeName(), q=True, cc=True)) + 'Shape')
            self.ae_view.camera_combo.setCurrentIndex(idx)
            pm.select(node)
        self.data_mapper.setCurrentModelIndex(index)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Delete):
            self.delete_items()

    def delete_items(self):
        selection = self.table_view.selectionModel().selectedRows()
        persistent_indexes = [QtCore.QPersistentModelIndex(index) for index in selection]
        for index in persistent_indexes:
            if index.isValid():
                self.dependency_model.removeRows(index.row(), 1, index.parent())

def create_shots():
    start = 1
    end = 24
    for i in range(10):
        pm.shot('shot_{}'.format(i), startTime=start, endTime=end)
        start = end + 1
        end = start + 24


def launch():
    ptr = mui.MQtUtil.mainWindow()
    app = shiboken.wrapInstance(long(ptr), QtWidgets.QWidget)
    create_shots()
    camera_sequencer = SequencerWidget(parent=app)
    camera_sequencer.show()


def launch_nomaya():
    create_shots()
    camera_sequencer = SequencerWidget()
    camera_sequencer.show()
    app.exec_()
    sys.exit(0)


if __name__ == '__main__':
    if MAYA_HEADLESS:
        launch_nomaya()
    else:
        if MAYA_AVAILABLE:
            launch()
        else:
            launch_nomaya()
