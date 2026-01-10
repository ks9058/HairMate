from .colors import PRIMARY_GREEN, WHITE, BLACK

# 로그인 화면 버튼 스타일 (기존 유지)
LOGIN_BUTTON_STYLE = f"""
    QPushButton {{
        border: 3px solid {PRIMARY_GREEN}; 
        border-radius: 10px;
        color: {BLACK};
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_GREEN};
        color: {WHITE};
    }}
    QPushButton:pressed {{
        color: {WHITE};
        background-color: {PRIMARY_GREEN};
    }}
"""

DASHBOARD_STYLE = f"""
    QMainWindow {{
        background-color: {WHITE};
    }}

    /* 사이드바 프레임 */
    QFrame#sidebar_frame {{
        background-color: {PRIMARY_GREEN};
        border: none;
    }}

    /* 1. 사이드바 버튼 공통 기본 스타일 */
    QFrame#sidebar_frame QPushButton {{
        text-align: left;
        padding-left: 20px;
        background-color: transparent;
        color: {WHITE};
        border: none;
        font-weight: bold;
        height: 50px;
        qproperty-iconSize: 24px 24px; /* 아이콘 크기 고정 */
    }}

    /* 2. 사이드바 버튼 공통 호버/클릭 효과 */
    QFrame#sidebar_frame QPushButton:hover, 
    QFrame#sidebar_frame QPushButton:pressed {{
        background-color: {WHITE};
        color: {BLACK};
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
    }}

    /* 3. 각 버튼별 아이콘 설정 (평상시 흰색 / 호버 시 검정색) */
    
    /* 고객관리 */
    QPushButton#customer_registration_btn {{ qproperty-icon: url(:/assets/icons/customer_info_icon.png); }}
    QPushButton#customer_registration_btn:hover {{ qproperty-icon: url(:/assets/icons/customer_info_black_icon.png); }}
    
    /* 매출등록 */
    QPushButton#sales_registration_btn {{ qproperty-icon: url(:/assets/icons/sales_registration_icon.png); }}
    QPushButton#sales_registration_btn:hover {{ qproperty-icon: url(:/assets/icons/sales_registration_black_icon.png); }}
    
    /* 매출통계 */
    QPushButton#sales_statistics_btn {{ qproperty-icon: url(:/assets/icons/sales_statistics_icon.png); }}
    QPushButton#sales_statistics_btn:hover {{ qproperty-icon: url(:/assets/icons/sales_statistics_black_icon.png); }}
    
    /* 설정 및 하위 버튼들 (나머지도 같은 방식으로 추가) */
    QPushButton#setting_btn {{ qproperty-icon: url(:/assets/icons/setting_icon.png); }}
    QPushButton#setting_btn:hover {{ qproperty-icon: url(:/assets/icons/setting_black_icon.png); }}

    /* 종료 버튼 */
    QPushButton#exit_btn {{ qproperty-icon: url(:/assets/icons/exit_icon.png); }}
    QPushButton#exit_btn:hover {{ qproperty-icon: url(:/assets/icons/exit_black_icon.png); }}

    /* 헤더 구분선 스타일 */
    QWidget#header_widget {{
        border-bottom: 1px solid {PRIMARY_GREEN};
    }}

    /* 날짜 라벨 스타일 설정 */
    QLabel#date_label {{
        color: #7A7A7A;  
        font-size: 16px;
        font-weight: bold;
        margin-right: 10px;
    }}
"""