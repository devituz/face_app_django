import os
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from .models import Students, SearchRecord
import face_recognition
from PIL import Image

from django.utils.timezone import localtime





@api_view(['POST'])
def upload_image(request):
    name = request.data.get('name')
    identifier = request.data.get('identifier')  # Foydalanuvchi kiritgan ID
    image_url = request.FILES.get('image_url')


    if Students.objects.filter(identifier=identifier).exists():
        return Response({"detail": "This identifier exists"}, status=status.HTTP_400_BAD_REQUEST)


    if not image_url:
        return Response({"detail": "Fayl berilmagan"}, status=status.HTTP_400_BAD_REQUEST)

    # Faylni saqlash
    file_location = os.path.join(settings.MEDIA_ROOT, 'students', image_url.name)
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    # Faylni yozish
    with open(file_location, "wb") as buffer:
        for chunk in image_url.chunks():
            buffer.write(chunk)

    # Yuzni aniqlash
    image = face_recognition.load_image_file(file_location)
    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) == 0:
        return Response({"detail": "Yuz aniqlanmadi"}, status=status.HTTP_400_BAD_REQUEST)

    face_encoding = face_encodings[0].tolist()

    new_student = Students(
        name=name,
        identifier=identifier,
        image_path=file_location,
        face_encoding=face_encoding
    )
    new_student.save()

    return Response({
        "message": "Image loaded and face saved",
        "student_id": new_student.id,
        "identifier": identifier
    })


@api_view(['POST'])
def update_image(request, id):
    name = request.data.get('name')
    image_url = request.FILES.get('image_url')

    # Kamida bittasi kiritilganligini tekshirish
    if not name and not image_url:
        return Response({"detail": "Iltimos, kamida bitta parametr yuboring: name yoki image_url."}, status=status.HTTP_400_BAD_REQUEST)

    # Berilgan ID bo‘yicha yozuvni qidirish
    existing_image = Students.objects.filter(id=id).first()
    if not existing_image:
        return Response({"detail": "Yozuv topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    # Faylni saqlash agar image_url yuborilgan bo'lsa
    if image_url:
        file_location = os.path.join(settings.MEDIA_ROOT, 'uploads', image_url.name)
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as buffer:
            for chunk in image_url.chunks():
                buffer.write(chunk)

        # Yuzni aniqlash
        image = face_recognition.load_image_file(file_location)
        face_encodings = face_recognition.face_encodings(image)

        if len(face_encodings) == 0:
            return Response({"detail": "Yuz aniqlanmadi"}, status=status.HTTP_400_BAD_REQUEST)

        face_encoding = face_encodings[0].tolist()

        # Rasm va yuzni yangilash
        existing_image.image_path = file_location
        existing_image.face_encoding = face_encoding

    # Agar name yuborilgan bo'lsa, yangilash
    if name:
        existing_image.name = name

    existing_image.save()

    return Response({"message": "Ma'lumotlar yangilandi", "student_id": existing_image.id})




@api_view(['POST'])
def search_image(request):
    file = request.FILES.get('file')
    scan_id = request.data.get('scan_id')

    if not file or not scan_id:
        return Response({"detail": "Fayl yoki scan_id yuborilmadi"}, status=status.HTTP_400_BAD_REQUEST)

    # --- Faylni diskka saqlashni vaqtinchalik o'chirib turamiz ---
    # search_folder = os.path.join(settings.MEDIA_ROOT, 'searches')
    # os.makedirs(search_folder, exist_ok=True)
    # file_location = os.path.join(search_folder, file.name)
    #
    # with open(file_location, "wb") as buffer:
    #     for chunk in file.chunks():
    #         buffer.write(chunk)

    # Rasmni xotirada ochamiz
    image = Image.open(file)

    try:
        exif = image._getexif()
        if exif is not None:
            orientation_tag = 274
            orientation = exif.get(orientation_tag)
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except Exception:
        pass

    # Rasmni xotirada saqlaymiz (diskka emas)
    image_stream = io.BytesIO()
    image.save(image_stream, format='JPEG')
    image_stream.seek(0)

    # Face recognition uchun rasmni xotiradan yuklaymiz
    search_image = face_recognition.load_image_file(image_stream)
    search_face_encodings = face_recognition.face_encodings(search_image)

    if len(search_face_encodings) == 0:
        return Response({"detail": "Siz yuborgan rasmda inson yuzi mavjud emas"}, status=status.HTTP_400_BAD_REQUEST)

    search_face_encoding = search_face_encodings[0]
    students = Students.objects.all()

    for student in students:
        match = face_recognition.compare_faces([student.face_encoding], search_face_encoding, tolerance=0.4)
        if match[0]:
            student.scan_id = scan_id
            student.save()

            search_record = SearchRecord.objects.create(
                search_image_path=None,  # --- Rasm manzili vaqtinchalik yo‘q ---
                student_id=student.id,
                scan_id=scan_id
            )

            created_at_uz = localtime(search_record.created_at).strftime("%Y-%m-%d %H:%M:%S")

            return Response({
                "message": "Yuz topildi",
                "id": student.id,
                "name": student.name,
                "identifier": student.identifier,
                "scan_id": scan_id,
                "created_at": created_at_uz,
            })

    return Response({
        "detail": "Siz yuborgan rasmda inson yuzilari bilan mos kelmadi",
    })

