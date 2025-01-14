from PyQt5 import QtWidgets
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException
import sys
import json
import os

class ModbusReaderApp(QtWidgets.QMainWindow):
    CONFIG_FILE = "modbus_config.json"

    def __init__(self):
        super(ModbusReaderApp, self).__init__()
        self.init_ui()

        self.client = None
        self.load_config()
        self.update_fields()

    def init_ui(self):
        self.setWindowTitle("Modbus Reader")

        # Main layout
        main_layout = QtWidgets.QVBoxLayout()

        # Connection Configuration
        config_group = QtWidgets.QGroupBox("Connection Configuration")
        config_layout = QtWidgets.QFormLayout()

        self.protocol_combo = QtWidgets.QComboBox()
        self.protocol_combo.addItems(["TCP/IP", "RTU"])
        self.protocol_combo.currentTextChanged.connect(self.update_fields)
        config_layout.addRow("Protocol:", self.protocol_combo)

        self.host_input = QtWidgets.QLineEdit("127.0.0.1")
        config_layout.addRow("IP Address (TCP/IP) / Serial Port (RTU):", self.host_input)

        self.port_input = QtWidgets.QLineEdit("502")
        config_layout.addRow("Port (TCP/IP) / Baudrate (RTU):", self.port_input)

        self.slave_id_input = QtWidgets.QSpinBox()
        self.slave_id_input.setRange(1, 255)
        self.slave_id_input.setValue(1)
        config_layout.addRow("Slave ID:", self.slave_id_input)

        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Register Configuration
        register_group = QtWidgets.QGroupBox("Register Configuration")
        register_layout = QtWidgets.QFormLayout()

        self.start_address_input = QtWidgets.QSpinBox()
        self.start_address_input.setRange(0, 65535)
        self.start_address_input.setValue(0)
        register_layout.addRow("Start Address:", self.start_address_input)

        self.register_count_input = QtWidgets.QSpinBox()
        self.register_count_input.setRange(1, 125)
        self.register_count_input.setValue(10)
        register_layout.addRow("Number of Registers:", self.register_count_input)

        self.operation_combo = QtWidgets.QComboBox()
        self.operation_combo.addItems(["Read Coils", "Read Discrete Inputs", "Read Holding Registers", "Read Input Registers"])
        register_layout.addRow("Operation:", self.operation_combo)

        register_group.setLayout(register_layout)
        main_layout.addWidget(register_group)

        # Read Button
        self.read_button = QtWidgets.QPushButton("Read Data")
        self.read_button.clicked.connect(self.read_data)
        main_layout.addWidget(self.read_button)

        # Results Table
        self.result_table = QtWidgets.QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["Register Address", "Value"])
        main_layout.addWidget(self.result_table)

        # Set Main Widget
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_fields(self):
        protocol = self.protocol_combo.currentText()
        if protocol == "TCP/IP":
            self.host_input.setPlaceholderText("IP Address")
            self.port_input.setPlaceholderText("Port")
            self.host_input.setText("127.0.0.1")
            self.port_input.setText("502")
        elif protocol == "RTU":
            self.host_input.setPlaceholderText("Serial Port")
            self.port_input.setPlaceholderText("Baudrate")
            self.host_input.setText("COM1")
            self.port_input.setText("9600")

    def read_data(self):
        protocol = self.protocol_combo.currentText()
        host = self.host_input.text()
        port = int(self.port_input.text())
        slave_id = self.slave_id_input.value()
        start_address = self.start_address_input.value()
        register_count = self.register_count_input.value()
        operation = self.operation_combo.currentText()

        self.save_config()  # Save configuration before attempting to read data

        try:
            # Initialize client
            if protocol == "TCP/IP":
                self.client = ModbusTcpClient(host, port=port)
            elif protocol == "RTU":
                self.client = ModbusSerialClient(port=host, baudrate=port, timeout=1)

            if not self.client.connect():
                QtWidgets.QMessageBox.critical(self, "Connection Error", "Failed to connect to the Modbus device.")
                return

            # Perform selected operation
            if operation == "Read Coils":
                response = self.client.read_coils(start_address, register_count, slave=slave_id)
            elif operation == "Read Discrete Inputs":
                response = self.client.read_discrete_inputs(start_address, register_count, slave=slave_id)
            elif operation == "Read Holding Registers":
                response = self.client.read_holding_registers(start_address, register_count, slave=slave_id)
            elif operation == "Read Input Registers":
                response = self.client.read_input_registers(start_address, register_count, slave=slave_id)

            if response.isError():
                QtWidgets.QMessageBox.critical(self, "Modbus Error", str(response))
                return

            # Display results
            self.result_table.setRowCount(0)
            for i, value in enumerate(response.bits if operation in ["Read Coils", "Read Discrete Inputs"] else response.registers):
                self.result_table.insertRow(i)
                self.result_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(start_address + i)))
                self.result_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(value)))

        except ModbusException as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

        finally:
            if self.client:
                self.client.close()

    def save_config(self):
        config = {
            "protocol": self.protocol_combo.currentText(),
            "host": self.host_input.text(),
            "port": self.port_input.text(),
            "slave_id": self.slave_id_input.value(),
            "start_address": self.start_address_input.value(),
            "register_count": self.register_count_input.value(),
            "operation": self.operation_combo.currentText()
        }
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                config = json.load(f)
                self.protocol_combo.setCurrentText(config.get("protocol", "TCP/IP"))
                self.host_input.setText(config.get("host", "127.0.0.1"))
                self.port_input.setText(config.get("port", "502"))
                self.slave_id_input.setValue(config.get("slave_id", 1))
                self.start_address_input.setValue(config.get("start_address", 0))
                self.register_count_input.setValue(config.get("register_count", 10))
                self.operation_combo.setCurrentText(config.get("operation", "Read Holding Registers"))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = ModbusReaderApp()
    main_window.show()
    sys.exit(app.exec_())
