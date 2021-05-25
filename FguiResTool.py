import os
import sys
from pathlib import Path
from typing import List

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize, QModelIndex, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem, QGuiApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QLabel, QCheckBox, QMessageBox

import CheckResMd5 as crm
import mainGUI


# 全局自定义事件 参考：https://zhuanlan.zhihu.com/p/89759440
class GSignal(QObject):
    refresh = pyqtSignal()
    delete_com = pyqtSignal(str, str)

    def __init__(self):
        super(GSignal, self).__init__()


global_signal = GSignal()


class SourceItem(QWidget):
    def __init__(self, data: crm.VoHash, *args, **kwargs):
        super(SourceItem, self).__init__(*args, **kwargs)
        self.cur_data = data
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tfContent = QLabel()
        layout.addWidget(self.tfContent)
        self.setData(data)

    def setData(self, data: crm.VoHash):
        self.cur_data = data
        name_str = data.get_name()
        count_str = '({0}) '.format(len(data.com_list))
        self.tfContent.setText(count_str + name_str)
        pass

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
        if data.exclude:  # 设置为图集排除的资源
            des_str = '<font color="#ff0000">{0}</font> {1}'.format('(×)', des_str)
        if not data.exported:  # 没有设置为导出的资源
            des_str = '<font color="#ff0000">{0}</font> {1}'.format('(未导出)', des_str)
        des_str = '({0}) {1}'.format(len(data.refs), des_str)
        self.cb = QCheckBox('', self)
        self.cb.resize(16, 16)
        layout.addWidget(self.cb)
        self.tfContent = QLabel(des_str, self)
        layout.addWidget(self.tfContent)
        # 增加弹性布局 pyqt布局相关：https://segmentfault.com/a/1190000017845249
        layout.addStretch(1)

        # 右键菜单 https://www.pythonf.cn/read/152969
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.custom_right_menu)

    def sizeHint(self) -> QSize:
        return QSize(200, 22)

    def custom_right_menu(self, pos):
        menu = QtWidgets.QMenu()
        op1 = menu.addAction('打开文件')
        op2 = menu.addAction('定位文件')
        op3 = menu.addAction('打开package.xml')
        op4 = menu.addAction('复制文件名')
        op5 = menu.addAction('复制url')
        menu.addSeparator()
        op6 = menu.addAction('删除资源')
        op99 = None
        if self.cur_data and not self.cur_data.exported:
            menu.addSeparator()
            op99 = menu.addAction('**设置为导出')
        action = menu.exec_(self.mapToGlobal(pos))

        if action == op1:  # 直接使用默认程序打开文件
            os.startfile(self.cur_data.url)

        elif action == op2:  # 打开资源管理器并定位到相应文件
            os.system('explorer.exe /select,' + str(self.cur_data.url))

        elif action == op3:
            os.startfile(self.cur_data.file_pkg)

        elif action == op4:
            cb = QGuiApplication.clipboard()
            cb.setText(self.cur_data.name)

        elif action == op5:
            cb = QGuiApplication.clipboard()
            cb.setText('ui://{0}'.format(self.cur_data.uid))

        elif action == op6:
            if len(self.cur_data.refs) > 0:
                QMessageBox.warning(self, '错误', '该资源存在引用，不能删除', QMessageBox.Ok)
            else:
                global_signal.delete_com.emit(self.cur_data.md5, self.cur_data.uid)

        elif op99 and action == op99:
            self.cur_data.node.set('exported', 'true')
            self.cur_data.tree.write(str(self.cur_data.file_pkg), encoding='utf-8', xml_declaration=True)
            self.cur_data.exported = True
            global_signal.refresh.emit()


