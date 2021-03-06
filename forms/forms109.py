import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from api.stationar.stationar_func import hosp_get_hosp_direction
from forms.forms_func import primary_reception_get_data
from laboratory.settings import FONTS_FOLDER
from api.plans.sql_func import get_plans_by_pk
from doctor_call.models import DoctorCall
from laboratory.utils import strdatetime
from list_wait.models import ListWait
import datetime
from utils.dates import normalize_dash_date, try_parse_range


def form_01(request_data):
    # план операций
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=20 * mm, rightMargin=12 * mm, topMargin=6 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("План операций")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.5
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_LEFT
    style.firstLineIndent = 0
    style.spaceAfter = 1.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 16
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.firstLineIndent = 0
    styleCenter.alignment = TA_CENTER

    data = request_data["pks_plan"]
    pks_plan = [int(i) for i in data.split(',')]
    plans = get_plans_by_pk(pks_plan)

    objs = []
    objs.append(Paragraph("План операций", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))

    opinion = [
        [
            Paragraph('Дата операции', styleTB),
            Paragraph('№ Истории', styleTB),
            Paragraph('Пациент', styleTB),
            Paragraph('Вид операции', styleTB),
            Paragraph('Врач - хирург', styleTB),
            Paragraph('Отделение', styleTB),
            Paragraph('Анестезиолог', styleTB),
        ],
    ]

    for i in plans:
        doc_fio = ''
        if i[6]:
            doc_fio = i[6].split(' ')
            if len(doc_fio) == 1:
                doc_fio = doc_fio[0]
            elif len(doc_fio) == 2:
                doc_fio = f"{doc_fio[0]} {doc_fio[1]}"
            else:
                doc_fio = f"{doc_fio[0]} {doc_fio[1][0]}.{doc_fio[2][0]}."
        anesthetist_fio = ''
        if i[9]:
            anesthetist_fio = i[9].split(' ')
            anesthetist_fio = f"{anesthetist_fio[0]} {anesthetist_fio[1][0]}.{anesthetist_fio[2][0]}."
        strike_o = ""
        strike_cl = ""
        if i[10]:
            strike_o = "<strike>"
            strike_cl = "</strike>"
        department = i[7] if i[7] else i[16]

        hosp_nums_obj = hosp_get_hosp_direction(i[2])
        hosp_first_num = hosp_nums_obj[0].get('direction')
        primary_reception_data = primary_reception_get_data(hosp_first_num)
        if primary_reception_data['weight']:
            weight = f", Вес-{primary_reception_data['weight']}"
        else:
            weight = ''
        opinion.append(
            [
                Paragraph(f"{strike_o}{i[3]}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i[2]}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i[11]} {i[12]} {i[13]}, {i[14]}{weight}{strike_cl}", style),
                Paragraph(f"{strike_o}{i[4]}{strike_cl}", style),
                Paragraph(f"{strike_o}{doc_fio}{strike_cl}", style),
                Paragraph(f"{strike_o}{department}{strike_cl}", style),
                Paragraph(f"{strike_o}{anesthetist_fio}{strike_cl}", style),
            ]
        )

    tbl = Table(opinion, colWidths=(30 * mm, 27 * mm, 50 * mm, 50 * mm, 40 * mm, 30 * mm, 40 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_02(request_data):
    # Вызов врача
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=20 * mm, rightMargin=12 * mm, topMargin=6 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма – Вызов врача")

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.5
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_LEFT
    style.firstLineIndent = 0
    style.spaceAfter = 1.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 16
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.firstLineIndent = 0
    styleCenter.alignment = TA_CENTER

    date = request_data["date"]
    district = int(request_data.get("district", -1) or -1)
    is_canceled = int(request_data["cancel"])
    doc_assigned = int(request_data.get("doc", -1) or -1)
    purpose_id = int(request_data.get("purpose", -1) or -1)
    hospital = int(request_data.get("hospital_pk", -1) or -1)
    cancel = True if is_canceled == 0 else False

    is_external = int(request_data.get("external", 1))
    external = True if is_external == 0 else False
    out_call = ''
    if external:
        out_call = " <u>внешние</u>"

    objs = []
    objs.append(Paragraph(f"Вызова (обращения){out_call} {normalize_dash_date(date)}", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))

    time_start = f'{date} {request_data.get("time_start", "00:00")}'
    time_end = f'{date} {request_data.get("time_end", "23:59")}'
    datetime_start = datetime.datetime.strptime(time_start, '%Y-%m-%d %H:%M')
    datetime_end = datetime.datetime.strptime(time_end, '%Y-%m-%d %H:%M')
    if external:
        doc_call = DoctorCall.objects.filter(
            create_at__range=[datetime_start, datetime_end],
        )
    else:
        doc_call = DoctorCall.objects.filter(create_at__range=[datetime_start, datetime_end])
    doc_call = doc_call.filter(is_external=external, cancel=cancel)

    if hospital > -1:
        doc_call = doc_call.filter(hospital__pk=hospital)
    if doc_assigned > -1:
        doc_call = doc_call.filter(doc_assigned__pk=doc_assigned)
    if district > -1:
        doc_call = doc_call.filter(district_id__pk=district)
    if purpose_id > -1:
        doc_call = doc_call.filter(purpose=purpose_id)

    if external:
        doc_call = doc_call.order_by('hospital', 'pk')
    elif hospital + doc_assigned + district + purpose_id > -4:
        doc_call = doc_call.order_by("pk")
    else:
        doc_call = doc_call.order_by("district__title")

    strike_o = ""
    strike_cl = ""

    if cancel:
        strike_o = "<strike>"
        strike_cl = "</strike>"

    opinion = [
        [
            Paragraph('№ п/п', styleTB),
            Paragraph('Пациент', styleTB),
            Paragraph('Адрес', styleTB),
            Paragraph('Участок', styleTB),
            Paragraph('Телефон', styleTB),
            Paragraph('Услуга', styleTB),
            Paragraph('Примечание', styleTB),
            Paragraph('Врач', styleTB),
            Paragraph('Цель', styleTB),
        ],
    ]

    count = 0
    what_purpose = ''
    who_doc_assigned = ''
    for i in doc_call:
        count += 1
        title = ''
        if i.district:
            title = i.district.title
        if i.doc_assigned:
            who_doc_assigned = i.doc_assigned.get_full_fio()
        if i.purpose:
            what_purpose = i.get_purpose_display()
        org = ""
        if i.hospital:
            org = f"<br/>{i.hospital.short_title or i.title}"

        create_at = strdatetime(i.create_at)

        opinion.append(
            [
                Paragraph(f"{strike_o}{count}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i.client.individual.fio()} ({i.client.number_with_type()}){org}<br/>{create_at}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{i.address.replace('<', '&lt;').replace('>', '&gt;')}{strike_cl}", styleCenter),
                Paragraph(f"{strike_o}{title}{strike_cl}", style),
                Paragraph(f"{strike_o}{(i.phone or i.client.phone).replace('<', '&lt;').replace('>', '&gt;')}{strike_cl}", style),
                Paragraph(f"{strike_o}{i.research.title}{strike_cl}", style),
                Paragraph(f"{strike_o}{i.comment.replace('<', '&lt;').replace('>', '&gt;')[:400]}{strike_cl}", style),
                Paragraph(f"{strike_o}{who_doc_assigned}{strike_cl}", style),
                Paragraph(f"{strike_o}{what_purpose}{strike_cl}", style),
            ]
        )

    tbl = Table(opinion, colWidths=(10 * mm, 40 * mm, 35 * mm, 15 * mm, 25 * mm, 40 * mm, 35 * mm, 30 * mm, 25 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def form_03(request_data):
    # Лист ожидания
    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=20 * mm, rightMargin=12 * mm, topMargin=6 * mm, bottomMargin=4 * mm, allowSplitting=1, title="Форма {}".format("План операций")
    )

    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 10.5
    style.leading = 12
    style.spaceAfter = 0 * mm
    style.alignment = TA_LEFT
    style.firstLineIndent = 0
    style.spaceAfter = 1.5 * mm

    styleCenterBold = deepcopy(style)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 16
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'

    styleTB = deepcopy(style)
    styleTB.firstLineIndent = 0
    styleTB.alignment = TA_CENTER
    styleTB.fontName = "PTAstraSerifBold"

    styleCenter = deepcopy(style)
    styleCenter.firstLineIndent = 0
    styleCenter.alignment = TA_CENTER

    dates = request_data["date"].split(",")
    date_start, date_end = try_parse_range(dates[0], dates[1])

    objs = []
    objs.append(Paragraph(f"Лист ожидани: {dates[0]} - {dates[1]}", styleCenterBold))
    objs.append(Spacer(1, 5 * mm))

    research_pk = int(request_data["research_pk"])
    if research_pk > -1:
        list_wait = ListWait.objects.filter(
            exec_at__range=(
                date_start,
                date_end,
            ),
            research_id__pk=research_pk,
        ).order_by("exec_at")
    else:
        list_wait = ListWait.objects.filter(
            exec_at__range=(
                date_start,
                date_end,
            )
        ).order_by("exec_at")

    opinion = [
        [
            Paragraph('№ п/п', styleTB),
            Paragraph('Пациент', styleTB),
            Paragraph('Телефон', styleTB),
            Paragraph('Услуга', styleTB),
            Paragraph('Статус', styleTB),
            Paragraph('Примечание', styleTB),
        ],
    ]

    count = 0
    for i in list_wait:
        count += 1
        opinion.append(
            [
                Paragraph(f"{count}", styleCenter),
                Paragraph(f"{i.client.individual.fio()} ({i.client.number_with_type()})", styleCenter),
                Paragraph(f"{i.client.phone}", styleCenter),
                Paragraph(f"{i.research.title}", style),
                Paragraph(f"{i.get_work_status_display()}", style),
                Paragraph(f"{i.comment}", style),
            ]
        )

    tbl = Table(opinion, colWidths=(10 * mm, 80 * mm, 30 * mm, 50 * mm, 30 * mm, 40 * mm), splitByRow=1, repeatRows=1)

    tbl.setStyle(
        TableStyle(
            [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5 * mm),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        )
    )

    objs.append(tbl)
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()

    return pdf
