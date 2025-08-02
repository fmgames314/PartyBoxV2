
#!/usr/bin/env python

# this is what was used before to run script before options --> #run with sudo python3 main.py --led-rows=32 --led-cols=32 --led-chain=6 --led-slowdown-gpio=4 --led-pixel-mapper "Rotate:180"
# 
# 

#rgb matrix library
from rgbmatrix import graphics, RGBMatrix, RGBMatrixOptions
#async
import websockets
import asyncio
from asyncio import gather, run, Event
import subprocess
import base64
from PIL import Image
import socket
import aiohttp
#generic
import json
import sys
import os
import re
import time
#import other files in same directory
import socketEvents as SE
import panelEffects as PE
import dspApi as DSP

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
state["DSP"] = DSP  
#system variables
state["listOfWebsocks"] = []
state["listOfBrowersClients"] = []
#rgb panel variables
state["panelCenter"] = state["PE"].panelOption(32,128)
state["panelLeft"] = state["PE"].panelOption(0,32)
state["panelRight"] = state["PE"].panelOption(160,32)
state["fftData"] = []
#dsp settings
state["DSP_preset"] = -1
state["DSP_source"] = "Unknown"
state["DSP_volume"] = 1
state["DSP_mute"] = "Unknown"
state["DSP_db_input"] = [-200,-200]
state["DSP_db_output"] = [-200,-200,-200,-200] 
#make the matrix obj
state["matrix"] = RGBMatrix(options = options)




state["panelCenter"].option_blackBackground = 1
state["panelCenter"].option_regularText = 1
state["panelCenter"].regularText_setFont(2) #0,1,2
state["panelCenter"].regularText_setColor(120,120,120)
state["panelCenter"].regularText_setScroll(1)
state["panelCenter"].regularText_setScrollSpeed(.7)
state["panelCenter"].regularText_setText("Party Box!")

state["panelCenter"].option_fft = 1
state["panelCenter"].option_fftCircles = 1
state["panelCenter"].emotexti_setText("💣")

state["panelLeft"].option_fft = 0
state["panelRight"].option_fft = 0

state["panelLeft"].option_blackBackground = 1
state["panelLeft"].option_emotexti = 1
state["panelLeft"].emotexti_setText("🎉")

state["panelRight"].option_blackBackground = 1
state["panelRight"].option_emotexti = 1
state["panelRight"].emotexti_setText("📦")


# state["panelRight"].option_regularText = 1
# state["panelRight"].regularText_setScroll(0)
# state["panelRight"].regularText_setText("potato")

            


async def handleLedMatrix(state):
    # Build and broadcast a PIL framebuffer each frame for exact parity (60 fps target)
    double_buffer = state["matrix"].CreateFrameCanvas()
    while True:
        try:
            # Compose in PIL first
            fb_img = Image.new("RGB", (192, 32), (0,0,0))

            # Draw panels into the image
            try:
                state["panelCenter"].draw_to_image(fb_img, state)
                state["panelLeft"].draw_to_image(fb_img, state)
                state["panelRight"].draw_to_image(fb_img, state)
            except Exception as e:
                # in case the new method isn't present, fall back to legacy drawing
                double_buffer.Clear()
                state["panelCenter"].draw(double_buffer,state)
                state["panelLeft"].draw(double_buffer,state)
                state["panelRight"].draw(double_buffer,state)

            # Push the composed image to the LED matrix
            try:
                double_buffer.SetImage(fb_img, 0, 0)
            except Exception:
                # Some builds require SetImage(image) without offsets; try that
                try:
                    double_buffer.SetImage(fb_img)
                except Exception:
                    pass

            # Broadcast framebuffer to any connected UIs (RGB888 base64)
            try:
                raw = fb_img.tobytes()
                b64 = base64.b64encode(raw).decode("ascii")
                await SE.sendToAllBrowsersGuis(state, "framebuffer", {"w": 192, "h": 32, "data": b64})
            except Exception as e:
                # non-fatal
                pass

            # Swap to hardware and sleep ~1/60s
            double_buffer = state["matrix"].SwapOnVSync(double_buffer)
            await asyncio.sleep(1/60.0)
        except Exception as e:
            # keep running
            await asyncio.sleep(1/60.0)





async def postLoop(state):
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                miniDspUrl = 'http://127.0.0.1:5380/devices/0'
                async with session.get(miniDspUrl) as resp:
                    dspData = await resp.json()
                    state["DSP_preset"] = dspData["master"]["preset"]
                    state["DSP_source"] = dspData["master"]["source"]
                    state["DSP_volume"] = dspData["master"]["volume"]
                    state["DSP_mute"] = dspData["master"]["mute"]
                    state["DSP_db_input"] = dspData["input_levels"]
                    state["DSP_db_output"] = dspData["output_levels"]
                    # print(state["DSP_preset"],state["DSP_source"],state["DSP_volume"],state["DSP_mute"],state["DSP_db_input"],state["DSP_db_output"])
            await asyncio.sleep(.25)
        except:
            print("Failed to connect to MiniDSP Service")
            await asyncio.sleep(5)
        
    

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
        print("Client Connected")
        state["listOfWebsocks"].append(websocket)
        # make the handlers
        consumer_task = asyncio.ensure_future(consumer_handler(websocket,state))
        producer_task = asyncio.ensure_future(producer_handler(websocket,state))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        print("Disconnected")
        state["listOfWebsocks"].remove(websocket)
    return handler




async def eventLoop(state):
    await gather(
        handleLedMatrix(state),
        postLoop(state),
        websockets.serve(createHandler(state), "0.0.0.0", 1997),
    )

#execute the asyncio loop
run(eventLoop(state))
