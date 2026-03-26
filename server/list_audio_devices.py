import sounddevice as sd


def main():
    devices = sd.query_devices()
    for index, device in enumerate(devices):
        in_channels = device.get("max_input_channels", 0)
        out_channels = device.get("max_output_channels", 0)
        print(
            f"[{index}] {device['name']} | input={in_channels} | output={out_channels}"
        )


if __name__ == "__main__":
    main()
