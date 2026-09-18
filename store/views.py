import csv, io, json
import os
import uuid
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_http_methods
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.urls import reverse

from .models import (
    LunarMonth, NewMoon, HistoricalDate, LunarEvent,
    SolarEvent, Advertisement, SiteSetting
)


# ============================================================
# MONTH DEFAULTS
# ============================================================
MONTH_DEFAULTS = [
    ('ᱢᱟᱜᱽ', 'MAG', False), ('ᱯᱷᱟᱹᱜᱩᱱ', 'FAGUN', False), ('ᱪᱟᱹᱛ', 'CHAIT', False),
    ('ᱵᱟᱹᱭᱥᱟᱹᱠ', 'BAISAK', False), ('ᱡᱷᱮᱸᱴ', 'JHET', False),
    ('ᱵᱟᱺᱰᱭᱟᱹ ᱡᱷᱮᱸᱴ', 'BADYA JHET', True), ('ᱟᱥᱟᱲ', 'ASAR', False),
    ('ᱥᱟᱱ', 'SAN', False), ('ᱵᱷᱟᱫᱚᱨ', 'BHADOR', False), ('ᱫᱟᱸᱥᱟᱸᱭ', 'DANSAY', False),
    ('ᱥᱚᱨᱦᱟᱭ', 'SARHAY', False), ('ᱟᱸᱜᱷᱟᱲ', 'ANGHAR', False), ('ᱯᱩᱥ', 'PUS', False)
]


def ensure_months():
    for i, (o, e, x) in enumerate(MONTH_DEFAULTS, 1):
        LunarMonth.objects.get_or_create(
            order=i,
            defaults={'olchiki_name': o, 'english_name': e, 'is_extra': x, 'active': True}
        )


# ============================================================
# JSON SERIALIZERS
# ============================================================
def month_json(m):
    return {
        'id': m.id, 'order': m.order,
        'olchiki_name': m.olchiki_name,
        'english_name': m.english_name,
        'is_extra': m.is_extra,
    }


def hist_json(x):
    return {
        'id': x.id, 'date': x.gregorian.isoformat(),
        'bDay': x.bengali_day, 'bMonth': x.bengali_month, 'bYear': x.bengali_year,
        'sDay': x.santali_day, 'sMonth': x.santali_month, 'sYear': x.santali_year,
        'note': x.note,
    }


def event_json(x):
    return {
        'id': x.id,
        'month': x.month_order,
        'month_name': x.month_name or '',
        'day': x.day,
        'title': x.title,
        'description': x.description,
        'image': x.image,
        'label': x.label,
        'event_type': x.event_type or 'lunar_day',
    }


def solar_json(x):
    return {
        'id': x.id, 'date': x.date.isoformat(),
        'title': x.title,
        'description': x.short_description,
        'details': x.details,
        'image': x.image,
    }


def ad_json(x):
    return {
        'id': x.id, 'slot': x.slot,
        'business_name': x.business_name,
        'image': x.image,
        'target_url': x.target_url,
        'start_date': x.start_date.isoformat() if x.start_date else None,
        'end_date': x.end_date.isoformat() if x.end_date else None,
        'priority': x.priority,
    }


def staff_required(request):
    return request.user.is_authenticated and request.user.is_staff


# ============================================================
# IMAGE UPLOAD
# ============================================================
@login_required
@require_http_methods(['POST'])
def upload_image(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin login required'}, status=403)

    f = request.FILES.get('image')
    if not f:
        return JsonResponse({'error': 'Image file required'}, status=400)

    allowed = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.bmp', '.avif'}
    ext = os.path.splitext(f.name.lower())[1]

    if ext not in allowed:
        return JsonResponse({
            'error': 'Allowed image types: JPG, JPEG, PNG, WEBP, GIF, SVG, BMP, AVIF'
        }, status=400)

    if f.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'Image must be 10 MB or smaller'}, status=400)

    try:
        upload_dir = settings.MEDIA_ROOT / 'calendar_images'
        upload_dir.mkdir(parents=True, exist_ok=True)

        fs = FileSystemStorage(
            location=upload_dir,
            base_url=settings.MEDIA_URL + 'calendar_images/'
        )

        safe_name = f"{uuid.uuid4().hex}{ext}"
        saved = fs.save(safe_name, f)

        return JsonResponse({'ok': True, 'url': fs.url(saved), 'name': saved})

    except Exception as e:
        return JsonResponse({'error': f'Image upload failed: {str(e)}'}, status=500)


