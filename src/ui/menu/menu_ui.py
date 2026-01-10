# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'menu.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QSpacerItem, QStackedWidget,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(1348, 640)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(180, 0))
        self.frame.setStyleSheet(u"background-color: #0C604F;")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, -1, 0)
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")
        self.label.setMinimumSize(QSize(0, 70))
        font = QFont()
        font.setFamilies([u"Kaushan Script"])
        font.setPointSize(28)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.customer_registration_btn = QPushButton(self.frame)
        self.customer_registration_btn.setObjectName(u"customer_registration_btn")
        self.customer_registration_btn.setMinimumSize(QSize(150, 50))
        font1 = QFont()
        font1.setPointSize(11)
        font1.setBold(True)
        self.customer_registration_btn.setFont(font1)
        self.customer_registration_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"    background-color: transparent;\n"
"    color: white;\n"
"    border: none;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"	qproperty-icon: url(\"assets/icons/customer_info_black_icon.png\");\n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")
        icon = QIcon()
        icon.addFile(u"../../../assets/icons/customer_info_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.customer_registration_btn.setIcon(icon)
        self.customer_registration_btn.setIconSize(QSize(32, 32))

        self.verticalLayout.addWidget(self.customer_registration_btn)

        self.sales_registration_btn = QPushButton(self.frame)
        self.sales_registration_btn.setObjectName(u"sales_registration_btn")
        self.sales_registration_btn.setMinimumSize(QSize(150, 50))
        self.sales_registration_btn.setFont(font1)
        self.sales_registration_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"    background-color: transparent;\n"
"    color: white;\n"
"    border: none;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")
        icon1 = QIcon()
        icon1.addFile(u"../../../assets/icons/sales_registration_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.sales_registration_btn.setIcon(icon1)
        self.sales_registration_btn.setIconSize(QSize(32, 32))

        self.verticalLayout.addWidget(self.sales_registration_btn)

        self.sales_statistics_btn = QPushButton(self.frame)
        self.sales_statistics_btn.setObjectName(u"sales_statistics_btn")
        self.sales_statistics_btn.setMinimumSize(QSize(150, 50))
        self.sales_statistics_btn.setFont(font1)
        self.sales_statistics_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"    background-color: transparent;\n"
"    color: white;\n"
"    border: none;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")
        icon2 = QIcon()
        icon2.addFile(u"../../../assets/icons/sales_statistics_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.sales_statistics_btn.setIcon(icon2)
        self.sales_statistics_btn.setIconSize(QSize(32, 32))

        self.verticalLayout.addWidget(self.sales_statistics_btn)

        self.setting_btn = QPushButton(self.frame)
        self.setting_btn.setObjectName(u"setting_btn")
        self.setting_btn.setMinimumSize(QSize(150, 50))
        self.setting_btn.setFont(font1)
        self.setting_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"    background-color: transparent;\n"
"    color: white;\n"
"    border: none;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")
        icon3 = QIcon()
        icon3.addFile(u"../../../assets/icons/setting_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.setting_btn.setIcon(icon3)
        self.setting_btn.setIconSize(QSize(32, 32))

        self.verticalLayout.addWidget(self.setting_btn)

        self.sub_menu_frame = QFrame(self.frame)
        self.sub_menu_frame.setObjectName(u"sub_menu_frame")
        self.sub_menu_frame.setStyleSheet(u"border: none;\n"
"\n"
"")
        self.sub_menu_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.sub_menu_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.sub_menu_frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, -1, -1, -1)
        self.auth_management_btn = QPushButton(self.sub_menu_frame)
        self.auth_management_btn.setObjectName(u"auth_management_btn")
        self.auth_management_btn.setMinimumSize(QSize(140, 40))
        font2 = QFont()
        font2.setPointSize(10)
        font2.setBold(True)
        self.auth_management_btn.setFont(font2)
        self.auth_management_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"    background-color: transparent;\n"
"    color: #000000;\n"
"    border: none;\n"
"	padding-left: 10px;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")

        self.verticalLayout_2.addWidget(self.auth_management_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.point_ratio_change_btn = QPushButton(self.sub_menu_frame)
        self.point_ratio_change_btn.setObjectName(u"point_ratio_change_btn")
        self.point_ratio_change_btn.setMinimumSize(QSize(140, 40))
        self.point_ratio_change_btn.setFont(font2)
        self.point_ratio_change_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"    background-color: transparent;\n"
"    color: #000000;\n"
"    border: none;\n"
"	padding-left: 10px;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")

        self.verticalLayout_2.addWidget(self.point_ratio_change_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.category_service_management_btn = QPushButton(self.sub_menu_frame)
        self.category_service_management_btn.setObjectName(u"category_service_management_btn")
        self.category_service_management_btn.setMinimumSize(QSize(140, 40))
        self.category_service_management_btn.setFont(font2)
        self.category_service_management_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"    background-color: transparent;\n"
"    color: #000000;\n"
"    border: none;\n"
"	padding-left: 10px;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")

        self.verticalLayout_2.addWidget(self.category_service_management_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.backup_btn = QPushButton(self.sub_menu_frame)
        self.backup_btn.setObjectName(u"backup_btn")
        self.backup_btn.setMinimumSize(QSize(140, 40))
        self.backup_btn.setFont(font2)
        self.backup_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"    background-color: transparent;\n"
"    color: #000000;\n"
"    border: none;\n"
"	padding-left: 10px;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")

        self.verticalLayout_2.addWidget(self.backup_btn, 0, Qt.AlignmentFlag.AlignLeft)

        self.pushButton_10 = QPushButton(self.sub_menu_frame)
        self.pushButton_10.setObjectName(u"pushButton_10")
        self.pushButton_10.setMinimumSize(QSize(140, 40))
        self.pushButton_10.setFont(font2)
        self.pushButton_10.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"    background-color: transparent;\n"
