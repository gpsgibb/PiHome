import subprocess

def command(cmd):
    out = subprocess.check_output(cmd)
    out=out.decode().rstrip()
    return "%s"%out
