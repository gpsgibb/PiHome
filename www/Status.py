import subprocess

#executes a shell command and returns its output
def command(cmd):
    out = subprocess.check_output(cmd)
    out=out.decode().rstrip()
    return "%s"%out