class RefItem(QWidget):
    def __init__(self, data: crm.VoRef, *args, **kwargs):
        super(RefItem, self).__init__(*args, **kwargs)
        self.cur_data = data
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        des_str = '(t={0}) '.format(data.type.value) + data.file.name + '@' + data.pkg
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

        global_signal.refresh.connect(self.on_refresh)
        global_signal.delete_com.connect(self.on_del_com_item)

    def on_refresh(self):
        self.show_com_list(self.cur_hash_vo)

    def on_del_com_item(self, p_md5, p_uid):
        model = self.view.listAll.model()
        count = model.rowCount()
        for i in range(count):
            mi = model.index(i, 0)
            item: SourceItem = self.view.listAll.indexWidget(mi)
            if item.cur_data.key == p_md5:
                voh: crm.VoHash = crm.md5_map[p_md5]
                for j in range(len(voh.com_list) - 1, -1, -1):
                    voc = voh.com_list[j]
                    if voc.uid == p_uid:
                        del voh.com_list[j]
                        path_com = Path(voc.url)
                        if path_com.exists():
                            path_com.unlink()  # 删除本地文件
                        voc.node.getparent().remove(voc.node)  # 删除package.xml里面的引用
                        voc.tree.write(str(voc.file_pkg), encoding='utf-8', xml_declaration=True)
                        # voc.node.getroottree().write(voc.file_pkg, encoding='utf-8', xml_declaration=True)
                        break
                if len(voh.com_list) < 1:
                    # 删除项
                    model.removeRow(i)
                    del self.hash_list[i]
                else:
                    # 更新项
                    item.setData(voh)
                    self.show_com_list(voh)
                break
        pass

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

            reserved_com = crm.get_com_by_uid(self.cur_hash_vo.reserved_uid)

            new_refs: List[crm.VoRef] = []
            for i in range(len(s_com_list) - 1, -1, -1):
                com = s_com_list[i]
                if com.uid == self.cur_hash_vo.reserved_uid:  # 跳过保留的资源
                    continue
                for j in range(len(com.refs) - 1, -1, -1):
                    ref = com.refs[j]
                    # print(ref.type)
                    if ref.type == crm.RefType.IMAGE:
                        # image替换
                        ref.node.set('src', reserved_com.com_id)
                        ref.node.set('fileName', reserved_com.fileName)
                        # print(ref.pkg, reserved_com.pkg)
                        if ref.pkg == reserved_com.pkg:
                            if 'pkg' in ref.node:  # 删除pkg属性
                                del ref.node.attrib['pkg']
                        else:  # 替换pkg属性
                            ref.node.set('pkg', reserved_com.pkg_id)
                        ref.tree.write(str(ref.file), encoding='utf-8', xml_declaration=True)
                        ref.uid = reserved_com.uid  # 设置新的uid
                        del com.refs[j]  # 从原来的引用列表中删除
                        new_refs.append(ref)  # 添加到新引用列表
                    elif ref.type == crm.RefType.FNT:
                        # 字体替换
                        pass
                    else:
                        # url替换
                        xml_str = ref.file.read_text(encoding='utf-8')
                        new_str = xml_str.replace(ref.uid, reserved_com.uid)
                        ref.file.write_text(new_str, encoding='utf-8')
                        ref.uid = reserved_com.uid  # 设置新的uid
                        del com.refs[j]  # 从原来的引用列表中删除
                        new_refs.append(ref)  # 添加到新引用列表
                        pass
                pass
            if len(new_refs) > 0:
                reserved_com.refs.extend(new_refs)

                self.show_com_list(self.cur_hash_vo)
                self.show_ref_list([])
                QMessageBox.information(self, '提示', '合并成功', QMessageBox.Yes)
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
        root_url = 'I:/sanguo2/client/sanguo2UI'
        # root_url = 'I:/newQz/client/yxqzUI'
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

        # for v in self.hash_list:
        #     item = QStandardItem()
        #     self._model_all.appendRow(item)
        #     index = self._model_all.indexFromItem(item)
        #     sitem = SourceItem(v)
        #     item.setSizeHint(sitem.sizeHint())
        #     self.view.listAll.setIndexWidget(index, sitem)
        self.show_source_list()

        self.statusBar().showMessage('共有{0}个重复资源'.format(len(self.hash_list)))
        pass

    def show_source_list(self):
        self._model_all = QStandardItemModel(self)
        self.view.listAll.setModel(self._model_all)
        # 选中处理
        self.view.listAll.selectionModel().currentChanged.connect(self.on_list_all_selected_change)

        for v in self.hash_list:
            item = QStandardItem()
            self._model_all.appendRow(item)
            index = self._model_all.indexFromItem(item)
            sitem = SourceItem(v)
            item.setSizeHint(sitem.sizeHint())
            self.view.listAll.setIndexWidget(index, sitem)

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
    main_win.setWindowTitle('FGUI资源查重工具')

    sys.exit(app.exec_())
