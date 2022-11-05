
#!/usr/bin/env python

# this is what was used before to run script before options --> #run with sudo python3 main.py --led-rows=32 --led-cols=32 --led-chain=6 --led-slowdown-gpio=4 --led-pixel-mapper "Rotate:180"
# 
# 

#rgb matrix library
from samplebase import SampleBase
from rgbmatrix import graphics, RGBMatrix, RGBMatrixOptions
#async
import websockets
import asyncio
from asyncio import gather, run, Event
import subprocess
import socket
#generic
import json
import sys
import os
import re
import time
#import other files in same directory
import socketEvents as SE
import panelEffects as PE

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.chain_length = 6
options.pixel_mapper_config = "Rotate:180"
options.gpio_slowdown = 4

#state variable this is passed around to all of the async tasks to allow everything to access everything
state = {}
state["SE"] = SE   
state["PE"] = PE  
#user changable options
state["panelCenter"] = state["PE"].panelOption(32,128)
state["panelLeft"] = state["PE"].panelOption(0,32)
state["panelRight"] = state["PE"].panelOption(160,32)

#make the matrix obj
state["matrix"] = RGBMatrix(options = options)




state["panelCenter"].option_blackBackground = 1
state["panelCenter"].option_regularText = 1
state["panelCenter"].regularText_setFont(2) #0,1,2
state["panelCenter"].regularText_setColor(30,255,255)
state["panelCenter"].regularText_setScroll(1)
state["panelCenter"].regularText_setScrollSpeed(.5)
state["panelCenter"].regularText_setText("Test")

state["panelLeft"].option_blackBackground = 1
state["panelLeft"].option_emotexti = 1
state["panelLeft"].emotexti_setText("🎄")

state["panelRight"].option_blackBackground = 1
state["panelRight"].option_emotexti = 1
state["panelRight"].emotexti_setText("🎃")


state["panelRight"].option_regularText = 1
state["panelRight"].regularText_setScroll(0)
state["panelRight"].regularText_setText("potato")

            

async def handleLedMatrix(state):
    double_buffer = state["matrix"].CreateFrameCanvas()
    while True:
        double_buffer.Clear()
        state["panelCenter"].draw(double_buffer)
        state["panelLeft"].draw(double_buffer)
        state["panelRight"].draw(double_buffer)
        await asyncio.sleep(0.01) #this defines the refresh rate of the panels
        double_buffer = state["matrix"].SwapOnVSync(double_buffer)
        # state["matrix"].Clear()



async def consumer_handler(websocket,state):
    async for message in websocket:
        try:
            packet = json.loads(message)
            # print(packet)
            try:
                await SE.process_websocket_event(websocket,packet,packet["event"],state)
            except Exception as e:
                print("bad websocket packet, probably no event name: "+str(e))
        except Exception as e:
            print("failed to packet.loads: " + str(e))
            print("Here is the failed message: " + str(message))


async def producer_handler(websocket,state):
    while True:
        # do we need to brodcast anything all the time to everyone? 
        await asyncio.sleep(10)




def createHandler(state):
    async def handler(websocket, path) -> None:
        #read in global value state 
        state = getState()
        #await SE.sendPacketToWSClient(websocket,"updateFields",state) #send a packet here to do it one time on client connect
        register(websocket)
        # make the handlers
        consumer_task = asyncio.ensure_future(consumer_handler(websocket,state))
        producer_task = asyncio.ensure_future(producer_handler(websocket,state))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    return handler



import pyaudio

FORMAT = pyaudio.paInt16
RATE = 44100
CHANNELS = 1

def initMicrophone():
    device_index = find_input_device()
    print(device_index)
    stream = pa.open( format = FORMAT,
                  channels = 2,
                  rate = RATE,
                  input = True,
                  input_device_index = device_index,
                  frames_per_buffer = INPUT_FRAMES_PER_BLOCK)

async def processAudioSignal(state):
    pa = pyaudio.PyAudio()
    initMicrophone()

async def eventLoop(state):
    await gather(
        handleLedMatrix(state),
        websockets.serve(createHandler(state), "0.0.0.0", 1997),
        processAudioSignal(state),
    )

#execute the asyncio loop
run(eventLoop(state))
