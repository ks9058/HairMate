import os
from PySide6.QtGui import QIcon, QFontDatabase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCE_DIR = os.path.join(BASE_DIR, "resources")

def load_fonts() -> str:
    """resources/ 폴더의 KaushanScript-Regular.ttf 폰트를 DB에 등록하고 패밀리명을 반환합니다."""
    font_path = os.path.join(RESOURCE_DIR, "KaushanScript-Regular.ttf")
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
    return "Georgia"

def get_icon(icon_name: str) -> QIcon:
    """resources/ 폴더의 SVG 아이콘 경로를 받아 QIcon 객체를 생성합니다."""
    icon_path = os.path.join(RESOURCE_DIR, icon_name)
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    print(f"[Warning] 아이콘 파일을 찾을 수 없습니다: {icon_path}")
    return QIcon()

class Colors:
    PRIMARY = "#0C604F"
    SUB = "#0EA985"
    PRIMARY_HOVER = "#084E3E"
    PRIMARY_PRESSED = "#063C30"

    BACKGROUND = "#F2F3F5"
    GRAY = "#D9D9D9"
    WHITE = "#FFFFFF"
    TEXT_MAIN = "#000000"
    TEXT_MUTED = "#7A7A7A"
    BORDER = "#CCCCCC"
    BORDER_LIGHT = "#E0E0E0"

    DANGER = "#D70000"
    SUCCESS = "#16A085"

class Styles:
    PRIMARY_BUTTON = f"""
        QPushButton {{
            background-color: {Colors.PRIMARY};
            color: {Colors.WHITE};
            border: none;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            font-family: 'Inter', 'Malgun Gothic', sans-serif;
        }}
        QPushButton:hover {{
            background-color: {Colors.PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {Colors.PRIMARY_PRESSED};
        }}
    """

    # 메인 사이드바 버튼 (오른쪽 라운드 10px, 높이 46px, 키운 아이콘 맞춤 패딩)
    SIDEBAR_BUTTON = f"""
        QPushButton {{
            color: {Colors.WHITE};
            background-color: transparent;
            border: none;
            text-align: left;
            padding-left: 18px;
            font-size: 13px;
            font-weight: bold;
            font-family: 'Inter', 'Malgun Gothic', sans-serif;
            height: 46px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            margin-right: 12px;
        }}
        QPushButton:hover, QPushButton:checked {{
            color: {Colors.TEXT_MAIN};
            background-color: {Colors.WHITE};
        }}
    """

    # 서브 사이드바 버튼 (소형 우측 라운드 8px, 높이 34px)
    SIDEBAR_SUB_BUTTON = f"""
        QPushButton {{
            color: #E0E0E0;
            background-color: transparent;
            border: none;
            text-align: left;
            padding-left: 36px;
            font-size: 11px;
            font-weight: normal;
            font-family: 'Inter', 'Malgun Gothic', sans-serif;
            height: 34px;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            margin-right: 18px;
        }}
        QPushButton:hover, QPushButton:checked {{
            color: {Colors.TEXT_MAIN};
            background-color: {Colors.WHITE};
            font-weight: bold;
        }}
    """