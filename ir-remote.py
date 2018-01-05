# IR Raw implementation 

import machine , utime , sys , ujson , math
frameTimeout = 500000
def enable_ir_receiver( pin ):
	global ir_recv , ir_recv_buffer ,ir_lastInt , ir_lastMark
	ir_recv = machine.Pin( pin , machine.Pin.IN , machine.Pin.PULL_UP)
	ir_recv.irq (trigger = machine.Pin.IRQ_RISING|machine.Pin.IRQ_FALLING, handler=ir_recv_handler)
	ir_recv_buffer = []
	ir_lastInt = 0 #TODO
	ir_lastMark = 0 #TODO
	
def enable_ir_transmitter( pin ):
	global ir_transmitter	
	try :	
		ir_transmitter.deinit() #Solving redeclare bug
	except NameError:
		pass
	ir_transmitter = machine.PWM(machine.Pin(pin))
	ir_transmitter.freq(38000)
	
def ir_recv_handler(state):
	global ir_lastInt , ir_lastMark , ir_recv_buffer , ir_lastSpace
	deltaTime = math.floor((utime.ticks_us() - ir_lastInt)/100)*100	#beautify number
	#deltaTime = utime.ticks_us() - ir_lastInt
	ir_lastInt = utime.ticks_us() 
	if  not ir_recv.value():#record space
		ir_lastSpace = deltaTime
		ir_recv_buffer.append([ir_lastMark,ir_lastSpace])
		ir_lastMark = 0
		ir_lastSpace = 0
	else:#record mark
		ir_lastMark = deltaTime
		
def dataReady ():
	global ir_lastInt , ir_lastSpace , ir_lastMark
	if len(ir_recv_buffer) > 0 and utime.ticks_diff(utime.ticks_us(),ir_lastInt) > frameTimeout:
		if ir_lastMark != 0 or  ir_lastSpace != 0 :
			ir_recv_buffer.append([ir_lastMark,ir_lastSpace])
			ir_lastMark = 0
			ir_lastSpace = 0
		return True 
	# ===== Avoiding too big space time , constantly feeding
	if utime.ticks_diff(utime.ticks_us(),ir_lastInt) > frameTimeout and  len(ir_recv_buffer) == 0:
		ir_lastInt = utime.ticks_us() 
	return False 
def _mark(us):
  ir_transmitter.duty(512)
  utime.sleep_us(us)
def _space(us):
  ir_transmitter.duty(0)
  utime.sleep_us(us)



def fileExist(fileName):
	try:
		f = open(fileName, "r")
		exists = True
		f.close()
	except OSError:
		exists = False
	return exists

def learnIR ( cmd_name , protocol = None , length = None , thres = 10 , overwrite = False):
	#cmd_name is the name to be save in flash 
		# cmd_name = TOTO -> ir_TOTO.json
	#protocol if you have already know the protocol 
	#length if you already know the length  , usually > 50
	#thres is default to 10 , every command having length < 10 will be ignored 
	global ir_recv_buffer
	if fileExist('ir_'+cmd_name+'.json') == False or overwrite == True:
		while True :
			if dataReady() :
				#======= Condition =================
				dataNotValid = False
				if length != None and 	 len(ir_recv_buffer) != length :
					dataNotValid = False
				if len(ir_recv_buffer) < thres :
					dataNotValid = True
					
				#=====================================
				if dataNotValid == False: # good to go
					package_buffer = {}
					package_buffer['Protocol'] = 'UNKNOWN' #TODO
					package_buffer['Length'] = len(ir_recv_buffer)
					package_buffer['Frequency'] = 'UNKNOWN' #TODO
					package_buffer['Data'] = ir_recv_buffer
					print()
					print()
					print(ir_recv_buffer)
					print()
					print()
					package_buffer['Decode']= 'UNKNOWN' #TODO
					
					#=============== Sendable Data =========
					f= open('ir_'+cmd_name+'.json','w')
					f.write(ujson.dumps(package_buffer))
					print(ujson.dumps(package_buffer))
				
					f.close()
					#=============== Fast Recognise ========
					if fileExist('ir_all.json') == False :
						f = open ( 'ir_all.json' , "w") 
						f.close()
					
					f = open('ir_all.json','r')
					if len(f.read()) != 0 :
						list = ujson.loads(f.read())
						node = { 'name' : cmd_name , 'decode' : package_buffer['Decode'] }
						list.append(node)
						f.close()
						f = open('ir_all.json','w')
						f.write(ujson.dumps(list))
						f.close()
						list.clear()
						node.clear()
					#================= CLEAN ============
					
					ir_recv_buffer.clear()
					package_buffer.clear()
					#================= BREAK ============
					break
				
	else :
		print( "Command ", cmd_name , " has already learned ")
		return 
		
		

def sendIR ( cmd_name ) :
	if fileExist('ir_'+cmd_name+'.json'):
		f = open ( 'ir_'+cmd_name+'.json')
		data = ujson.loads(f.read())
		timings = data['Data']
		if data['Frequency'] == 'UNKNOWN':
			ir_transmitter.freq(38000)
		else :
			ir_transmitter(data['Frequency']))
		for i in range ( 0 , len(timings) ):
			_mark(timings[i][0])
			_space(timings[i][1])
		f.close()
	else :
		return None 
		
def send_ir ( buffer ):
	for i in range ( 0 , len(ir_recv_buffer) ):
		_mark(buffer[i][0])
		_space(buffer[i][1])
	#send a raw bufffer , example , send_ir(ir_recv_buffer)
		
enable_ir_receiver(16)
enable_ir_transmitter(17)

learnIR("motherfucker", overwrite = True)
sendIR('motherfucker')

while True :
	dataReady() # without this line , ir_recv_buffer will be memory leak
	# because this function determine when to stop based on frameTimeout
	# keep this function run in loop or timer
	sendIR('motherfucker')
