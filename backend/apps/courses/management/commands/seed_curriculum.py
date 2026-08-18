"""
"Dasturlash" kursiga haqiqiy dars rejasini o'rnatadi — 5 bo'lim, 96 dars
(Scratch, Python, PostgreSQL, Django/DRF/Telegram Bot, Deployment).

    python manage.py seed_curriculum

Idempotent: modul va darslar (course, order) bo'yicha get_or_create qilinadi,
sarlavha/matn har chaqirilganda joriy holatga yangilanadi. Eski placeholder
modullar (bo'sh "Scratch"/"Python"/"PostgreSQL"/"Django" — seed_school'dan
qolgan) haqiqiy bo'lim nomlariga almashtiriladi.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.courses.models import Course, Lesson, LessonType, Module

# (bo'lim nomi, [(mavzu, topshiriq tavsifi), ...])
CURRICULUM: list[tuple[str, list[tuple[str, str]]]] = [
    ("Scratch bilan tanishuv va asosiy tushunchalar", [
        ("Scratch bilan tanishuv. Harakat bloklari",
         "Scratch interfeysi. Sahna (Stage), Sprite, Bloklar paneli bilan tanishish. Birinchi "
         "kichik harakat: “Mushukni yuritish”. Move, Turn, Go to bloklari. Sahna "
         "koordinatalari. Oddiy animatsiya. Mushukni chap/o'ng harakatlantirish. Mushukni "
         "aylantirish va 4 tomonga harakatlantirish."),
        ("Tovush va tashqi ko'rinish bloklari. Hodisalar (Events)",
         "Look (Ko'rinish) bloklari. Sound bloklari bilan tanishish. Kostyumlar (Costumes) "
         "almashishi. When green flag clicked. When key pressed. When sprite clicked. "
         "Mushukning “salom berish” animatsiyasi. Tugma bosilganda sprite harakat "
         "qiladigan mini mashq."),
        ("Takrorlash bloklari. Shart operatorlari",
         "Forever, Repeat. Oddiy sikl (Loop) tushunchasi. If, If-else. To'qnashuv (touching) "
         "bloklari. Mushukning chetga urilib qaytishi (bounce effect). Mushuk to'siqqa tegsa "
         "“oh!” deydi."),
        ("Sahna bilan ishlash",
         "Orqa fonlar almashishi. Yangi sahna qo'shish. Sahnalar o'rtasida o'tish. “Kunning "
         "vaqtiga qarab fon o'zgaradi” loyihasi."),
        ("Oddiy o'yin yaratish — 1-qism",
         "O'yin turi: Sharchani tutish o'yini. Ball, tezlik, to'qnashuv tushunchasi. "
         "Tushayotgan sharcha sprite yaratiladi."),
        ("Oddiy o'yin yaratish — 2-qism",
         "Ball qo'shish. “Game over” holati. Tovush qo'shish. O'yin ishchi holatga "
         "keltiriladi."),
        ("Matematik amallar bilan ishlash",
         "Random (tasodifiy sonlar). O'zgaruvchilar (Variables) bilan tanishish. Sprite ning "
         "tasodifiy joyga sakrashi."),
        ("Mini loyihalar kuni",
         "Mini animatsiya. Mini multfilm. Mini o'yin. Har guruh 1 loyihani boshlaydi."),
        ("Loyiha taqdimoti",
         "Har bir guruh o'z loyihasini taqdim etadi. O'qituvchi baholaydi. IT bo'yicha "
         "motivatsion suhbat. O'quvchi o'z o'yinini sinf oldida ko'rsatadi."),
    ]),
    ("Python dasturlash tili va algoritmlari", [
        ("(Python) Python bilan tanishuv",
         "Python tarixi va qo'llanish sohalari. Python interpreter qanday ishlaydi (compiled vs "
         "interpreted). Python va IDE o'rnatish (PyCharm, VS Code). Birinchi dastur: print() va "
         "input(). PEP8 va kod yozish madaniyati."),
        ("(Python) Sintaksis, o'zgaruvchilar va kommentariyalar",
         "O'zgaruvchi va nomlash qoidalari. Constants tushunchasi (UPPER_CASE). Comments: # va "
         "docstring. Type Conversion: int(), str(), float(), bool(). type() va isinstance() "
         "funksiyalari."),
        ("(Python) Stringlar va formatlash",
         "String yaratish va indekslash. String slicing ([start:stop:step]). F-strings, "
         "format(), % formatlash. Raw strings (r\"...\") va escape belgilari (\\n, \\t, \\\\). "
         "String metodlari: upper(), lower(), strip(), split(), join(), replace(), find()."),
        ("(Python) Sonlar va operatorlar",
         "Numbers: int, float, complex. Arifmetik operatorlar (+, -, *, /, //, %, **). "
         "Comparison operatorlar (==, !=, <, >, <=, >=). Logical operatorlar (and, or, not). "
         "Truthy va Falsy qiymatlar."),
        ("(Python) Shartli operatorlar va Control Flow",
         "if, elif, else tuzilmasi. Ichma-ich shartlar (nested if). Ternary operator (a if cond "
         "else b). match-case (Python 3.10+). Amaliy mashqlar."),
        ("(Python) while sikli",
         "while sikli tuzilishi va shartlari. break, continue, pass operatorlari. Cheksiz "
         "sikllar va ulardan chiqish. while-else konstruksiyasi. Amaliy mashqlar."),
        ("(Python) for sikli va range()",
         "for sikli sintaksisi. range() funksiyasi (start, stop, step). Iterables tushunchasi. "
         "Ichma-ich sikllar (nested loops). Amaliy: jadvallar va naqshlar."),
        ("(Python) Ro'yxatlar (List) — 1-qism",
         "List yaratish va indekslash. Slicing va elementlarni o'zgartirish. append(), "
         "insert(), extend(). remove(), pop(), del. len(), min(), max(), sum() funksiyalari."),
        ("(Python) Ro'yxatlar (List) — 2-qism",
         "sort(), sorted(), reverse(). List ustida iterate qilish. List comprehension (asosiy "
         "va shartli). map(), filter(), reduce() bilan tanishuv. Element indeksini topish."),
        ("(Python) Tuple va unpacking",
         "Tuple yaratish va xususiyatlari (immutable). Tuple packing va unpacking (a, b = (1, "
         "2)). * bilan unpacking (a, *rest = [1,2,3,4]). Tuple metodlari: count(), index(). "
         "Tuple vs List — qachon qaysi biri kerak."),
        ("(Python) Set (To'plamlar)",
         "Set yaratish va uniqueness xususiyati. add(), remove(), discard(), pop(). Union, "
         "intersection, difference, symmetric difference. Subset, superset, disjoint sets. Set "
         "comprehension, Frozenset."),
        ("(Python) Dictionary (Lug'atlar)",
         "Key-value tuzilmasi. Dict yaratish va elementga kirish. get(), keys(), values(), "
         "items(). update(), pop(), setdefault(). Ichma-ich dict (nested), Dict comprehension."),
        ("(Python) Funksiyalar — 1-qism",
         "def bilan funksiya yaratish. Parametrlar va return. Positional va keyword "
         "argumentlar. Default parameters. Docstring va funksiyani hujjatlash."),
        ("(Python) Funksiyalar — 2-qism",
         "*args va **kwargs. Local va global scope. Lambda funksiyalar (qisqa). Funksiyalar "
         "bilan amaliy mashqlar."),
        ("(Python) Exception handling",
         "Exception nima va qachon kerak. try, except, else, finally. Eng ko'p uchraydigan "
         "exceptionlar (ValueError, TypeError, ZeroDivisionError, IndexError, KeyError). raise "
         "bilan xato chiqarish. Bir nechta except bloklari."),
        ("(Python) Modullar va paketlar",
         "import, from ... import, as. __name__ va __main__. Module search path (sys.path). "
         "O'z modulini yaratish. Paket (package) tushunchasi va __init__.py, virtual muhit "
         "(venv)."),
        ("(Python) Fayllar bilan ishlash",
         "open() va rejimlar (r, w, a, x). with open(...) konstruksiyasi (context manager). "
         "read(), readline(), readlines(), write(), writelines(). CSV fayllar (csv moduli). "
         "JSON fayllar (json moduli)."),
        ("(Python) Git va GitHub asoslari",
         "Git va GitHub nima, qanday farqlari bor. git init, add, commit, push, pull. GitHub "
         "akkaunt va repository. .gitignore va README.md. Har dars yangi commit bilan "
         "GitHub'ga yuklash."),
        ("(Python) OOP — Class va Object",
         "Procedural vs OOP yondashuv. Class va object tushunchalari. __init__ va self. "
         "Instance va class atributlari. Static methods va class methods (@staticmethod, "
         "@classmethod)."),
        ("(Python) Encapsulation va Property",
         "Public, protected (_), private (__) atributlar. Name mangling tushunchasi. @property "
         "dekoratori. Getter, setter, deleter (@x.setter, @x.deleter). Read-only property."),
        ("(Python) Inheritance (Meros olish)",
         "Bir tomonlama meros olish. super() funksiyasi. Method overriding. isinstance() va "
         "issubclass(). Method Resolution Order (MRO) asoslari."),
        ("(Python) Multiple inheritance va Mixin",
         "Multiple inheritance. MRO chuqur (C3 linearization). Diamond problem. Mixin "
         "classlari va amaliy ishlatilishi. Composition vs Inheritance."),
        ("(Python) Polymorphism va Abstract Class",
         "Polimorfizm tushunchasi va Duck typing. Operator overloading. abc moduli, ABC, "
         "@abstractmethod. Abstract class yaratish. Interface tushunchasi Python'da."),
        ("(Python) Magic / Dunder metodlar",
         "__str__ va __repr__ (farqlari). __len__, __getitem__, __setitem__, __delitem__. "
         "__eq__, __lt__, __gt__, __hash__. __bool__, __call__, __del__. Amaliy: o'z konteyner "
         "classini yozish."),
        ("(Python) References va Memory boshqaruvi",
         "References (obyektlar xotirada qanday yashaydi). Dynamic typing chuqur. Mutable vs "
         "Immutable obyektlar. is vs == operatorlari farqi. None tushunchasi, Garbage "
         "collection asoslari, id() va sys.getsizeof()."),
        ("(Python) Sonlar chuqur va Sequence types",
         "Integer types (Python'da int cheksiz). decimal moduli (aniq hisoblar uchun). float "
         "muammolari (0.1 + 0.2 ≠ 0.3). fractions moduli. Sequence types umumiy "
         "xususiyatlari (list, tuple, str, range), collections.abc."),
        ("(Python) Closures va Decoratorlar — 1-qism",
         "Funksiya — birinchi sinf obyekti. Closures (yopilmalar) chuqur. nonlocal "
         "o'zgaruvchilar. Oddiy decorator yozish. @ sintaksisi va functools.wraps, amaliy: "
         "timer, logger."),
        ("(Python) Decoratorlar — 2-qism",
         "Argumentli decoratorlar (decorator factory). Class decoratorlar. Bir nechta "
         "decoratorlarni birlashtirish. functools.lru_cache (caching). @property ni decorator "
         "sifatida qayta ko'rish."),
        ("(Python) Iteratorlar va Generatorlar",
         "Iterable vs Iterator farqi. __iter__ va __next__ metodlari. yield va generator "
         "funksiya. Generator expressions, yield from. Lazy evaluation va memory afzalliklari."),
        ("(Python) Funksional dasturlash va Named Tuples",
         "map(), filter(), reduce() chuqur. zip(), enumerate(), any(), all(). sorted() va key "
         "parametri. collections.namedtuple va typing.NamedTuple. dataclasses moduli "
         "(asoslari)."),
        ("(Python) Context Managers va Standart kutubxona",
         "with statement chuqur. __enter__ va __exit__ metodlari. contextlib.contextmanager "
         "decorator. collections (Counter, defaultdict, deque, OrderedDict). itertools, "
         "functools foydali funksiyalari."),
        ("(Python) Descriptors va Meta Programming",
         "Descriptors tushunchasi (__get__, __set__, __delete__). Data va non-data "
         "descriptors. Metaclasses asoslari (type va class orqasida nima bor). Amaliy: o'z "
         "descriptor yozish. Meta programming qachon kerak."),
        ("(Python) Concurrency — Multithreading",
         "Concurrency vs Parallelism farqi. Threading moduli — Thread yaratish. Lock, "
         "RLock, Semaphore. Race condition va deadlock. GIL (Global Interpreter Lock), "
         "concurrent.futures.ThreadPoolExecutor."),
        ("(Python) Concurrency — Multiprocessing",
         "Process va Thread farqi. multiprocessing moduli. Pool va parallel hisoblash. "
         "Inter-process communication (Queue, Pipe). "
         "concurrent.futures.ProcessPoolExecutor."),
        ("(Python) Async I/O — 1-qism (asoslar)",
         "Sinxron va asinxron farqi. asyncio kirish. async va await sintaksisi. Coroutine va "
         "event loop. asyncio.run() va asyncio.sleep(), birinchi async dastur."),
        ("(Python) Async I/O — 2-qism (amaliyot)",
         "asyncio.gather(), asyncio.create_task(). aiohttp bilan async HTTP so'rovlar. "
         "aiofiles bilan async fayl o'qish. Async iterators va async context managers. Sync vs "
         "Async vs Threading taqqoslash."),
    ]),
    ("Database — PostgreSQL", [
        ("(Database) Database va PostgreSQL kirish",
         "Database va RDBMS tushunchasi. PostgreSQL nima va afzalliklari (MySQL bilan farqi). "
         "PostgreSQL va pgAdmin o'rnatish. psql buyruq satri va asosiy buyruqlar. Birinchi "
         "database yaratish (CREATE DATABASE)."),
        ("(Database) Jadval yaratish, Field turlari va Sequences",
         "CREATE TABLE sintaksisi va Primary Key. Field turlari: int, bigint, decimal, "
         "varchar, text, date, timestamp, boolean, uuid, json/jsonb. SERIAL, BIGSERIAL "
         "(auto-increment) va IDENTITY column. CREATE TABLE AS va SELECT INTO. Qachon qaysi "
         "turni tanlash."),
        ("(Database) INSERT va UPSERT",
         "INSERT INTO bilan yozuv qo'shish. Bir nechta yozuvni birga qo'shish (VALUES). "
         "RETURNING ifodasi. UPSERT (INSERT ... ON CONFLICT DO UPDATE / DO NOTHING). Amaliy: "
         "ma'lumot to'plamini bazaga yuklash."),
        ("(Database) SELECT asoslari",
         "SELECT * va aniq ustunlarni tanlash. WHERE bilan filterlash. Operatorlar: =, <>, <, "
         ">, <=, >=. AND, OR, NOT. Column aliases (AS), LIMIT, OFFSET."),
        ("(Database) UPDATE va DELETE",
         "UPDATE sintaksisi va SET. Bir nechta ustunni birga yangilash. UPDATE ... FROM "
         "(boshqa jadvaldan). DELETE FROM va WHERE shart bilan. DELETE ... USING (JOIN bilan), "
         "TRUNCATE bilan farqi, RETURNING."),
        ("(Database) Constraints va ALTER TABLE",
         "NOT NULL, UNIQUE, DEFAULT, CHECK. PRIMARY KEY va FOREIGN KEY. ALTER TABLE — "
         "ustun qo'shish/o'chirish. Field turini o'zgartirish (ALTER COLUMN ... TYPE ...). "
         "Constraint qo'shish/o'chirish, RENAME, DROP TABLE (CASCADE/RESTRICT)."),
        ("(Database) Chuqur SELECT — saralash, qidirish, NULL",
         "ORDER BY (ASC, DESC, NULLS FIRST/LAST). DISTINCT va DISTINCT ON. LIKE, ILIKE "
         "(case-insensitive). IN, NOT IN, BETWEEN. IS NULL, IS NOT NULL, CASE WHEN ... THEN "
         "... END."),
        ("(Database) Munosabatlar va JOIN turlari",
         "One-to-One, One-to-Many, Many-to-Many tushunchalari. FOREIGN KEY va ON DELETE "
         "CASCADE. ER diagramma asoslari (dbdiagram.io). INNER JOIN, LEFT JOIN, RIGHT JOIN. "
         "FULL OUTER JOIN, CROSS JOIN, SELF JOIN, table aliases."),
        ("(Database) Aggregatsiya, GROUP BY va Set operatorlari",
         "COUNT, SUM, AVG, MIN, MAX. GROUP BY va HAVING. UNION, UNION ALL. INTERSECT va "
         "EXCEPT. Amaliy: hisobotlar yaratish."),
        ("(Database) Subquery va CTE",
         "Subquery (ichki so'rovlar). ANY, ALL, EXISTS operatorlari. WITH (CTE) — Common "
         "Table Expression. Murakkab so'rovlarni soddalashtirish. Recursive CTE asoslari "
         "(qisqa)."),
        ("(Database) Transaksiyalar, Index va optimizatsiya",
         "Transaksiyalar: BEGIN, COMMIT, ROLLBACK. ACID tamoyillari, SAVEPOINT. Index nima va "
         "qachon kerak. Index turlari (B-tree, Hash, GIN), CREATE INDEX, DROP INDEX. EXPLAIN "
         "ANALYZE bilan so'rov tahlili."),
        ("(Database) Python + psycopg2 va yakuniy mini loyiha",
         "psycopg2 o'rnatish va Python'dan ulanish. cursor, execute(), fetchone(), fetchall(). "
         "Parametrlangan so'rovlar (SQL injection himoyasi). Connection pooling asoslari. "
         "Yakuniy mini loyiha: Python + PostgreSQL bilan to'liq CRUD ilova, GitHub'ga "
         "yuklash."),
    ]),
    ("Django, HTML, Jinja, REST Framework va Telegram Bot", [
        ("(Django) Django bilan tanishuv va o'rnatish",
         "Django nima, framework va kutubxona farqi. MVT arxitekturasi (Model-View-Template). "
         "Virtual muhit (venv) yaratish. Django o'rnatish (pip install django) va loyiha "
         "yaratish. runserver, loyiha tuzilishi (manage.py, settings.py, urls.py, wsgi.py)."),
        ("(Django) Sozlamalar va App yaratish",
         "settings.py ni chuqur ko'rib chiqish. INSTALLED_APPS, DATABASES, LANGUAGE_CODE, "
         "TIME_ZONE, DEBUG, ALLOWED_HOSTS. App yaratish (startapp) va INSTALLED_APPS'ga "
         "ulash. manage.py buyruqlari (migrate, createsuperuser, makemigrations). App "
         "tuzilishi (models.py, views.py, admin.py, apps.py)."),
        ("(Django) URL va View",
         "URL routing (urls.py) — path(), re_path(). Loyiha va app urls.py larini ulash "
         "(include()). Funksional view (FBV) yozish. HttpResponse qaytarish. URL parametrlari "
         "(<int:id>, <slug:name>), name= parametri."),
        ("(Django) Models — 1-qism (yaratish)",
         "Model class yaratish. Field turlari: CharField, IntegerField, TextField, DateField, "
         "DateTimeField, BooleanField, EmailField, URLField. Field parametrlari (max_length, "
         "null, blank, default, unique). Meta class (ordering, verbose_name), __str__ metodi. "
         "makemigrations va migrate, Django Admin'ga model qo'shish."),
        ("(Django) Models — 2-qism (munosabatlar)",
         "ForeignKey (One-to-Many) va on_delete parametri. OneToOneField. ManyToManyField. "
         "related_name va Reverse lookup. Migratsiyalar va munosabatlar, admin panelda "
         "ko'rsatish."),
        ("(Django) Django ORM",
         "QuerySet API: all(), filter(), get(), exclude(), order_by(), count(). first(), "
         "last(), exists(). create(), save(), delete(), update(). Bog'liq ob'ektlar bilan "
         "ishlash (book.author, author.book_set.all()). Django shell (python manage.py shell) "
         "bilan amaliyot."),
        ("(Django) Templates va render() (HTML asoslari bilan)",
         "templates/ papkasi va TEMPLATES sozlamasi. HTML asoslari: <!DOCTYPE>, <html>, "
         "<head>, <body>, h1-h6, p, a, img, ul, ol, div, span. render() funksiyasi va kontekst "
         "(context). View'dan template'ga modeldan olingan ma'lumot uzatish. {{ }} bilan "
         "ma'lumotni chiqarish."),
        ("(Django) DTL — sintaksis va filterlar",
         "DTL (Django Template Language) sintaksisi: {{ }}, {% %}, {# #}. Filterlar: upper, "
         "lower, length, default, date, truncatechars, join. Bir nechta filterlarni "
         "birlashtirish. Modeldan olingan ma'lumotlarni formatlash. Amaliy mashqlar."),
        ("(Django) DTL — shartlar, sikllar, inheritance",
         "Shartlar: {% if %}, {% elif %}, {% else %}, {% endif %}. Sikllar: {% for %} va "
         "forloop o'zgaruvchisi. QuerySet ustida iterate qilish. Template inheritance: {% "
         "extends %}, {% block %}. {% include %} va {% url %}."),
        ("(Django) Jinja template tili",
         "Jinja nima va Django'da qachon kerak (DTL bilan farqlari). Sintaksis va asosiy "
         "konstruksiyalar. Django'da Jinja2 backend qo'shish (TEMPLATES sozlamasi). Macro ({% "
         "macro %}) va kengaytirilgan filterlar. Qachon DTL, qachon Jinja ishlatish."),
        ("(Django) CSS asoslari",
         "CSS sintaksisi va selektorlar (class, id, element, descendant). CSS ulash usullari "
         "(inline, internal, external). Box model: margin, padding, border, width, height. "
         "Rang, font, text formatlash. Display turlari: block, inline, inline-block."),
        ("(Django) Bootstrap va Static fayllar",
         "Bootstrap CDN orqali ulash va asosiy tushunchalar. Grid tizimi (container, row, "
         "col-md-*, col-lg-*). Bootstrap komponentlari: navbar, card, button, form, modal. "
         "STATIC_URL, STATICFILES_DIRS, static/ papkasi. {% load static %} ishlatish, "
         "CSS/JS/rasmlarni ulash."),
        ("(Django) Django Admin chuqur",
         "Admin panelni sozlash, ModelAdmin class. list_display, list_filter, search_fields, "
         "ordering. list_editable, list_per_page. fieldsets va readonly_fields. Inline "
         "modellar (TabularInline, StackedInline), custom admin actions."),
        ("(Django) Forms — 1-qism (Form class)",
         "Django Form class va field turlari. GET va POST so'rovlari. Form'ni template'da "
         "ko'rsatish ({{ form.as_p }}). Form validatsiyasi (is_valid(), cleaned_data). CSRF "
         "himoyasi ({% csrf_token %})."),
        ("(Django) Forms — 2-qism (ModelForm)",
         "ModelForm yaratish va Meta class. ModelForm bilan CRUD (Create, Update). Custom "
         "validatsiya: clean_<field>() va clean() metodlari. Form widgets (forms.TextInput, "
         "forms.Textarea, attrs={}). Bootstrap bilan formani chiroyli qilish."),
        ("(Django) Class-Based Views — 1-qism",
         "FBV vs CBV taqqoslash (afzallik va kamchilik). View base class. TemplateView, "
         "RedirectView. ListView va DetailView. URL bilan ulash (MyView.as_view()), "
         "get_context_data() va get_queryset()."),
        ("(Django) Class-Based Views — 2-qism (CRUD)",
         "CreateView, UpdateView, DeleteView. FormView. success_url va get_success_url(). "
         "Mixinlar (LoginRequiredMixin, PermissionRequiredMixin). Mini CRUD ilova (blog yoki "
         "kitoblar boshqaruvi)."),
        ("(Django) Authentication (kirish/chiqish)",
         "django.contrib.auth tizimi va User modeli. Login va Logout view'lar (built-in CBV). "
         "LoginView, LogoutView. LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL. Password "
         "hashing va xavfsizlik, Bootstrap bilan dizayn."),
        ("(Django) Ro'yxatdan o'tish va Authorization",
         "Registration — UserCreationForm. Custom registration form. @login_required "
         "decorator va LoginRequiredMixin. Permissions va Groups (admin panelda ham). "
         "@permission_required decorator, Password reset (qisqacha)."),
        ("(Django) Custom User Model",
         "Django'ning default User modeli kamchiliklari. Custom User Model (AbstractUser vs "
         "AbstractBaseUser). Email bilan login (username o'rniga). AUTH_USER_MODEL "
         "sozlamasi. Qo'shimcha field qo'shish (avatar, telefon, bio), Profile model."),
        ("(Django) Media fayllar (rasm/file upload)",
         "MEDIA_URL va MEDIA_ROOT sozlamalari. ImageField va FileField. Pillow kutubxonasi "
         "(rasmlar uchun). Form orqali fayl yuklash (enctype=\"multipart/form-data\"). Rasm "
         "validatsiyasi va o'lcham cheklash, template'da ko'rsatish."),
        ("(Django) Pagination, Search va Filter",
         "Paginator class (Page, paginate_by). CBV'da paginate_by parametri. Bootstrap "
         "pagination. Qidiruv funksiyasi (Q obyektlari bilan). GET parametrlari "
         "(request.GET), filtering va sortlash."),
        ("(Django) Django ORM chuqur",
         "Q obyektlari (murakkab OR/AND so'rovlar). F obyektlari (database darajasida "
         "hisoblash). select_related va prefetch_related (N+1 muammosi). annotate va "
         "aggregate (Count, Sum, Avg). values() va values_list(), Raw SQL so'rovlar "
         "(qisqacha)."),
        ("(Django) Email, Cache, Sessions va xavfsizlik",
         "Email yuborish (send_mail, SMTP sozlash). Sessions ishlatish (request.session). "
         "Cookies bilan ishlash. Cache framework asoslari (memory cache, view caching). "
         "Xavfsizlik: SQL injection, XSS, CSRF, .env fayl, DEBUG=False, ALLOWED_HOSTS."),
        ("(Django) REST API va DRF kirish",
         "REST API tamoyillari (HTTP metodlari: GET, POST, PUT, PATCH, DELETE). Status "
         "kodlari (200, 201, 400, 401, 403, 404, 500). JSON formati va API'lar nima uchun "
         "kerak. DRF o'rnatish va INSTALLED_APPS'ga qo'shish. Birinchi API endpoint, "
         "Browsable API."),
        ("(Django) Serializers — 1-qism",
         "Serializer nima va qachon kerak. Serializer class va field turlari. serialize va "
         "deserialize jarayoni. ModelSerializer (Meta class, fields, exclude). "
         "read_only_fields va write_only_fields, shell'da sinash."),
        ("(Django) Serializers — 2-qism (validatsiya va nested)",
         "Serializer validatsiyasi: validate_<field>() va validate(). raise "
         "serializers.ValidationError. create() va update() metodlarini override qilish. "
         "Nested serializerlar (bog'liq modellar). SerializerMethodField (custom field), "
         "source= parametri."),
        ("(Django) APIView va Generic Views",
         "@api_view decorator (FBV uslubi). Request va Response obyektlari. APIView class "
         "(CBV uslubi). Generic Views: ListAPIView, RetrieveAPIView, CreateAPIView, "
         "UpdateAPIView, DestroyAPIView. ListCreateAPIView, RetrieveUpdateDestroyAPIView, "
         "Mixinlar."),
        ("(Django) ViewSet va Routers + GitHub jamoa ishi",
         "ModelViewSet va ReadOnlyModelViewSet. Router bilan URL avtomatizatsiyasi "
         "(DefaultRouter, SimpleRouter). @action decorator bilan custom endpoint. ViewSet vs "
         "APIView vs Generic Views taqqoslash. GitHub: branch, checkout, merge, Pull Request, "
         "kod review."),
        ("(Django) Authentication (DRF)",
         "DRF authentication tushunchasi. SessionAuthentication va BasicAuthentication. "
         "TokenAuthentication (DRF token). JWT (djangorestframework-simplejwt), token "
         "olish/yangilash. Token blacklist va logout, Postman/Thunder Client bilan sinash."),
        ("(Django) Permissions",
         "DRF permissions tushunchasi. AllowAny, IsAuthenticated, IsAdminUser. "
         "IsAuthenticatedOrReadOnly, DjangoModelPermissions. Object-level permissions. Custom "
         "Permission class yozish (has_permission, has_object_permission)."),
        ("(Django) Filtering, Search, Ordering, Pagination",
         "SearchFilter (qidiruv). OrderingFilter (saralash). django-filter kutubxonasi "
         "(DjangoFilterBackend, filterset_fields). PageNumberPagination va "
         "LimitOffsetPagination. Custom pagination class, filter_backends va "
         "pagination_class."),
        ("(Django) Throttling, CORS va Swagger + GitHub konflikt",
         "Rate limiting (Throttling) — AnonRateThrottle, UserRateThrottle. "
         "django-cors-headers o'rnatish va sozlash. Swagger/OpenAPI hujjatlari "
         "(drf-spectacular). API versioning asoslari. GitHub: merge conflict yechish, git "
         "rebase asoslari."),
        ("(Django) Telegram Bot — 1-qism (Aiogram asoslari)",
         "Telegram bot nima va qanday ishlaydi. BotFather orqali bot yaratish va token olish. "
         "Aiogram o'rnatish (pip install aiogram). Birinchi bot: /start, /help buyruqlari, "
         "handler'lar. Async/await Aiogram'da, polling rejimi, Inline va Reply tugmalar."),
        ("(Django) Telegram Bot — 2-qism (Django + ngrok + Webhook)",
         "Polling vs Webhook farqi (production'da webhook). Django + Aiogram integratsiyasi "
         "(Aiogram Django app sifatida). Bot uchun view yaratish (POST endpoint). ngrok "
         "o'rnatish va ishga tushirish (ngrok http 8000). HTTPS URL olish va Telegram'ga "
         "webhook o'rnatish (setWebhook), .env."),
        ("(Django) Telegram Bot — 3-qism (Django ORM bilan to'liq bot)",
         "Bot orqali Django modellariga ma'lumot qo'shish. Django ORM'ni async kontekstda "
         "ishlatish (sync_to_async). FSM (Finite State Machine) — ko'p bosqichli dialog. "
         "Foydalanuvchi ma'lumotlarini bazaga saqlash. Admin panel orqali bot ma'lumotlarini "
         "boshqarish, GitHub'ga yuklash + README."),
    ]),
    ("Deployment — Linux server", [
        ("(Deploy) Linux va VPS asoslari",
         "Linux Ubuntu terminal asosiy buyruqlari (ls, cd, pwd, mkdir, rm, cp, mv, cat, nano). "
         "Fayl tizimi va ruxsatlar (chmod, chown), foydalanuvchilar (sudo, adduser). Paketlar "
         "boshqaruvi (apt update, apt install). VPS sotib olish: AWS EC2 yoki DigitalOcean'da "
         "Ubuntu server ochish. SSH orqali serverga ulanish (ssh user@ip), SSH key, firewall "
         "(ufw)."),
        ("(Deploy) Server tayyorlash va loyihani ishga tushirish",
         "Server'ga paketlar o'rnatish: Python, pip, venv, PostgreSQL, Nginx, Git. "
         "PostgreSQL'da database va user yaratish. Loyihani GitHub'dan klonlash, venv va "
         "requirements.txt o'rnatish. Production sozlamalari (DEBUG=False, ALLOWED_HOSTS, "
         "STATIC_ROOT), migrate, collectstatic. Gunicorn o'rnatish va Django'ni ishga "
         "tushirish, Nginx reverse proxy, systemd service."),
        ("(Deploy) Domain, SSL, Telegram Bot Webhook va monitoring",
         "Domen ulash: domen sotib olish va DNS sozlash (A record VPS IP'ga). Nginx config'da "
         "server_name, SSL sertifikat (Certbot, Let's Encrypt), HTTPS. .env fayl va "
         "python-decouple (yashirin sozlamalar). Telegram bot webhook'ni production'da "
         "o'rnatish (real domen + HTTPS). Loglar va monitoring (journalctl, Nginx "
         "access/error log), server xavfsizligi."),
    ]),
]

LESSON_HOURS = 2  # barcha darslar TZ bo'yicha bir xil: 2 akademik soat


class Command(BaseCommand):
    help = "Dasturlash kursiga to'liq dars rejasini (96 dars, 5 bo'lim) o'rnatadi"

    def add_arguments(self, parser):
        parser.add_argument("--slug", default="dasturlash", help="Kurs slug'i")

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            course = Course.objects.get(slug=options["slug"])
        except Course.DoesNotExist as exc:
            raise CommandError(
                f"'{options['slug']}' slug'li kurs topilmadi — avval seed_school ishga "
                f"tushiring.",
            ) from exc

        section_titles = {section for section, _ in CURRICULUM}
        # seed_school'dan qolgan bo'sh placeholder modullarni (masalan qisqa
        # "Scratch"/"Python" nomli, haqiqiy bo'lim nomiga mos kelmaydigan)
        # tozalaymiz — faqat lekin ichida dars bo'lmaganlarini.
        for module in course.modules.exclude(title__uz__in=section_titles):
            if not module.lessons.exists():
                module.delete()

        total_lessons = 0
        for order, (section_title, lessons) in enumerate(CURRICULUM, start=1):
            module, _ = Module.objects.get_or_create(
                course=course, order=order, defaults={"title": {"uz": section_title}},
            )
            if module.title.get("uz") != section_title:
                module.title = {"uz": section_title}
                module.save(update_fields=["title", "updated_at"])

            for lesson_order, (topic, description) in enumerate(lessons, start=1):
                Lesson.objects.update_or_create(
                    module=module, order=lesson_order,
                    defaults={
                        "type": LessonType.TEXT,
                        "title": {"uz": topic},
                        "text_content": {"uz": description},
                        "is_required": True,
                    },
                )
                total_lessons += 1

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor: {len(CURRICULUM)} ta bo'lim, {total_lessons} ta dars "
            f"({total_lessons * LESSON_HOURS} akademik soat) '{course.slug}' kursiga o'rnatildi.",
        ))
