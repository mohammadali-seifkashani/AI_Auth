from django.http import HttpResponse
import pygame.camera
from django.shortcuts import render
from resemblyzer import preprocess_wav, VoiceEncoder
from itertools import groupby
from pathlib import Path
from tqdm import tqdm
import numpy as np
import face_recognition
import getpass
import random
import speech_recognition as sr
import subprocess
import convert_numbers
from os import listdir
from os.path import isfile, join


random_num = 0


def get_random_hadith():
    f = open('auth/hadith.txt', 'r')  # export PYTOHNPATH=$PYTHONPATH:$(pwd)
    texts = f.read().split('\n\n')
    hadith_count = len(texts)
    random_hadith_index1 = random.randint(0, hadith_count - 1)
    random_hadith_index2 = random.randint(0, hadith_count - 1)
    random_hadith_index3 = random.randint(0, hadith_count - 1)
    result = texts[random_hadith_index1] + '\n' + texts[random_hadith_index2] + '\n' + texts[random_hadith_index3]
    return result


def index(request):
    global random_num
    random_num = random.randint(0, 1000000000000000)
    context = {'number':random_num, 'hadith': get_random_hadith()}
    return render(request, 'auth/index.html', context)


def get_token():
    return 'token'


def submit(request):
    if 'email' in request.POST:
        takePictureAndStopCam('base')
        token = get_token()
        return HttpResponse(token)
    else:
        takePictureAndStopCam('new')
        face_equality = face_authentication()
        voice_equality, spoken_number_equlity = voice_authentication()
        token = get_token()
        string = str(face_equality) + '  ' + str(voice_equality) + '   ' + str(spoken_number_equlity)
        return HttpResponse(string)


def takePictureAndStopCam(filename):
    pygame.camera.init()
    pygame.camera.list_cameras()  # Camera detected or not
    cam = pygame.camera.Camera("/dev/video0", (640, 480))
    cam.start()
    img = cam.get_image()
    pygame.image.save(img, f"{filename}.jpg")
    cam.stop()


def face_authentication():
    known_image = face_recognition.load_image_file("base.jpg")
    unknown_image = face_recognition.load_image_file("new.jpg")

    biden_encoding = face_recognition.face_encodings(known_image)[0]
    unknown_encoding = face_recognition.face_encodings(unknown_image)[0]

    return face_recognition.compare_faces([biden_encoding], unknown_encoding)[0]


def voice_authentication():
    voice_equality = get_voice_equality()
    spoken_number_equality = conformity_percentage(str(get_spoken_number()), str(random_num))
    return voice_equality, spoken_number_equality


def conformity_percentage(str1, str2):
    counter = 0
    if len(str1) != len(str2):
        j = k = 0
        counter = abs(len(str1) - len(str2))
        for i in range(min(len(str1), len(str2))):
            if str1[j] != str2[k]:
                counter += 1
                k += 1
                continue
            j += 1
            k += 1
        result = 1 - counter / max(len(str1), len(str2))
        return result > .9
    else:
        for i in range(len(str1)):
            if str1[i] != str2[i]:
                counter += 1
        result = 1 - counter / len(str1)
        print('**************************************confomity: ', result)
        return result > .9


def get_spoken_number():
    onlyfiles = sorted([f for f in listdir('/home/mohammadali/Downloads/') if isfile(join('/home/mohammadali/Downloads/', f)) and f.endswith('ogg')])
    if onlyfiles[-2].startswith('base'):
        filename = onlyfiles[-1]
    else:
        filename = onlyfiles[-2].replace(' (', '\\ \\(').replace(')', '\\)')
    subprocess.run('ffmpeg -i ~/Downloads/{} ~/Downloads/audio.wav'.format(filename), shell=True, capture_output=True, input=b'y')

    r = sr.Recognizer()

    harvard = sr.AudioFile('/home/mohammadali/Downloads/audio.wav')
    with harvard as source:
        audio = r.record(source)

    result = r.recognize_google(audio, language='fa-IR').replace(' ', '')

    print('****************************************spoken vs given: ', convert_numbers.persian_to_english(result), random_num)
    return convert_numbers.persian_to_english(result)


def get_voice_equality():
    encoder = VoiceEncoder()

    wav_fpaths = list(Path("/home/{}/Downloads/".format(getpass.getuser())).glob("**/*.ogg"))
    if len(wav_fpaths) > 10:
        wav_fpaths = sorted(wav_fpaths)
        del wav_fpaths[3]

    speaker_wavs = {speaker: list(map(preprocess_wav, wav_fpaths)) for speaker, wav_fpaths in
                    groupby(tqdm(wav_fpaths, "Preprocessing wavs", len(wav_fpaths), unit="wavs"),
                            lambda wav_fpath: wav_fpath.parent.stem)}

    spk_embeds_a = np.array([encoder.embed_speaker(wavs[:len(wavs) // 2]) for wavs in speaker_wavs.values()])
    spk_embeds_b = np.array([encoder.embed_speaker(wavs[len(wavs) // 2:]) for wavs in speaker_wavs.values()])
    spk_sim_matrix = np.inner(spk_embeds_a, spk_embeds_b)

    print('**********************************voice_equality: ', spk_sim_matrix[0][0])
    return spk_sim_matrix[0][0] > 0.93
