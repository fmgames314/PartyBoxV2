#!/usr/bin/env python

#rgb matrix library
from samplebase import SampleBase
from rgbmatrix import graphics
#graphics
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pilmoji import Pilmoji
#generic
import time


def insert_newlines(string, every=64):
    return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

def stringWithEmojiToImage(inputStr,width,height,backgroundColor,textColor,fontSize):
    inputStr = insert_newlines(inputStr,max(1,round(width/fontSize)) ) 
    with Image.new('RGB', (width, height), backgroundColor) as image:
        font = ImageFont.truetype('./fonts/ARIALN.TTF', fontSize)
        with Pilmoji(image) as pilmoji:
            pilmoji.text((0, 0), inputStr.strip(), textColor, font)
            return image.convert('RGB')
            

class GraphicsTest(SampleBase):
    def __init__(self, *args, **kwargs):
        super(GraphicsTest, self).__init__(*args, **kwargs)

    def run(self):
        canvas = self.matrix
        fontNormal = graphics.Font()
        fontNormal.LoadFont("./fonts/7x13.bdf")
        fontLarge = graphics.Font()
        fontLarge.LoadFont("./fonts/10x20.bdf")        
        fontSmall = graphics.Font()    
        fontSmall.LoadFont("./fonts/5x7.bdf")       

        print(canvas)

        red = graphics.Color(255, 0, 0)
        # graphics.DrawLine(canvas, 5, 5, 22, 13, red)

        green = graphics.Color(0, 255, 0)
        # graphics.DrawCircle(canvas, 15, 15, 10, green)

        blue = graphics.Color(0, 0, 255)
        graphics.DrawText(canvas, fontNormal, 64, 10, blue, "Hello")
        graphics.DrawText(canvas, fontSmall, 32, 10, green, "Hello")
        graphics.DrawText(canvas, fontLarge, 115, 10, blue, "Hello")

        img = stringWithEmojiToImage("🎄",32,32,(0, 0, 0),(255, 255, 255),32)
        canvas.SetImage(img,0,0)

        img = stringWithEmojiToImage("🎃",32,32,(0, 0, 0),(255, 255, 255),32)
        canvas.SetImage(img,160,0)        

        time.sleep(10)
        canvas.Clear()



# Main function
if __name__ == "__main__":
    graphics_test = GraphicsTest()
    if (not graphics_test.process()):
        graphics_test.print_help()

#run with sudo python3 main.py --led-rows=32 --led-cols=32 --led-chain=6 --led-slowdown-gpio=4 --led-pixel-mapper "Rotate:180"