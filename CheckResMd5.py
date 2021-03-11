import hashlib
import xml.etree.ElementTree as et
from pathlib import Path
from typing import List
import re


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


class ComVo:
    uid = 0
    pkg_id = 0
    com_id = 0
    name = ''
    pkg = ''
    md5 = ''
    # 不导出
    exclude = False
    url = ''
    ref_pkgs: set = None
    ref_count = 0

    def __init__(self):
        self.ref_pkgs = set()


class VoHash:
    key = ''
    is_repeat = False
    url_list: List[str] = None
    com_list: List[ComVo] = None

    def __init__(self):
        self.url_list = []
        self.com_list = []

    def get_name(self):
        if len(self.com_list) > 0:
            return self.com_list[0].name
        else:
            return '无'

class VoRef:
    # 类型
    type = 0

def analyse_files(p_root_url):
    vo_map = {}
    path_res = Path(p_root_url) / 'assets'
    list_file = sorted(path_res.rglob('*.*'))
    repeat_list = []
    for v in list_file:
        if v.suffix == '.png' or v.suffix == '.jpg':
            furl = v.absolute()
            md5_str = hashs(str(furl), 'md5')
            if md5_str not in vo_map:
                vo_map[md5_str] = vo = VoHash()
                vo.key = md5_str
            else:
                vo = vo_map[md5_str]
            vo.url_list.append(furl)
            if not vo.is_repeat and len(vo.url_list) > 1:
                vo.is_repeat = True
                repeat_list.append(vo)
    for v in repeat_list:
        print('======', len(v.url_list), v.key)
        for fp in v.url_list:
            print(fp)


com_map = {}
md5_map = {}


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
            for node in root.iterfind('image'):
                src_com_id = node.get('src')
                src_pkg_id = node.get('pkg')
                if src_com_id:
                    if src_pkg_id:  # 有pkg属性则为外包资源
                        uid = src_pkg_id + src_com_id
                        pass
                    else:  # 无pkg属性则为本包资源
                        uid = pkg_id + src_com_id
                        pass
                    if uid in com_map:
                        com_map[uid].ref_pkgs.add(pkg_name)
                        com_map[uid].ref_count += 1
                pass
            for node in root.iterfind('list[@defaultItem]'):
                uid = node.get('defaultItem')
                # print(node.tag, node.attrib)
            for node in root.iterfind('.//*[@url]'):
                uid = node.get('url')
                # print(node.tag, node.attrib)
            for node in root.iterfind('.//*[@icon]'):
                uid = node.get('icon')
                # print(node.tag, node.attrib)
            for node in root.iterfind('.//*[@values]'):
                uid = node.get('values')
                # print(node.tag, node.attrib)
            for node in root.iterfind('.//property[@value]'):
                uid = node.get('value')
                # print(node.tag, node.attrib)
                pass
            pass
        if v.suffix == '.fnt':
            # print(str(v))
            fnt_str = v.read_text()
            find_list = re.findall('img=(\S+)', string=fnt_str)
            for src_com_id in find_list:
                uid = pkg_id + src_com_id
                if uid in com_map:
                    com_map[uid].ref_pkgs.add(pkg_name)
                    com_map[uid].ref_count += 1
            pass
    # for k in com_map:
    #     if len(com_map[k].ref_pkgs) > 0:
    #         print(com_map[k].ref_count, com_map[k].ref_pkgs)
    pass


if __name__ == '__main__':
    root_url = 'I:/newQz/client/yxqzUI'
    # analyse_files(root_url)
    analyse_xml(root_url)
    pass
