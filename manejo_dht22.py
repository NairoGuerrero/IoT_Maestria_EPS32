import dht
import ujson
import machine

class SensorDHT22:
    def __init__(self, pin, funcion):

        self.funcion_publicar = funcion
        self.pin = pin
        self.sensor = dht.DHT22(machine.Pin(pin))
        self.mensaje = {
            'id': 1,
            'humedad': None,
            'temperatura': None,
            'action': 'response',
        }
        self.timer = machine.Timer(1)
        self.periodo = 6000  # Periodo inicial en milisegundos

    def publicar_sensor(self):
        data = ujson.dumps(self.mensaje)
        print(data)
        self.cliente.publish(self.topico, data)

    def medir(self, nose):
        try:
            print('📏 Tomando medidas...')
            self.sensor.measure()
            self.mensaje['temperatura'] = self.sensor.temperature()
            self.mensaje['humedad'] = self.sensor.humidity()
            self.verificar_rangos()  # Verifica si se debe cambiar el periodo
        except Exception as e:
            print(f'Error al leer el sensor DHT22: {e}')
            self.mensaje['temperatura'] = None
            self.mensaje['humedad'] = None

        self.funcion_publicar('NaA', self.mensaje)

    def verificar_rangos(self):
        """
        Ajusta la frecuencia de toma de muestras si los valores superan ciertos umbrales.
        """
        temp = self.mensaje['temperatura']
        hum = self.mensaje['humedad']

        if temp is None or hum is None:
            return  # No cambia el periodo si los valores no son válidos

        nuevo_periodo = self.periodo  # Mantiene el período actual por defecto

        # Reglas de ajuste dinámico
        if temp > 31 or hum > 90:
            nuevo_periodo = 2000  # Acelera la toma de muestras si hay valores altos
        else:
            nuevo_periodo = 6000  # Vuelve al valor estándar

        if nuevo_periodo != self.periodo:
            self.ajustar_periodo(nuevo_periodo)

    def ajustar_periodo(self, nuevo_periodo):
        """
        Reinicia el temporizador con un nuevo período si es diferente al actual.
        """
        self.timer.deinit()
        print(f'⚠️ Cambiando el período del temporizador a {nuevo_periodo / 1000} segundos')
        self.periodo = nuevo_periodo
        self.timer.init(period=self.periodo, mode=machine.Timer.PERIODIC, callback=self.medir)

    def inicializar_sensor(self):
        try:
            self.timer.init(period=self.periodo, mode=machine.Timer.PERIODIC, callback=self.medir)
            print('sensor inicializado')
        except Exception as e:
            print(f'Error al inicializar el temporizador: {e}')
