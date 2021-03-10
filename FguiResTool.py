import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QSize, QModelIndex
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel

import mainGUI
import CheckResMd5 as crm


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


class MyMainWin(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.view = mainGUI.Ui_MainWindow()
        self.view.setupUi(self)

        self.view.btnClose.clicked.connect(self.on_close_click)
        self.view.btnSearch.clicked.connect(self.on_search_click)
        self.view.listAll.clicked.connect(self.on_list_all_click)

        self.img = QPixmap()

    def show_preview(self, p_url):
        self.img.load(p_url)
        if self.img.width() > self.view.labelImg.width() or self.img.height() > self.view.labelImg.height():
            img = self.img.scaled(self.view.labelImg.width(), self.view.labelImg.height(), Qt.KeepAspectRatio)
        else:
            img = self.img
        self.view.labelImg.setPixmap(img)
        pass

    def on_close_click(self):
        app = QApplication.instance()
        app.quit()

    def on_search_click(self):
        self._model = QStandardItemModel(self)
        self.view.listAll.setModel(self._model)

        root_url = 'I:/newQz/client/yxqzUI'
        crm.analyse_xml(root_url)
        self.md5_map = crm.md5_map
        self.hash_list = []
        for k in self.md5_map:
            vo: crm.VoHash = self.md5_map[k]
            if len(vo.com_list) < 2:
                # 只显示重复的资源
                continue
            item = QStandardItem()
            self._model.appendRow(item)
            self.hash_list.append(vo)

            index = self._model.indexFromItem(item)
            sitem = SourceItem(vo)
            item.setSizeHint(sitem.sizeHint())
            self.view.listAll.setIndexWidget(index, sitem)
        pass

    def on_list_all_click(self, p_model_index: QModelIndex):
        vo = self.hash_list[p_model_index.row()]
        self.show_preview(vo.com_list[0].url)
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_win = MyMainWin()
    main_win.show()
    main_win.setWindowTitle('FGUI资源去重工具')

    sys.exit(app.exec_())
