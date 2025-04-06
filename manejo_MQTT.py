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
        self.cliente = MQTTClient(self.ID, self.host, self.puerto)

        self.object_sensor = SensorDHT22(pin=13, funcion=self.publicar) ##Quitar

        self.prueba = True

        self.led = machine.Pin(16, machine.Pin.OUT)


    def publicar(self, topico, mensaje):
        print('Mensaje a publicar: ', mensaje)
        self.cliente.publish(topico, ujson.dumps(mensaje))

    def conectar(self):
        try:
            print('conectando..')
            self.cliente.connect()
            return self.cliente
        except OSError as e:
            print('ERROR : ', e)
            return False

    def sub_cb(self, topic, msg):

        data = ujson.loads(msg)
        print(f'{msg=}')
        self.led.value(data['dato_led'])

    def suscribir(self, topico):  ## Modificar esta funcion para poder recibir los datos del sensor ()

        self.cliente.set_callback(self.sub_cb)
        print('Suscribiendose al Topico....')
        self.cliente.subscribe(topico)
        print('Suscripcion exitosa')

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

    def inicializar_MQTT(self):
        # start_new_thread(self.publicar_estado, ('NaA',))
        self.object_sensor.inicializar_sensor() ##quitar
        self.prueba = True
        # self.suscribir(topico='AaN')
        start_new_thread(self.suscribir, ('AaN',))  # Ejecutar en hilo secundario



