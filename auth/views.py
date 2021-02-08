from django.http import HttpResponse
from django.shortcuts import render
import pygame.camera


def index(request):
    return render(request, 'auth/index.html')


def submit(request):
    pygame.camera.init()
    pygame.camera.list_cameras()  # Camera detected or not
    cam = pygame.camera.Camera("/dev/video0", (640, 480))
    cam.start()
    img = cam.get_image()
    pygame.image.save(img, "filename3.jpg")
    cam.stop()
    return HttpResponse('fawef')


def face():
    import cv2
    import face_recognition

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
