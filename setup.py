import click
import yaml
import time
import uuid

config = {
    "meta": {
        "created": int(round(time.time() * 1000)),
        "platform": ""
    },
    "apikey": "",
    "device_id": "",
    "temperature_sensors": [],
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
                            default=False,
                            type=click.BOOL)
        click.echo(f"setting relais {i+1} to GPRIO{gpio} (inverted={invert})..")
        config["relays"].append({
            "gpio": gpio,
            "invert": invert
        })

    scan = click.confirm(f"Do you want to scan for temperature probes now?",
                  default="y")
    if scan:
        temperature_sensor_id = ["aaa", "bb"]
        n_found = len(temperature_sensor_id)
        click.echo(f"{n_found} temperature probes found")

        for tsId in temperature_sensor_id:
            click.echo(f"saving sensor {tsId} to config..")
            config["temperature_sensors"].append(tsId)

    config["apikey"] = apikey
    config["device_id"] = "python_" + platform + "_" + str(uuid.uuid1())

    with open('bricks.yml', 'w') as outfile:
        yaml.dump(config, outfile, default_flow_style=False)
        click.echo("configfile bricks.yml created.")

    click.confirm(f"all done. Setup will exit. Do you want to reboot your {platform} (recommended)?",
                  default="y")

if __name__ == '__main__':
    main()