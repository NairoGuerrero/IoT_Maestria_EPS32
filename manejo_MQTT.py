import time

from umqtt.robust import MQTTClient
import machine
import ubinascii
import ujson
from _thread import start_new_thread
from manejo_dht22 import SensorDHT22

class ConexionMQTT:
    def __init__(self, host='test.mosquitto.org', puerto=1883):
        self.ID = ubinascii.hexlify(machine.unique_id())
        self.host = host
        self.puerto = puerto
        self.cliente = MQTTClient(self.ID, self.host, self.puerto, keepalive=5)
        self.cliente.DEBUG = True

        self.object_sensor = SensorDHT22(pin=13, funcion=self.publicar) ##Quitar

        self.prueba = True

        self.led = machine.Pin(16, machine.Pin.OUT)

        self.timer = machine.Timer(2)


    def publicar(self, topico, mensaje):
        try:
            # print('Mensaje a publicar: ', mensaje)
            self.cliente.publish(topico, ujson.dumps(mensaje))
        except OSError as e:
            print("Fallo al publicar, intentando reconectar:", e)
            if self.conectar():
                self.cliente.publish(topico, ujson.dumps(mensaje))

    def conectar(self, intentos_maximos=10):
        for intento in range(1, intentos_maximos + 1):
            try:
                print(f'[MQTT] Intento {intento} de {intentos_maximos}...')
                self.cliente.connect()
                print('[MQTT] Conexión exitosa.')
                return True
            except OSError as e:
                print(f'[MQTT] Error: {e}')
                time.sleep(3)

        print('[MQTT] ❌ No se pudo establecer conexión tras varios intentos.')
        print('[MQTT] Reiniciando el microcontrolador...')
        machine.reset()  # Reiniciar el microcontrolador

    def sub_cb(self, topic, msg):
        try:
            data = ujson.loads(msg)
            # print(data)
            if data.get('action') == 'response':
                valor = data.get('dato_led', None)
                if valor is not None:
                    self.led.value(valor)
            elif data.get('action') == 'request':
                if data.get('request_data') == 'estado_led':
                    estado = self.led.value()
                    respuesta = {
                        'action': 'response_led',
                        'dato_led': estado
                    }
                    self.publicar('NaA', respuesta)

                elif data.get('request_data') == 'estado_temperatura':

                    respuesta = {
                        'action': 'response_temperatura',
                        'dato_temperatura': self.object_sensor.sensor.temperature()
                    }
                    self.publicar('NaA', respuesta)

                elif data.get('request_data') == 'estado_humedad':
                    self.object_sensor.sensor.measure()
                    respuesta = {
                        'action': 'response_humedad',
                        'dato_humedad': self.object_sensor.sensor.humidity()
                    }
                    self.publicar('NaA', respuesta)

        except Exception as e:
            print('Error en callback:', e)

    def suscribir(self, topico):

        self.cliente.set_callback(self.sub_cb)
        print('Suscribiendose al Topico  ....')
        try:
            self.cliente.subscribe(topico)
            print('Suscripcion exitosa')
        except Exception as e:
            print('Error al suscribirse:', e)
            print('Intentando reconectar...')
            while not self.conectar():
                print('Reconexión fallida, reintentando en 5 segundos...')
                time.sleep(5)
            print('Reconexión exitosa, resuscribiendo al topico...')
            self.cliente.subscribe(topico)

        while self.prueba:
            try:
                self.cliente.check_msg()
            except OSError as e:
                print('Error con la conexion del cliente:', e)
                print('Intentando reconectar...')
                while not self.conectar():
                    print('Reconexión fallida, reintentando en 5 segundos...')
                    time.sleep(5)
                print('Reconexión exitosa, resuscribiendo al topico...')
                self.cliente.subscribe(topico)
            time.sleep(0.1)  # Evita saturar el microcontrolador

    def update_keep_alive(self, t):
        """
        Envía un mensaje de keep-alive cada 60 segundos.
        """
        if self.prueba:
            mensaje = {
                'action': 'keep-alive',
                'keep': 1
            }
            self.publicar('NaA', mensaje)
            # print('Mensaje de keep-alive enviado')
        else:
            self.timer.deinit()


    def inicializar_MQTT(self):
        self.prueba = True
        try:
            self.timer.init(period=1000, mode=machine.Timer.PERIODIC, callback=self.update_keep_alive)
        except Exception as e:
            print('Error al iniciar el temporizador:', e)
        self.object_sensor.inicializar_sensor()
        start_new_thread(self.suscribir, ('AaN',))  # Ejecutar en hilo secundario



