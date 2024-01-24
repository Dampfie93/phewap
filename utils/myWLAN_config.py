class WLANConfig:

    def __init__(self, ssid, pw, ip=None):
        self.ssid = ssid
        self.pw = pw
        self.ip = ip

wlan_list = [
    WLANConfig("UPC200548", "hjhSw7nsyjev"),    #0
    WLANConfig("UPC500540", "hjhSw7nsyjev"),    #1
    WLANConfig("Hotspot", "DiesIstEinHotspot")  #2
]

WLAN_DEFAULT = 0
WLAN_COUNTRY = "DE"