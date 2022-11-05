#graphics
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pilmoji import Pilmoji
from rgbmatrix import graphics

def insert_newlines(string, every=64):
    return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

def stringWithEmojiToImage(inputStr,width,height,backgroundColor,textColor,fontSize):
    # inputStr = insert_newlines(inputStr,max(1,round(width/fontSize)) ) 
    with Image.new('RGB', (width, height), backgroundColor) as image:
        font = ImageFont.truetype('./fonts/ARIALN.TTF', fontSize)
        with Pilmoji(image) as pilmoji:
            pilmoji.text((0, 0), inputStr.strip(), textColor, font)
            return image.convert('RGB')
     


class panelOption:
  def __init__(self,xOffset,width):
    #generic
    self.option_blackBackground = 0
    self.option_emotexti = 0
    self.option_regularText = 0
    self.option_clock = 0
    self.option_fft = 0
    self.colorMode = "rgb"
    self.xOffset = xOffset
    self.width = width
    #option_emotexti
    self.emotexti_text = ""
    self.emotexti_backColor = (0,0,0)
    self.emotexti_textColor = (255,255,255)
    self.emotexti_fontSize = 32
    self.emotexti_img= None
    #regularText
    self.fontNormal = graphics.Font()
    self.fontNormal.LoadFont("./fonts/7x13.bdf")
    self.fontLarge = graphics.Font()
    self.fontLarge.LoadFont("./fonts/10x20.bdf")        
    self.fontSmall = graphics.Font()    
    self.fontSmall.LoadFont("./fonts/5x7.bdf")  
    self.regularText_fonts = [self.fontSmall,self.fontNormal,self.fontLarge]
    self.regularText_color = graphics.Color(255,255,255)
    self.regularText_fontSize = 0
    self.regularText_text = ""
    self.regularText_scroll = 0
    self.regularText_scrollOffset = 0
    self.regularText_scrollSpeed = .4
    #decalre a black box
    self.blackBox = Image.new("RGB", (32, 32))  # Can be larger than matrix if wanted!!
    draw = ImageDraw.Draw(self.blackBox)  # Declare Draw instance before prims
    draw.rectangle((0, 0, self.width, 32), fill=(0, 0, 0))


  def regularText_setFont(self,fontSize):
    self.regularText_fontSize = max(min(fontSize,2),0 )
  def regularText_setColor(self,r,g,b):
    self.regularText_color = graphics.Color(r,g,b)
  def regularText_setText(self,text):
    self.regularText_text = text
  def regularText_setScrollSpeed(self,speed):
    self.regularText_scrollSpeed = speed
  def regularText_setScroll(self,scrollState):
    self.regularText_scroll = scrollState
    if scrollState == 0:
      self.regularText_scrollOffset = 0


  def emotexti_setText(self,text):
    self.emotexti_text = text
    self.img = stringWithEmojiToImage(self.emotexti_text,self.width,32,self.emotexti_backColor,self.emotexti_textColor,self.emotexti_fontSize)


  def draw(self,canvas):
    if self.option_blackBackground == 1:
      canvas.SetImage(self.blackBox, self.xOffset, 0)
    #emoji text which is an image
    if self.option_emotexti == 1:
      if self.img is not None:
        canvas.SetImage(self.img,self.xOffset,0)
    # regular graphics based text
    if self.option_regularText == 1:
      textLen = graphics.DrawText(canvas, self.regularText_fonts[self.regularText_fontSize], self.xOffset+self.regularText_scrollOffset, 32-10, self.regularText_color, self.regularText_text)
      if self.regularText_scroll == 1:
        self.regularText_scrollOffset-=self.regularText_scrollSpeed
        if self.regularText_scrollOffset < -textLen:
          self.regularText_scrollOffset = self.width

          


# graphics.DrawLine(canvas, 5, 5, 22, 13, red)
 # fontNormal = graphics.Font()
        # fontNormal.LoadFont("./fonts/7x13.bdf")
        # fontLarge = graphics.Font()
        # fontLarge.LoadFont("./fonts/10x20.bdf")        
        # fontSmall = graphics.Font()    
        # fontSmall.LoadFont("./fonts/5x7.bdf")       
        # red = graphics.Color(255, 0, 0)
        # graphics.DrawLine(state["matrix"], 5, 5, 22, 13, red)
        # green = graphics.Color(0, 255, 0)
        # graphics.DrawCircle(state["matrix"], 15, 15, 10, green)
        # blue = graphics.Color(0, 0, 255)
        # graphics.DrawText(state["matrix"], fontNormal, 64, 10, blue, "Hello")
        # graphics.DrawText(state["matrix"], fontSmall, 32, 10, green, "Hello")
        # graphics.DrawText(state["matrix"], fontLarge, 115, 10, blue, "Hello")