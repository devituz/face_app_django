import os
import face_recognition
import shutil
from django.conf import settings
from student_api.models import Students

# Fayllar manzillari
source_directory = 'rasmlar'  # Rasm fayllar manzili (relative yo'l)
target_directory = 'uploads/students'  # Faqat relative yo'l

# To'liq manzilni qo'shish
base_directory = '/home/user/loyiha/ai_university/ai_app/'  # Loyihaning asosiy manzili

# Flag fayli
flag_file = 'processing_flag.txt'


# Talaba rasmlarini qayta ishlash va saqlash
def process_and_save_student_images():
    # Agar flag fayli mavjud bo'lsa, dasturs qayta ishlamasin
    if os.path.exists(flag_file):
        print("Kod allaqon ishlayapti. Flag fayli mavjud.")
        return

    # Flag faylini yaratish
    with open(flag_file, 'w') as f:
        f.write("Processing started.")

    total_images = 0
    successful_faces = 0  # Real yuzlar soni

    try:
        # "rasmlar" papkasidan fayllarni o'qish
        for image_file in os.listdir(source_directory):
            file_path = os.path.join(source_directory, image_file)

            # Faylni faqat rasm bo'lsa ishlatish
            if os.path.isfile(file_path) and image_file.lower().endswith(('jpg', 'jpeg', 'png')):
                total_images += 1

                try:
                    # Fayl nomidan talaba ismini olish (fayl kengaytmasiz)
                    student_name = os.path.splitext(image_file)[0]  # Fayl nomidan kengaytmasiz qismini olish

                    # Rasmni yuklab olish
                    image = face_recognition.load_image_file(file_path)
                    face_encodings = face_recognition.face_encodings(image)

                    if len(face_encodings) > 0:
                        # Yuzni kodlash
                        face_encoding = face_encodings[0].tolist()

                        # Yangi fayl manzilini yaratish (uploads/students/rasm_nomi)
                        target_path = os.path.join(target_directory, image_file)

                        # Faylni ko'chirish (rasmlar papkasidan uploads/students papkasiga)
                        os.makedirs(target_directory, exist_ok=True)  # target papkasini yaratish
                        shutil.copy(file_path, target_path)

                        # To'liq manzilni olish va uni bazaga qo'shish
                        full_target_path = os.path.join(base_directory, target_directory, image_file).replace(os.sep,
                                                                                                              '/')

                        # Yangi talaba ob'ektini yaratish
                        new_student = Students(name=student_name, image_path=full_target_path,
                                               face_encoding=face_encoding)

                        # Talabani bazaga qo'shish
                        new_student.save()  # Django ORM metodini ishlatish (commit avtomatik bo'ladi)

                        successful_faces += 1
                        print(f"Talaba: {student_name}, rasm saqlandi.")

                    else:
                        print(f"Yuz aniqlanmadi: {image_file}")

                except Exception as e:
                    print(f"Xatolik yuz berdi {image_file}: {e}")

        # Agar real yuzlar qolmasa (successful_faces = 0), dastur to'xtaydi
        if successful_faces == 0:
            print("Real yuzlar qolmadi. Dastur to'xtatildi.")
            return

    finally:
        # Flag faylini o'chirish
        os.remove(flag_file)
        print("Kod ishlashini yakunladi.")


# Funksiyani ishga tushurish
if __name__ == "__main__":
    process_and_save_student_images()
