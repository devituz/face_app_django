import os
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings
from .models import Students, SearchRecord
import face_recognition
from PIL import Image, ExifTags
import time
from .serializers import StudentsSerializer, SearchRecordSerializer
from django.utils.timezone import localtime
import pytz
import json
from datetime import datetime

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


class StudentsPagination(PageNumberPagination):
    page_size = 10  # Har bir sahifada 9 ta foydalanuvchi


@api_view(['GET'])
def get_user_images(request):
    # `created_at` bo‘yicha eng so‘nggilari birinchi chiqishi uchun saralash
    students = Students.objects.all().order_by('-created_at')

    paginator = StudentsPagination()
    result_page = paginator.paginate_queryset(students, request)
    serializer = StudentsSerializer(result_page, many=True)

    uzbekistan_tz = pytz.timezone("Asia/Tashkent")

    # JSON formatini o‘zgartirish
    for student in serializer.data:
        # Fayl URL'ini to‘g‘ri shaklga keltirish
        file_name = student['image_path'].split("/")[-1]  # Fayl nomini olish
        student['image_url'] = request.build_absolute_uri(f"{settings.MEDIA_URL}students/{file_name}")

        # image_path ni olib tashlash
        del student['image_path']

        # `created_at` bo‘lsa, uni O‘zbekiston vaqtiga aylantiramiz
        if 'created_at' in student:
            try:
                # `created_at` stringni datetime obyektiga aylantirish
                utc_time = datetime.fromisoformat(student['created_at'])  # ISO formatni avtomatik o‘qiydi
                local_time = utc_time.astimezone(uzbekistan_tz)  # UTC dan O‘zbekiston vaqtiga o‘tkazish

                # Yangi formatga o‘tkazish (Masalan: "Mar 25, 2025 14:45:30")
                student['created_at'] = local_time.strftime("%b %d, %Y %H:%M:%S")
            except ValueError:
                pass  # Xatolik bo‘lsa, o‘zgartirishsiz qoldiramiz

    return Response({"students": serializer.data})



@api_view(['GET'])
def get_user_json(request):
    students = Students.objects.all()
    serializer = StudentsSerializer(students, many=True)

    uzbekistan_tz = pytz.timezone("Asia/Tashkent")

    # JSON formatini o'zgartirish
    for student in serializer.data:
        # Fayl URL'ini to'g'ri shaklga keltirish
        file_name = student['image_path'].split("/")[-1]  # Fayl nomini olish
        student['image_url'] = request.build_absolute_uri(f"{settings.MEDIA_URL}students/{file_name}")

        # image_path ni olib tashlash
        del student['image_path']

        # `created_at` bo'lsa, uni O‘zbekiston vaqtiga aylantiramiz
        if 'created_at' in student:
            try:
                # `created_at` string ko‘rinishida kelgan vaqtni datetime obyektiga o‘tkazish
                utc_time = datetime.fromisoformat(student['created_at'])  # ISO 8601 formatini avtomatik o‘qiydi
                local_time = utc_time.astimezone(uzbekistan_tz)  # UTC dan O‘zbekiston vaqtiga o‘tkazish

                # Yangi formatga o‘tkazish (Masalan: "Feb 13, 2025 12:30:45")
                student['created_at'] = local_time.strftime("%b %d, %Y %H:%M:%S")
            except ValueError:
                pass  # Xatolik yuz bersa, shunchaki `created_at` o‘zgartirilmaydi

    return Response({"students": serializer.data})


@api_view(['GET'])
def search_user_json(request):
    query = request.GET.get('query', '').strip()

    if not query:
        return Response({})  # Agar query bo'sh bo'lsa, bo'sh obyekt qaytariladi

    student = Students.objects.filter(
        Q(name__icontains=query) | Q(identifier__icontains=query)
    ).first()  # Faqat bitta natija qaytariladi

    if not student:
        return Response({})  # Agar topilmasa, bo'sh obyekt qaytariladi

    serializer = StudentsSerializer(student)
    student_data = serializer.data

    # Fayl URL'ini to'g'ri shaklga keltirish
    file_name = student_data['image_path'].split("/")[-1]
    student_data['image_url'] = request.build_absolute_uri(f"{settings.MEDIA_URL}students/{file_name}")

    # image_path ni olib tashlash
    del student_data['image_path']

    # `created_at`ni O‘zbekiston vaqtiga aylantirish
    uzbekistan_tz = pytz.timezone("Asia/Tashkent")
    if 'created_at' in student_data:
        try:
            utc_time = datetime.fromisoformat(student_data['created_at'])
            local_time = utc_time.astimezone(uzbekistan_tz)
            student_data['created_at'] = local_time.strftime("%b %d, %Y %H:%M:%S")
        except ValueError:
            pass

    return Response(student_data)


