
#graphics
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps
from pilmoji import Pilmoji
from rgbmatrix import graphics
import time

def insert_newlines(string, every=64):
    return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

def stringWithEmojiToImage(inputStr,width,height,backgroundColor,textColor,fontSize):
    # inputStr = insert_newlines(inputStr,max(1,round(width/fontSize)) ) 
    with Image.new('RGB', (width, height), backgroundColor) as image:
        font = ImageFont.truetype('./fonts/ARIALN.TTF', fontSize)
        with Pilmoji(image) as pilmoji:
          try:
            pilmoji.text((0, 0), inputStr.strip(), textColor, font)
          except:
            print("Failed to make emoji image")
          return image.convert('RGB')
     


class panelOption:
  def __init__(self,xOffset,width):
    #generic
    self.option_blackBackground = 0
    self.option_emotexti = 0
    self.option_regularText = 0
    self.option_clock = 0
    self.option_fft = 0
    self.option_fftCircles = 0
    self.colorMode = "rgb"
    self.xOffset = xOffset
    self.width = width
    #option_emotexti
    self.emotexti_text = ""
    self.emotexti_backColor = (0,0,0)
    self.emotexti_textColor = (255,255,255)
    self.emotexti_fontSize = 32
    self.img= None
    #regularText
    self.fontNormal = graphics.Font()
    self.fontNormal.LoadFont("./fonts/7x13.bdf")
    self.fontLarge = graphics.Font()
    self.fontLarge.LoadFont("./fonts/10x20.bdf")        
    self.fontSmall = graphics.Font()    
    self.fontSmall.LoadFont("./fonts/5x7.bdf")  
    self.regularText_fonts = [self.fontSmall,self.fontNormal,self.fontLarge]
    self.regularText_color = graphics.Color(255,255,255)
    self.regularText_colorPIL = (255,255,255)
    self.regularText_fontSize = 0
    self.regularText_text = ""
    self.regularText_scroll = 0
    self.regularText_scrollOffset = 0
    self.regularText_scrollSpeed = .4
    #fft color stuff
    self.fft_color1 = (0,0,255)
    self.fft_color2 = (255,40,50)
    #decalre a black box
    self.blackBox = Image.new("RGB", (max(1,self.width), 32))
    draw = ImageDraw.Draw(self.blackBox)
    draw.rectangle((0, 0, self.width, 32), fill=(0, 0, 0))


  def regularText_setFont(self,fontSize):
    self.regularText_fontSize = max(min(fontSize,2),0 )
  def regularText_setColor(self,r,g,b):
    self.regularText_color = graphics.Color(r,g,b)
    self.regularText_colorPIL = (r,g,b)
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
    try:
      img = stringWithEmojiToImage(self.emotexti_text,self.width,32,self.emotexti_backColor,self.emotexti_textColor,self.emotexti_fontSize)
      if img.size != (self.width,32):
        img = img.resize((self.width,32))
      self.img = img.convert("RGB")
    except Exception as e:
      print("emotexti_setText failed:", e)
      self.img = None


  def LerpColour(self,c1,c2,t):
    return (c1[0]+(c2[0]-c1[0])*t,c1[1]+(c2[1]-c1[1])*t,c1[2]+(c2[2]-c1[2])*t)

  def DrawSpecialLine(self,canvas,x1,y1,x2,y2,list_of_colors):
    no_steps = max(0, y1-y2)
    if no_steps <= 0: return
    for i in range(no_steps):
      t = i/float(no_steps)
      c = self.LerpColour(list_of_colors[0], list_of_colors[1], t)
      canvas.SetPixel(x1, y1-i, int(c[0]), int(c[1]), int(c[2]))

  def draw(self,canvas,state):
    # black bg
    if self.option_blackBackground == 1:
      canvas.SetImage(self.blackBox, self.xOffset, 0)
    # FFT
    if self.option_fft == 1 and len(state.get("fftData", []))>0:
      screenSquish = max(1, int(round(len(state["fftData"])/self.width,0)))
      adjustedFftData = state["fftData"][::screenSquish]
      for idx, val in enumerate(adjustedFftData):
        if self.option_fftCircles == 1:
          volPow = min(255,int(val*10))
          radius = int(round(max((val/2),0),0))
          for i in range(radius):
            color = graphics.Color(volPow ,volPow,volPow)
            volPow-=12
            graphics.DrawCircle(canvas, (self.xOffset+self.width)-idx , 0, i, color)
            if volPow <= 0: break
        # gradient bar
        self.DrawSpecialLine(canvas,self.xOffset+idx,32,self.xOffset+idx,int(32-val), [self.fft_color1, self.fft_color2])
    # emoji/text image
    if self.option_emotexti == 1 and self.img is not None:
      canvas.SetImage(self.img,self.xOffset,0)
    # regular text
    if self.option_regularText == 1:
      textLen = graphics.DrawText(canvas, self.regularText_fonts[self.regularText_fontSize], self.xOffset+int(self.regularText_scrollOffset), 32-10, self.regularText_color, self.regularText_text)
      if self.regularText_scroll == 1:
        self.regularText_scrollOffset-=self.regularText_scrollSpeed
        if self.regularText_scrollOffset < -textLen:
          self.regularText_scrollOffset = self.width
    # clock (small overlay)
    if self.option_clock == 1:
      now = time.localtime()
      timestr = time.strftime("%H:%M", now)
      graphics.DrawText(canvas, self.fontSmall, self.xOffset+1, 1+7, graphics.Color(255,255,255), timestr)

  # ---------- PIL-based exact rendering ----------
  def _ensure_pil_fonts(self):
    try:
      if not hasattr(self, "_pil_font_small"):
        self._pil_font_small = ImageFont.load_path("./fonts/5x7.bdf")
      if not hasattr(self, "_pil_font_normal"):
        self._pil_font_normal = ImageFont.load_path("./fonts/7x13.bdf")
      if not hasattr(self, "_pil_font_large"):
        self._pil_font_large = ImageFont.load_path("./fonts/10x20.bdf")
    except Exception:
      try:
        if not hasattr(self, "_pil_font_small"):
          self._pil_font_small = ImageFont.truetype("./fonts/ARIALN.TTF", 7)
        if not hasattr(self, "_pil_font_normal"):
          self._pil_font_normal = ImageFont.truetype("./fonts/ARIALN.TTF", 13)
        if not hasattr(self, "_pil_font_large"):
          self._pil_font_large = ImageFont.truetype("./fonts/ARIALN.TTF", 20)
      except Exception:
        self._pil_font_small = None
        self._pil_font_normal = None
        self._pil_font_large = None

  def _pil_text_font(self):
    self._ensure_pil_fonts()
    if self.regularText_fontSize == 2: return self._pil_font_large
    if self.regularText_fontSize == 1: return self._pil_font_normal
    return self._pil_font_small

  def draw_to_image(self, fb_img, state):
    """Pure PIL render into fb_img (RGB 192x32)."""
    draw = ImageDraw.Draw(fb_img)
    x0, w = self.xOffset, self.width

    # 1) Black background
    if self.option_blackBackground == 1:
      draw.rectangle((x0, 0, x0 + w - 1, 31), fill=(0,0,0))

    # 2) FFT
    if self.option_fft == 1 and len(state.get("fftData", []))>0:
      data = state["fftData"]
      screenSquish = max(1, int(round(len(data)/w, 0)))
      adjusted = data[::screenSquish]

      # circles
      if self.option_fftCircles == 1:
        for idx, val in enumerate(adjusted):
          volPow = min(255, int(val*10))
          radius = int(round(max(val/2, 0), 0))
          for r in range(radius):
            c = (volPow, volPow, volPow)
            bbox = [(x0+w)-idx-r, 0-r, (x0+w)-idx+r, 0+r]
            draw.ellipse(bbox, outline=c)
            volPow -= 12
            if volPow <= 0: break

      # bars
      for idx, val in enumerate(adjusted):
        y_top = int(max(0, round(32 - val)))
        total = 32 - y_top
        if total <= 0: continue
        for i in range(total):
          t = i/float(total)
          r = int(self.fft_color1[0] + (self.fft_color2[0]-self.fft_color1[0])*t)
          g = int(self.fft_color1[1] + (self.fft_color2[1]-self.fft_color1[1])*t)
          b = int(self.fft_color1[2] + (self.fft_color2[2]-self.fft_color1[2])*t)
          fb_img.putpixel((x0 + idx, 32 - i - 1), (r,g,b))

    # 3) Emoji/Text image overlay (mask black so it doesn't wipe FFT)
    if self.option_emotexti == 1 and self.img is not None:
      try:
        img = self.img if self.img.size==(self.width,32) else self.img.resize((self.width,32))
        gray = ImageOps.grayscale(img)
        mask = gray.point(lambda v: 255 if v>0 else 0)
        fb_img.paste(img, (x0,0), mask)
      except Exception as e:
        print("paste emotexti img failed:", e)

    # 4) Regular text overlay (baseline-correct)
    if self.option_regularText == 1 and self.regularText_text:
      font = self._pil_text_font()
      if font is not None:
        baseline_y = 32 - 10
        try:
          ascent, descent = font.getmetrics()
        except Exception:
          ascent, descent = (8,2)
        top_y = baseline_y - ascent
        try:
          text_w = int(ImageDraw.Draw(fb_img).textlength(self.regularText_text, font=font))
        except Exception:
          text_w = len(self.regularText_text)*6
        if self.regularText_scroll == 1:
          self.regularText_scrollOffset -= self.regularText_scrollSpeed
          if self.regularText_scrollOffset < -text_w:
            self.regularText_scrollOffset = w
          x_offset = int(self.regularText_scrollOffset)
        else:
          self.regularText_scrollOffset = 0
          x_offset = 0

        timestr = ""
        if self.option_clock == 1:
          now = time.localtime()
          timestr = time.strftime("%H:%M:%S", now)
          f = self._pil_font_small or ImageFont.load_default()

        draw.text((x0 + x_offset, top_y), self.regularText_text+timestr, fill=self.regularText_colorPIL, font=font)


