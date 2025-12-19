# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'login_screen.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_login(object):
    def setupUi(self, login):
        if not login.objectName():
            login.setObjectName(u"login")
        login.resize(1186, 883)
        font = QFont()
        font.setFamilies([u"\uc870\uc120\uad75\uc740\uace0\ub515"])
        font.setPointSize(18)
        font.setBold(True)
        login.setFont(font)
        login.setAutoFillBackground(False)
        login.setStyleSheet(u"")
        self.centralwidget = QWidget(login)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer = QSpacerItem(108, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setEnabled(True)
        self.label.setMinimumSize(QSize(0, 200))
        font1 = QFont()
        font1.setFamilies([u"Kaushan Script"])
        font1.setPointSize(56)
        font1.setBold(True)
        font1.setItalic(False)
        font1.setStyleStrategy(QFont.PreferDefault)
        self.label.setFont(font1)
        self.label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.label.setStyleSheet(u"color: #000000;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setMinimumSize(QSize(400, 50))
        self.pushButton.setMaximumSize(QSize(400, 200))
        font2 = QFont()
        font2.setFamilies([u"\ub9d1\uc740 \uace0\ub515"])
        font2.setPointSize(18)
        font2.setWeight(QFont.DemiBold)
        self.pushButton.setFont(font2)
        self.pushButton.setStyleSheet(u"")
        icon = QIcon()
        icon.addFile(u"../../../assets/icons/google_logo.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QSize(26, 26))

        self.verticalLayout.addWidget(self.pushButton, 0, Qt.AlignmentFlag.AlignHCenter)

        self.verticalSpacer_2 = QSpacerItem(108, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        login.setCentralWidget(self.centralwidget)

        self.retranslateUi(login)

        QMetaObject.connectSlotsByName(login)
    # setupUi

    def retranslateUi(self, login):
        login.setWindowTitle(QCoreApplication.translate("login", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("login", u"HairMate", None))
        self.pushButton.setText(QCoreApplication.translate("login", u"  \uad6c\uae00 \uacc4\uc815\uc73c\ub85c \ub85c\uadf8\uc778", None))
    # retranslateUi

