from student_api.models import Students, SearchRecord
import os
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import face_recognition
from PIL import Image
from django.utils.timezone import localtime
from student_api.serializers import SearchRecordSerializer



@api_view(['POST'])
def search_candidate(request):
    file = request.FILES.get('file')
    scan_id = request.data.get('scan_id')
    search_folder = os.path.join(settings.MEDIA_ROOT, 'searches')
    os.makedirs(search_folder, exist_ok=True)
    file_location = os.path.join(search_folder, file.name)

    with open(file_location, "wb") as buffer:
        for chunk in file.chunks():
            buffer.write(chunk)

    image = Image.open(file_location)
    try:
        exif = image._getexif()
        if exif is not None:
            for tag, value in exif.items():
                if tag == 274:  # Orientation tag
                    if value == 3:
                        image = image.rotate(180, expand=True)
                    elif value == 6:
                        image = image.rotate(270, expand=True)
                    elif value == 8:
                        image = image.rotate(90, expand=True)
        image.save(file_location)
    except (AttributeError, KeyError, IndexError):
        pass

    search_image = face_recognition.load_image_file(file_location)
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

            # SearchRecord obyektini yaratamiz va o‘zgaruvchiga saqlaymiz
            search_record = SearchRecord.objects.create(
                search_image_path=file_location,
                student_id=student.id,
                scan_id=scan_id
            )

            file_name = student.image_path.split("/")[-1]
            file_url = request.build_absolute_uri(f"{settings.MEDIA_URL}students/{file_name}")
            created_at_uz = localtime(search_record.created_at).strftime("%Y-%m-%d %H:%M:%S")


            return Response({
                "message": "Yuz topildi",
                "id": student.id,
                "name": student.name,
                "identifier": student.identifier,
                "scan_id": scan_id,
                "file": file_url,
                "created_at": created_at_uz,  # ✅ O‘zbekiston vaqti bo‘yicha qaytariladi
            })

    return Response({
        "detail": "Siz yuborgan rasmda inson yuzilari bilan mos kelmadi",
    })


@api_view(['POST'])
def get_me_register(request):
    scan_id = request.data.get('scan_id')

    # scan_id bo‘yicha SearchRecordlarni olish, id bo‘yicha kamayish tartibida saralash
    search_records = SearchRecord.objects.filter(scan_id=scan_id).order_by('-id')

    if not search_records.exists():
        return Response({"detail": "Ushbu scan_id uchun yozuv topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    result = []

    for record in search_records:
        student = record.student

        # Student image URL
        student_image_path = None
        if student and student.image_path:
            student_image_name = student.image_path.split("/")[-1]
            student_image_path = request.build_absolute_uri(f"{settings.MEDIA_URL}students/{student_image_name}")

        # Search image URL
        search_image_url = None
        if record.search_image_path:
            search_file_name = record.search_image_path.split("/")[-1]
            search_image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}searches/{search_file_name}")

        serialized_record = SearchRecordSerializer(record).data

        # student_image listini hosil qilish
        student_images = [student_image_path,search_image_url]
        student_images = [img for img in student_images if img]  # None bo'lganlarini olib tashlaymiz

        # search_image_path ni olib tashlab, student_image ni qo'shamiz
        filtered_record = {key: value for key, value in serialized_record.items() if key != "search_image_path"}

        result.append({
            **filtered_record,
            "student_name": student.name if student else "Noma'lum",
            "student_image": student_images,  # Bitta list sifatida qaytarish
            "identifier": record.student.identifier if record.student else None,

        })

    return Response({"results": result})