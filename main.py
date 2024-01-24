from webserver.phew import access_point, connect_to_wifi, is_connected_to_wifi, dns, server
from webserver.phew.template import render_template
import json
import machine
import os
import time
import _thread
from alarm_manager import Alarm

Alarm.getAlarmListfromJson()
print(Alarm.alarm_list)


AP_NAME = "pi pico"
AP_DOMAIN = "pipico.net"
PACKAGES_PATH = "webserver"
AP_TEMPLATE_PATH = PACKAGES_PATH + "/ap_templates"
APP_TEMPLATE_PATH = PACKAGES_PATH + "/app_templates"
WIFI_FILE = PACKAGES_PATH + "/wifi.json"
WIFI_MAX_ATTEMPTS = 3

def machine_reset():
    time.sleep(1)
    print("Resetting...")
    machine.reset()

def convert_unix_to_datetime_local(unix_time=None):
    if unix_time is None:
        unix_time = time.time()
    year, month, day, hour, minute, _, _, _ = time.localtime(unix_time)
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}".format(year, month, day, hour, minute)

def convert_datetime_local_to_unix(datetime_time):
    date_part, time_part = datetime_time.split('T')
    year, month, day     = map(int, date_part.split('-'))
    hour, minute         = map(int, time_part.split(':'))
    tm = (year, month, day, hour, minute, 0, -1, -1, -1)
    unix_timestamp = time.mktime(tm)
    return unix_timestamp


def setup_mode():
    print("Entering setup mode...")
    
    def ap_index(request):
        if request.headers.get("host").lower() != AP_DOMAIN.lower():
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN.lower())

        return render_template(f"{AP_TEMPLATE_PATH}/index.html")

    def ap_configure(request):
        print("Saving wifi credentials...")

        with open(WIFI_FILE, "w") as f:
            json.dump(request.form, f)
            f.close()

        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{AP_TEMPLATE_PATH}/configured.html", ssid = request.form["ssid"])
        
    def ap_catch_all(request):
        if request.headers.get("host") != AP_DOMAIN:
            return render_template(f"{AP_TEMPLATE_PATH}/redirect.html", domain = AP_DOMAIN)

        return "Not found.", 404

    server.add_route("/", handler = ap_index, methods = ["GET"])
    server.add_route("/configure", handler = ap_configure, methods = ["POST"])
    server.set_callback(ap_catch_all)

    ap = access_point(AP_NAME)
    ip = ap.ifconfig()[0]
    dns.run_catchall(ip)

def application_mode():
    print("Entering application mode.")
    onboard_led = machine.Pin("LED", machine.Pin.OUT)

    def app_index(request):
        return render_template(f"{APP_TEMPLATE_PATH}/index.html")

    def app_toggle_led(request):
        onboard_led.toggle()
        return "OK"
    
    def app_get_time(request):
        return f"{time.gmtime()[3]:02d}:{time.gmtime()[4]:02d}"
    
    def app_get_date(request):
        return f"{time.gmtime()[2]:02d}.{time.gmtime()[1]:02d}.{time.gmtime()[0]:04d}"
    
    def app_reset(request):
        # Deleting the WIFI configuration file will cause the device to reboot as
        # the access point and request new configuration.
        os.remove(WIFI_FILE)
        # Reboot from new thread after we have responded to the user.
        _thread.start_new_thread(machine_reset, ())
        return render_template(f"{APP_TEMPLATE_PATH}/reset.html", access_point_ssid = AP_NAME)

    def app_set_alarm(request):
        # Get alarm time from request
        time = request.form.get("alarmtime")
        hour, minute = map(int, time.split(':'))

        # Check for repeat
        mon = True if request.form.get("cbox_mon") == "on" else False
        tue = True if request.form.get("cbox_tue") == "on" else False
        wed = True if request.form.get("cbox_wed") == "on" else False
        thu = True if request.form.get("cbox_thu") == "on" else False
        fri = True if request.form.get("cbox_fri") == "on" else False
        sat = True if request.form.get("cbox_sat") == "on" else False
        sun = True if request.form.get("cbox_sun") == "on" else False
        repeat = 1 if (mon or tue or wed or thu or fri or sat or sun) else 0
        
        # Set weekdays
        if repeat == 1:
            weekday = ''.join(['1' if day else '0' for day in [mon, tue, wed, thu, fri, sat, sun]])
            weekday_str = weekday
        else:
            weekday = "11111111"
            weekday_str = "Einmalig"

        # Add alarm to list
        alarm = Alarm.addAlarm(hour, minute, repeat, weekday)
        sec_till_alarm = alarm["time"] - time.time()
        print(f"Alarm set for {sec_till_alarm} seconds from now.")
        return render_template(f"{APP_TEMPLATE_PATH}/setalarm.html", alarmtime=time, weekdays=weekday_str)

    
    def app_catch_all(request):
        return "Not found.", 404

    server.add_route("/", handler = app_index, methods = ["GET"])
    server.add_route("/time", handler = app_get_time, methods = ["GET"])
    server.add_route("/date", handler = app_get_date, methods = ["GET"])
    server.add_route("/toggle", handler = app_toggle_led, methods = ["GET"])
    server.add_route("/reset", handler = app_reset, methods = ["GET"])
    server.add_route("/time", handler = app_get_time, methods = ["GET"])
    server.add_route("/setalarm", handler = app_set_alarm, methods = ["POST"])
    # Add other routes for your application...
    server.set_callback(app_catch_all)

# Figure out which mode to start up in...
try:
    os.stat(WIFI_FILE)

    # File was found, attempt to connect to wifi...
    with open(WIFI_FILE) as f:
        wifi_current_attempt = 1
        wifi_credentials = json.load(f)
        
        while (wifi_current_attempt < WIFI_MAX_ATTEMPTS):
            ip_address = connect_to_wifi(wifi_credentials["ssid"], wifi_credentials["password"])

            if is_connected_to_wifi():
                print(f"Connected to wifi, IP address {ip_address}")
                break
            else:
                wifi_current_attempt += 1
                
        if is_connected_to_wifi():
            application_mode()
        else:
            
            # Bad configuration, delete the credentials file, reboot
            # into setup mode to get new credentials from the user.
            print("Bad wifi connection!")
            print(wifi_credentials)
            os.remove(WIFI_FILE)
            machine_reset()

except Exception:
    # Either no wifi configuration file found, or something went wrong, 
    # so go into setup mode.
    setup_mode()

# Start the web server...
server.run()