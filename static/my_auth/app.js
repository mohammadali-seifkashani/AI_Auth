var video = document.querySelector("#videoElement");

if (navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({video: true})
        .then(function (stream) {
            video.srcObject = stream;
        })
        .catch(function (err0r) {
            console.log("Something went wrong!");
        });

}

var width = 500;    // We will scale the photo width to this
var height = 400;     // This will be computed based on the input stream

function takepicture() {
    video = document.getElementById('videoElement');
    canvas2 = document.getElementById('canvas');
    photo = document.getElementById('photo');
    var context = canvas2.getContext('2d');
    if (width && height) {
        canvas2.width = width;
        canvas2.height = height;
        context.drawImage(video, 0, 0, width, height);

        var data = canvas2.toDataURL('image/png');
        image = document.getElementById('image');
        image.value = data;

        photo.setAttribute('src', data);
    }
}

function signin_click() {
    help_text = 'لطفا در صوت اول پسورد اول (ایستا) خودتان را و در صوت دوم عدد زیر را (هریک) دو رقم-دو رقم و یا سه رقم-سه رقم از سمت چپ با تلفظ فارسی بخوانید.';
    h40 = header.children[0];
    h40.innerHTML = help_text;
    h41.innerHTML = number;
    email_exists = false;
}

function signup_click() {
    help_text = 'لطفا جملات زیر را با لذت  در سه صوت بخوانید: 😊';
    h40 = header.children[0];
    h40.innerHTML = help_text;
    h41.innerHTML = speaking_text;
    email_exists = true;
}

function stop_webcam() {
    var stream = video.srcObject;
    var tracks = stream.getTracks();

    for (var i = 0; i < tracks.length; i++) {
        var track = tracks[i];
        track.stop();
    }
    video.srcObject = null;
}

function submit(){
    takepicture();

    if (email_exists) {
        for (i = 0; i < 3; i++) {
            let audio_num = `audio${i+1}`;
            console.log(audio_num);
            audio = document.getElementById(audio_num);
            audio.value = url[i];
        }
    } else {
        audio = document.getElementById('audio1');
        audio.value = url[0];
        audio = document.getElementById('audio2');
        audio.value = url[1];
    }
    window.URL.revokeObjectURL(url);

    let image_value = document.getElementById('image').value;
    let audio1_value = document.getElementById('audio1').value;
    let audio2_value = document.getElementById('audio2').value;
    let audio3_value = document.getElementById('audio3').value;

    csrftoken = null;
    let data = {'image': image_value, 'audio1': audio1_value, 'audio2': audio2_value, 'audio3': audio3_value};
    if (email_exists) {
        let email = document.getElementById('email').value;
        let password = document.getElementById('password').value;
        let fiels_ok = true;
        if (email  === '') {
            document.getElementById('email_empty').style.display = 'block';
            fiels_ok = false;
        }
        if (password === '') {
            document.getElementById('password_empty').style.display = 'block';
            fiels_ok = false;
        }
        if (!fiels_ok) {
            alert('لطفا فیلدهای خواسته شده را پر کنید.');
            return;
        }

        data['email'] = email;
        data['password'] = password;
        csrftoken = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    } else {
        csrftoken = document.getElementsByName('csrfmiddlewaretoken')[1].value;
    }

    let token = null;

    (async () => {
        const rawResponse = await fetch('http://127.0.0.1:8000/auth/submit/', {
            method: 'POST',
            mode: 'cors', // no-cors, *cors, same-origin
            cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });
        const content = await rawResponse.json();

        token = content['token'];

        if (content.hasOwnProperty('error')) {
            alert(content['error']);
            return;
        }

        //document.cookie = `sessionid=${token}; path=/`;
        //sessionStorage.setItem('Authorization', token);
        location.replace(`/auth/home/?token=${token}`);
    })();
}