import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize, QModelIndex
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel, QCheckBox, QMessageBox

import CheckResMd5 as crm
import mainGUI


class SourceItem(QWidget):
    def __init__(self, data: crm.VoHash, *args, **kwargs):
        super(SourceItem, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        name_str = data.get_name()
        count_str = '({0}) '.format(len(data.com_list))
        self.tfContent = QLabel(count_str + name_str, self)
        layout.addWidget(self.tfContent)

    def sizeHint(self) -> QSize:
        return QSize(200, 22)


class ComItem(QWidget):
    def __init__(self, data: crm.ComVo, *args, **kwargs):
        super(ComItem, self).__init__(*args, **kwargs)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.cur_data = data
        des_str = data.name + '@' + data.pkg

        hash_vo: crm.VoHash = crm.md5_map[data.md5]
        if hash_vo.reserved_uid == data.uid:  # 保留资源着色显示
            des_str = '<font color="#0000ff">{0}</font>'.format(des_str)
        if data.exclude:  # 设置为不导出的资源
            des_str = '<font color="#ff0000">{0}</font> {1}'.format('(×)', des_str)
        des_str = '({0}) {1}'.format(len(data.refs), des_str)
        self.cb = QCheckBox('', self)
        self.cb.resize(16, 16)
        layout.addWidget(self.cb)
        self.tfContent = QLabel(des_str, self)
        layout.addWidget(self.tfContent)
        # 增加弹性布局 pyqt布局相关：https://segmentfault.com/a/1190000017845249
        layout.addStretch(1)

    def sizeHint(self) -> QSize:
        return QSize(200, 22)


class RefItem(QWidget):
    def __init__(self, data: crm.VoRef, *args, **kwargs):
        super(RefItem, self).__init__(*args, **kwargs)
        self.cur_data = data
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        des_str = data.file.name + '@' + data.pkg
        self.tfContent = QLabel(des_str, self)
        layout.addWidget(self.tfContent)

        # 右键菜单 https://www.pythonf.cn/read/152969
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.custom_right_menu)

    def sizeHint(self) -> QSize:
        return QSize(200, 22)

    def custom_right_menu(self, pos):
        menu = QtWidgets.QMenu()
        op1 = menu.addAction('打开文件')
        op2 = menu.addAction('定位文件')
        action = menu.exec_(self.mapToGlobal(pos))

        if action == op1:  # 直接使用默认程序打开文件
            os.startfile(self.cur_data.file)
        elif action == op2:  # 打开资源管理器并定位到相应文件
            os.system('explorer.exe /select,' + str(self.cur_data.file))


