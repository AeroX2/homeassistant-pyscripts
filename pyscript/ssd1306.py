import time
import sched
from threading import Thread

import board
import digitalio
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont
import adafruit_ssd1306

import pyscript

class ClockService():
    
    running = False
    scheduler = sched.scheduler()
    wave_obj = None

    def beep(self):
        import simpleaudio as sa

        if self.wave_obj is None:
            self.wave_obj = sa.WaveObject.from_wave_file("beep.wav")

        for _ in range(3):
            play_obj = self.wave_obj.play()
            play_obj.wait_done()

    def set_alarm(self, alarm):
        if self.scheduler.empty():
            self.scheduler.enter(time.gmtime(alarm), 1, self.beep)

    @pyscript_compile
    def draw_loop(self):
        print("Starting draw loop")
        
        WIDTH = 128
        HEIGHT = 32

        i2c = board.I2C()
        oled = adafruit_ssd1306.SSD1306_I2C(
            WIDTH, HEIGHT, i2c, addr=0x3C,
        )

        font = ImageFont.load_default()

        print("Loading finished")

        self.running = True
        while self.running:
            #oled.fill(0)
            #oled.show()
            
            image = Image.new("1", (oled.width, oled.height))
            draw = ImageDraw.Draw(image)

            text = time.strftime("%-I:%M:%S %p")
            (font_width, font_height) = font.getsize(text)
            draw.text(
                (
                    oled.width // 2 - font_width // 2,
                    oled.height // 2 - font_height // 2,
                ),
                text,
                font=font,
                fill=255,
            )

            if not self.scheduler.empty():
                time_left = self.scheduler.run(False)
                alarm = time.strftime("%H:%M:%S", time.gmtime(time_left))
                (font_width, font_height) = font.getsize(alarm)

                draw.text(
                    (
                        oled.width // 2 - font_width // 2,
                        oled.height // 2 - font_height // 2 + font_height,
                    ),
                    alarm,
                    font=font,
                    fill=255,
                )

            oled.image(image)
            oled.show()
            time.sleep(0.01)
    
    @pyscript_compile
    def stop(self):
        self.running = False

pyscript.clock_service = ClockService()

@service
def start_clock():
    task.executor(pyscript.clock_service.draw_loop)
        
@service
def stop_clock():
    task.executor(pyscript.clock_service.stop)