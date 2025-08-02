import traceback
import asyncio

# ---- Under-glow safety: global throttle (1 msg/sec) ----
MIN_UNDERLIGHT_INTERVAL = 1.0  # seconds


async def set_under_fade(state,fadeOrNot):
    output_dict = {}
    output_dict["stat"] = fadeOrNot
    await state["SE"].sendToAllWebsocks(state,"control_underRGBfade",output_dict)

async def set_underlights(state, r, g, b, *, min_interval=MIN_UNDERLIGHT_INTERVAL):
    """Safe one-shot under-glow setter that enforces a minimum interval between writes."""
    await set_under_fade(state,0)
    last = state.get("_under_last_ts", 0.0)
    now = asyncio.get_running_loop().time()
    wait = max(0.0, min_interval - (now - last))
    if wait > 0:
        await asyncio.sleep(wait)
    output_dict = {"r": r, "g": g, "b": b}
    await state["SE"].sendToAllWebsocks(state, "control_underRGBcolor", output_dict)
    state["_under_last_ts"] = asyncio.get_running_loop().time()

def config_panel_fft(panel, c1, c2, *, black=True, circles=False, regular_text_off=True):
    """Set a panel to FFT mode (no emoji)."""
    if regular_text_off and hasattr(panel, "option_regularText"):
        panel.option_regularText = 0
    panel.option_blackBackground = 1 if black else 0
    panel.option_fft = 1
    panel.option_fftCircles = 1 if circles else 0
    panel.fft_color1 = c1
    panel.fft_color2 = c2
    if hasattr(panel, "option_emotexti"):
        panel.option_emotexti = 0  # ensure emojis off

def config_panel_emoji(panel, text, *, black=True, regular_text_off=True):
    """Set a panel to Emoji mode (no FFT)."""
    if regular_text_off and hasattr(panel, "option_regularText"):
        panel.option_regularText = 0
    panel.option_blackBackground = 1 if black else 0
    panel.option_fft = 0
    panel.option_fftCircles = 0
    if hasattr(panel, "option_emotexti"):
        panel.option_emotexti = 1
    # Emoji/text setter for emoji-only widget
    if hasattr(panel, "emotexti_setText"):
        panel.emotexti_setText(text)

def config_panel_text(panel, text, color=(255,255,255), *, scroll=1, speed=1, black=True):
    panel.option_regularText = 1
    panel.regularText_setColor(color[0],color[1],color[2])
    panel.regularText_setScroll(scroll)
    panel.regularText_setScrollSpeed(speed)
    panel.regularText_setText(text)

# ---- Spots (using your latest mapping) ----
dictSpotColors = {
    "red_1": 4,
    "green_1": 5,
    "blue_1": 6,
    "orange_1": 8,
    "green_2": 9,
    "blue_2": 10,
    "orange_2": 12,
    "aqua": 13,
    "dark_purple": 14,
    "light_orange": 16,
    "darker_aqua": 17,
    "medium_purple": 18,
    "yellow": 20,
    "ocean_blue": 21,
    "pink": 22,
    "white": 7,
}

async def spotlights(state, spotnum, colorStr):
    # double-send for reliability
        output_dict = {"spotLightNum": spotnum, "spotLightButton": 3} #on command just in case
        await state["SE"].sendToAllWebsocks(state, "control_spotlight", output_dict)
        await asyncio.sleep(1)
        output_dict = {"spotLightNum": spotnum, "spotLightButton": dictSpotColors[colorStr]}
        await state["SE"].sendToAllWebsocks(state, "control_spotlight", output_dict)
        await asyncio.sleep(1)

