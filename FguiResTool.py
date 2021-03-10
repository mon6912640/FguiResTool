import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget

import mainGUI


class SourceItem(QWidget):
    def __init__(self, text, *args, **kwargs):
        super(SourceItem, self).__init__(*args, **kwargs)

    def sizeHint(self) -> QSize:
        return QSize(200, 100)


class MyMainWin(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.view = mainGUI.Ui_MainWindow()
        self.view.setupUi(self)

        self.view.btnClose.clicked.connect(self.on_close_click)
        self.view.btnSearch.clicked.connect(self.on_search_click)

        pic_url1 = 'I:/newQz/client/yxqzUI/assets/bag/res/背包标题.png'
        pic_url2 = 'I:/newQz/client/yxqzUI/assets/bag/res/分解背景.jpg'
        self.img = QPixmap()
        print(self.img.width(), self.img.height())
        self.img.load(pic_url1)
        print(self.img.width(), self.img.height())
        self.img.load(pic_url2)
        print(self.img.width(), self.img.height())
        # print(self.view.labelImg.width(), self.view.labelImg.height())
        if self.img.width() > self.view.labelImg.width() or self.img.height() > self.view.labelImg.height():
            img = self.img.scaled(self.view.labelImg.width(), self.view.labelImg.height(), Qt.KeepAspectRatio)
            print(img.width(), img.height())
        else:
            img = self.img
        self.view.labelImg.setPixmap(img)

    def on_close_click(self):
        app = QApplication.instance()
        app.quit()
    
    def on_search_click(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_win = MyMainWin()
    main_win.show()
    main_win.setWindowTitle('FGUI资源去重工具')

    sys.exit(app.exec_())
