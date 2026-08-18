# Onlayn ta'lim platformasi — MVP

TZ v3.0 (B2B2C marketplace) asosida qurilgan onlayn ta'lim platformasi. To'liq talablar uchun loyihaga biriktirilgan Texnik Topshiriqqa qarang.

## Stek

| Qatlam | Texnologiya |
|---|---|
| Backend | Python 3.12, Django 5.x, DRF 3.15 |
| Frontend | Next.js (App Router), React 19 |
| DB | PostgreSQL 16 |
| Kesh / navbat | Redis 7, Celery 5 |
| Fayl saqlash | MinIO (S3-mos) |
| Video | Bunny Stream (HLS + CDN) |
| To'lov | Payme |
| SMS | Eskiz.uz |
| Admin panel | Django Admin + django-unfold |

Arxitektura tafsilotlari: TZ 5-bo'lim (modulli monolit, `services.py`/`selectors.py` qatlamlari, domain event bus).

## Loyiha strukturasi

```
backend/
├── config/            # settings (base/local/staging/production), urls, celery
├── apps/
│   ├── core/          # BaseModel (UUID, i18n, org_id), event bus, RFC7807 xatolar
│   ├── accounts/       # User, OTP, Device, Session, 2FA
│   ├── rbac/           # Permission, Role, RoleAssignment (scope bilan)
│   ├── audit/           # AuditLog (append-only), impersonation
│   ├── catalog/         # Category, Review, qidiruv, tavsiyalar
│   ├── courses/         # Course, Module, Lesson, CourseVersion, VideoAsset, FileAsset
│   ├── groups/          # Group, GroupSchedule, GroupMembership, JoinRequest
│   ├── enrollment/      # Enrollment, Progress, drip-content, playback token
│   ├── assessments/     # Quiz, Question, Attempt, Answer
│   ├── assignments/     # Homework, Submission, Grade, gradebook
│   ├── certificates/    # Certificate, shablon, ochiq verifikatsiya
│   ├── payments/        # Order, Payment (Payme), double-entry Ledger, Promo
│   ├── payouts/         # PayoutRequest, o'qituvchi balansi
│   ├── notifications/   # Shablon, sozlama, SMS/email/push dispatch
│   ├── communication/   # Dars ostidagi izoh va Q&A
│   └── analytics/       # Event, DailyAggregate, hisobotlar
├── libs/                # Tashqi provayder wrapper'lari (Payme, Bunny, Eskiz)
└── templates/           # Sertifikat PDF shabloni (WeasyPrint)

frontend/
├── app/                 # Next.js App Router sahifalari
├── components/          # Qayta ishlatiladigan UI qismlari
└── lib/api.js           # Axios klient + JWT refresh interceptor

nginx/                   # Reverse proxy konfiguratsiyasi
scripts/                 # Backup va boshqa operatsion skriptlar
```

## Lokal ishga tushirish (Docker Compose)

```bash
cp .env.example .env
# .env faylidagi SECRET_KEY, PAYME_*, BUNNY_*, ESKIZ_* qiymatlarini to'ldiring

docker compose up --build
```

Ishga tushgandan so'ng (barcha yo'llar nginx orqali, 8080-portda):

- Sayt: http://localhost:8080
- Backend API: http://localhost:8080/api/v1/
- Swagger UI: http://localhost:8080/api/schema/swagger-ui/
- Django Admin: http://localhost:8080/admin/
- MinIO konsol: http://localhost:9001

Birinchi marta ishga tushirishda:

```bash
docker compose exec backend python manage.py seed_rbac    # 3 ta rol va huquqlar
docker compose exec backend python manage.py seed_demo    # demo kurs, guruhlar, manager/mentor
docker compose exec backend python manage.py createsuperuser
```

`seed_demo` quyidagi demo hisoblarni yaratadi (parol `demo1234`):
`manager` — kurs va guruhlarni boshqaradi, `mentor` — so'rovlarni tasdiqlaydi.

