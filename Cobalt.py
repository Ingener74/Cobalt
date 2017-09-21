import json
import os
import sys

from PyQt5.QtCore import Qt, QThread, QMutex, QWaitCondition, QDateTime
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QSystemTrayIcon
from pynput.mouse import Listener, Button, Controller

from mainwidget import Ui_MainWidget


class MainWidget(QWidget, Ui_MainWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent, Qt.Window)
        self.setupUi(self)

    def keyPressEvent(self, q_key_event):
        if q_key_event.key() == Qt.Key_Escape:
            self.close()


class MouseThread(QThread):
    MOVE = 0
    CLICK = 1

    def __init__(self, events=None, parent=None):
        QThread.__init__(self, parent)

        self.rec = False
        self.events = events or []

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
            if button == Button.right and pressed:
                self.rec = False
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
                            if event['pressed']:
                                mouse.press(Button.left)
                            else:
                                mouse.release(Button.left)
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
        json.dump(self.events, open('record', 'w+'), indent=True)


def create_and_show_tray():
    icon = QIcon(':/main/main.png')
    menu = QMenu()

    do_action = menu.addAction('Record')
    do_action.triggered.connect(mouseThread.record)

    play_action = menu.addAction('Play')
    play_action.triggered.connect(mouseThread.play)

    show_main_widget = menu.addAction('Show settings')
    show_main_widget.triggered.connect(mainWidget.show)

    def on_close():
        mouseThread.save()
        mainWidget.close()

    close_action = menu.addAction('Close')
    close_action.triggered.connect(on_close)

    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setContextMenu(menu)
    tray.show()
    return tray


app = QApplication(sys.argv)

mainWidget = MainWidget()

mouseThread = MouseThread(json.load(open('record')) if os.path.isfile('record') else None)
mouseThread.start()

tray = create_and_show_tray()

sys.exit(app.exec_())
