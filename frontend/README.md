# Frontend

ה־frontend נפרד לחלוטין מה־backend. הוא Vanilla HTML/CSS/JavaScript — ללא npm וללא תהליך build.

## הגדרת כתובת ה־API

פתחי את `config.js` ושני רק את המשתנה הבא:

```js
const API_BASE_URL = "http://localhost:8000/api/v1";
```

לדוגמה, בשרת: `https://api.example.com/api/v1`.

## הרצה מקומית

מתוך התיקייה `frontend`:

```powershell
python -m http.server 5500
```

ואז פתחי `http://localhost:5500`.

ה־backend צריך לרוץ בנפרד בפורט 8000. עבור כתובת frontend אחרת, הגדירי ב־backend את `FRONTEND_ORIGINS`, לדוגמה:

```powershell
$env:FRONTEND_ORIGINS="http://localhost:5500"
```

## מבנה

- `index.html` — מבנה העמוד והטופס.
- `styles.css` — העיצוב בלבד.
- `config.js` — כתובת ה־backend בלבד.
- `app.js` — טעינת שעות פנויות ושליחת הזמנה, עם פונקציות והערות ברורות.

## Admin Panel

במסך יש קישור **ניהול**. הזיני את `ADMIN_SECRET_KEY` המוגדר ב־backend בתור Admin token.

הפאנל מאפשר:

- צפייה ב־100 התורים האחרונים.
- הוספת חלון זמן שבועי.
- צפייה בכל חלונות הזמן ומחיקה שלהם.

הטוקן אינו נשמר בדפדפן; הוא נמחק ברענון העמוד או בלחיצה על "יציאה".
