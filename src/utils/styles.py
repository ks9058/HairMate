from .colors import PRIMARY_GREEN, WHITE, BLACK

# 스타일 세트 (f-string 활용)
LOGIN_BUTTON_STYLE = f"""
    QPushButton {{
        border: 3px solid {PRIMARY_GREEN}; 
        border-radius: 10px;
        color: {BLACK};
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_GREEN};
    }}
    QPushButton:pressed {{
        color: {WHITE};
        background-color: {PRIMARY_GREEN};
    }}
"""
