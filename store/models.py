from django.db import models

class LunarMonth(models.Model):
    order = models.PositiveSmallIntegerField(unique=True)
    olchiki_name = models.CharField(max_length=80)
    english_name = models.CharField(max_length=60)
    is_extra = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    class Meta:
        ordering = ['order']
    def __str__(self): return f'{self.order}. {self.english_name}'

class NewMoon(models.Model):
    date = models.DateField(unique=True)
    lunar_year = models.PositiveIntegerField(null=True, blank=True)
    month_order = models.PositiveSmallIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    class Meta: ordering = ['date']
    def __str__(self): return str(self.date)

class HistoricalDate(models.Model):
    gregorian = models.DateField(unique=True)
    bengali_day = models.PositiveSmallIntegerField(null=True, blank=True)
    bengali_month = models.CharField(max_length=40, blank=True)
    bengali_year = models.PositiveIntegerField(null=True, blank=True)
    santali_day = models.PositiveSmallIntegerField(null=True, blank=True)
    santali_month = models.CharField(max_length=80, blank=True)
    santali_year = models.PositiveIntegerField(null=True, blank=True)
    note = models.TextField(blank=True)
    class Meta: ordering = ['gregorian']
    def __str__(self): return str(self.gregorian)

class LunarEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ('lunar_day', 'Lunar Day'),
        ('full_moon', 'Full Moon'),
        ('new_moon',  'New Moon'),
    ]
    
    month_order = models.PositiveSmallIntegerField(null=True, blank=True)
    month_name = models.CharField(max_length=80, blank=True)
    day = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.CharField(max_length=500, blank=True)
    label = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True)
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='lunar_day',
    )

    class Meta:
        ordering = ['month_order', 'day', 'title']

    def __str__(self):
        return self.title

class SolarEvent(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=300, blank=True)
    details = models.TextField(blank=True)
    image = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    class Meta: ordering = ['date']
    def __str__(self): return f'{self.date} - {self.title}'

class Advertisement(models.Model):
    SLOT_CHOICES = [('left_top','Left Top'),('right_top','Right Top'),('right_bottom','Right Bottom'),('featured','Featured')]
    slot = models.CharField(max_length=30, choices=SLOT_CHOICES)
    business_name = models.CharField(max_length=160)
    image = models.URLField(blank=True)
    target_url = models.URLField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    priority = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    class Meta: ordering = ['slot', '-priority', 'business_name']
    def __str__(self): return self.business_name

class SiteSetting(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.TextField(blank=True)
    def __str__(self): return self.key