# ============================================================
# ADMIN PANEL
# ============================================================
def admin_panel(request):
    if not staff_required(request):
        return redirect(f'{reverse("login")}?next={request.path}')
    return render(request, 'admin.html')


# ============================================================
# BOOTSTRAP
# ============================================================
@require_GET
def bootstrap(request):
    ensure_months()
    return JsonResponse({
        'months': [month_json(x) for x in LunarMonth.objects.filter(active=True)],
        'history': [hist_json(x) for x in HistoricalDate.objects.all()],
        'newMoons': [
            {
                'id': x.id,
                'date': x.date.isoformat(),
                'lunar_year': x.lunar_year,
                'month_order': x.month_order,
                'note': x.note,
            } for x in NewMoon.objects.all()
        ],
        'events': [event_json(x) for x in LunarEvent.objects.filter(active=True)],
        'solarEvents': [solar_json(x) for x in SolarEvent.objects.filter(active=True)],
        'ads': [ad_json(x) for x in Advertisement.objects.filter(active=True)],
        'settings': {x.key: x.value for x in SiteSetting.objects.all()},
    })


# ============================================================
# CALENDAR MONTH
# ============================================================
@require_GET
def calendar_month(request):
    try:
        y = int(request.GET['year'])
        m = int(request.GET['month'])
    except (KeyError, ValueError):
        return JsonResponse({'error': 'year and month required'}, status=400)

    start = date(y, m, 1)
    end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)

    return JsonResponse({
        'history': {
            x.gregorian.isoformat(): hist_json(x)
            for x in HistoricalDate.objects.filter(gregorian__gte=start, gregorian__lt=end)
        },
        'newMoons': [
            {
                'id': x.id,
                'date': x.date.isoformat(),
                'lunar_year': x.lunar_year,
                'month_order': x.month_order,
            } for x in NewMoon.objects.filter(
                date__gte=start - timedelta(days=40),
                date__lt=end + timedelta(days=40)
            )
        ],
        'events': [event_json(x) for x in LunarEvent.objects.filter(active=True)],
        'solarEvents': [
            solar_json(x) for x in SolarEvent.objects.filter(
                active=True, date__gte=start, date__lt=end
            )
        ],
        'ads': [ad_json(x) for x in Advertisement.objects.filter(active=True)],
    })


# ============================================================
# DATA API (POST / PUT / DELETE)
# ============================================================
@login_required
@require_http_methods(['POST', 'PUT', 'DELETE'])
def data_api(request, kind):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin login required'}, status=403)

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    model_map = {
        'month': LunarMonth,
        'moon': NewMoon,
        'history': HistoricalDate,
        'event': LunarEvent,
        'solar': SolarEvent,
        'ad': Advertisement,
        'setting': SiteSetting,
    }

    Model = model_map.get(kind)
    if not Model:
        return JsonResponse({'error': 'Unknown resource'}, status=404)

    obj = Model.objects.filter(pk=body.get('id')).first() if body.get('id') else None

    # ---------- DELETE ----------
    if request.method == 'DELETE':
        if not obj:
            return JsonResponse({'error': 'Not found'}, status=404)
        obj.delete()
        return JsonResponse({'ok': True})

    # ---------- CREATE / UPDATE ----------
    if kind == 'month':
        obj = obj or Model()
        obj.order = int(body['order'])
        obj.olchiki_name = body.get('olchiki_name', '')
        obj.english_name = body.get('english_name', '')
        obj.is_extra = bool(body.get('is_extra'))
        obj.active = True

    elif kind == 'moon':
        obj = obj or Model()
        obj.date = body['date']
        obj.lunar_year = body.get('lunar_year') or None
        obj.month_order = body.get('month_order') or None
        obj.note = body.get('note', '')

    elif kind == 'history':
        obj = obj or Model()
        obj.gregorian = body['date']
        obj.bengali_day = body.get('bDay') or None
        obj.bengali_month = body.get('bMonth', '')
        obj.bengali_year = body.get('bYear') or None
        obj.santali_day = body.get('sDay') or None
        obj.santali_month = body.get('sMonth', '')
        obj.santali_year = body.get('sYear') or None
        obj.note = body.get('note', '')

    elif kind == 'event':
        obj = obj or Model()
        # month_order nullable — সাঁওতালি নাম ভিত্তিক ম্যাচিং-এর জন্য
        month_val = body.get('month')
        obj.month_order = int(month_val) if month_val not in (None, '', 0) else None
        obj.month_name = body.get('month_name', '')
        obj.day = int(body.get('day', 1))
        obj.title = body['title']
        obj.description = body.get('description', '')
        obj.image = body.get('image', '')
        obj.label = body.get('label', '')
        obj.event_type = body.get('event_type', 'lunar_day')
        obj.active = True

    elif kind == 'solar':
        obj = obj or Model()
        obj.date = body['date']
        obj.title = body['title']
        obj.short_description = body.get('description', '')
        obj.details = body.get('details', '')
        obj.image = body.get('image', '')
        obj.active = True

    elif kind == 'ad':
        obj = obj or Model()
        obj.slot = body['slot']
        obj.business_name = body['business_name']
        obj.image = body.get('image', '')
        obj.target_url = body.get('target_url', '')
        obj.start_date = body.get('start_date') or None
        obj.end_date = body.get('end_date') or None
        obj.priority = int(body.get('priority', 0))
        obj.active = True

    elif kind == 'setting':
        obj, _ = Model.objects.get_or_create(key=body['key'])
        obj.value = body.get('value', '')

    try:
        obj.save()
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'ok': True, 'id': obj.id})


