import os
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from student_api.models import Students, SearchRecord
import face_recognition
from rest_framework.decorators import api_view

import os
from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.conf import settings
import face_recognition
import pytz
from datetime import datetime

from student_api.serializers import StudentsSerializer


@api_view(['POST'])
def create_candidate(request):
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
def update_candidate(request, id):
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


class StudentsPagination(PageNumberPagination):
    page_size = 10  # Har bir sahifada 9 ta foydalanuvchi


@api_view(['GET'])
def get_candidate(request):
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
def get_candidate_json(request):
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
def search_candidate_json(request):
    query = request.GET.get('query', '').strip()

    if not query:
        return Response([])

    # `query` ga mos keladigan barcha studentlarni olish
    students = Students.objects.filter(
        Q(name__icontains=query) | Q(identifier__icontains=query)
    )

    if not students.exists():
        return Response([])  # Agar hech narsa topilmasa, bo'sh ro'yxat qaytariladi

    serializer = StudentsSerializer(students, many=True)  # Ko'p obyektni serialize qilish
    students_data = serializer.data

    # Ma'lumotlarni qayta ishlash
    uzbekistan_tz = pytz.timezone("Asia/Tashkent")

    for student in students_data:
        # Fayl URL'ini to'g'ri shaklga keltirish
        file_name = student['image_path'].split("/")[-1]
        student['image_url'] = request.build_absolute_uri(f"{settings.MEDIA_URL}students/{file_name}")

        # image_path ni olib tashlash
        del student['image_path']

        # `created_at` ni O‘zbekiston vaqtiga o'zgartirish
        if 'created_at' in student:
            try:
                utc_time = datetime.fromisoformat(student['created_at'])
                local_time = utc_time.astimezone(uzbekistan_tz)
                student['created_at'] = local_time.strftime("%b %d, %Y %H:%M:%S")
            except ValueError:
                pass

    return Response(students_data)


def get_search(request):
    query = request.GET.get('query', None)  # 'query' parametrini olish

    # Agar query bo'lsa, faqat o'sha so'rovlar bilan ishlaymiz
    if query:
        search_records = SearchRecord.objects.select_related('student').filter(
            student__name__icontains=query  # 'name' bo'yicha qidiruv
        ).order_by('-created_at')
    else:
        # Agar query bo'lmasa, barcha yozuvlarni olish
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
def delete_by_id(request):
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
def delete_search_candidate(request):
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
