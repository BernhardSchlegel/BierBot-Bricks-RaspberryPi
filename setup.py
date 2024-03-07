import os
import time
import uuid

import click
import yaml
from w1thermsensor import W1ThermSensor

config = {
    "meta": {"created": int(round(time.time() * 1000)), "platform": ""},
    "apikey": "",
    "device_id": "",
    "temperature_sensors": [],
    "relays": [],
    "start_fullscreen": False,
}


@click.command()
@click.option(
    "--apikey",
    "-a",
    prompt="Please enter your API key from bricks.bierbot.com",
    required=1,
)
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["RaspberryPi", "other"]),
    multiple=False,
    show_default=True,
    default="RaspberryPi",
    prompt="Select the platform you're on. Hit RETURN for RaspberryPi!",
    required=1,
)
@click.option("--relays", "-r", prompt="How many relays do you want to configure?", required=1)

def main(apikey: str, platform: str, relays: int) -> None:
    """Simple program that greets NAME for a total of COUNT times."""
    
    # Get the original UID and GID if running with sudo
    uid = int(os.getenv("SUDO_UID", os.getuid()))
    gid = int(os.getenv("SUDO_GID", os.getgid()))
    print(f"UID: {uid}")
    print(f"GID: {gid}")

    config["meta"]["platform"] = platform  # type: ignore [attr-defined,index]

    for i in range(0, int(relays)):
        gpio = click.prompt(
            f"Please enter the GPIO number for relay {i+1} (e.g. GPIO26 would be 37)",
            type=click.INT,
        )
        invert = click.prompt(f"Do you want to invert relay {i+1}?", default="n", type=click.BOOL)
        click.echo(f"setting relais {i+1} to GPRIO{gpio} (inverted={invert})..")
        config["relays"].append({"gpio": gpio, "invert": invert})  # type: ignore [attr-defined,index]

    scan = click.confirm(f"Do you want to scan for temperature probes now?", default=True)
    n_temperature_probes_found = 0
    if scan:
        temperature_sensor_ids = []

        for sensor in W1ThermSensor.get_available_sensors():
            click.echo("Sensor found: %s (T=%.2f°C)" % (sensor.id, sensor.get_temperature()))
            temperature_sensor_ids.append(sensor.id)

        n_temperature_probes_found = len(temperature_sensor_ids)
        click.echo(f"{n_temperature_probes_found} temperature probes found")

        for tsId in temperature_sensor_ids:
            click.echo(f"saving sensor {tsId} to config..")
            config["temperature_sensors"].append(tsId)  # type: ignore [attr-defined]

    config["apikey"] = apikey
    config["device_id"] = "python_" + platform + "_" + str(uuid.uuid1())

    # Call is_bookworm to determine if the OS is bookworm
    bookworm_flag = is_bookworm()

    create_autostart = click.prompt(
        f"Do you want us to add the BierBot Bricks service to autostart / bootup?",
        default="y",
        type=click.BOOL,
    )
    if create_autostart:
        click.echo("creating autostart...")
        current_directory = os.getcwd()

        click.echo("creating autostart file ./sys/bierbot.service...")

        # Using readlines()
        if bookworm_flag:
            template_file = open("./sys/bierbot.service.bookworm.template", "r")
        else:
            template_file = open("./sys/bierbot.service.template", "r")
        lines = template_file.readlines()
        lines_ready = [line.replace("$$$REPO_ROOT$$$", current_directory) for line in lines]
        template_file.close()

        # writing to file
        out_file = open("./sys/bierbot.service", "w")
        out_file.writelines(lines_ready)
        out_file.close()
        os.chown("./sys/bierbot.service", uid, gid)

        click.echo("copying service file to final location...")
        res = os.system("sudo cp ./sys/bierbot.service /etc/systemd/system/bierbot.service")
        click.echo(f"returned {res}. OK={res==0}")
        res = os.system("sudo chmod 644 /etc/systemd/system/bierbot.service")
        click.echo(f"chmodding went OK={res==0}")
        click.echo("enabling autostart...")
        res = os.system("sudo systemctl enable bierbot.service")
        click.echo(f"returned {res}. OK={res==0}")

    start_fullscreen = False

    start_ui = click.prompt(
        f"Do you the BierBot Bricks UI to be started on startup?",
        default="y",
        type=click.BOOL,
    )

    if create_autostart and start_ui:

        # Define the directory and file paths
        directory = os.path.expanduser("~/.config/autostart")
        file_path = os.path.join(directory, "bierbot.desktop")

        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        # Open the file, overwriting any old one, and write initial lines
        with open(file_path, "w") as file:
            file.write("[Desktop Entry]\n")
            file.write("Type=Application\n")
        
        # Set ownership of ~/.config/autostart/bierbot.desktop to current user
        os.chown(directory, uid, gid)
        os.chown(file_path, uid, gid)

        start_fullscreen = click.prompt(
            f"Do you want the status screen to be started in fullscreen?",
            default=True,
            type=click.BOOL,
        )

        if start_fullscreen:
            with open(file_path, "a") as file:
                file.write("Exec=chromium-browser --start-maximized --start-fullscreen --disable-session-crashed-bubble --disable-infobars https://bricks.bierbot.com/#/status\n")
        else:
            with open(file_path, "a") as file:
                file.write("Exec=chromium-browser --disable-session-crashed-bubble --disable-infobars https://bricks.bierbot.com/#/status\n")

    config["start_ui"] = start_ui
    config["start_fullscreen"] = start_fullscreen
    config["meta"]["create_autostart"] = create_autostart  # type: ignore [index]

    if n_temperature_probes_found + int(relays) > 3:
        click.secho(
            "WARNING: Currently, only 3 interfaces (Relay + Temperaure) are supported in the FREE tier.",
            fg="yellow",
            bold=True,
        )

    with open("bricks.yaml", "w") as outfile:
        yaml.dump(config, outfile, default_flow_style=False)
        click.echo("config file bricks.yml created.")

    with open("bricks.log", "w"):
        os.utime("bricks.log", None)
        
    # Set ownership of bricks.yaml to current user
    os.chown("bricks.yaml", uid, gid)
    os.chown("bricks.log", uid, gid)

    reboot = click.confirm(
        f"all done. Setup will exit. Do you want to reboot your {platform} (recommended)?",
        default=True,
    )
    if reboot:
        click.echo("rebooting now")
        res = os.system("sudo shutdown -r now")

# Module to check for bookworm
def is_bookworm():
    try:
        with open("/etc/os-release", "r") as file:
            for line in file:
                if line.lower().startswith("version_codename=bookworm"):
                    return True
    except FileNotFoundError:
        pass
    return False


if __name__ == "__main__":
    main()
