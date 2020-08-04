from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import simplejson as json

from directory.models import Fractions, Researches


@login_required
def fractions(request):
    request_data = json.loads(request.body)
    pk = int(request_data['pk'])
    research = Researches.objects.get(pk=pk)
    fractions_list = []
    for f in Fractions.objects.filter(research=research).order_by("sort_weight"):
        fractions_list.append({
            "pk": f.pk,
            "title": f.title,
            "units": f.units,
            "fsli": f.get_fsli_code(),
        })
    return JsonResponse({
        "fractions": fractions_list,
        "title": research.get_title(),
    })


@login_required
def save_fsli(request):
    request_data = json.loads(request.body)
    fractions = request_data['fractions']
    for fd in fractions:
        f = Fractions.objects.get(pk=fd['pk'])
        nf = fd['fsli'].strip() or None
        if f != f.get_fsli_code():
            f.fsli = nf
            f.save(update_fields=['fsli'])
    return JsonResponse({"ok": True})


def fraction(request):
    request_data = json.loads(request.body)
    pk = request_data['pk'] or -1
    if Fractions.objects.filter(pk=pk).exists():
        f = Fractions.objects.get(pk=pk)
        ft = f.title
        rt = f.research.get_title()
        return JsonResponse({"title": f"{rt} – {ft}" if ft != rt and ft else rt})

    return JsonResponse({"title": None})
