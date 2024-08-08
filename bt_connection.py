import bluetooth
from PyQt5 import QtCore


class BluetoothWorker(QtCore.QThread):
    connection_status = QtCore.pyqtSignal(bool, str)  # Emit True/False and message

    def __init__(self, target_name="LolinD32"):
        super().__init__()
        self.target_name = target_name
        self.sock = None

    def run(self):
        nearby_devices = bluetooth.discover_devices(duration=4, lookup_names=True)
        adresa = ""

        for addr, name in nearby_devices:
            if name == "LolinD32":
                adresa = addr

        if adresa is None:
            self.connection_status.emit(False, "LolinD32 nije pronađen")
            return

        port = 1  # Standard port for RFCOMM
        try:
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.connect((addr, port))
            self.connection_status.emit(True, "Spojen na LolinD32")
        except:
            self.connection_status.emit(False, "Nema konekcije")
