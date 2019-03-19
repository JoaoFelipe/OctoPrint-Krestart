# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
import RPi.GPIO as GPIO
import time
import thread

class KrestartPlugin(octoprint.plugin.SettingsPlugin,
                     #octoprint.plugin.AssetPlugin,
                     octoprint.plugin.TemplatePlugin,
                     octoprint.plugin.StartupPlugin,
                     octoprint.plugin.ShutdownPlugin,
                     octoprint.plugin.RestartNeedingPlugin):

    def on_after_startup(self):
        self._logger.info("Krestart - startup")
        GPIO.setmode(GPIO.BOARD)
        led_pin = int(self._settings.get(["led_pin"]))
        btn_pin = int(self._settings.get(["btn_pin"]))
        self._logger.info("Krestart - L:{}, B:{}".format(led_pin, btn_pin))
        GPIO.setup(led_pin, GPIO.OUT)
        GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.output(led_pin, GPIO.LOW)
        GPIO.remove_event_detect(btn_pin)
        GPIO.add_event_detect(btn_pin, GPIO.FALLING, callback=self._btn_click, bouncetime=200)
        self._active = False
        self._clicks = 0
        self._led_status = False

    def on_shutdown(self):
        GPIO.cleanup()

    def _blink(self, wait=0.5, wait_after=0.5):
        led_pin = int(self._settings.get(["led_pin"])) 
        GPIO.output(led_pin, not self._led_status)
        time.sleep(wait)
        GPIO.output(led_pin, self._led_status)
        time.sleep(wait_after)


    def _execute_command(self):
        wait = float(self._settings.get(["click_timeout"]))
        self._logger.info("Krestart - thread wait {}".format(wait))
        time.sleep(wait)
        if self._clicks > 5 or not self._active:
            self._logger.info("Krestart - canceled")
            self._blink()
        elif self._clicks != 0:
            self._logger.info("Krestart - processing {} clicks".format(self._clicks))

            command, condition = {
                1: ("status", lambda self: True),
                2: ("firmware_restart", lambda self: self._printer.is_ready()),
                3: ("restart", lambda self: self._printer.is_ready()),
                4: ("M112", lambda self: True),
            }.get(self._clicks, ("", lambda self: False))
            
            self._logger.info("Krestart - preparing {}".format(command))
            if not condition(self):
                self._logger.info("Krestart - precondition failed. Aborting")
                self._blink()
            else:
                if not self._printer.commands(command):
                    self._logger.info("Krestart - command failed")
                    self._blink()

        self._blink(1.0, 0)
        self._active = False
        self._clicks = 0

    def _btn_click(self, channel=None):
        led_pin = int(self._settings.get(["led_pin"]))
        if not self._active:
            self._active = True
            self._clicks = 0
            thread.start_new_thread(self._execute_command, tuple())
        self._clicks += 1
        GPIO.output(led_pin, not self._led_status)
        time.sleep(0.1)
        GPIO.output(led_pin, self._led_status)
        self._logger.info("Krestart - click ({})".format(self._clicks))

    def get_settings_defaults(self):
        return dict(
            led_pin="11",
            btn_pin="12",
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

