from django.http import HttpResponse
from django.shortcuts import render
import pygame.camera
from resemblyzer import preprocess_wav, VoiceEncoder
from itertools import groupby
from pathlib import Path
from tqdm import tqdm
import numpy as np
import cv2
import face_recognition
import getpass


def index(request):
    return render(request, 'auth/index.html')


def submit(request):
    takePictureAndStopCam()
    print(request.POST['email'])
    return HttpResponse(str(request.POST))


def takePictureAndStopCam():
    pygame.camera.init()
    pygame.camera.list_cameras()  # Camera detected or not
    cam = pygame.camera.Camera("/dev/video0", (640, 480))
    cam.start()
    img = cam.get_image()
    pygame.image.save(img, "filename3.jpg")
    cam.stop()


def face():
    image = cv2.imread('filename.jpg')
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb)
    encoding1 = face_recognition.face_encodings(rgb, boxes)

    # read 2nd image and store encoding
    image = cv2.imread('filename3.jpg')
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb)
    encoding2 = face_recognition.face_encodings(rgb, boxes)

    known_face_encodings = [encoding1]

    # now you can compare two encodings
    # optionally you can pass threshold, by default it is 0.6
    matches = face_recognition.compare_faces(known_face_encodings, encoding2[0], tolerance=0.06)
    print(matches)


def voice():
    encoder = VoiceEncoder()

    wav_fpaths = list(Path("/home/{}/Downloads/".format(getpass.getuser())).glob("**/*.ogg"))

    speaker_wavs = {speaker: list(map(preprocess_wav, wav_fpaths)) for speaker, wav_fpaths in
                    groupby(tqdm(wav_fpaths, "Preprocessing wavs", len(wav_fpaths), unit="wavs"),
                            lambda wav_fpath: wav_fpath.parent.stem)}

    spk_embeds_a = np.array([encoder.embed_speaker(wavs[:len(wavs) // 2]) for wavs in speaker_wavs.values()])
    spk_embeds_b = np.array([encoder.embed_speaker(wavs[len(wavs) // 2:]) for wavs in speaker_wavs.values()])
    spk_sim_matrix = np.inner(spk_embeds_a, spk_embeds_b)

    print(spk_sim_matrix)