class MyMainWin(QMainWindow):
    cur_hash_vo: crm.VoHash = None
    cur_com_vo: crm.ComVo = None

    def __init__(self):
        QMainWindow.__init__(self)

        self.view = mainGUI.Ui_MainWindow()
        self.view.setupUi(self)

        self.view.btnClose.clicked.connect(self.on_close_click)
        self.view.btnSearch.clicked.connect(self.on_search_click)
        self.view.btnSelectAll.clicked.connect(self.on_select_all)
        self.view.btnReverse.clicked.connect(self.on_reverse)
        self.view.btnCancelAll.clicked.connect(self.on_cancel_all)
        self.view.btnSave.clicked.connect(self.on_save)
        self.view.btnMerge.clicked.connect(self.on_merge)

        self.img = QPixmap()

    def on_save(self):
        while True:
            if not self.cur_hash_vo:
                break
            if not self.cur_com_vo:
                QMessageBox.warning(self, '注意', '没有选中要保留的资源', QMessageBox.Ok)
                break
            self.cur_hash_vo.reserved_uid = self.cur_com_vo.uid
            self.show_com_list(self.cur_hash_vo)
            break
        pass

    def on_merge(self):
        while True:
            if not self.cur_hash_vo:
                break
            if not self.cur_hash_vo.reserved_uid:
                QMessageBox.warning(self, '注意', '没有设置保留资源', QMessageBox.Ok)
                break
            s_com_list = []
            # 遍历ListView
            model = self.view.listShow.model()  # 先获取model
            count = model.rowCount()  # 获取model长度
            for i in range(count):
                mi = model.index(i, 0)  # 获取QModelIndex
                item: ComItem = self.view.listShow.indexWidget(mi)  # 通过QModelIndex获取具体的item
                if item.cb.checkState() == Qt.Checked:
                    s_com_list.append(item.cur_data)
                    pass
            if len(s_com_list) < 1:
                QMessageBox.warning(self, '注意', '并没有勾选资源', QMessageBox.Ok)
            break
        pass

    def on_select_all(self):
        # 遍历ListView
        model = self.view.listShow.model()  # 先获取model
        count = model.rowCount()  # 获取model长度
        for i in range(count):
            mi = model.index(i, 0)  # 获取QModelIndex
            item: ComItem = self.view.listShow.indexWidget(mi)  # 通过QModelIndex获取具体的item
            item.cb.setChecked(True)
        pass

    def on_reverse(self):
        # 遍历ListView
        model = self.view.listShow.model()  # 先获取model
        count = model.rowCount()  # 获取model长度
        for i in range(count):
            mi = model.index(i, 0)  # 获取QModelIndex
            item: ComItem = self.view.listShow.indexWidget(mi)  # 通过QModelIndex获取具体的item
            if item.cb.checkState() == Qt.Checked:
                item.cb.setChecked(False)
            else:
                item.cb.setChecked(True)
        pass

    def on_cancel_all(self):
        # 遍历ListView
        model = self.view.listShow.model()  # 先获取model
        count = model.rowCount()  # 获取model长度
        for i in range(count):
            mi = model.index(i, 0)  # 获取QModelIndex
            item: ComItem = self.view.listShow.indexWidget(mi)  # 通过QModelIndex获取具体的item
            # print(item.cb.checkState())
            item.cb.setChecked(False)
        pass

    def show_preview(self, p_url):
        self.img.load(p_url)
        if self.img.width() > self.view.labelImg.width() or self.img.height() > self.view.labelImg.height():
            img = self.img.scaled(self.view.labelImg.width(), self.view.labelImg.height(), Qt.KeepAspectRatio)
        else:
            img = self.img
        self.view.labelImg.setPixmap(img)
        pass

    def on_list_all_selected_change(self, cur_index: QModelIndex, last_index: QModelIndex):
        """
        选中处理函数
        :param cur_index:
        :param last_index:
        :return:
        """
        if cur_index:
            vo = self.hash_list[cur_index.row()]
            self.cur_hash_vo = vo
            if vo:
                self.show_preview(vo.com_list[0].url)
                self.show_com_list(vo)
                self.show_ref_list([])
        pass

    def on_list_show_selected_change(self, cur_index: QModelIndex, last_index: QModelIndex):
        if cur_index and self.cur_hash_vo:
            vo = self.cur_hash_vo.com_list[cur_index.row()]
            self.cur_com_vo = vo
            self.show_ref_list(vo.refs)
        pass

    def on_close_click(self):
        app = QApplication.instance()
        app.quit()

    def on_search_click(self):
        self._model_all = QStandardItemModel(self)
        self.view.listAll.setModel(self._model_all)
        # 选中处理
        self.view.listAll.selectionModel().currentChanged.connect(self.on_list_all_selected_change)

        # root_url = 'I:/sanguo2/client/sanguo2UI'
        root_url = 'I:/newQz/client/yxqzUI'
        crm.analyse_xml(root_url)
        self.md5_map = crm.md5_map
        self.hash_list = []
        for k in self.md5_map:
            vo: crm.VoHash = self.md5_map[k]
            if len(vo.com_list) < 2:
                # 只显示重复的资源
                continue
            self.hash_list.append(vo)

        self.hash_list.sort(key=lambda e: len(e.com_list), reverse=True)

        for v in self.hash_list:
            item = QStandardItem()
            self._model_all.appendRow(item)
            index = self._model_all.indexFromItem(item)
            sitem = SourceItem(v)
            item.setSizeHint(sitem.sizeHint())
            self.view.listAll.setIndexWidget(index, sitem)

        self.statusBar().showMessage('共有{0}个重复资源'.format(len(self.hash_list)))
        pass

    def show_com_list(self, p_hash):
        vo = p_hash
        if vo:
            self._com_model = QStandardItemModel(self)
            self.view.listShow.setModel(self._com_model)
            # 选中处理
            self.view.listShow.selectionModel().currentChanged.connect(self.on_list_show_selected_change)

            for v in vo.com_list:
                item = QStandardItem()
                self._com_model.appendRow(item)

                m_index = self._com_model.indexFromItem(item)
                com_item = ComItem(v)
                item.setSizeHint(com_item.sizeHint())
                self.view.listShow.setIndexWidget(m_index, com_item)
        pass

    def show_ref_list(self, p_ref_list):
        self._ref_model = QStandardItemModel(self)
        self.view.listRef.setModel(self._ref_model)

        for v in p_ref_list:
            item = QStandardItem()
            self._ref_model.appendRow(item)

            m_index = self._ref_model.indexFromItem(item)
            ref_item = RefItem(v)
            item.setSizeHint(ref_item.sizeHint())
            self.view.listRef.setIndexWidget(m_index, ref_item)
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_win = MyMainWin()
    main_win.show()
    main_win.setWindowTitle('FGUI资源去重工具')

    sys.exit(app.exec_())
