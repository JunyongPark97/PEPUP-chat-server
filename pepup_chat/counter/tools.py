from .models import FastCounter
from django.db.models import F


class FastCounterHelper:
    def get(self, key):
        counter, _ = FastCounter.objects.get_or_create(key=key)
        return counter.count

    def increment_and_get(self, key):
        counter, _ = FastCounter.objects.get_or_create(key=key)
        FastCounter.objects.filter(key=key).update(count=F('count')+1)
        return counter.count + 1


fast_counter_helper = FastCounterHelper()
