# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import RPi.GPIO as GPIO
import time
import thread
import os


class KrestartPlugin(octoprint.plugin.SettingsPlugin,
                     #octoprint.plugin.AssetPlugin,
                     octoprint.plugin.TemplatePlugin,
                     octoprint.plugin.StartupPlugin,
                     octoprint.plugin.ShutdownPlugin,
                     octoprint.plugin.RestartNeedingPlugin):

    def on_after_startup(self):
        self._logger.info("Krestart - startup")
        GPIO.setmode(GPIO.BOARD)
        led_pin = self.led_pin = int(self._settings.get(["led_pin"])) 
        btn1_pin = self.btn1_pin = int(self._settings.get(["btn1_pin"])) 
        btn2_pin = self.btn2_pin = int(self._settings.get(["btn2_pin"])) 
        btn3_pin = self.btn3_pin = int(self._settings.get(["btn3_pin"])) 
        self._logger.info("Krestart - L:{}".format(led_pin))
        GPIO.setup(led_pin, GPIO.OUT)
        GPIO.setup(btn1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(btn2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(btn3_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(led_pin, GPIO.HIGH)
        GPIO.remove_event_detect(btn1_pin)
        GPIO.remove_event_detect(btn2_pin)
        GPIO.remove_event_detect(btn3_pin)
        GPIO.add_event_detect(btn1_pin, GPIO.FALLING, callback=self._btn_click1, bouncetime=200)
        GPIO.add_event_detect(btn2_pin, GPIO.FALLING, callback=self._btn_click2, bouncetime=200)
        GPIO.add_event_detect(btn3_pin, GPIO.FALLING, callback=self._btn_click3, bouncetime=200)
        self._led_status = True
        self._active1 = False
        self._active2 = False
        self._active3 = False
        self._clicks1 = 0
        self._clicks2 = 0
        self._clicks3 = 0

    def on_shutdown(self):
        GPIO.cleanup()

    def _blink(self, wait=0.5, wait_after=0.5):
        led_pin = self.led_pin #int(self._settings.get(["led_pin"])) 
        GPIO.output(led_pin, not self._led_status)
        time.sleep(wait)
        GPIO.output(led_pin, self._led_status)
        time.sleep(wait_after)
    
    def exe_status(self):
        self._printer.commands("status")
        return True

    def exe_firmware_restart(self):
        if self._printer.is_ready():
            self._printer.commands("firmware_restart")
            return True
        return False

    def exe_restart(self):
        if self._printer.is_ready():
            self._printer.commands("restart")
            return True
        return False

    def exe_m112(self):
        self._printer.commands("M112")
        return True

    def exe_os_shutdown(self):
        os.system('sudo shutdown -h now')
        return True

    def exe_os_restart(self):
        os.system('sudo shutdown -r now')
        return True

    def exe_connect(self):
        self._printer.connect("/tmp/printer")
        return True

    def _execute_command(self, cname, aname, btn, commands):
        setattr(self, aname, True)
        setattr(self, cname, 1)
        wait = float(self._settings.get(["click_timeout"]))
        self._logger.info("Krestart - thread wait {}".format(wait))
        time.sleep(wait)
        clicks = getattr(self, cname, 0)
        active = getattr(self, aname, 0)
        for i in range(btn + 1):
            self._blink()
        if active and clicks in commands:
            self._logger.info("Krestart - processing {} clicks to {}".format(clicks, btn))
            if not commands[clicks]():
                for i in range(10):
                    self._blink(0.1)
                self._logger.info("Krestart - command failed")
            else:
                self._logger.info("Krestart - command ok")

        else:
            self._logger.info("Krestart - no command")
        self._blink(1.0, 0)
        setattr(self, aname, False)
        setattr(self, cname, 0)

    def _btn_click1(self, channel=None):
        if not self._active1:
            thread.start_new_thread(self._execute_command, (
                '_clicks1', '_active1', 1, {
                    1: self.exe_status,
                    2: self.exe_firmware_restart,
                    3: self.exe_restart,
                })
            )
        else:
            self._clicks1 += 1
        self._blink(0.1)
        self._logger.info("Krestart - click 1 ({})".format(self._clicks1))


    def _btn_click2(self, channel=None):
        if not self._active2:
            thread.start_new_thread(self._execute_command, (
                '_clicks2', '_active2', 2, {
                    1: self.exe_connect,
                    2: self.exe_m112,
                })
            )
        else:
            self._clicks2 += 1
        self._blink(0.1)
        self._logger.info("Krestart - click 2 ({})".format(self._clicks2))


    def _btn_click3(self, channel=None):
        if not self._active3:
            thread.start_new_thread(self._execute_command, (
                '_clicks3', '_active3', 3, {
                    1: self.exe_status,
                    2: self.exe_os_shutdown,
                    3: self.exe_os_restart
                })
            )
        else:
            self._clicks3 += 1
        self._blink(0.1)
        self._logger.info("Krestart - click 3 ({})".format(self._clicks3))

    def get_settings_defaults(self):
        return dict(
            led_pin="12",
            btn1_pin="11",
            btn2_pin="13",
            btn3_pin="15",
            click_timeout="3",
        )

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False),
        ]

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/krestart.js"],
            css=["css/krestart.css"],
            less=["less/krestart.less"]
        )

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            krestart=dict(
                displayName="Krestart Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="JoaoFelipe",
                repo="OctoPrint-Krestart",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/JoaoFelipe/OctoPrint-Krestart/archive/{target_version}.zip"
            )
        )


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Krestart Plugin"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = KrestartPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