def allsearch(request):
    # SearchRecord dan barcha yozuvlarni olish va created_at bo‘yicha teskari saralash
    search_records = SearchRecord.objects.select_related('student').order_by('-created_at')

    # JSON formatiga moslashtirish
    data = []
    for record in search_records:
        student = {
            "id": record.student.id if record.student else None,
            "name": record.student.name if record.student else None,
            "identifier": record.student.identifier if record.student else None,
            "created_at": record.student.created_at if record.student else None,
        }

        # Agar student mavjud bo'lsa, image_path ni ishlatib image_url ni yaratish
        if record.student and record.student.image_path:
            file_name = record.student.image_path.split("/")[-1]  # Fayl nomini olish
            student["image_url"] = request.build_absolute_uri(f"{settings.MEDIA_URL}students/{file_name}")

        # search_image_path ni to'g'ri yo'lga moslashtirish
        search_file_name = record.search_image_path.split("/")[-1]  # Fayl nomini olish
        search_image_url = request.build_absolute_uri(f"{settings.MEDIA_URL}searches/{search_file_name}")

        data.append({
            "id": record.id,
            "search_image_urls": search_image_url,
            "scan_id": record.scan_id,
            "student": student,
            "created_at": record.created_at
        })

    # JSON formatida javob qaytarish
    return JsonResponse({"search_records": data}, safe=False)


@api_view(['POST'])
def getme_register(request):
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
        student_images = [search_image_url, student_image_path]
        student_images = [img for img in student_images if img]  # None bo'lganlarini olib tashlaymiz

        # search_image_path ni olib tashlab, student_image ni qo'shamiz
        filtered_record = {key: value for key, value in serialized_record.items() if key != "search_image_path"}

        result.append({
            **filtered_record,
            "student_name": student.name if student else "Noma'lum",
            "student_image": student_images,  # Bitta list sifatida qaytarish
        })

    return Response({"results": result})


@api_view(['POST'])
def delete_records_by_id(request):
    # Yuborilgan id larni olish
    record_ids = request.data.get('ids', [])

    if not record_ids:
        return Response({"detail": "ID'lar berilmagan"}, status=status.HTTP_400_BAD_REQUEST)

    deleted_count = 0

    # Har bir ID bo‘yicha SearchRecord dan yozuvlarni topish va o‘chirish
    for record_id in record_ids:
        try:
            record = SearchRecord.objects.get(id=record_id)  # ID bo‘yicha qidirish
            record.delete()  # Agar topilsa, o‘chirish
            deleted_count += 1
        except SearchRecord.DoesNotExist:
            continue  # ID topilmasa, davom etadi

    if deleted_count == 0:
        return Response({"detail": "Berilgan ID bo‘yicha yozuvlar topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"message": f"{deleted_count} ta yozuv muvaffaqiyatli o‘chirildi"})


@api_view(['POST'])
def delete_candidate_records(request):
    # 'ids' ni olish
    ids = request.data.get('ids', [])

    # 'ids' massiv ekanini tekshirish
    if not isinstance(ids, list) or not ids:
        return Response({"detail": "ids massivda berilishi kerak"}, status=status.HTTP_400_BAD_REQUEST)

    # IDs bo'yicha o'chirilishi kerak bo'lgan studentlarni topish
    students_to_delete = Students.objects.filter(id__in=ids)
    deleted_count = students_to_delete.count()

    if deleted_count == 0:
        return Response({"detail": "Hech qanday mos Kandidat topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    # O'chirish jarayoni
    students_to_delete.delete()
    return Response({"message": f"{deleted_count} ta kandidat muvaffaqiyatli o'chirildi"})