# ---- Presets (1..8 are your current ones, adding 9..14) ----
async def doPreset(state, preset):
    try:
        if preset == 1:  # Slime Green
            # Panel + underlights first
            config_panel_fft(state["panelCenter"], (20, 120, 20), (0, 255, 0), circles=True)
            config_panel_emoji(state["panelLeft"],  "🟩")
            config_panel_emoji(state["panelRight"], "🟩")
            await set_underlights(state, 20, 255, 60)
            # Spotlights last
            await spotlights(state, 0, "green_1")
            await spotlights(state, 1, "green_2")
            await spotlights(state, 2, "green_1")

        elif preset == 2:  # Christmas
            config_panel_fft(state["panelCenter"], (220, 0, 0), (0, 180, 0), circles=True)
            config_panel_emoji(state["panelLeft"],  "🎄")
            config_panel_emoji(state["panelRight"], "🎁")
            await set_underlights(state, 0, 130, 0)
            await spotlights(state, 0, "red_1")
            await spotlights(state, 1, "white")
            await spotlights(state, 2, "green_1")

        elif preset == 3:  # Fall
            config_panel_fft(state["panelCenter"], (200, 90, 0), (255, 160, 40), circles=True)
            config_panel_emoji(state["panelLeft"],  "🍂")
            config_panel_emoji(state["panelRight"], "🍁")
            await set_underlights(state, 255, 120, 20)
            await spotlights(state, 0, "orange_1")
            await spotlights(state, 1, "light_orange")
            await spotlights(state, 2, "yellow")

        elif preset == 4:  # Fire (all FFT)
            config_panel_fft(state["panelCenter"], (0, 0, 0),(255, 30, 0) , circles=True)
            config_panel_fft(state["panelLeft"],  (0, 0, 0), (255, 0, 0))
            config_panel_fft(state["panelRight"], (0, 0, 0), (255, 0, 0))
            await set_underlights(state, 255, 40, 0)
            await spotlights(state, 0, "red_1")
            await spotlights(state, 1, "red_1")
            await spotlights(state, 2, "red_1")

        elif preset == 5:  # 4th of July
            config_panel_fft(state["panelCenter"], (255, 255, 255), (0, 80, 200), circles=True)
            config_panel_emoji(state["panelLeft"],  "🎆")
            config_panel_emoji(state["panelRight"], "🇺🇸")
            await set_underlights(state, 127, 127, 127)
            await spotlights(state, 0, "red_1")
            await spotlights(state, 1, "white")
            await spotlights(state, 2, "blue_2")

        elif preset == 6:  # Purple (all FFT)
            config_panel_fft(state["panelCenter"], (128, 0, 200), (255, 0, 200), circles=True)
            config_panel_fft(state["panelLeft"],  (80, 0, 160), (180, 0, 255))
            config_panel_fft(state["panelRight"], (80, 0, 160), (180, 0, 255))
            await set_underlights(state, 170, 0, 255)
            await spotlights(state, 0, "dark_purple")
            await spotlights(state, 1, "medium_purple")
            await spotlights(state, 2, "pink")

        elif preset == 7:  # Pure White (all FFT)
            config_panel_fft(state["panelCenter"], (255, 255, 255), (255, 255, 255), circles=False)
            config_panel_fft(state["panelLeft"],  (255, 255, 255), (255, 255, 255))
            config_panel_fft(state["panelRight"], (255, 255, 255), (255, 255, 255))
            await set_underlights(state, 127, 127, 127)
            await spotlights(state, 0, "white")
            await spotlights(state, 1, "white")
            await spotlights(state, 2, "white")

        elif preset == 8:  # Florida
            config_panel_fft(state["panelCenter"], (255, 160, 60),(0, 180, 200), circles=True)
            config_panel_emoji(state["panelLeft"],  "🌴")
            config_panel_emoji(state["panelRight"], "🦩")
            await set_underlights(state, 0, 200, 180)
            await spotlights(state, 0, "light_orange")
            await spotlights(state, 1, "aqua")
            await spotlights(state, 2, "pink")

        elif preset == 9:  # Happy Birthday
            config_panel_text(state["panelCenter"], "Happy Birthday!",
                              color=(255,255,255), scroll=True, speed=2, black=True)
            config_panel_emoji(state["panelLeft"],  "🎂")
            config_panel_emoji(state["panelRight"], "🎉")
            await set_under_fade(state,1)
            await spotlights(state, 0, "pink")
            await spotlights(state, 1, "yellow")
            await spotlights(state, 2, "pink")

        elif preset == 10:  # Halloween
            config_panel_fft(state["panelCenter"], (255, 120, 0), (90, 0, 120), circles=True)
            config_panel_emoji(state["panelLeft"],  "🎃")
            config_panel_emoji(state["panelRight"], "👻")
            await set_underlights(state, 255, 90, 0)
            await spotlights(state, 0, "light_orange")
            await spotlights(state, 1, "dark_purple")
            await spotlights(state, 2, "orange_2")

        elif preset == 11:  # Thanksgiving
            config_panel_fft(state["panelCenter"], (180, 80, 0), (255, 170, 60), circles=True)
            config_panel_emoji(state["panelLeft"],  "🦃")
            config_panel_emoji(state["panelRight"], "🥧")
            await set_underlights(state, 255, 140, 40)
            await spotlights(state, 0, "orange_1")
            await spotlights(state, 1, "yellow")
            await spotlights(state, 2, "light_orange")

        elif preset == 12:  # Space
            config_panel_fft(state["panelCenter"], (10, 20, 80), (120, 0, 160), circles=True)
            config_panel_emoji(state["panelLeft"],  "🚀")
            config_panel_emoji(state["panelRight"], "🪐")
            await set_underlights(state, 0, 40, 120)
            await spotlights(state, 0, "ocean_blue")
            await spotlights(state, 1, "medium_purple")
            await spotlights(state, 2, "darker_aqua")

        elif preset == 13:  # Flower
            config_panel_fft(state["panelCenter"], (255, 120, 180), (60, 200, 120), circles=True)
            config_panel_emoji(state["panelLeft"],  "🌸")
            config_panel_emoji(state["panelRight"], "🌼")
            await set_underlights(state, 255, 150, 200)
            await spotlights(state, 0, "pink")
            await spotlights(state, 1, "aqua")
            await spotlights(state, 2, "light_orange")

        elif preset == 14:  # Lo‑Fi Night (chill club vibe, all FFT)
            config_panel_fft(state["panelCenter"], (20, 20, 60), (80, 0, 120), circles=False)
            config_panel_fft(state["panelLeft"],  (10, 30, 70), (0, 80, 120))
            config_panel_fft(state["panelRight"], (10, 30, 70), (0, 80, 120))
            await set_underlights(state, 0, 40, 80)
            await spotlights(state, 0, "medium_purple")
            await spotlights(state, 1, "ocean_blue")
            await spotlights(state, 2, "dark_purple")

        elif preset == 15:  # Ocean Theme
            # Center panel FFT with deep-to-teal ocean gradient
            config_panel_fft(state["panelCenter"], (0, 30, 80), (0, 150, 200), circles=True)
            # Side panels with wave and dolphin emojis
            config_panel_emoji(state["panelLeft"],  "🌊")
            config_panel_emoji(state["panelRight"], "🐬")
            # Under‑glow in soft teal
            await set_underlights(state, 0, 100, 150)
            # Spotlights: deep blue, aqua, darker aqua
            await spotlights(state, 0, "ocean_blue")
            await spotlights(state, 1, "aqua")
            await spotlights(state, 2, "darker_aqua")

        elif preset == 16:  # Ice Blues
            # Center panel FFT with pale-to-bright ice‑blue gradient
            config_panel_fft(state["panelCenter"], (180, 220, 255), (140, 200, 255), circles=False)
            # Side panels with snowflake and snowman emojis
            config_panel_emoji(state["panelLeft"],  "🟦")
            config_panel_emoji(state["panelRight"], "🟦")
            # Under‑glow in frosty blue
            await set_underlights(state, 150, 200, 255)
            # Spotlights: crisp white, ocean blue, white
            await spotlights(state, 0, "white")
            await spotlights(state, 1, "ocean_blue")
            await spotlights(state, 2, "white")

        else:
            pass

    except Exception:
        print("Exception occurred during doPreset:")
        traceback.print_exc()
