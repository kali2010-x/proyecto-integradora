"""sistema.py - Lecturas del estado de la Raspberry (temperatura, throttling, frecuencias)."""
import os, subprocess, struct


def _vcgencmd(*args):
    try:
        return subprocess.run(["vcgencmd", *args], capture_output=True, text=True, timeout=2).stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def temperatura_c():
    s = _vcgencmd("measure_temp")            # "temp=49.6'C"
    try:
        return float(s.split("=")[1].split("'")[0])
    except (IndexError, ValueError):
        return None


def throttled():
    s = _vcgencmd("get_throttled")           # "throttled=0x0"
    return s.split("=")[1] if "=" in s else None


def frecuencia_cpu_mhz():
    try:
        return int(open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").read()) / 1000
    except OSError:
        return None


def frecuencia_bus_i2c_hz(bus):
    """Lee la frecuencia de reloj configurada en el device tree para /dev/i2c-<bus>."""
    ruta = f"/sys/class/i2c-adapter/i2c-{bus}/of_node/clock-frequency"
    try:
        return struct.unpack(">I", open(ruta, "rb").read()[:4])[0]
    except OSError:
        return None


def estado(bus=None):
    d = {"temp_c": temperatura_c(), "throttled": throttled(), "cpu_mhz": frecuencia_cpu_mhz()}
    if bus is not None:
        d["i2c_hz"] = frecuencia_bus_i2c_hz(bus)
    return d


if __name__ == "__main__":
    print(estado(bus=3))