## Rollar va ro'yxatdan o'tish oqimi

Tizimda **3 ta rol** bor:

| Rol | Vazifasi |
|-----|----------|
| **manager** | Kurs ochadi, guruh yaratadi, dars vaqtlarini belgilaydi, guruhga mentor biriktiradi |
| **mentor** | O'z guruhlariga kelgan ro'yxatdan o'tish so'rovlarini tasdiqlaydi/rad etadi, o'quvchilarni guruhlar orasida ko'chiradi |
| **o'quvchi** | Ro'yxatdan o'tib guruh tanlaydi; mentor tasdiqlagach guruh kursini ko'radi |

Ro'yxatdan o'tish oqimi:

1. Mehmon **faqat** login/register sahifasini ko'radi — kurslar autentifikatsiyasiz **yopiq**.
2. O'quvchi ism, familiya, username va parol (kamida 4 belgi) kiritadi va **guruhni tanlaydi**.
3. Hisob `pending` holatda ochiladi — o'quvchi tizimga kira oladi, lekin kurslarni ko'ra olmaydi.
4. Mentor so'rovni ko'rib chiqib **tasdiqlaydi** → o'quvchi guruhga qo'shiladi va kursga yoziladi.

> Telefon+OTP orqali kirish faqat **mavjud** hisob uchun ishlaydi — u orqali
> yangi hisob ochib bo'lmaydi, aks holda mentor tasdig'ini chetlab o'tish mumkin bo'lardi.

## Lokal ishga tushirish (Docker'siz)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example ../.env   # yoki backend/.env
export DJANGO_SETTINGS_MODULE=config.settings.local

python manage.py migrate
python manage.py seed_rbac
python manage.py createsuperuser
python manage.py runserver
```

PostgreSQL, Redis va MinIO lokal xizmat sifatida ishlab turishi kerak (yoki `docker compose up postgres redis minio`).

Celery worker va beat alohida terminal oynalarida:

```bash
celery -A config worker -l info -Q default,media
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Test

```bash
cd backend
pytest --cov=apps --cov-report=term-missing
```

NF-06: biznes-logika (`services.py`) uchun test qamrovi ≥ 70% CI'da majburiy (`.github/workflows/ci.yml`). Har bir app o'z `tests/` papkasiga ega (`apps/<name>/tests/`); `factories.py`larda factory-boy orqali test ma'lumotlari yaratiladi.

## Kod sifati

```bash
ruff check .
mypy apps config libs
bandit -r apps config libs -x '*/tests/*,*/migrations/*'
```

## Muhim arxitektura qoidalari

- **Qatlamlanish**: `models.py` faqat struktura, `selectors.py` — o'qish, `services.py` — barcha yozish. View'lar yupqa, biznes-logikasiz.
- **Domain event'lar**: modullar bir-birining model/service'ini to'g'ridan-to'g'ri import qilmaydi (masalan `payments` va `enrollment`) — `apps/core/events.py` orqali gaplashadi.
- **RBAC**: granular permission (`group.create`, `student.approve`, ...), scope (`global`/`course`/`organization`). Yangi rol — faqat admin paneldan, kod o'zgarishisiz.
- **Ledger**: barcha pul harakati double-entry, append-only (`apps/payments/models.py::LedgerEntry`). Balans hech qachon alohida saqlanmaydi — har doim ledger'dan hisoblanadi.
- **Kelajakka tayyorlik (D01-D12)**: UUID PK, `organization_id` (B2B), JSONB i18n, video provayder abstraksiyasi va h.k. — TZ 5.5.1-bandga qarang.

## Qamrovga kirmaydi (MVP)

Mobil ilovalar, jonli darslar, AI-modullar, B2B/SSO, real vaqtdagi chat, gamifikatsiya va h.k. — TZ 12-bo'limdagi keyingi bosqichlar ro'yxatiga qarang.
