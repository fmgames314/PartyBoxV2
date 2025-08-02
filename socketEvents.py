
import json
import time
from PIL import ImageColor
import stylePresets as PRESETS

# Utility ------------------------------------------------------------------
def _get_panel_from_name(state, name):
    if not name:
        return None
    n = str(name).strip().upper()
    if n == "LEFT":   return state.get("panelLeft")
    if n == "CENTER": return state.get("panelCenter")
    if n == "RIGHT":  return state.get("panelRight")
    return None

def _hex_to_rgb(s):
    try:
        h = str(s or "").strip().lstrip("#")
        if len(h) != 6: return (255,255,255)
        return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))
    except Exception:
        return (255,255,255)

async def sendPacketToWSClient(websocket,eventName,inputDict):
    try:
        payload = dict(inputDict or {})
        payload["event"] = eventName
        await websocket.send(json.dumps(payload))
    except Exception as e:
        print("couldn't send data to websocket: " + str(e))
        raise

async def sendToAllWebsocks(state, eventName, inputDict):
    # optional broadcast helper (only works if main.py tracks listOfWebsocks)
    lst = list(state.get("listOfWebsocks", []))
    dead = []
    for ws in lst:
        try:
            print(eventName,inputDict)
            await sendPacketToWSClient(ws, eventName, inputDict)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            state["listOfWebsocks"].remove(ws)
        except Exception:
            pass

async def sendToAllBrowsersGuis(state,eventName,inputDict):
    # optional broadcast helper (only works if main.py tracks listOfWebsocks)
    lst = list(state.get("listOfBrowersClients", []))
    dead = []
    for ws in lst:
        try:
            # print(eventName,inputDict)
            await sendPacketToWSClient(ws, eventName, inputDict)
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            state["listOfBrowersClients"].remove(ws)
        except Exception:
            pass

# Panel state serialization -------------------------------------------------
def _panel_to_dict(p):
    return {
        "option_blackBackground": int(getattr(p, "option_blackBackground", 0)),
        "option_emotexti":        int(getattr(p, "option_emotexti", 0)),
        "option_regularText":     int(getattr(p, "option_regularText", 0)),
        "option_clock":           int(getattr(p, "option_clock", 0)),
        "option_fft":             int(getattr(p, "option_fft", 0)),
        "option_fftCircles":      int(getattr(p, "option_fftCircles", 0)),

        "regularText_text":       getattr(p, "regularText_text", ""),
        "regularText_fontSize":   int(getattr(p, "regularText_fontSize", 0)),
        "regularText_scroll":     int(getattr(p, "regularText_scroll", 0)),
        "regularText_scrollSpeed":float(getattr(p, "regularText_scrollSpeed", 0.4)),
        "regularText_color":      list(getattr(p, "regularText_colorPIL", (255,255,255))),

        "emotexti_text":          getattr(p, "emotexti_text", ""),
        "emotexti_fontSize":      int(getattr(p, "emotexti_fontSize", 32)),
        "emotexti_backColor":     list(getattr(p, "emotexti_backColor", (0,0,0))),
        "emotexti_textColor":     list(getattr(p, "emotexti_textColor", (255,255,255))),

        "fft_color1":             list(getattr(p, "fft_color1", (0,0,255))),
        "fft_color2":             list(getattr(p, "fft_color2", (255,40,50))),
    }

async def _send_all_panel_state(websocket, state):
    out = {
        "LEFT":   _panel_to_dict(state["panelLeft"]),
        "CENTER": _panel_to_dict(state["panelCenter"]),
        "RIGHT":  _panel_to_dict(state["panelRight"]),
    }
    if websocket not in state["listOfBrowersClients"]:
        state["listOfBrowersClients"].append(websocket)
    await sendPacketToWSClient(websocket, "give_panel_state", out)

