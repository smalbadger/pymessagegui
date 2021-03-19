'''
Created on Mar 14, 2021

@author: smalb
'''
import sys
from copy import deepcopy
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QFormLayout,
    QPushButton, 
    QApplication,
    QLabel,
    QLineEdit,
    QLabel,
)
from PySide6.QtCore import Slot
from pymessagelib import MessageBuilder, Nibbles, Bytes, Bits, Bit, Byte, Field

class PyMessageGuiWidget(QWidget):

    def __init__(self, definitions={}):
        
        super().__init__()
        
        self.cur_message = None
        
        self.top_level_layout = QHBoxLayout(self)
        self.msg_btn_layout = QVBoxLayout()
        self.main_area_layout = QVBoxLayout()
        self.field_layout = QFormLayout()
        self.top_level_layout.addLayout(self.msg_btn_layout)
        self.top_level_layout.addStretch()
        self.top_level_layout.addLayout(self.main_area_layout)
        self.main_area_layout.addLayout(self.field_layout)
        self.msg_staging_label = QLabel()
        self.main_area_layout.addWidget(self.msg_staging_label)
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
        
        # Clear all fields
        while self.field_layout.rowCount():
            self.field_layout.removeRow(0)
            
        # Construct a message object
        self.cur_message_class = self.btn_classes[self.sender()]
        kwargs = {}
        for name, field in self.cur_message_class.format.items():
            if field.is_writable:
                kwargs[name] = 'b0'
        self.cur_message = self.cur_message_class(**kwargs)
        
        self.cur_field_mapping = {}
        for name, field in self.cur_message.get_field_name_mapping().items():
            name_widget = QLabel(f"{name} ({field._unit_length} {type(field).__name__})")
            edit_widget = QLineEdit()
            edit_widget.textChanged.connect(self.on_field_value_changed)
            edit_widget.field = field
            edit_widget.setText(field.render())
            
            if not field.is_writable:
                edit_widget.setEnabled(False)
                
            self.cur_field_mapping[name] = (name_widget, edit_widget)
            self.field_layout.addRow(name_widget, edit_widget)
        
    @Slot()
    def on_field_value_changed(self):
        new_text = self.sender().text()
        valid = self.sender().field.value_is_valid(new_text)
        
        # Determine if there are any bad fields - update the good fields
        all_good = True
        for nw, fw in self.cur_field_mapping.values():
            text = fw.text()
            field = fw.field
            if field.value_is_valid(text):
                color = "green"
                if field.is_writable:
                    self.cur_message.__setattr__(fw.field.name, text)
            else:
                color = "red"
                all_good = False
                
            all_colors = f"{color} {color} {color} {color}"
            fw.setStyleSheet(f"QLineEdit{{ border-width: 1px; border-style: solid; border-color: {all_colors};}}");
        
        for nw, fw in self.cur_field_mapping.values():
            if self.sender() is not fw:
                fw.setText(fw.field.render())
        
        # Update the staged message label
        if all_good:
            color = "green"
            staged_msg = self.cur_message.render()
        else:
            color = "red"
            staged_msg = "INVALID MESSAGE DATA"
        self.msg_staging_label.setText(staged_msg)
        self.msg_staging_label.setStyleSheet(f"QLabel {{color : {color}; }}");
        
        
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