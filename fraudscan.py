#!/usr/bin/python3

import os
import re
import cv2
import time
import pytesseract
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

TEMP_DIR = 'temp'
EVIDENCE_DIR = 'evidence'
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def extract_frames(filepath, file, interval):
    # check if the file is a video file
    _, ext = os.path.splitext(filepath)
    if ext not in ['.mp4', '.avi', '.mkv']:
        return

    # use OpenCV to extract frames
    try:
        cap = cv2.VideoCapture(filepath)
    except:
        print("Failed to load video")   

    try:     
        fps = int(cap.get(cv2.CAP_PROP_FPS))
    except:
        print("Failed to load video (fps)")

    frame_count = 0
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_count > 1200: # 10 Minutes (hard stop) every 30 seconds snapshot
           cap.release()
           break

        if frame_count % (fps * interval) == 0:
            try:
                temp_frame = os.path.join(TEMP_DIR, f'inspect_{file}_{frame_count}.jpg')
                temp_content = os.path.join(TEMP_DIR, f'content_{file}_{frame_count}.dat')
                cv2.imwrite(temp_frame, frame)
            except:
                print("Failed to analyze video")
            try:
                data = pytesseract.image_to_string(temp_frame, config='-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz01234567890.://@%?=&,;_- ') # Tune OCR 
                
                #
                # ML model goes here basic
                #
                
                keywords = {
                            'social': ['snapchat','facebook','tiktok','instagram','framatalk','discord','youtube','omegle'],
                            'gambling':['draftkings','gambling'],
                            'pornography':['porn','pornhub','xhamster','xvidoes','sex'],
                            'games':['roblox','steam','minecraf','now.gg','fortnite'],
                            'crypto':['miner','crypto'],
                            'hacking':['masscan'],
                            'proxies':['proxy','socks5','browserling','homeworkistrash','vpn'],
                            'software':['downloads','setup','.exe','.zip','github','anonfiles'],
                            'accounts':['password','inbox'],
                            'illegal':['torrent','checker']
                        }

                keystore = []
                for key, values in keywords.items():
                    for value in values:
                        keystore.append([key, value])

                for category,keyword in keystore:
                    
                    fraud = re.search(keyword, data)

                    if fraud is not None:
                        evidence_frame = os.path.join(EVIDENCE_DIR, f'{category}_{file}_{frame_count}.jpg')
                        evidence_content = os.path.join(EVIDENCE_DIR, f'{category}_{file}_{frame_count}.dat')
                        cv2.imwrite(evidence_frame, frame)
                        with open(evidence_content, 'a') as f:
                            f.write(data)

            except:
                print("OCR Reading Error")
        frame_count += 1
    cap.release()

def list_files(directory):
    directory = os.path.abspath(directory)
    for root, dirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(root, file)
            print(path)
            executor = ThreadPoolExecutor(max_workers=4)
            executor.submit(extract_frames,path,file,30)
            time.sleep(1.1) # prevents runway threads tune 


list_files("videos/") # Change this to location of video files in mp4, avi, mkv formats
