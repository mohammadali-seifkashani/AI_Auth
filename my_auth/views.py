import ast
import base64
import os
import shutil
import uuid
from django.http import JsonResponse
from django.shortcuts import render
from resemblyzer import preprocess_wav, VoiceEncoder
from itertools import groupby
from pathlib import Path
from rest_framework.authtoken.models import Token
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from tqdm import tqdm
import numpy as np
import face_recognition
import random
import speech_recognition as sr
import subprocess
import convert_numbers
from my_auth.models import MyUser
from .customauth import ExampleAuthentication


random_num = 0


def index(request):
    global random_num
    random_num = random.randint(0, 10000000000)
    context = {'number': random_num, 'hadith': get_random_hadith()}
    return render(request, 'my_auth/index.html', context)


def submit(request):
    response = get_dict_from_bytes(request.body)
    if 'email' in response:  # sign-up
        email = response['email']
        password = response['password']
        image_dir_path = f'media/images/{email}'
        voice_dir_path = f'media/voices/{email}'
        try:
            os.mkdir(image_dir_path)
            os.mkdir(voice_dir_path)
        except FileExistsError:
            return JsonResponse({'error': 'Email Already Exists!'})

        user = MyUser.objects.create(email=email, revealing_password=password)
        save_image(email, response['image'][22:], 'base')
        save_voice(email, response['audio1'][32:], 'base1')
        save_voice(email, response['audio2'][32:], 'base2')
        save_voice(email, response['audio3'][32:], 'base3')

        token = Token.objects.create(user=user)
        json_response = JsonResponse({'token': token.key})
        return json_response
    else:  # sign-in
        filename = uuid.uuid4().__str__()
        user = check_static_password_and_get_user(response['audio1'][32:], filename)
        if not user:
            return JsonResponse({'error': 'Invalid User!'})

        move_first_audio_to_user_voices_folder(user.email, filename)
        save_voice(user.email, response['audio2'][32:], 'new')
        save_image(user.email, response['image'][22:], 'new')

        face_equality = face_authentication(user.email)

        if not face_equality:
            remove_fiels_of_signin(user.email, filename)
            return JsonResponse({'error': 'Invalid User Face!'})

        voice_equality, spoken_number_equlity = voice_authentication(user.email)
        if not voice_equality:
            remove_fiels_of_signin(user.email, filename)
            return JsonResponse({'error': 'Invalid User Voice!'})
        if not spoken_number_equlity:
            remove_fiels_of_signin(user.email, filename)
            return JsonResponse({'error': 'Spoken Captcha Number not Equal!'})

        remove_fiels_of_signin(user.email, filename)

        token_str = Token.objects.get(user=user).key
        json_response = JsonResponse({'token': token_str})
        return json_response


class HomePageView(APIView):
    authentication_classes = [ExampleAuthentication]
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'my_auth/home.html'

    def get(self, request):
        response = Response({'profiles': 2})
        return response


def save_image(email, image_base64, name):
    imgdata = base64.b64decode(image_base64)
    filename = f'media/images/{email}/{name}.jpg'
    with open(filename, 'wb') as f:
        f.write(imgdata)


def save_voice(email, voice_base64, name):
    if voice_base64 == '':
        return
    voicedata = base64.b64decode(voice_base64)
    filename = f'media/voices/{email}/{name}.ogg'
    with open(filename, 'wb') as f:
        f.write(voicedata)


def check_static_password_and_get_user(voice_base64, filename):
    wav_file = open("media/voices/{}.ogg".format(filename), "wb")
    decode_string = base64.b64decode(voice_base64)
    wav_file.write(decode_string)
    try:
        spoken_number = get_spoken_number(filename)
        user = MyUser.objects.get(revealing_password=spoken_number)
    except Exception:
        return None
    return user


def move_first_audio_to_user_voices_folder(email, filename):
    filepath = f'/home/mohammadali/PycharmProjects/AI_Auth/media/voices/{filename}.ogg'
    destination_path = f'/home/mohammadali/PycharmProjects/AI_Auth/media/voices/{email}/{filename}.ogg'
    os.remove(filepath.replace('ogg', 'wav'))
    os.replace(filepath, destination_path)


