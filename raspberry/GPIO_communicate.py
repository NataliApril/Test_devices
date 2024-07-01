from gpiozero import LED, Button
from signal import pause
import time

class GPIO_communicate():
	''' read digital pin '''
	def read_pin(self, pin):
		button = Button(pin)
		return button.is_pressed
	
	''' write digital signal '''
	def write_pin(self, pin, val, t):
		led = LED(pin)
		if val > 0:
			led.on()
			time.sleep(t)
		else:
			led.off()
			time.sleep(t)
			
