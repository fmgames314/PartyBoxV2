import asyncio
import time
import websockets
import json
import requests
import pyaudio
import math
import sys
import numpy as np
import struct

state = {}

# Audio Format (check Audio MIDI Setup if on Mac)
FORMAT = pyaudio.paInt16
RATE = 44100
CHANNELS = 1
# Set these parameters (How much data to plot per FFT)
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
high_cutoff = 500
coeff_for_cutoff = 1.01459

    
def connectToAudioStream(state):
    if miniDspIndex == -1:
        print("Failed to load miniDSP input. is it plugged in?")
    else:
        state["stream"] = p.open( format = FORMAT,
                          channels = 1,
                          rate = RATE,
                          input = True,
                          input_device_index = miniDspIndex,
                          frames_per_buffer = INPUT_FRAMES_PER_BLOCK)





def streamAudioIn(state):
    try:
        block = state["stream"].read(INPUT_FRAMES_PER_BLOCK)
        count = len(block)/2
        format = "%dh"%(count)
        shorts = struct.unpack( format, block )
        if CHANNELS == 1:
          return np.array(shorts)
        else:
          l = shorts[::2]
          r = shorts[1::2]
          return np.array(l)
    except:
        connectToAudioStream(state)
        return streamAudioIn(state)

def exponentially_bucket( arr, coeff):
    buckets = []
    previous_index = 0
    for i in range(0, 128):
      index = int((coeff**i)) + previous_index
      buckets.append(arr[previous_index+1:index+1])
      previous_index = index
    return buckets

def average_buckets( buckets):
    averages = []
    for bucket in buckets:
      if len(bucket) != 0:
        averages.append(max(bucket))
      else:
        averages.append(0)
    return averages
def get_spectrum( data):
    T = 1.0/RATE
    N = data.shape[0]
    Pxx = (1./N)*np.fft.fft(data)
    # Not the real size, this is actually 2205. The first and second halves of the
    # data are a mirror image of one another so you can throw away the second half.
    # The full size of the spectrum is 1102 but we're ignoring the real highs.
    Pxx = Pxx[0:1102]
    return (np.absolute(Pxx)).tolist()
def scale_buckets( data, min_value, max_value):
    res = []
    max_allowed = 29
    min_allowed = 1
    for x in data:
      res.append((max_allowed - min_allowed) * (x - min_value) / (max_value - min_value) + min_allowed)
    return res

def readAudio(state):
    data = streamAudioIn(state)
    Pxx = get_spectrum(data)
    max_value = max(Pxx)
    min_value = min(Pxx)
    PxxTop = Pxx[high_cutoff:]
    Pxx = Pxx[0:high_cutoff]
    Pxx = exponentially_bucket(Pxx, coeff_for_cutoff)
    # Add all of the really highs to the last bucket
    Pxx[-1] = Pxx[-1] + PxxTop
    Pxx = average_buckets(Pxx)  
    # Turn off all LEDS if there is an extremely low audio input
    if max_value > .2:
        Pxx = scale_buckets(Pxx, min_value, max_value)
    else:
        Pxx = np.zeros(len(Pxx))
    columns = []
    for col in Pxx:
        col = round(col,2)
        columns.append(col)
    output_dict = {"data":columns}
    return output_dict



async def sendPacketToWSClient(websocket,eventName,inputDict):
    try:
        inputDict["event"] = eventName
        json_out = json.dumps(inputDict)
        await websocket.send(str(json_out))
    except Exception as e:
        print("couldn't send data to websocket" + str(e))

async def consumer_handler(websocket,state):
    try:
        async for message in websocket:
            try:
                packet = json.loads(message)
                try:
                    print(packet)
                    # FOR A SENSOR WE DONT CARE WHAT SERVER SAYS
                    # if packet["event"] == "control":
                    #     device_name = packet["device_name"]
                    #     power_state = packet["power_state"]
                    #     await power_device(state,device_name,power_state)
                except Exception as e:
                    print("bad websocket packet, probably no event name: "+str(e))
            except Exception as e:
                print("failed to packet.loads: " + str(e))
                print("Here is the failed message: " + str(message))
    except:
        print("websocket died? reset?")
        return 0


async def producer_handler(websocket,state):
    while True:
        try:
            output_dict = readAudio(state)
            await sendPacketToWSClient(websocket,"spectrum_data",output_dict)
            await asyncio.sleep(.001)
        except Exception as e:
            print("failed to send a websocket packet: " + str(e))
            await asyncio.sleep(30)




async def websocket_connection(state):
    while True:
        print("starting websocket connection")
        try:
            uri = "ws://localhost:1997"
            async with websockets.connect(uri) as websocket:
                status = await handler(websocket,state)
        except Exception as e:
            print("Problem with websocket: error: "+str(e))
            await asyncio.sleep(1)


async def handler(websocket,state):
    consumer_task = asyncio.ensure_future(consumer_handler(websocket,state))
    producer_task = asyncio.ensure_future(producer_handler(websocket,state))
    done, pending = await asyncio.wait([consumer_task, producer_task],return_when=asyncio.FIRST_COMPLETED,)
    for task in pending:
        task.cancel()
        return 0



########################################main start of script##########################################
#make pyaudio object and otehr variables
p = pyaudio.PyAudio()
miniDspIndex = -1
#find where the mini dsp is
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            if "miniDSP" in p.get_device_info_by_host_api_device_index(0, i)["name"]:
                miniDspIndex = i
connectToAudioStream(state)

#loop stuff
loop = asyncio.get_event_loop()
loop.create_task(websocket_connection(state))
loop.run_forever()
