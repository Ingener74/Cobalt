import json
import os
import sys

from PyQt5.QtCore import Qt, QThread, QMutex, QWaitCondition, QDateTime, pyqtSignal, QRegularExpression
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon, QListWidgetItem
from pynput.mouse import Listener, Button, Controller

from mainwidget import Ui_MainWidget
from selectrecord import Ui_WidgetSelectRecord
from startrecord import Ui_WidgetStartRecord


class Application(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)

        self.mouse = None
        self.main_widget = MainWidget()

        self.start_widget = StartRecordWidget()
        self.start_widget.on_start.connect(self.on_start_record)

        self.records = json.load(open('records.json', 'r')) if os.path.isfile('records.json') else []
        self.select_widget = SelectRecordWidget(None, records=self.records)
        self.select_widget.on_play_selected.connect(self.on_start_play)

        icon = QIcon(':/main/main.png')
        menu = QMenu()

        self.record_action = menu.addAction('Record')
        self.record_action.triggered.connect(self.start_widget.show)

        self.play_action = menu.addAction('Play')
        self.play_action.triggered.connect(self.select_widget.show)

        self.show_main_widget = menu.addAction('Show settings')
        self.show_main_widget.triggered.connect(self.main_widget.show)

        close_action = menu.addAction('Close')
        close_action.triggered.connect(self.quit)

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(icon)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def on_start_record(self, name, description):
        self.record_action.setEnabled(False)
        self.mouse = MouseThread(name=name, description=description)
        self.mouse.mouse_input_record_end.connect(self.on_end_record)
        self.mouse.mouse_input_saved.connect(self.on_save_record)
        self.mouse.start()
        self.mouse.record()

    def on_end_record(self, name, description):
        self.record_action.setEnabled(True)
        self.mouse.save()
        self.tray.showMessage('Запись с именем {} закончина'.format(name),
                              '''Запись: {}
Описание: {}'''.format(name, description),
                              QSystemTrayIcon.Information)

    def on_save_record(self, name, description, file_name):
        self.records.append({
            'name': name,
            'description': description,
            'file_name': file_name
        })
        self.select_widget.set_records(self.records)
        json.dump(self.records, open('records.json', 'w+'), indent=True)

    def on_start_play(self, record):
        self.mouse = MouseThread(record=self.records[record])
        self.mouse.mouse_input_play_end.connect(self.on_end_play)
        self.mouse.start()

    def on_end_play(self, name, description):
        self.tray.showMessage('Воспроизведение записи {} закончено'.format(name),
                              '''Запись: {}
Описание: {}'''.format(name, description),
                              QSystemTrayIcon.Information)


class MainWidget(QWidget, Ui_MainWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent, Qt.Window)
        self.setupUi(self)

    def keyPressEvent(self, q_key_event):
        if q_key_event.key() == Qt.Key_Escape:
            self.hide()

    def closeEvent(self, q_close_event):
        self.hide()
        q_close_event.ignore()


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

    def showEvent(self, q_show_event):
        self.lineEditName.clear()
        self.textEditDescription.clear()

    def closeEvent(self, q_close_event):
        self.hide()
        q_close_event.ignore()


class SelectRecordWidget(QWidget, Ui_WidgetSelectRecord):
    on_play_selected = pyqtSignal(int)

    def __init__(self, parent=None, records=[]):
        QWidget.__init__(self, parent, Qt.Window)
        self.setupUi(self)
        self.pushButtonStart.setEnabled(False)
        self.set_records(records)

        self.listWidgetSelect.itemClicked.connect(self.item_clicked)
        self.listWidgetSelect.itemDoubleClicked.connect(self.item_dbl_clicked)

    def set_records(self, records):
        for record in records:
            self.listWidgetSelect.addItem(QListWidgetItem(record['name'] + ': ' + record['description']))

    def closeEvent(self, q_close_event):
        self.hide()
        q_close_event.ignore()

    def keyPressEvent(self, q_key_event):
        if q_key_event.key() == Qt.Key_Escape:
            self.hide()

    def on_start_play(self):
        if self.listWidgetSelect.currentRow() >= 0:
            self.item_dbl_clicked()

    def item_clicked(self):
        self.pushButtonStart.setEnabled(self.listWidgetSelect.currentRow() >= 0)

    def item_dbl_clicked(self):
        self.on_play_selected.emit(self.listWidgetSelect.currentRow())
        self.hide()


class MouseThread(QThread):
    MOVE = 0
    CLICK = 1

    mouse_input_record_end = pyqtSignal(str, str)
    mouse_input_play_end = pyqtSignal(str, str)
    mouse_input_saved = pyqtSignal(str, str, str)

    def __init__(self, parent=None, name='', description='', record=None):
        QThread.__init__(self, parent)

        if record is None:
            self.name = name
            self.description = description
            self.events = None
        else:
            self.name = record['name']
            self.description = record['description']
            self.events = \
                json.load(open(record['file_name'], 'r+'))['events'] if os.path.isfile(record['file_name']) else []

        self.mutex = QMutex()
        self.cond = QWaitCondition()

    def on_move(self, x, y):
        if self.events is not None:
            self.events.append({'type': MouseThread.MOVE,
                                'x': x,
                                'y': y,
                                'ts': QDateTime.currentDateTime().toMSecsSinceEpoch()})

    def on_click(self, x, y, button, pressed):
        if self.events is not None:
            if button == Button.middle and pressed:
                self.mouse_input_record_end.emit(self.name, self.description)
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
                            Button.right if event['button'] == Button.right.value else Button.middle
                        if event['pressed']:
                            mouse.press(b)
                        else:
                            mouse.release(b)
            self.mouse_input_play_end.emit(self.name, self.description)

        else:
            with Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll) as listener:
                listener.join()

    def record(self):
        self.events = []

    def save(self):
        json_file_name = self.name + '_' + QDateTime.currentDateTime().toString('hh_mm_dd_MM_yyyy') + '.json'
        json.dump({'name': self.name,
                   'description': self.description,
                   'events': self.events}, open(json_file_name, 'w+'), indent=True)
        self.mouse_input_saved.emit(self.name, self.description, json_file_name)


app = Application(sys.argv)
sys.exit(app.exec_())
