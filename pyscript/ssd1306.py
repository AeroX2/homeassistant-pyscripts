import time
import sched
from queue import Empty
from multiprocessing import Queue

import board
import digitalio
import PIL.Image as Image
import PIL.ImageDraw as ImageDraw
import PIL.ImageFont as ImageFont
import adafruit_ssd1306

import pyscript


class ClockService:

    running = False
    scheduler = sched.scheduler()
    wave_obj = None

    @pyscript_compile
    def beep(self):
        import requests

        f = open("/config/pyscript/beep.wav", "rb")
        fd = f.read()
        r = requests.post(
            "http://localhost:12101/api/play-wav",
            headers={"Content-Type": "audio/wav"},
            data=fd,
        )

    @pyscript_compile
    def set_alarm_rel(self, time):
        hours, minutes = map(int, time.split(":"))
        delta = hours * 60 * 60 + minutes * 60
        if self.scheduler.empty():
            print("Setting an alarm for {} seconds".format(delta))
            self.scheduler.enter(delta, 1, self.beep)

    # def set_alarm_abs(self, time):
    #    if self.scheduler.empty():
    #        self.scheduler.enter(time.gmtime(time), 1, self.beep)

    @pyscript_compile
    def loop(self, q):
        print("Starting draw loop")

        WIDTH = 128
        HEIGHT = 32

        i2c = board.I2C()
        oled = adafruit_ssd1306.SSD1306_I2C(
            WIDTH,
            HEIGHT,
            i2c,
            addr=0x3C,
        )

        font = ImageFont.load_default()

        print("Loading finished")

        self.running = True
        while True:
            try:
                m, d = q.get_nowait()
                if m == "stop":
                    self.running = False
                    break
                elif m == "set_alarm_rel":
                    self.set_alarm_rel(d)
                elif m == "stop_alarm":
                    list(map(self.scheduler.cancel, self.scheduler.queue))
            except Empty:
                pass

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


pyscript.queue = Queue()
pyscript.clock_service = ClockService()


@service
def start_clock():
    task.executor(pyscript.clock_service.loop, pyscript.queue)


@service
def stop_clock():
    pyscript.queue.put(("stop", ""))


@service
def set_alarm_rel(time):
    pyscript.queue.put(("set_alarm_rel", time))


@service
def stop_alarm():
    pyscript.queue.put(("stop_alarm", ""))


@service
def beep():
    task.executor(pyscript.clock_service.beep)
