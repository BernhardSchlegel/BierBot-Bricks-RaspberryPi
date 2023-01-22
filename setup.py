import click
import yaml
import time
import uuid
from w1thermsensor import W1ThermSensor
from mcp9600 import MCP9600, I2C_ADDRESSES
import os

config = {
    "meta": {
        "created": int(round(time.time() * 1000)),
        "platform": ""
    },
    "apikey": "",
    "device_id": "",
    "temperature_sensors_mcp9600": [],
    "temperature_sensors_w1": [],
    "relays": []
}


@click.command()
@click.option('--apikey', "-a",
              prompt='Please enter your API key from bricks.bierbot.com',
              required=1)
@click.option('--platform', '-p',
              type=click.Choice(["RaspberryPi", "other"]), multiple=False, show_default=True,
              default="RaspberryPi",
              prompt="Select the platform you're on. Hit RETURN for RaspberryPi!",
              required=1)
@click.option('--relays', "-r",
              prompt='How many relays do you want to configure?',
              required=1)
def main(apikey, platform, relays):
    """Simple program that greets NAME for a total of COUNT times."""
    config["meta"]["platform"] = platform


    for i in range(0, int(relays)):
        gpio = click.prompt(f"Please enter the GPIO number for relay {i+1} (e.g. GPIO26 would be 37)",
                     type=click.INT)
        invert = click.prompt(f"Do you want to invert relay {i+1}?",
                            default="n",
                            type=click.BOOL)
        click.echo(f"setting relais {i+1} to GPRIO{gpio} (inverted={invert})..")
        config["relays"].append({
            "gpio": gpio,
            "invert": invert
        })

    scan = click.confirm(f"Do you want to scan for temperature probes now?",
                  default="y")
    if scan:
        
        for sensor_type in ("w1", "mcp9600"):
            if click.confirm(f"Scan for {sensor_type!r} sensors?", default="y"):
            
                config_key = f"temperature_sensors_{sensor_type}"
                n_temperature_probes_found = 0
                temperature_sensor_ids = []

                if sensor_type == "w1":
        
                    for sensor in W1ThermSensor.get_available_sensors():
                        click.echo("Sensor found: %s (T=%.2f°C)" % (sensor.id, sensor.get_temperature()))
                        temperature_sensor_ids.append(sensor.id)
            
                elif sensor_type =='mcp9600':
                    
                    for addr in I2C_ADDRESSES:
                        try:
                            device = MCP9600(i2c_addr=addr)
                        except RuntimeError:
                            continue
                        click.echo(f"Sensor found: {addr=} {device.get_hot_junction_temperature()}")
                        temperature_sensor_ids.append(device._i2c_addr)
            
                n_temperature_probes_found = len(temperature_sensor_ids)
                click.echo(f"{n_temperature_probes_found} temperature probes found")
                config.setdefault(config_key, [])
                config[config_key].extend(temperature_sensor_ids)


    config["apikey"] = apikey
    config["device_id"] = "python_" + platform + "_" + str(uuid.uuid1())

    create_autostart = click.prompt(f"Do you want us to add the BierBot Bricks service to autostart / bootup?",
                                    default="y",
                                    type=click.BOOL)
    if create_autostart:
        click.echo("creating autostart...")
        currentDirectory = os.getcwd()
        
        click.echo("creating autostart file ./sys/bierbot.service...")
        
        # Using readlines()
        template_file = open('./sys/bierbot.service.template', 'r')
        lines = template_file.readlines()
        lines_ready = [line.replace("$$$REPO_ROOT$$$", currentDirectory) for line in lines]
        template_file.close()
        
        # writing to file
        out_file = open('./sys/bierbot.service', 'w')
        out_file.writelines(lines_ready)
        out_file.close()
 
        click.echo("copying service file to final location...")
        res = os.system("sudo cp ./sys/bierbot.service /etc/systemd/system/bierbot.service")
        click.echo(f"returned {res}. OK={res==0}")
        res = os.system("sudo chmod 644 /etc/systemd/system/bierbot.service")
        click.echo(f"chmodding went OK={res==0}")
        click.echo("enabling autostart...")
        res = os.system("sudo systemctl enable bierbot.service")
        click.echo(f"returned {res}. OK={res==0}")

    start_fullscreen = False
    

    start_ui = click.prompt(f"Do you the BierBot Bricks UI to be started on startup?",
                                    default="y",
                                    type=click.BOOL)
    
    if create_autostart and start_ui:
        start_fullscreen = click.prompt(f"Do you want the status screen to be started in fullscreen?",
                                        default="y",
                                        type=click.BOOL)
        
        if  start_fullscreen:
            # sudo tee necessary instead of &>> because of "sudo" requirements
            os.system('echo "chromium-browser --start-fullscreen --disable-session-crashed-bubble --disable-infobars https://bricks.bierbot.com/#/status" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart')
        else:
            os.system('echo "chromium-browser --disable-session-crashed-bubble --disable-infobars https://bricks.bierbot.com/#/status" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart')

    config["start_ui"] = start_ui
    config["start_fullscreen"] = start_fullscreen
    config["meta"]["create_autostart"] = create_autostart

    if n_temperature_probes_found + int(relays) > 3:
        click.secho("WARNING: Currently, only 3 interfaces (Relay + Temperaure) are supported.", fg='yellow', bold=True)

    with open('bricks.yaml', 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)
        click.echo("config file bricks.yml created.")

    reboot = click.confirm(f"all done. Setup will exit. Do you want to reboot your {platform} (recommended)?",
                  default="y")
    if reboot:
        click.echo("rebooting now")
        res = os.system("sudo shutdown -r now")

if __name__ == '__main__':
    main()
