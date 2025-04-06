"""
This module provides functions to connect to a WiFi network and to launch a server.

Functions:
    conexion_red() -> bool:
        Connects to a WiFi network using credentials from a configuration file.
        Returns True if the connection is successful, otherwise returns False.

    lanzar_servidor() -> None:
        Launches a server with a predefined SSID and password.
"""

import time
import network
import json
from machine import Pin
import machine
import socket
import re

import network
import json
import time
from machine import Pin
import network
import json
import time
from machine import Pin, Timer


class Servidor:
    def __init__(self, ssid='ESP_NAIRO', password='123456789'):
        self.red = network.WLAN(network.AP_IF)
        self.red.active(True)
        self.red.config(essid=ssid, password=password, authmode=3)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def lanzar(self):
        self.red.active(True)
        self.socket.bind(('', 80))
        self.socket.listen(3)
        print('Servidor lanzado')
        print('Servidor lanzado en la IP:', self.red.ifconfig()[0])
        while True:
            conn, addr = self.socket.accept()
            request = conn.recv(1024)
            request_str = str(request)
            print(f'Contenido del request: {request_str}')

            if 'GET' in request_str:
                with open('index.html', 'r') as file:
                    html_content = file.read()
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: text/html\n')
                conn.send('Connection: close\n\n')
                conn.sendall(html_content)

                pattern = r"nombre_red=([^&]+)&password=([^&\s]+)"
                match = re.search(pattern, request)

                if match is not None:
                    request_red = match.group(1)
                    request_password = match.group(2)
                    with open('config.txt', 'w') as file:
                        json.dump({'red': request_red, 'password': request_password}, file)
                        print(f'Credenciales guardadas: {request_red}, {request_password}')
                    break

            conn.close()
        machine.reset()


class ConexionWiFi:
    def __init__(self, config_file='config.txt'):
        self.config_file = config_file

        self.wifi = network.WLAN(network.STA_IF)

        self.led = Pin(2, Pin.OUT)

    def conectar(self):
        try:
            # Leer configuración WiFi
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                ssid = config.get('red')
                password = config.get('password')

            if not ssid or not password:
                raise ValueError("⚠️ El archivo de configuración no tiene SSID o contraseña")

        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️ Error al leer el archivo de configuración: {e}")
            return False

        try:
            self.wifi.active(True)

            # 🔎 Verificar si la red está disponible antes de conectar
            redes_disponibles = [net[0].decode() for net in self.wifi.scan()]
            if ssid not in redes_disponibles:
                print(f"❌ La red '{ssid}' no está disponible")
                return False

            self.wifi.connect(ssid, password)
            timeout = 15  # Tiempo máximo de espera

            for _ in range(timeout):


                if self.wifi.isconnected():
                    self.led.on()
                    print(f"✅ Conectado a {ssid} - IP: {self.wifi.ifconfig()[0]}")
                    return True


                print("Conectando...")
                self.led.on()
                time.sleep(0.5)
                self.led.off()
                time.sleep(0.5)

            print("⏳ Tiempo de espera agotado. No se pudo conectar.")
            return False

        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