# Event processor -----------------------------------------------------------
async def process_websocket_event(websocket, packet, eventName, state):
    # print(packet)
    # FFT stream from microservice
    if eventName == "spectrum_data":
        state["fftData"] = packet.get("data", [])
        return

    # DSP controls/state ----------------------------------------------------
    if eventName == "set_volume":
        try:
            await state["DSP"].setDSPVolume(state, packet.get("volume", 0))
        except Exception:
            pass
        return

    if eventName == "set_dsp_source":
        # Provide a stub; implement DSP.setDSPSource if available
        src = str(packet.get("source", "")).strip()
        state["DSP_source"] = src
        try:
            if hasattr(state["DSP"], "setDSPSource"):
                await state["DSP"].setDSPSource(state, src)
        except Exception as e:
            print("Failed to set DSP source:", e)
        return

    if eventName == "get_miniDspState":
        output_dict = {
            "DSP_preset":   state.get("DSP_preset", -1),
            "DSP_source":   state.get("DSP_source", "Unknown"),
            "DSP_volume":   state.get("DSP_volume", 0),
            "DSP_mute":     state.get("DSP_mute", "Unknown"),
            "DSP_db_input": state.get("DSP_db_input", []),
            "DSP_db_output":state.get("DSP_db_output", []),
        }
        await sendPacketToWSClient(websocket, "give_miniDspState", output_dict)
        return

    # Panel state -----------------------------------------------------------
    if eventName == "get_panel_state":
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_panel_option":
        panel = _get_panel_from_name(state, packet.get("panel"))
        option = str(packet.get("option", ""))
        val = int(packet.get("state", 0))
        if panel is not None and hasattr(panel, option):
            setattr(panel, option, val)
        else:
            print(f"Unknown panel/option in set_panel_option: {packet!r}")
        # Return fresh state
        await _send_all_panel_state(websocket, state)
        return

    # Regular text ----------------------------------------------------------
    if eventName == "set_regularText_text":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            panel.regularText_setText(packet.get("text", "") or "")
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_regularText_scroll":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            panel.regularText_setScroll(int(packet.get("state", 0)))
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_regularText_scrollSpeed":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            try:
                panel.regularText_setScrollSpeed(float(packet.get("speed", 0.4)))
            except Exception: pass
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_regularText_fontSize":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            try:
                panel.regularText_setFont(int(packet.get("size", 0)))
            except Exception: pass
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_regularText_color":
        panel = _get_panel_from_name(state, packet.get("panel"))
        color = _hex_to_rgb(packet.get("color"))
        if panel is not None:
            try:
                panel.regularText_setColor(color[0], color[1], color[2])
            except Exception: pass
        await _send_all_panel_state(websocket, state)
        return

    # Emoji/Text image parameters ------------------------------------------
    if eventName == "set_emoji_text":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            panel.emotexti_setText(packet.get("text", "") or "")
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_emotexti_fontSize":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            try:
                panel.emotexti_fontSize = int(packet.get("size", 32))
                panel.emotexti_setText(panel.emotexti_text or "")
            except Exception: pass
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_emotexti_backColor":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            panel.emotexti_backColor = _hex_to_rgb(packet.get("color"))
            panel.emotexti_setText(panel.emotexti_text or "")
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_emotexti_textColor":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            panel.emotexti_textColor = _hex_to_rgb(packet.get("color"))
            panel.emotexti_setText(panel.emotexti_text or "")
        await _send_all_panel_state(websocket, state)
        return

    # FFT colors ------------------------------------------------------------
    if eventName == "set_fft_color_1":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            panel.fft_color1 = _hex_to_rgb(packet.get("color"))
        print("sendcolor")
        await _send_all_panel_state(websocket, state)
        return

    if eventName == "set_fft_color_2":
        panel = _get_panel_from_name(state, packet.get("panel"))
        if panel is not None:
            panel.fft_color2 = _hex_to_rgb(packet.get("color"))
        await _send_all_panel_state(websocket, state)
        return

    # Rear light remotes / spotlight ---------------------------------------
    if eventName == "set_setUnderRGBColor":
        color = packet.get("color", "#ffffff")
        output_dict = {}
        output_dict["r"] = ImageColor.getcolor(color, "RGB")[0]
        output_dict["g"] = ImageColor.getcolor(color, "RGB")[1]
        output_dict["b"] = ImageColor.getcolor(color, "RGB")[2]
        await sendToAllWebsocks(state,"control_underRGBcolor",output_dict)
        
    if eventName == "set_setUnderRGBFade":
        output_dict = {}
        output_dict["stat"] = int(packet.get("stat", 0))
        await sendToAllWebsocks(state,"control_underRGBfade",output_dict)

    # spotlights
    if eventName == "set_spotlight":
        spotNum = int(packet.get("group", 0))
        spotButton = int(packet.get("index", 0))
        #now send to all to get it to ESP32
        output_dict = {}
        output_dict["spotLightNum"] = spotNum
        output_dict["spotLightButton"] = spotButton
        await sendToAllWebsocks(state,"control_spotlight",output_dict)

    if eventName == "preset":
        presetNum = int(packet.get("presetNum", 0))
        await PRESETS.doPreset(state,presetNum)
        

    # Unknown event
    # print("Unknown event:", eventName)
    return

