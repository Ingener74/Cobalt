import json
import os
import sys

from PyQt5.QtCore import Qt, QThread, QMutex, QWaitCondition, QDateTime, pyqtSignal, QRegularExpression
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon, QMessageBox
from pynput.mouse import Listener, Button, Controller

from mainwidget import Ui_MainWidget
from selectrecord import Ui_WidgetSelectRecord
from startrecord import Ui_WidgetStartRecord


class MainWidget(QWidget, Ui_MainWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent, Qt.Window)
        self.setupUi(self)

        self.mouse = None
        self.start_widget = StartRecordWidget(self)
        self.start_widget.on_start.connect(self.on_start_record)

        self.select_widget = SelectRecordWidget(self)

        self.records = json.load(open('records.json', 'r')) if os.path.isfile('records.json') else []

    def keyPressEvent(self, q_key_event):
        if q_key_event.key() == Qt.Key_Escape:
            self.close()

    def on_record_end(self):
        self.mouse.save()
        QMessageBox.critical(None, 'Info', 'Record recorded')

    def on_record_saved(self, name, description, file_name):
        self.records.append({
            'name': name,
            'description': description,
            'file_name': file_name
        })
        json.dump(self.records, open('records.json', 'w+'), indent=True)

    def on_start_record(self, name, description):
        self.mouse = MouseThread(name=name, description=description)
        self.mouse.record_end.connect(self.on_record_end)
        self.mouse.record_saved.connect(self.on_record_saved)
        self.mouse.start()
        self.mouse.record()


class StartRecordWidget(QWidget, Ui_WidgetStartRecord):
    on_start = pyqtSignal(str, str)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent, Qt.Window)
        self.setupUi(self)
        self.re = QRegularExpression('[_a-zA-Z0-9]+')
        self.pushButtonStart.clicked.connect(self.on_start_clicked)
        self.pushButtonStart.setEnabled(False)
        self.lineEditName.textChanged.connect(self.on_name_changed)

    def on_start_clicked(self):
        if len(self.lineEditName.text()) > 0:
            self.on_start.emit(self.lineEditName.text(), self.textEditDescription.toPlainText())
            self.hide()

    def on_name_changed(self, text):
        match = self.re.match(text)
        match_captured_text = match.hasMatch() and match.captured(0) == text
        self.pushButtonStart.setEnabled(match_captured_text)
        self.lineEditName.setStyleSheet('background-color: #48FA7E' if match_captured_text else
                                        'background-color: #FA4848')

    def keyPressEvent(self, q_key_event):
        if q_key_event.key() == Qt.Key_Escape:
            self.hide()

    def closeEvent(self, q_close_event):
        self.hide()
        q_close_event.ignore()


class SelectRecordWidget(QWidget, Ui_WidgetSelectRecord):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent, Qt.Window)
        self.setupUi(self)
        self.pushButtonStart.setEnabled(False)

    def closeEvent(self, q_close_event):
        self.hide()
        q_close_event.ignore()

    def keyPressEvent(self, q_key_event):
        if q_key_event.key() == Qt.Key_Escape:
            self.hide()


class MouseThread(QThread):
    MOVE = 0
    CLICK = 1

    record_end = pyqtSignal()
    record_saved = pyqtSignal(str, str, str)

    def __init__(self, parent=None, name='', description='', record=None):
        QThread.__init__(self, parent)

        self.rec = False
        if record is None:
            self.name = name
            self.description = description
            self.events = []
        else:
            self.name = record['name']
            self.description = record['description']
            self.events = record['events']

        self.mutex = QMutex()
        self.cond = QWaitCondition()

    def on_move(self, x, y):
        if self.rec:
            self.events.append({'type': MouseThread.MOVE,
                                'x': x,
                                'y': y,
                                'ts': QDateTime.currentDateTime().toMSecsSinceEpoch()})

    def on_click(self, x, y, button, pressed):
        if self.rec:
            if button == Button.middle and pressed:
                self.rec = False
                self.record_end.emit()
                return False
            self.events.append({'type': MouseThread.CLICK,
                                'x': x,
                                'y': y,
                                'button': button.value,
                                'pressed': pressed,
                                'ts': QDateTime.currentDateTime().toMSecsSinceEpoch()})
        if not pressed:
            return True

    def on_scroll(self, x, y, dx, dy):
        pass

    def run(self):
        if len(self.events) > 0:
            mouse = Controller()

            try:
                self.mutex.lock()
                self.cond.wait(self.mutex)

                if len(self.events) > 0:
                    mouse.position = (self.events[0]['x'], self.events[0]['y'])

                def next_event():
                    for idx, event in enumerate(self.events):
                        if idx < len(self.events) - 1:
                            QThread.msleep(self.events[idx + 1]['ts'] - self.events[idx]['ts'])
                            event['x'] = self.events[idx + 1]['x'] - event['x']
                            event['y'] = self.events[idx + 1]['y'] - event['y']
                            yield event
                    return None

                for event in next_event():
                    if event is not None:
                        if event['type'] == MouseThread.MOVE:
                            mouse.move(event['x'], event['y'])
                        elif event['type'] == MouseThread.CLICK:
                            b = Button.left if event['button'] == Button.left.value else \
                                Button.right if event['button'] == Button.right.value else \
                                    Button.middle
                            if event['pressed']:
                                mouse.press(b)
                            else:
                                mouse.release(b)
            finally:
                self.mutex.unlock()
        else:
            with Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll) as listener:
                listener.join()

    def record(self):
        self.rec = True

    def play(self):
        if len(self.events) > 0:
            self.cond.wakeOne()

    def save(self):
        json_file_name = self.name + '_' + QDateTime.currentDateTime().toString('hh_mm_dd_MM_yyyy') + '.json'
        json.dump({'name': self.name,
                   'description': self.description,
                   'events': self.events}, open(json_file_name, 'w+'), indent=True)
        self.record_saved.emit(self.name, self.description, json_file_name)


def create_and_show_tray():
    icon = QIcon(':/main/main.png')
    menu = QMenu()

    do_action = menu.addAction('Record')
    do_action.triggered.connect(main_widget.start_widget.show)

    play_action = menu.addAction('Play')
    play_action.triggered.connect(main_widget.select_widget.show)

    show_main_widget = menu.addAction('Show settings')
    show_main_widget.triggered.connect(main_widget.show)

    def on_close():
        main_widget.close()

    close_action = menu.addAction('Close')
    close_action.triggered.connect(on_close)

    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setContextMenu(menu)
    tray.show()
    return tray


app = QApplication(sys.argv)

main_widget = MainWidget()

tray = create_and_show_tray()

sys.exit(app.exec_())