"    color: #000000;\n"
"    border: none;\n"
"	padding-left: 10px;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 10px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")

        self.verticalLayout_2.addWidget(self.pushButton_10, 0, Qt.AlignmentFlag.AlignLeft)


        self.verticalLayout.addWidget(self.sub_menu_frame)

        self.verticalSpacer = QSpacerItem(20, 29, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.exit_btn = QPushButton(self.frame)
        self.exit_btn.setObjectName(u"exit_btn")
        self.exit_btn.setMinimumSize(QSize(150, 50))
        self.exit_btn.setFont(font1)
        self.exit_btn.setStyleSheet(u"/* \uae30\ubcf8 \uc0c1\ud0dc */\n"
"QPushButton {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"    background-color: transparent;\n"
"    color: white;\n"
"    border: none;\n"
"}\n"
"\n"
"/* \ud638\ubc84(\ub9c8\uc6b0\uc2a4 \uc62c\ub838\uc744 \ub54c) \ubc0f \ud504\ub808\uc2a4(\ud074\ub9ad\ud588\uc744 \ub54c) \uc0c1\ud0dc */\n"
"QPushButton:hover, \n"
"QPushButton:pressed {\n"
"    text-align: left;\n"
"    padding-left: 20px;\n"
"	\n"
"    background-color: white;\n"
"    color: black;\n"
"    \n"
"    border-top-right-radius: 10px;\n"
"    border-bottom-right-radius: 10px;\n"
"}")
        icon4 = QIcon()
        icon4.addFile(u"../../../assets/icons/exit_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.exit_btn.setIcon(icon4)
        self.exit_btn.setIconSize(QSize(32, 32))

        self.verticalLayout.addWidget(self.exit_btn)


        self.horizontalLayout.addWidget(self.frame)

        self.stackedWidget = QStackedWidget(Form)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.page_9 = QWidget()
        self.page_9.setObjectName(u"page_9")
        self.frame_2 = QFrame(self.page_9)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setGeometry(QRect(0, 50, 2001, 20))
        font3 = QFont()
        font3.setUnderline(False)
        self.frame_2.setFont(font3)
        self.frame_2.setStyleSheet(u"color: #0C604F;")
        self.frame_2.setFrameShape(QFrame.Shape.HLine)
        self.frame_2.setFrameShadow(QFrame.Shadow.Plain)
        self.frame_2.setLineWidth(2)
        self.frame_2.setMidLineWidth(0)
        self.date_label = QLabel(self.page_9)
        self.date_label.setObjectName(u"date_label")
        self.date_label.setGeometry(QRect(40, 20, 201, 31))
        self.date_label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.stackedWidget.addWidget(self.page_9)
        self.page_10 = QWidget()
        self.page_10.setObjectName(u"page_10")
        self.stackedWidget.addWidget(self.page_10)

        self.horizontalLayout.addWidget(self.stackedWidget)


        self.retranslateUi(Form)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"HairMate", None))
        self.customer_registration_btn.setText(QCoreApplication.translate("Form", u"  \uace0\uac1d\uad00\ub9ac", None))
        self.sales_registration_btn.setText(QCoreApplication.translate("Form", u"  \ub9e4\ucd9c\ub4f1\ub85d", None))
        self.sales_statistics_btn.setText(QCoreApplication.translate("Form", u"  \ub9e4\ucd9c\ubd84\uc11d", None))
        self.setting_btn.setText(QCoreApplication.translate("Form", u"  \uc124\uc815", None))
        self.auth_management_btn.setText(QCoreApplication.translate("Form", u"\uad6c\uae00 \uacc4\uc815 \uc778\uc99d", None))
        self.point_ratio_change_btn.setText(QCoreApplication.translate("Form", u"\ud3ec\uc778\ud2b8 \uad00\ub9ac", None))
        self.category_service_management_btn.setText(QCoreApplication.translate("Form", u"\uc2dc\uc220 \uce74\ud14c\uace0\ub9ac \uad00\ub9ac", None))
        self.backup_btn.setText(QCoreApplication.translate("Form", u"\ubc31\uc5c5", None))
        self.pushButton_10.setText(QCoreApplication.translate("Form", u"\ubcf5\uc6d0", None))
        self.exit_btn.setText(QCoreApplication.translate("Form", u"  \uc885\ub8cc", None))
        self.date_label.setText(QCoreApplication.translate("Form", u"\ub0a0\uc9dc", None))
    # retranslateUi

