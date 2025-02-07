import time
from instagrapi import Client


username = "devit_uz"
password = "s75S7xg6xi^fUZT"


def login_to_instagram():

    cl = Client()
    cl.login(username, password)
    return cl



cl = login_to_instagram()

post_url = "https://www.instagram.com/reel/DC5tgoRomPDvMxbt1-gz1VL9vxUXF2jFms9d_c0/"
media_id = cl.media_id(cl.media_pk_from_url(post_url))

comments = [
    "🇮🇳 Raja Kumar Oshiqbaxsh – har bir gapida “jonim” deb gapiradigan, lekin hech kim uni jiddiy qabul qilmaydigan yigit 💘😂",
    "🇮🇳 Sulton G‘o‘r – har bir gapini “bilaman” deb boshlaydi, lekin hayotda bir marta ham amalda ishlatmagan 🤓🤣",
    "🇮🇳 Raja Kumar Jo‘nashga Tayyormi? – '5 minutda chiqaman' deb, so‘ng 2 soat oynak oldida turgan shahzoda ⏳👑😂",
    "🇮🇳 Maharaja Gap Yoqmaydi – odamlarning gapini tinglashga toqati yo‘q, lekin o‘zi gap boshlasa, hamma eshitishi shart deb o‘ylaydi 🙉😆",
    "🇮🇳 Raja Kumar “Kelishgan” – o‘zini juda chiroyli deb hisoblaydi, lekin hamma uni kulgili deb o‘ylaydi 😎😂",
    "🇮🇳 Sulton Matematika – 2x2=5 deb o‘ylaydigan, lekin biznes boshlashni xohlovchi shahzoda 📊🤣",
    "🇮🇳 Maharaja “Bu Kim?” – har safar yangi odam bilan tanishib, 10 daqiqada esdan chiqaradigan yigit 🤔😅",
    "🇮🇳 Raja Kumar Selfiboz – har joyda selfi tushib, keyin 'men tabiatni his qilyapman' deb yozadigan shahzoda 📸😆",
    "🇮🇳 Sulton Suhbatdosh – hech kim unga savol bermasa ham, o‘zining hayot tarixini soatlab gapirib beradigan yigit 🎤😂",
    "🇮🇳 Raja Kumar Hamma Biladi – nima haqida gap bo‘lsa ham, o‘sha mavzuda mutaxassisdek gapiradigan, lekin hech qanday dalil ko‘rsatmaydigan yigit 🙄🤣",
] * 10  # 10 martadan yozish



for i, comment in enumerate(comments, start=1):
    try:
        cl.media_comment(media_id, comment)
        print(f"{i}-chi izoh muvaffaqiyatli qoldirildi: {comment}")
    except Exception as e:
        print(f"{i}-chi izohni qoldirishda xatolik yuz berdi: {e}")


    time.sleep(10)


    if i % 35 == 0:
        print("35 ta izohdan keyin yangi login amalga oshirilyapti...")
        cl = login_to_instagram()

print("Barcha izohlar muvaffaqiyatli qoldirildi!")
