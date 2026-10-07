"""生成 sldworks_gen.py（SolidWorks 类型库早绑定包装）。

用法：python make_typelib_wrapper.py [sldworks.tlb 路径]
默认在注册表 InstallSource 附近找；找不到就从注册表查 SolidWorks Folder。
生成后与本目录 sw_common.py 放在同一目录即可 import。
"""
import os
import sys
import winreg


def find_tlb():
    if len(sys.argv) > 1:
        return sys.argv[1]
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\SolidWorks\SOLIDWORKS 2024\Setup") as k:
            root = winreg.QueryValueEx(k, "SolidWorks Folder")[0]
        p = os.path.join(root, "sldworks.tlb")
        if os.path.exists(p):
            return p
    except OSError:
        pass
    raise SystemExit("未找到 sldworks.tlb，请手动传入路径")


def main():
    from win32com.client import makepy
    tlb = find_tlb()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sldworks_gen.py")
    sys.argv = ["makepy", "-o", out, tlb]
    makepy.main()
    print("已生成:", out)


if __name__ == "__main__":
    main()
