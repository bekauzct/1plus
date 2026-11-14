"""O'zbek tili (lotin) — manba lug'at. Kirill va yangi lotin shu fayldan avtomatik hosil qilinadi.

``TL`` — varaq (hujjat) shabloni yorliqlari, ``UI`` — forma va interfeys matnlari,
``SAMPLE`` — namuna ma'lumotlar, ``SITE`` — landing/SEO matnlari.
``TL``, ``UI`` (prototipdagi kalitlar) va ``SAMPLE`` prototip bilan aynan bir xil bo'lishi
``tests/test_i18n.py`` da tekshiriladi.
"""

from typing import Any

TL: dict[str, Any] = {
    "title": "Ma’lumotnoma",
    "photo": "Rasm 3×4",
    "tugYil": "Tug‘ilgan yili:",
    "tugJoy": "Tug‘ilgan joyi:",
    "millati": "Millati:",
    "partiya": "Partiyaviyligi:",
    "malumoti": "Ma’lumoti:",
    "tamomlagan": "Tamomlagan:",
    "mutax": "Ma’lumoti bo‘yicha mutaxassisligi:",
    "ilmiyD": "Ilmiy darajasi:",
    "ilmiyU": "Ilmiy unvoni:",
    "qTil": "Qaysi chet va MDH xalqlari tillarini biladi:",
    "qMuk": "Davlat mukofotlari bilan taqdirlanganmi?",
    "qDep": "Xalq deputatlari, respublika, viloyat, shahar va tuman kengashi deputatimi? Yoki, boshqa saylanadigan organlarning a’zosimi?",
    "mehnat": "MEHNAT FAOLIYATI",
    "relSfx": "ning yaqin qarindoshlari haqida",
    "relTitle": "MA’LUMOT",
    "thRel": "Qarindoshligi",
    "thFish": "F.I.Sh",
    "thTug": "Tug‘ilgan yili va joyi",
    "thIsh": "Ish joyi va lavozimi",
    "thTur": "Turar joyi",
    "yy": "yy.",
    "y": "y.",
    "hv": "h.v.",
    "blankName": "________________",
}

