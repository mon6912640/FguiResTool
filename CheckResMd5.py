import hashlib
import xml.etree.ElementTree as et
from pathlib import Path
from typing import List
import re
from enum import Enum


def hashs(p_fname, p_type="md5", block_size=64 * 1024):
    """
    Support md5(), sha1(), sha224(), sha256(), sha384(), sha512(),
    blake2b(), blake2s(),
    sha3_224, sha3_256, sha3_384, sha3_512, shake_128, and shake_256
    :param p_fname:
    :param p_type:
    :param block_size:
    :return:
    """
    with open(p_fname, 'rb') as file:
        hc = hashlib.new(p_type, b"")
        while True:
            data = file.read(block_size)
            if not data:
                break
            hc.update(data)
        return hc.hexdigest()


class RefType(Enum):
    IMAGE = 0
    URL = 1
    FNT = 2


class VoRef:
    # 类型
    type = 0
    node = None
    file: Path = None
    uid = ''
    pkg = ''


class ComVo:
    uid = ''
    pkg_id = ''
    com_id = ''
    name = ''
    pkg = ''
    md5 = ''
    # 不导出
    exclude = False
    url = ''
    ref_pkgs: set = None
    ref_count = 0
    refs: List[VoRef] = None

    def __init__(self):
        self.ref_pkgs = set()
        self.refs = []


class VoHash:
    key = ''
    com_list: List[ComVo] = None

    def __init__(self):
        self.com_list = []

    def get_name(self):
        if len(self.com_list) > 0:
            return self.com_list[0].name
        else:
            return '无'


com_map = {}
md5_map = {}


def add_ref(uid, file, ):
    global com_map
    pass


def analyse_xml(p_root_url):
    global com_map
    com_map = {}
    path_res = Path(p_root_url) / 'assets'
    global md5_map
    md5_map = {}
    name_pkg_id_map = {}  # 包名与包id的映射
    list_file = sorted(path_res.rglob('package.xml'))
    for v in list_file:
        pkg = v.parent.name  # 包名
        # print('-------', pkg)
        xml_vo = et.parse(str(v))
        root = xml_vo.getroot()
        if root.tag != 'packageDescription':
            continue
        pkg_id = root.get('id')
        name_pkg_id_map[pkg] = pkg_id
        for com in root.iterfind('resources/image'):
            com_id = com.get('id')
            path_img = v.parent.joinpath('.' + com.get('path'), com.get('name'))
            if not path_img.exists():
                continue  # 不存在资源
            else:
                url = str(path_img.absolute())
                md5_str = hashs(url)
                com_vo = ComVo()
                com_vo.uid = pkg_id + com_id
                com_vo.pkg_id = pkg_id
                com_vo.com_id = com_id
                com_vo.name = com.get('name')
                com_vo.pkg = pkg
                com_vo.md5 = md5_str
                com_vo.url = url
                com_map[com_vo.uid] = com_vo

                if md5_str not in md5_map:
                    md5_map[md5_str] = hash_vo = VoHash()
                    hash_vo.key = md5_str
                else:
                    hash_vo = md5_map[md5_str]
                hash_vo.com_list.append(com_vo)

        excluded_str = root.find('publish').get('excluded')
        if excluded_str:
            excluded_list = excluded_str.split(',')
            for cid in excluded_list:
                uid = pkg_id + cid
                if uid in com_map:
                    # 设置不导出
                    com_map[uid].exclude = True
    for k in com_map:
        if com_map[k].exclude:
            # print(com_map[k].url)
            pass

    list_file = sorted(path_res.rglob('*.*'))
    for v in list_file:
        if v.name == 'package.xml':
            continue
        if not (v.suffix == '.xml' or v.suffix == '.fnt'):
            continue
        temp_path = str(v.relative_to(path_res).as_posix())
        pkg_name = temp_path.split('/')[0]
        if pkg_name in name_pkg_id_map:
            pkg_id = name_pkg_id_map[pkg_name]
        else:
            continue
        if v.suffix == '.xml':
            xml_vo = et.parse(str(v))
            root = xml_vo.getroot().find('displayList')

            # 直接搜索ui://xxxxxx
            xml_str = v.read_text(encoding='utf-8')
            find_list = re.findall('ui://(\w+)', string=xml_str)
            # print(v.name, find_list)
            for uid in find_list:
                if uid in com_map:
                    ref_vo = VoRef()
                    ref_vo.uid = uid
                    ref_vo.type = RefType.URL
                    ref_vo.file = v
                    ref_vo.pkg = pkg_name
                    com_map[uid].refs.append(ref_vo)
                    # com_map[uid].ref_pkgs.add(pkg_name)
                    # com_map[uid].ref_count += 1

            # 查找image标签
            for node in root.iterfind('image'):
                # 图片引用
                src_com_id = node.get('src')
                src_pkg_id = node.get('pkg')
                if src_com_id:
                    if src_pkg_id:  # 有pkg属性则为外包资源
                        uid = src_pkg_id + src_com_id
                    else:  # 无pkg属性则为本包资源
                        uid = pkg_id + src_com_id
                    if uid in com_map:
                        ref_vo = VoRef()
                        ref_vo.uid = uid
                        ref_vo.type = RefType.IMAGE
                        ref_vo.file = v
                        ref_vo.pkg = pkg_name
                        ref_vo.node = node
                        com_map[uid].refs.append(ref_vo)
                        # com_map[uid].ref_pkgs.add(pkg_name)
                        # com_map[uid].ref_count += 1
                # print(node.tag, node.attrib)
                pass
            # for node in root.iterfind('list[@defaultItem]'):
            #     # 列表的项目资源
            #     uid = node.get('defaultItem')
            #     # print(node.tag, node.attrib)
            # for node in root.iterfind('.//*[@url]'):
            #     # Loader/列表的单独的项目资源引用
            #     uid = node.get('url')
            #     # print(node.tag, node.attrib)
            # for node in root.iterfind('.//*[@icon]'):
            #     # 组件图标属性
            #     uid = node.get('icon')
            #     # print(node.tag, node.attrib)
            # for node in root.iterfind('.//property[@value]'):
            #     # 自定义属性
            #     uid = node.get('value')
            #     # print(node.tag, node.attrib)
            # for node in root.iterfind('.//*[@values]'):
            #     # 图标控制器
            #     uid = node.get('values')
            #     # print(v.name, node.tag, node.attrib)
            # for node in root.iterfind('.//*[@default]'):
            #     # print(v.name, node.tag, node.attrib)
            #     pass
        if v.suffix == '.fnt':
            # print(str(v))
            fnt_str = v.read_text()
            find_list = re.findall('img=(\S+)', string=fnt_str)
            for src_com_id in find_list:
                uid = pkg_id + src_com_id
                if uid in com_map:
                    ref_vo = VoRef()
                    ref_vo.uid = uid
                    ref_vo.type = RefType.FNT
                    ref_vo.file = v
                    ref_vo.pkg = pkg_name
                    com_map[uid].refs.append(ref_vo)
            pass
    # for k in com_map:
    #     if len(com_map[k].ref_pkgs) > 0:
    #         print(com_map[k].ref_count, com_map[k].ref_pkgs)
    pass


if __name__ == '__main__':
    root_url = 'I:/newQz/client/yxqzUI'
    analyse_xml(root_url)
    pass
