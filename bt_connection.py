import bluetooth
from PyQt5 import QtCore


class BluetoothWorker(QtCore.QThread):
    connection_status = QtCore.pyqtSignal(bool, str)  # Emitiraj True/False i poruku

    def __init__(self):
        super().__init__()
        self.sock = None

    # Pronalaženje i spajanje na bluetooth uređaj 
    def run(self):
        nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
        adresa = ""

        for addr, name in nearby_devices:
            if name == "LolinD32":
                adresa = addr          # Postavljanje bluetooth adrese mikrokontrolera

        if adresa is None:
            self.connection_status.emit(False, "LolinD32 nije pronađen")
            return

        port = 1  # Standard port for RFCOMM
        try:
            self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.sock.connect((addr, port))
            self.connection_status.emit(True, "Spojen na LolinD32")
        except:
            self.connection_status.emit(False, "Neuspješno")
