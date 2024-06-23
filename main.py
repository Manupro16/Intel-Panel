import ssl


class App:
    def __init__(self):
        self.cert_path = "riotgames.pem"
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    pass




if __name__ == '__main__':
    app = App()