def face_authentication(email):
    path = f'/home/mohammadali/PycharmProjects/AI_Auth/media/images/{email}'
    known_image = face_recognition.load_image_file(f"{path}/base.jpg")
    unknown_image = face_recognition.load_image_file(f"{path}/new.jpg")

    try:
        biden_encoding = face_recognition.face_encodings(known_image)[0]
        unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
    except Exception:
        return False

    return face_recognition.compare_faces([biden_encoding], unknown_encoding)[0]


def voice_authentication(email):
    global random_num
    voice_equality = get_voice_equality(email)
    spoken_number_equality = conformity_percentage(get_spoken_number(email + '/new'), str(random_num))
    return voice_equality, spoken_number_equality


def get_voice_equality(email):
    encoder = VoiceEncoder()

    wav_fpaths = list(Path(f"/home/mohammadali/PycharmProjects/AI_Auth/media/voices/{email}").glob("**/*.ogg"))

    speaker_wavs = {speaker: list(map(preprocess_wav, wav_fpaths)) for speaker, wav_fpaths in
                    groupby(tqdm(wav_fpaths, "Preprocessing wavs", len(wav_fpaths), unit="wavs"),
                            lambda wav_fpath: wav_fpath.parent.stem)}

    spk_embeds_a = np.array([encoder.embed_speaker(wavs[:len(wavs) // 2]) for wavs in speaker_wavs.values()])
    spk_embeds_b = np.array([encoder.embed_speaker(wavs[len(wavs) // 2:]) for wavs in speaker_wavs.values()])
    spk_sim_matrix = np.inner(spk_embeds_a, spk_embeds_b)

    print(spk_sim_matrix[0][0])
    return spk_sim_matrix[0][0] > 0.93


def get_spoken_number(file_path_name):
    base_path = '/home/mohammadali/PycharmProjects/AI_Auth/media/voices/'
    file_path = base_path + file_path_name
    subprocess.run(f'ffmpeg -i {file_path}.ogg {base_path}{file_path_name}.wav',
                   shell=True, capture_output=True, input=b'y')
    r = sr.Recognizer()
    harvard = sr.AudioFile(f'{base_path}{file_path_name}.wav')
    with harvard as source:
        audio = r.record(source)
    result = r.recognize_google(audio, language='fa-IR')
    print(convert_numbers.persian_to_english(result))
    return convert_numbers.persian_to_english(result)


def get_random_hadith():
    f = open('my_auth/hadith.txt', 'r')  # export PYTOHNPATH=$PYTHONPATH:$(pwd)
    texts = f.read().split('\n\n')
    hadith_count = len(texts)
    random_hadith_index1 = random.randint(0, hadith_count - 1)
    random_hadith_index2 = random.randint(0, hadith_count - 1)
    random_hadith_index3 = random.randint(0, hadith_count - 1)
    result = texts[random_hadith_index1] + '\n' + texts[random_hadith_index2] + '\n' + texts[random_hadith_index3]
    return result


def remove_fiels_of_signin(email, filename):
    base_path = '/home/mohammadali/PycharmProjects/AI_Auth/media/'
    base_voices_path = base_path + f'voices/{email}/'
    base_images_path = base_path + f'images/{email}/'
    os.remove(base_voices_path + f'{filename}.ogg')
    os.remove(base_voices_path + 'new.ogg')
    os.remove(base_voices_path + 'new.wav')
    os.remove(base_images_path + 'base.jpg')
    os.rename(base_images_path + 'new.jpg', base_images_path + 'base.jpg')


def testing_removing():
    shutil.rmtree('media/images/')
    shutil.rmtree('media/voices/')
    os.mkdir('media/images/')
    os.mkdir('media/voices')
    MyUser.objects.all().delete()


def get_dict_from_bytes(bytes_object):
    dict_str = bytes_object.decode("UTF-8")
    return ast.literal_eval(dict_str)


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
        return result > .9