UI: dict[str, Any] = {
    "sample": "Namuna bilan to‘ldirish",
    "tabForm": "✎ To‘ldirish",
    "tabPrev": "👁 Ko‘rish",
    "filled": "To‘ldirildi",
    "s1": "Shaxsiy ma’lumotlar",
    "s2": "Ma’lumoti va ilmiy daraja",
    "s3": "Tillar, mukofotlar, deputatlik",
    "s4": "Mehnat faoliyati",
    "s5": "Yaqin qarindoshlari",
    "photoBox": "Rasm 3×4",
    "photoUp": "Rasm yuklash",
    "photoRm": "O‘chirish",
    "photoHint": "Oq fonli, 3×4 rasm. Avtomatik kesiladi.",
    "fFish": "Familiya, ism, otasining ismi",
    "phFish": "Karimov Aziz Rustam o‘g‘li",
    "fLav": "Hozirgi ish joyi / o‘qish joyi va lavozimi",
    "phLav": "2024-yil 1-sentabrdan buyon ... talabasi",
    "hLav": "Odatda: “20XX-yil N-oydan buyon [tashkilot] [lavozim]”",
    "fTugSana": "Tug‘ilgan sanasi",
    "fMillati": "Millati",
    "phMillati": "O‘zbek",
    "fTugJoy": "Tug‘ilgan joyi",
    "phTugJoy": "Samarqand viloyati, Norboy tumani",
    "fPartiya": "Partiyaviyligi",
    "no": "Yo‘q",
    "fMal": "Ma’lumoti",
    "phMal": "Oliy",
    "malChips": ["O‘rta", "O‘rta maxsus", "Oliy", "Tugallanmagan oliy"],
    "fTam": "Tamomlagan (o‘quv yurti va yili)",
    "phTam": "2020-yil, Toshkent davlat iqtisodiyot universiteti",
    "fMut": "Ma’lumoti bo‘yicha mutaxassisligi",
    "phMut": "Iqtisodchi",
    "fIlD": "Ilmiy darajasi",
    "fIlU": "Ilmiy unvoni",
    "fTil": "Qaysi chet va MDH xalqlari tillarini biladi",
    "phTil": "Rus tili, ingliz tili",
    "tilChips": ["Rus tili", "Ingliz tili", "Turk tili", "Koreys tili"],
    "fMuk": "Davlat mukofotlari bilan taqdirlanganmi?",
    "fDep": "Deputatmi yoki saylanadigan organ a’zosimi?",
    "addM": "+ Davr qo‘shish",
    "hM": "“Gacha” bo‘sh qolsa — “h.v.” (hozirgi vaqtgacha) deb yoziladi.",
    "period": "-davr",
    "fDan": "Dan (yil)",
    "fGacha": "Gacha (yil)",
    "phGacha": "h.v.",
    "fMatn": "Ish joyi va lavozimi",
    "phMatn": "Tashkilot nomi, lavozimi",
    "addR": "+ Qarindosh qo‘shish",
    "relDef": "Qarindosh",
    "fRel": "Qarindoshligi",
    "phRel": "Otasi",
    "fYil": "Tug‘ilgan yili",
    "fRFish": "F.I.Sh",
    "phRFish": "Familiya Ism Otasining ismi",
    "fRJoy": "Tug‘ilgan joyi",
    "phRJoy": "Viloyat, tuman",
    "fIsh": "Ish joyi va lavozimi",
    "phIsh": "Tashkilot, lavozim (yoki: Uy bekasi, Pensioner)",
    "ishChips": ["Uy bekasi", "Pensioner", "Vaqtincha ishlamaydi", "Talaba"],
    "fTurar": "Turar joyi",
    "phTurar": "Viloyat, tuman, mahalla, uy",
    "same": "↑ Yuqoridagidek",
    "rels": [
        "Otasi",
        "Onasi",
        "Akasi",
        "Ukasi",
        "Opasi",
        "Singlisi",
        "Turmush o‘rtog‘i",
        "Eri",
        "Xotini",
        "O‘g‘li",
        "Qizi",
        "Qaynotasi",
        "Qaynonasi",
    ],
    "up": "Yuqoriga",
    "down": "Pastga",
    "del": "O‘chirish",
    "clear": "Hammasini tozalash",
    "page1": "1-sahifa · Ma’lumotnoma",
    "page2": "2-sahifa · Qarindoshlar",
    "phPrevFish": "Familiya Ism Otasining ismi",
    "phPrevLav": "Hozirgi ish joyi va lavozimi…",
    "noMehnat": "Mehnat faoliyati kiritilmagan",
    "noRel": "Qarindoshlar kiritilmagan",
    "tSample": "Namuna yuklandi — o‘zingiznikiga almashtiring",
    "mSampleX": "Hozirgi kiritilgan ma’lumotlar namuna bilan almashtiriladi. Davom etasizmi?",
    "mClearX": "Barcha kiritilgan ma’lumotlar o‘chiriladi.",
    "cancel": "Bekor qilish",
    "yes": "Ha",
    "tCleared": "Tozalandi",
    "tSaved": "Fayl saqlandi",
    "tDeclined": "Bekor qilindi",
    "tWait": "Biroz kuting va qayta urinib ko‘ring",
    "tDl": "Yuklab olinmoqda…",
    "tNoDl": "Bu oynada yuklab olish ishlamadi",
    "tWordErr": "Word faylini yaratib bo‘lmadi",
    "tPdfErr": "PDF yaratib bo‘lmadi",
    "preparing": "Tayyorlanmoqda…",
    "tPhotoErr": "Rasmni o‘qib bo‘lmadi",
    "tConv": "Kiritilgan matn ham o‘girildi",
    "undo": "Qaytarish",
    "tLangOnly": "Shablon tili almashdi. Ma’lumotlarni shu tilda kiriting.",
    "fname": "obyektivka",
    "langTitle": "Hujjat tili",
}

