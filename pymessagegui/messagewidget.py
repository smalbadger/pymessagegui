'''
Created on Mar 14, 2021

@author: smalb
'''
import sys
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QFormLayout,
    QPushButton, 
    QApplication,
    QLabel,
    QLineEdit,
)
from PySide6.QtCore import Slot
from pymessagelib import MessageBuilder, Nibbles, Bytes, Bits, Bit, Byte, Field

class PyMessageGuiWidget(QWidget):

    def __init__(self, definitions={}):
        
        super().__init__()
        
        self.cur_message = None
        
        self.top_level_layout = QHBoxLayout(self)
        self.msg_btn_layout = QVBoxLayout()
        self.field_layout = QFormLayout()
        self.top_level_layout.addLayout(self.msg_btn_layout)
        self.top_level_layout.addStretch()
        self.top_level_layout.addLayout(self.field_layout)
        self.top_level_layout.addStretch()
        
        self.builder = MessageBuilder(definitions)
        self.btn_classes = {}
        for msg in self.builder.message_classes:
            msg_btn = QPushButton(msg.__name__)
            self.btn_classes[msg_btn] = msg
            msg_btn.clicked.connect(self.show_fields)
            self.msg_btn_layout.addWidget(msg_btn)
        self.msg_btn_layout.addStretch()
        
        
    @Slot()
    def show_fields(self):
        
        # clear all fields
        while self.field_layout.rowCount():
            self.field_layout.removeRow(0)
            
        # render new fields
        self.cur_message = self.btn_classes[self.sender()]
        self.cur_field_mapping = {}
        for name, field in self.cur_message.format.items():
            name_widget = QLabel(name)
            edit_widget = QLineEdit()
            self.cur_field_mapping[name] = (name_widget, edit_widget)
            self.field_layout.addRow(name_widget, edit_widget)
        
        
        
if __name__ == '__main__':
    
    msg_fmts = {
        "GET_ADDR": {
            "id": Nibbles(4, value="x14"),
            "length": Nibbles(4, value=lambda id: id.render(fmt=Field.Format.Hex, pad_to_length=4)),
            "ptr": Bytes(4),
            "addr": Bits(11),
            "pad": Bits(3, value="b000"),
            "crc": Bytes(2, value=lambda ptr: ptr.render(fmt=Field.Format.Hex)[:5]),
        },
        "FILL_KEY": {
            "id": Nibbles(4, value="x0015"),
            "ptr": Bytes(3),
            "addr": Bits(2),
            "pad": Bits(4, value="b0000"),
            "crc": Bytes(4, value=lambda pad: pad.render()),
        },
        "WRITE_REGISTER_RESPONSE": {
            "mid": Nibbles(4, value="x1014"),
            "length": Bytes(2, value="x0001"),
            "success": Byte(),
        },
        "READ_REGISTER_REQUEST": {
            "mid": Nibbles(4, value="x0015"),
            "length": Bytes(2, value="x0004"),
            "addr": Bytes(4),
        },
        "READ_REGISTER_RESPONSE": {
            "mid": Nibbles(4, value="x0014", fmt=Field.Format.Hex),
            "length": Bytes(2, value="x0008"),
            "addr": Bytes(4),
            "data": Bytes(4),
        },
    }
    
    
    app = QApplication(sys.argv)
    t = PyMessageGuiWidget(msg_fmts)
    t.show()
    sys.exit(app.exec_())