#version = 2.0
from machine import *
from time import *
import sys
"""
	Platform Note :;
		ESP32 is a sensitive platform , limited memory , no allocation memory when in ISR
		Therefore , there is a pre_buffer bytearray to optimize runtime speed
		Also , don't use this with _thread , not sure why .
"""
class Remote:
	def __init__(self):
		# Initialize GPIO
		self.recv = Pin(26 , Pin.IN , Pin.PULL_UP)
		self.recv.irq(trigger = Pin.IRQ_RISING|Pin.IRQ_FALLING , handler = self._handler)
		self.pwm = PWM(Pin(25) , duty = 0 , freq = 38000)
		
		# Initialize Buffer , see ISR note !
		self.buffer = [0 for x in range(1000)]
		self.bin = 0
		self.length = 0
		
		# Initialize Timing Property
		self.prev_irq = 0
		
		# Initialize User Interface
		self.learning = None 
		self.event_list = {}
		
	def _handler(self , source):
		self.time = ticks_us()
		if self.prev_irq == 0:
			self.prev_irq = self.time
			self.length = 0
			return
		self.buffer[self.length] = ticks_diff(self.time , self.prev_irq)
		self.prev_irq = self.time
		self.length += 1
		
	def _routine(self):
		while True :
			sleep_ms(200)
			if ticks_diff(ticks_us(),self.prev_irq) > 200000 and self.length > 0 :
				self._debug()
				print('DECODED = [{},{}] '.format(self.decode()[1],self.length))
				
				#self._send ( self.buffer , self.length , 40 )
				
				self.length = 0
				self.prev_irq = 0
				for x in range(len(self.buffer)):
					self.buffer[x] = 0
	def _debug(self):
		print('__________________RECV  {}  ______ {} _______'.format(self.length , self.bin))
		for x in range(self.length//8) :
			for i in range(8):
				print(self.buffer[x*8+i] , end = '\t' if  self.buffer[x*8+i]*50 > 300 else '#\t')
			print()
		for x in range(self.length%8):
			print( self.buffer[self.length//8 + x] , end = '\t' if  self.buffer[self.length//8 + x]*50 > 300 else '#\t')
			
		print('------------------------------------------')
		
		
	"""
		
	"""
	# Learn the next message and then written to the file . This is non-blocking
	def learn (self , name ):
		self.learning = name
		
	def event(self , name):
		self.event_list[name] = self._load(name)
	
	def _load(self,name):
		pass
	def inside	( self,t , r ):
		# avoid string allocation !
		if t[0] == r[0] and t[1] == r[1] :
			return True
		if t[1] > r[1] :
			return False 
		for x in range(r[1]-t[1]+1):
			if 	(((((2**(r[1]-x-t[1]\
				)-1)|((2**x -1)<<(t[\
				1]+(r[1]-x-t[1]))))^\
				(2**r[1]-1))&r[0])>>\
				(r[1]-x-t[1]))==t[0]:
				return True
		return False	
		
	def send(self,packet,length = None , mul = 40):
		length = length or len(packet)
		self.recv.irq(trigger = 0 , handler = None) # Disable IRQ Receiving Channel
		p = packet
		# Heavily optimize needed
		sleep = sleep_us
		duty = self.pwm.duty
		n = 0 # prev
		b = ticks_diff
		c = ticks_us
		d = self.buffer
		for x in range(length):
			if x%2 == 0 :
				duty(512)
			else :
				duty(0)
			sleep( p[x]) 
		duty(0)
		sleep_ms(3) # magic
		self.recv.irq(trigger = Pin.IRQ_RISING|Pin.IRQ_FALLING , handler = self._handler) # Re-enable IRQ
	
	def decode(self):
		self.bin = 0
		m = 50000
		for x in range(self.length):
			m = min(self.buffer[x],m)
		for x in range(0,self.length,2):
			if self.buffer[x+1] > m*3 and self.buffer[x] > m*3:
				continue
			if self.buffer[x+1] > self.buffer[x]*3//2 :
				self.bin += 2**(x//2)
			else :
				pass
		return hex(self.bin) , bin(self.bin)
		
remote = Remote()	
remote._routine()
		
		
		