SAMPLE: dict[str, Any] = {
    "fish": "Karimov Aziz Rustam o‘g‘li",
    "lavozim": "2024-yil 2-sentabrdan buyon Toshkent axborot texnologiyalari universiteti Dasturiy injiniring fakulteti talabasi",
    "tugSana": "12.03.2006",
    "tugJoy": "Toshkent viloyati, Chirchiq shahri",
    "millati": "O‘zbek",
    "partiya": "Yo‘q",
    "malumoti": "O‘rta maxsus",
    "tamomlagan": "2024-yil, Chirchiq shahar 2-son politexnikumi",
    "mutaxassislik": "Kompyuter tizimlari texnigi",
    "ilmiyDaraja": "Yo‘q",
    "ilmiyUnvon": "Yo‘q",
    "tillar": "Rus tili, ingliz tili",
    "mukofot": "Yo‘q",
    "deputat": "Yo‘q",
    "photo": "",
    "mehnat": [
        {
            "dan": "2021",
            "gacha": "2024",
            "matn": "Chirchiq shahar 2-son politexnikumi o‘quvchisi",
        },
        {
            "dan": "2024",
            "gacha": "",
            "matn": "Toshkent axborot texnologiyalari universiteti Dasturiy injiniring fakulteti talabasi",
        },
    ],
    "qarindosh": [
        {
            "rel": "Otasi",
            "fish": "Karimov Rustam Bahodirovich",
            "yil": "1976",
            "joy": "Toshkent viloyati, Chirchiq shahri",
            "ish": "“Chirchiq transport” MChJ\nhaydovchi",
            "turar": "Toshkent viloyati, Chirchiq shahri, Navbahor ko‘chasi 14-uy",
        },
        {
            "rel": "Onasi",
            "fish": "Karimova Dilnoza Akramovna",
            "yil": "1980",
            "joy": "Toshkent viloyati, Bo‘stonliq tumani",
            "ish": "Chirchiq shahar 7-maktab\no‘qituvchi",
            "turar": "Toshkent viloyati, Chirchiq shahri, Navbahor ko‘chasi 14-uy",
        },
        {
            "rel": "Singlisi",
            "fish": "Karimova Madina Rustam qizi",
            "yil": "2010",
            "joy": "Toshkent viloyati, Chirchiq shahri",
            "ish": "Chirchiq shahar 7-maktab\no‘quvchisi",
            "turar": "Toshkent viloyati, Chirchiq shahri, Navbahor ko‘chasi 14-uy",
        },
    ],
}

# ---------------------------------------------------------------------------
# Sayt uchun qo'shimcha matnlar (prototipda yo'q). Lotin qisqartmalarini (JSON, PDF)
# satrlarga qo'shmang: kirillga o'girilganda buziladi — ularni shablonda alohida yozing
# yoki uz_cyr.FIXUPS ga qo'shing.
# ---------------------------------------------------------------------------
UI.update(
    {
        "langLabel": "Til",
        "menu": "Menyu",
        "navHome": "Bosh sahifa",
        "navEditor": "Muharrir",
        "skip": "Asosiy qismga o‘tish",
        "privacy": "Ma’lumotlaringiz serverda saqlanmaydi",
        "exportJson": "eksport",
        "importJson": "import",
        "jsonHint": "Boshqa qurilmaga ko‘chirish uchun faylga saqlang",
        "tImported": "Ma’lumotlar yuklandi",
        "tImportErr": "Faylni o‘qib bo‘lmadi yoki formati noto‘g‘ri",
        "cropTitle": "Rasmni kesish (3×4)",
        "cropApply": "Saqlash",
        "rotate": "Burish",
        "drag": "Sudrab tartiblash",
        "errDate": "Sana noto‘g‘ri. Masalan: 12.03.2006",
        "errYear": "Yil 4 xonali bo‘lsin (masalan, 2020)",
        "tTooBig": "Rasm juda katta (5 MB gacha)",
        "tPhotoType": "Bu rasm formati qo‘llab-quvvatlanmaydi",
        "tRate": "So‘rovlar juda ko‘p. Bir daqiqadan keyin urinib ko‘ring",
        "tNet": "Server bilan aloqa yo‘q. Qayta urinib ko‘ring",
        "tInvalid": "Ba’zi maydonlar noto‘g‘ri to‘ldirilgan",
        "close": "Yopish",
        "updating": "Yangilanmoqda…",
    }
)

