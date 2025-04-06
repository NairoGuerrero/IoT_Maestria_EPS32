from conexion import ConexionWiFi
from conexion import Servidor
from manejo_dht22 import SensorDHT22
from manejo_MQTT import ConexionMQTT

from machine import Timer, Pin, reset


class MainProcess:
    def __init__(self):
        self.object_conexion_wifi = ConexionWiFi()
        self.object_conexion_mqtt = ConexionMQTT()
        self.object_servidor = Servidor()
        self.timer = Timer(0)  # Timer para validar conexión
        self.estado_reconexion = True
        self.pin_estado = Pin(14, Pin.IN, Pin.PULL_UP)
        self.pin_estado.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=self.handle_interrupt)

        self.mensaje = {
            "id":1,
            "dato_led": self.pin_estado.value()
        }

        self.reintentos = 0

    def handle_interrupt(self, pin):
        self.mensaje["dato_led"] = pin.value()
        print("Interrupción detectada en el pin:", pin.value())
        self.object_conexion_mqtt.publicar('NaA', self.mensaje)

    def run(self):
        is_conect = self.object_conexion_wifi.conectar() if self.estado_reconexion else True
        if is_conect:
            print("Conexión exitosa")
            cliente = self.object_conexion_mqtt.conectar()
            self.iniciar_verificacion()
            if cliente:
                self.object_conexion_mqtt.inicializar_MQTT()
                print('Conectado a MQTT')
        else:
            self.timer.init(period=60000*2, mode=Timer.PERIODIC, callback=self.quitar_servidor)
            print('Lanzando servidor...')
            self.object_servidor.lanzar()


    def verificar_conexion(self, t):
        """Función que verifica cada segundo si sigue conectado a WiFi."""
        if not self.object_conexion_wifi.wifi.isconnected():
            print("⚠️ Conexión perdida. Intentando reconectar...")
            self.object_conexion_wifi.led.off()
            self.object_conexion_mqtt.object_sensor.timer.deinit()  # Detener temporizador del sensor
            self.object_conexion_mqtt.prueba = False
            if self.object_conexion_wifi.conectar():  # Intentar reconectar
                self.object_conexion_mqtt.conectar()
                self.object_conexion_mqtt.inicializar_MQTT()
            else:
                self.reintentos += 1
                if self.reintentos >= 60:  # Si no se conecta en 1 minuto (60 segundos)
                    print("🔄 Reiniciando el microcontrolador...")
                    reset()  # Reiniciar el microcontrolador
        else:
            self.reintentos = 0  # Reiniciar el contador de reintentos si se conecta
            self.object_conexion_wifi.led.on()  # Mantener LED encendido si está conectado
    def iniciar_verificacion(self):
        """Inicia el Timer 0 para verificar la conexión cada segundo."""
        self.timer.init(period=1000, mode=Timer.PERIODIC, callback=self.verificar_conexion)

    def quitar_servidor(self, t):
        print("🔄 Reiniciando el microcontrolador para intentar reconectar...")
        reset()