# ============================================================
# IMPORT CSV
# ============================================================
@login_required
@require_http_methods(['POST'])
def import_csv(request, kind):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin login required'}, status=403)

    if 'file' not in request.FILES:
        return JsonResponse({'error': 'CSV file required'}, status=400)

    raw = request.FILES['file'].read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(raw))
    count = 0

    try:
        for r in reader:
            if kind == 'history':
                HistoricalDate.objects.update_or_create(
                    gregorian=r['gregorian'],
                    defaults={
                        'bengali_day': r.get('bengali_day') or None,
                        'bengali_month': r.get('bengali_month', ''),
                        'bengali_year': r.get('bengali_year') or None,
                        'santali_day': r.get('santali_day') or None,
                        'santali_month': r.get('santali_month', ''),
                        'santali_year': r.get('santali_year') or None,
                        'note': r.get('note', ''),
                    }
                )
                count += 1

            elif kind == 'moon':
                NewMoon.objects.update_or_create(
                    date=r['date'],
                    defaults={
                        'lunar_year': r.get('lunar_year') or None,
                        'month_order': r.get('month_order') or None,
                        'note': r.get('note', ''),
                    }
                )
                count += 1

            elif kind == 'event':
                # month_order nullable
                m_val = r.get('month')
                month_order = int(m_val) if m_val not in (None, '', '0') else None
                LunarEvent.objects.create(
                    month_order=month_order,
                    month_name=r.get('month_name', ''),
                    day=int(r.get('day', 1)),
                    title=r['title'],
                    description=r.get('description', ''),
                    image=r.get('image', ''),
                    label=r.get('label', ''),
                    event_type=r.get('event_type', 'lunar_day'),
                    active=True,
                )
                count += 1

            else:
                return JsonResponse({'error': 'Unsupported import type'}, status=400)

    except (KeyError, ValueError) as e:
        return JsonResponse({'error': f'CSV error: {e}'}, status=400)

    return JsonResponse({'ok': True, 'count': count})


# ============================================================
# EXPORT CSV
# ============================================================
@login_required
@require_GET
def export_csv(request, kind):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Admin login required'}, status=403)

    fields = []
    rows = []

    if kind == 'history':
        fields = ['gregorian', 'bengali_day', 'bengali_month', 'bengali_year',
                  'santali_day', 'santali_month', 'santali_year', 'note']
        rows = [
            [x.gregorian, x.bengali_day, x.bengali_month, x.bengali_year,
             x.santali_day, x.santali_month, x.santali_year, x.note]
            for x in HistoricalDate.objects.all()
        ]

    elif kind == 'moon':
        fields = ['date', 'lunar_year', 'month_order', 'note']
        rows = [[x.date, x.lunar_year, x.month_order, x.note] for x in NewMoon.objects.all()]

    elif kind == 'event':
        fields = ['month', 'month_name', 'day', 'title', 'description',
                  'image', 'label', 'event_type']
        rows = [
            [x.month_order, x.month_name, x.day, x.title, x.description,
             x.image, x.label, x.event_type]
            for x in LunarEvent.objects.all()
        ]

    else:
        return JsonResponse({'error': 'Unsupported export type'}, status=400)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename={kind}.csv'
    w = csv.writer(response)
    w.writerow(fields)
    w.writerows(rows)
    return response