SITE: dict[str, Any] = {
    "metaTitle": "Obyektivka namuna — online to‘ldirish, PDF va Word",
    "metaDesc": (
        "Obyektivka (ma’lumotnoma) ni online yozing: namuna asosida to‘ldiring, A4 varaqni darhol "
        "ko‘ring va PDF yoki Word faylini yuklab oling. Bepul, ro‘yxatdan o‘tmasdan."
    ),
    "keywords": "obyektivka, obyektivka namuna, ma’lumotnoma yozish, obyektivka yozish, obyektivka pdf, obyektivka word",
    "editorTitle": "Obyektivka yozish — online muharrir",
    "editorDesc": (
        "Obyektivkani online to‘ldiring: chapda forma, o‘ngda A4 varaqning jonli ko‘rinishi. "
        "PDF va Word yuklab olish, 4 til."
    ),
    "heroKicker": "Bepul · Ro‘yxatdan o‘tmasdan",
    "heroH1": "Obyektivkani bir necha daqiqada online to‘ldiring",
    "heroSub": (
        "Namuna asosida ma’lumotnoma yozing, A4 varaqni jonli ko‘ring va PDF yoki Word faylini yuklab oling. "
        "To‘rt xil yozuvda: lotin, yangi lotin, kirill va rus tilida."
    ),
    "start": "Boshlash",
    "seeSample": "Namunani ko‘rish",
    "privacyP": (
        "Kiritgan ma’lumotlaringiz faqat brauzeringizda saqlanadi. Ko‘rinish va fayl yaratish uchun server ularni "
        "faqat so‘rov davomida xotirada ishlatadi — diskka, bazaga yoki jurnalga yozilmaydi."
    ),
    "whatH": "Obyektivka nima?",
    "whatP": (
        "Obyektivka (ma’lumotnoma) — ishga kirish, o‘qishga hujjat topshirish yoki lavozimga tayinlanishda "
        "so‘raladigan rasmiy hujjat. Unda shaxsiy ma’lumotlar, ma’lumoti, mehnat faoliyati va yaqin "
        "qarindoshlar haqidagi ma’lumot bo‘ladi."
    ),
    "stepsH": "Uch qadamda tayyor",
    "steps": [
        {
            "t": "To‘ldiring",
            "d": "Formani to‘ldiring yoki namuna bilan boshlang. Tezkor tugmalar yozishni osonlashtiradi.",
        },
        {
            "t": "Tekshiring",
            "d": "A4 varaq jonli yangilanadi: 1-sahifa ma’lumotnoma, 2-sahifa yaqin qarindoshlar.",
        },
        {"t": "Yuklab oling", "d": "Tayyor hujjatni PDF yoki Word faylida yuklab oling va chop eting."},
    ],
    "sampleH": "Namuna varaq",
    "sampleP": "Hujjat aynan shu ko‘rinishda tayyorlanadi: rasm, mehnat faoliyati va qarindoshlar jadvali bilan.",
    "featH": "Imkoniyatlar",
    "feats": [
        {"t": "To‘rt yozuv", "d": "Lotin, yangi lotin, kirill va rus. Til almashganda matn ham o‘giriladi."},
        {
            "t": "Jonli ko‘rinish",
            "d": "Yozgan maydoningiz varaqda belgilanadi va ko‘rinadigan joyga suriladi.",
        },
        {"t": "Rasmni kesish", "d": "Rasmni yuklang va 3×4 nisbatda kerakli joyini kesib oling."},
        {
            "t": "Boshqa qurilmaga ko‘chirish",
            "d": "Ma’lumotlarni faylga saqlab, boshqa qurilmada davom ettiring.",
        },
    ],
    "faqH": "Ko‘p beriladigan savollar",
    "faq": [
        {
            "q": "Obyektivka uchun pul to‘lash kerakmi?",
            "a": "Yo‘q, xizmat bepul. Ro‘yxatdan o‘tish ham shart emas.",
        },
        {
            "q": "Ma’lumotlarim qayerda saqlanadi?",
            "a": (
                "Faqat sizning brauzeringizda. Server ma’lumotlarni faqat ko‘rinish va fayl tayyorlash vaqtida "
                "xotirada ishlatadi va hech qayerga yozmaydi."
            ),
        },
        {
            "q": "Qaysi formatda yuklab olsam bo‘ladi?",
            "a": "PDF (chop etish uchun) va Word (keyinchalik tahrirlash uchun).",
        },
        {
            "q": "Kirill yozuvida obyektivka yozsa bo‘ladimi?",
            "a": (
                "Ha. Yozuvni almashtirsangiz, kiritgan matningiz ham avtomatik o‘giriladi. "
                "Xohlasangiz, “Qaytarish” tugmasi bilan bekor qilasiz."
            ),
        },
        {
            "q": "Rasm qanday bo‘lishi kerak?",
            "a": "3×4 o‘lchamli, oq fonli rasm. Yuklaganingizdan keyin kerakli joyini kesib olasiz.",
        },
        {
            "q": "Boshqa qurilmada davom ettirsam bo‘ladimi?",
            "a": "Ha: ma’lumotlarni faylga eksport qiling va boshqa qurilmada import qiling.",
        },
    ],
    "footer": "Obyektivka namuna va online muharrir",
    "notFound": "Sahifa topilmadi",
    "backHome": "Bosh sahifaga qaytish",
}
