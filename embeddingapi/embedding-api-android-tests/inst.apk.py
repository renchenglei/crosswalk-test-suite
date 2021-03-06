#!/usr/bin/env python

import os
import shutil
import glob
import time
import sys
import subprocess
from optparse import OptionParser, make_option


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARAMETERS = None
ADB_CMD = "adb"


def doCMD(cmd):
    # Do not need handle timeout in this short script, let tool do it
    print "-->> \"%s\"" % cmd
    output = []
    cmd_return_code = 1
    cmd_proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    while True:
        output_line = cmd_proc.stdout.readline().strip("\r\n")
        cmd_return_code = cmd_proc.poll()
        if output_line == '' and cmd_return_code is not None:
            break
        sys.stdout.write("%s\n" % output_line)
        sys.stdout.flush()
        output.append(output_line)

    return (cmd_return_code, output)


def uninstResources():
    action_status = True
    cmd = "%s -s %s shell rm -r /sdcard/device_files" % (
        ADB_CMD, PARAMETERS.device)
    (return_code, output) = doCMD(cmd)
    return action_status


def instResources():
    action_status = True
    source_path = os.path.join(SCRIPT_DIR, "device_files")
    if os.path.exists(source_path):
        cmd = "%s -s %s push %s /sdcard/" % (
            ADB_CMD, PARAMETERS.device,source_path)
    (return_code, output) = doCMD(cmd)
    return action_status


def uninstPKGs():
    action_status = True
    for root, dirs, files in os.walk(SCRIPT_DIR):
        for file in files:
            if file.endswith(".apk"):
                index_start = str(file).index("_")
                index_end = str(file).index(".")
                cmd = "%s -s %s uninstall org.xwalk.embedding.test.%s" % (
                    ADB_CMD, PARAMETERS.device, str(file)[index_start + 1: index_end])
                (return_code, output) = doCMD(cmd)
                for line in output:
                    if "Failure" in line:
                        action_status = False
                        break
    if action_status:
        uninstResources()

    return action_status


def instPKGs():
    action_status = True
    for root, dirs, files in os.walk(SCRIPT_DIR):
        for file in files:
            if file.endswith(".apk"):
                cmd = "%s -s %s install %s" % (ADB_CMD,
                                               PARAMETERS.device, os.path.join(root, file))
                (return_code, output) = doCMD(cmd)
                for line in output:
                    if "Failure" in line:
                        action_status = False
                        break
    if action_status:
        instResources()

    return action_status


def main():
    try:
        usage = "usage: inst.py -i"
        opts_parser = OptionParser(usage=usage)
        opts_parser.add_option(
            "-s", dest="device", action="store", help="Specify device")
        opts_parser.add_option(
            "-i", dest="binstpkg", action="store_true", help="Install package")
        opts_parser.add_option(
            "-u", dest="buninstpkg", action="store_true", help="Uninstall package")
        global PARAMETERS
        (PARAMETERS, args) = opts_parser.parse_args()
    except Exception as e:
        print "Got wrong option: %s, exit ..." % e
        sys.exit(1)

    if not PARAMETERS.device:
        (return_code, output) = doCMD("adb devices")
        for line in output:
            if str.find(line, "\tdevice") != -1:
                PARAMETERS.device = line.split("\t")[0]
                break

    if not PARAMETERS.device:
        print "No device found"
        sys.exit(1)

    if PARAMETERS.binstpkg and PARAMETERS.buninstpkg:
        print "-i and -u are conflict"
        sys.exit(1)

    if PARAMETERS.buninstpkg:
        if not uninstPKGs():
            sys.exit(1)
    else:
        if not instPKGs():
            sys.exit(1)

if __name__ == "__main__":
    main()
    sys.exit(0)
