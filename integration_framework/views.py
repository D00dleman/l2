import random

import simplejson as json
from rest_framework.decorators import api_view
from rest_framework.response import Response

import directions.models as directions
from laboratory.settings import AFTER_DATE
from slog.models import Log
from tfoms.integration import match_enp
from utils.data_verification import data_parse
from utils.dates import normalize_date
from . import sql_if


@api_view()
def next_result_direction(request):
    from_pk = request.GET.get("fromPk")
    after_date = request.GET.get("afterDate")
    if after_date == '0':
        after_date = AFTER_DATE
    next_n = int(request.GET.get("nextN", 1))
    type_researches = request.GET.get("research", '*')
    d_start = f'{after_date}'
    dirs = sql_if.direction_collect(d_start, type_researches, next_n)

    next_time = None
    naprs = []
    if dirs:
        for i in dirs:
            naprs.append(i[0])
            next_time = i[3]

    return Response({"next": naprs, "next_time": next_time, "n": next_n, "fromPk": from_pk, "afterDate": after_date})


@api_view()
def get_dir_amd(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_amd(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def get_dir_n3(request):
    next_n = int(request.GET.get("nextN", 5))
    dirs = sql_if.direction_resend_n3(next_n)
    result = {"ok": False, "next": []}
    if dirs:
        result = {"ok": True, "next": [i[0] for i in dirs]}

    return Response(result)


@api_view()
def result_amd_send(request):
    result = json.loads(request.GET.get("result"))
    resp = {"ok": False}
    if result['error']:
        for i in result['error']:
            dir_pk = int(i.split(':')[0])
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, error_amd=True)
        resp = {"ok": True}
    if result['send']:
        for i in result['send']:
            data_amd = i.split(':')
            dir_pk = int(data_amd[0])
            amd_num = data_amd[1]
            directions.Napravleniya.objects.filter(pk=dir_pk).update(need_resend_amd=False, amd_number=amd_num, error_amd=False)
        resp = {"ok": True}

    return Response(resp)


@api_view()
def direction_data(request):
    pk = request.GET.get("pk")
    research_pks = request.GET.get("research", '*')
    direction = directions.Napravleniya.objects.get(pk=pk)
    card = direction.client
    individual = card.individual

    iss = directions.Issledovaniya.objects.filter(napravleniye=direction, time_confirmation__isnull=False)
    if research_pks != '*':
        iss = iss.filter(research__pk__in=research_pks.split(','))

    if not iss:
        return Response({"ok": False,})

    iss_index = random.randrange(len(iss))

    return Response(
        {
            "ok": True,
            "pk": pk,
            "createdAt": direction.data_sozdaniya,
            "patient": {
                **card.get_data_individual(full_empty=True, only_json_serializable=True),
                "family": individual.family,
                "name": individual.name,
                "patronymic": individual.patronymic,
                "birthday": individual.birthday,
                "sex": individual.sex,
                "card": {"base": {"pk": card.base_id, "title": card.base.title, "short_title": card.base.short_title,}, "pk": card.pk, "number": card.number,},
            },
            "issledovaniya": [x.pk for x in iss],
            "timeConfirmation": iss[iss_index].time_confirmation,
            "docLogin": iss[iss_index].doc_confirmation.rmis_login,
            "docPassword": iss[iss_index].doc_confirmation.rmis_password,
            "department_oid": iss[iss_index].doc_confirmation.podrazdeleniye.oid,
        }
    )


@api_view()
def issledovaniye_data(request):
    pk = request.GET.get("pk")
    ignore_sample = request.GET.get("ignoreSample") == 'true'
    i = directions.Issledovaniya.objects.get(pk=pk)

    sample = directions.TubesRegistration.objects.filter(issledovaniya=i, time_get__isnull=False).first()
    results = directions.Result.objects.filter(issledovaniye=i, fraction__fsli__isnull=False)

    if (not ignore_sample and not sample) or not results.exists():
        return Response({"ok": False,})

    results_data = []

    for r in results:
        results_data.append(
            {
                "pk": r.pk,
                "fsli": r.fraction.get_fsli_code(),
                "value": r.value.replace(',', '.'),
                "units": r.get_units(),
                "ref": list(map(lambda rf: rf if '.' in rf else rf + '.0', map(lambda f: f.replace(',', '.'), (r.calc_normal(only_ref=True) or '').split("-")))),
            }
        )

    return Response(
        {
            "ok": True,
            "pk": pk,
            "sample": {"date": sample.time_get.date() if sample else i.time_confirmation.date(),},
            "date": i.time_confirmation.date(),
            "results": results_data,
            "code": i.research.code,
        }
    )


@api_view()
def make_log(request):
    key = request.GET.get("key")
    keys = request.GET.get("keys", key).split(",")
    t = int(request.GET.get("type"))
    body = {}

    if request.method == "POST":
        body = json.loads(request.body)

    for k in keys:
        if t in (60000, 60001, 60002, 60003) and k:
            directions.Napravleniya.objects.filter(pk=k).update(need_resend_n3=False)

            Log.log(key=k, type=t, body=json.dumps(body.get(k, {})))
    return Response({"ok": True})


@api_view(['POST'])
def check_enp(request):
    enp, bd = data_parse(request.body, {'enp': str, 'bd': str})

    enp = enp.replace(' ', '')

    tfoms_data = match_enp(enp)

    if tfoms_data:
        bdate = tfoms_data.get('birthdate', '').split(' ')[0]
        if normalize_date(bd) == normalize_date(bdate):
            return Response({"ok": True, 'patient_data': tfoms_data})

        return Response({"ok": False, 'message': 'Неверные данные или нет прикрепления к поликлинике'})

    return Response({"ok": False})
