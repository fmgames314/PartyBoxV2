import asyncio
from asyncio import gather, run, Event
import socket
import aiohttp
import json


async def setDSPVolume(state,volume):
    try:
        postData = """{"master_status": {"volume": """+str(volume)+"""}}"""
        async with aiohttp.ClientSession() as session:
                miniDspUrl = 'http://127.0.0.1:5380/devices/0/config'
                async with session.post(miniDspUrl, data=postData) as resp:
                    dspResponse = await resp.json(content_type=None)
    except:
        print("Failed to set volume on miniDSP")
    # try:
    #     postData = """{"master": [{"volume": """+str(volume)+""","index": 1}]}"""
    #     async with aiohttp.ClientSession() as session:
    #             miniDspUrl = 'http://127.0.0.1:5380/devices/0/config'
    #             async with session.post(miniDspUrl, data=postData) as resp:
    #                 dspResponse = await resp.json(content_type=None)
    # except:
    #     print("Failed to set volume on miniDSP")        