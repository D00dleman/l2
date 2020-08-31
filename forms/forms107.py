import locale
import os.path
import sys
from copy import deepcopy
from io import BytesIO
import simplejson as json
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Indenter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from appconf.manager import SettingManager
from directions.models import Napravleniya
from laboratory.settings import FONTS_FOLDER
from api.stationar.stationar_func import hosp_get_hosp_direction, get_temperature_list
from reportlab.lib import colors
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.widgets.markers import makeMarker


def form_01(request_data):
    """
    Температурный лист (АД, Пульс)
    на входе: type=107.01&hosps_pk=[113110]&titles=['Температура (°C)', 'Пульс', 'Давление']
    """
    num_dir = json.loads(request_data["hosp_pks"])
    direction_obj = Napravleniya.objects.get(pk=num_dir[0])
    hosp_nums_obj = hosp_get_hosp_direction(num_dir[0])
    hosp_nums = ''
    for i in hosp_nums_obj:
        hosp_nums = hosp_nums + ' - ' + str(i.get('direction'))

    ind_card = direction_obj.client
    patient_data = ind_card.get_data_individual()

    if sys.platform == 'win32':
        locale.setlocale(locale.LC_ALL, 'rus_rus')
    else:
        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    pdfmetrics.registerFont(TTFont('PTAstraSerifBold', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Bold.ttf')))
    pdfmetrics.registerFont(TTFont('PTAstraSerifReg', os.path.join(FONTS_FOLDER, 'PTAstraSerif-Regular.ttf')))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=15 * mm, rightMargin=5 * mm, topMargin=13 * mm, bottomMargin=10 * mm, allowSplitting=1, title="Форма {}".format("Лист показателей")
    )
    width, height = landscape(A4)
    styleSheet = getSampleStyleSheet()
    style = styleSheet["Normal"]
    style.fontName = "PTAstraSerifReg"
    style.fontSize = 12
    style.leading = 15
    style.spaceAfter = 0.5 * mm
    styleBold = deepcopy(style)
    styleBold.fontName = "PTAstraSerifBold"
    styleCenter = deepcopy(style)
    styleCenter.alignment = TA_CENTER
    styleCenter.fontSize = 12
    styleCenter.leading = 15
    styleCenter.spaceAfter = 1 * mm
    styleCenterBold = deepcopy(styleBold)
    styleCenterBold.alignment = TA_CENTER
    styleCenterBold.fontSize = 12
    styleCenterBold.leading = 15
    styleCenterBold.face = 'PTAstraSerifBold'
    styleCenterBold.borderColor = black
    styleJustified = deepcopy(style)
    styleJustified.alignment = TA_JUSTIFY
    styleJustified.spaceAfter = 4.5 * mm
    styleJustified.fontSize = 12
    styleJustified.leading = 4.5 * mm

    objs = []

    styleT = deepcopy(style)
    styleT.alignment = TA_LEFT
    styleT.fontSize = 10
    styleT.leading = 4.5 * mm
    styleT.face = 'PTAstraSerifReg'

    if patient_data['age'] < SettingManager.get("child_age_before", default='15', default_type='i'):
        patient_data['serial'] = patient_data['bc_serial']
        patient_data['num'] = patient_data['bc_num']
    else:
        patient_data['serial'] = patient_data['passport_serial']
        patient_data['num'] = patient_data['passport_num']

    card_num_obj = patient_data['card_num'].split(' ')
    p_card_num = card_num_obj[0]

    title_page = [
        Indenter(left=0 * mm),
        Spacer(1, 2 * mm),
        Paragraph('<font fontname="PTAstraSerifBold" size=13>Показатели жизненно важных функций</font><br/>', styleCenter),
        Paragraph('({} № {} {})'.format(patient_data['fio'], p_card_num, hosp_nums), styleCenter),
    ]
    objs.extend(title_page)
    objs.append(Spacer(1, 3 * mm))

    result = get_temperature_list(num_dir[0])
    titles = json.loads(request_data["titles"])
    count_in_graph = 26
    if 'Температура (°C)' in titles:
        result_data = result['Температура (°C)']
        min_max = result_data['min_max']
        count_param = count_len_param(result_data, count_in_graph)
        for i in range(count_param):
            elements = count_graph_el(count_in_graph, result_data)
            temp_obj = [
                Paragraph(' <u>Температура (°C)</u>', style),
                Spacer(1, 2 * mm),
                draw_temper_pulse({'data': elements[0], 'xtext': elements[1], 'min_max': min_max}, 1, 250 * mm, 27 * mm),
                Spacer(1, 10 * mm),
            ]
            objs.append(KeepTogether(temp_obj))

    if 'Пульс (уд/с)' in titles:
        result_data = result['Пульс (уд/с)']
        min_max = result_data['min_max']
        count_param = count_len_param(result_data, count_in_graph)
        for i in range(count_param):
            elements = count_graph_el(count_in_graph, result_data)
            temp_obj = [
                Paragraph(' <u>Пульс (уд/с)</u>', style),
                Spacer(1, 2 * mm),
                draw_temper_pulse({'data': elements[0], 'xtext': elements[1], 'min_max': min_max}, 10, 250 * mm, 27 * mm),
                Spacer(1, 10 * mm),
            ]
            objs.append(KeepTogether(temp_obj))

    if 'Давление' in titles:
        diastolic = 'Диастолическое давление (мм рт.с)'
        systolic = 'Систолическое давление (мм рт.с)'
        result_data = {diastolic: result[diastolic], systolic: result[systolic]}
        min_max_diastolic = result_data[diastolic]['min_max']
        min_max_systolic = result_data[systolic]['min_max']
        count_param = count_len_param(result_data[diastolic], count_in_graph)
        for i in range(count_param):
            elements = count_graph_el_pressure(count_in_graph, result_data, diastolic, systolic, min_max_diastolic, min_max_systolic)
            temp_obj = [
                Paragraph(
                    '<u>Давление:</u> (<img src="forms/img/squreline.png" width="20" height="10" />  систолическое, '
                    '<img src="forms/img/strokedot.png" width="20" height="10" />  диастолическое)',
                    style,
                ),
                Spacer(1, 2 * mm),
                draw_pressure(elements, 10, 250 * mm, 45 * mm),
                Spacer(1, 10 * mm),
            ]
            objs.append(KeepTogether(temp_obj))
    doc.build(objs)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def count_len_param(param_object, count_in_graph):
    len_param = len(param_object['data'])
    count_param = 0
    if len_param > count_in_graph:
        count_param = len_param // count_in_graph
    if len_param % count_in_graph > 0 or count_param == 0:
        count_param += 1
    return count_param


def count_graph_el(count_in_graph, param_object):
    data = param_object['data'][:count_in_graph]
    del param_object['data'][:count_in_graph]
    xtext = param_object['xtext'][:count_in_graph]
    del param_object['xtext'][:count_in_graph]

    return data, xtext


def count_graph_el_pressure(count_in_graph, param_object, diastolic, systolic, min_max_diastolic, min_max_systolic):
    data_diastolic = param_object[diastolic]['data'][:count_in_graph]
    del param_object[diastolic]['data'][:count_in_graph]

    data_systolic = param_object[systolic]['data'][:count_in_graph]
    del param_object[systolic]['data'][:count_in_graph]

    xtext_diastolic = param_object[diastolic]['xtext'][:count_in_graph]
    del param_object[diastolic]['xtext'][:count_in_graph]

    xtext_systolic = param_object[systolic]['xtext'][:count_in_graph]
    del param_object[systolic]['xtext'][:count_in_graph]

    return {
        diastolic: {'data': data_diastolic, 'xtext': xtext_diastolic, 'min_max': min_max_diastolic},
        systolic: {'data': data_systolic, 'xtext': xtext_systolic, 'min_max': min_max_systolic},
    }


def draw_temper_pulse(value, step, x_coord, y_coord):
    drawing = Drawing(x_coord, y_coord)
    data = []
    catNames = []
    min_value = 0
    max_value = 0
    for k, v in value.items():
        if k == 'data':
            data1 = tuple([i for i in v])
            data.append(data1)
        if k == 'xtext':
            catNames = [i.replace(' ', '\n') for i in v]
        if k == 'min_max':
            min_value = v[0] - step
            max_value = v[1] + step

    lc = HorizontalLineChart()
    lc.x = 15
    lc.y = 0
    lc.height = 28 * mm
    lc.width = 250 * mm
    lc.data = data
    lc.joinedLines = 1
    lc.strokeColor = colors.white
    lc.strokeColor = None
    # из markers
    lc.lines.symbol = makeMarker('FilledSquare')
    lc.lines.symbol.size = 4
    # lineLabels - свойства надбисей линии из textlabels class Label(Widget):
    lc.lineLabels.fontSize = 9
    lc.lineLabels.fontName = 'PTAstraSerifBold'
    lc.lineLabels.angle = 0
    lc.lineLabels.dx = 2
    lc.lineLabels.dy = 1
    lc.lines[0].strokeColor = colors.black
    lc.lineLabelFormat = '%3.1f'

    lc.categoryAxis.categoryNames = catNames
    lc.categoryAxis.labels.boxAnchor = 'n'
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.dy = -2
    lc.categoryAxis.labels.dx = 0
    lc.categoryAxis.labels.fontSize = 9
    lc.categoryAxis.labels.fontName = 'PTAstraSerifReg'
    lc.categoryAxis.labels.leading = 8

    lc.valueAxis.valueMin = min_value
    lc.valueAxis.valueMax = max_value
    lc.valueAxis.valueStep = step
    lc.valueAxis.labels.fontName = 'PTAstraSerifReg'
    lc.valueAxis.labels.fontSize = 9
    drawing.add(lc)

    return drawing


def draw_pressure(value, step, x_coord, y_coord):
    drawing = Drawing(x_coord, y_coord)
    data = []
    data_diastolic = value['Диастолическое давление (мм рт.с)']
    data1 = [i for i in data_diastolic['data']]
    data.append(tuple(data1))
    min_max = data_diastolic['min_max']
    data_systolic = value['Систолическое давление (мм рт.с)']
    data1 = [i for i in data_systolic['data']]
    data.append(tuple(data1))
    catNames = [i.replace(' ', '\n') for i in data_diastolic['xtext']]
    min_max.extend(data_systolic['min_max'])
    min_value = min(min_max) - step
    max_value = max(min_max) + step

    lc = HorizontalLineChart()
    lc.x = 15
    lc.y = 0
    lc.height = 45 * mm
    lc.width = 250 * mm
    lc.data = data
    lc.joinedLines = 1
    lc.strokeColor = colors.white
    # из markers
    lc.lines[0].symbol = makeMarker('FilledCircle')
    lc.lines.symbol = makeMarker('FilledSquare')
    lc.lines.symbol.size = 4
    # lineLabels - свойства надбисей линии из textlabels class Label(Widget):
    lc.lineLabels.fontSize = 9
    lc.lineLabels.fontName = 'PTAstraSerifBold'
    lc.lineLabels.angle = 0
    lc.lineLabels.dx = 2
    lc.lineLabels.dy = -1
    lc.lines[0].strokeColor = colors.black
    lc.lines[1].strokeColor = colors.black
    lc.lines[0].strokeDashArray = [3, 3]
    lc.lineLabelFormat = '%3.1f'

    lc.categoryAxis.categoryNames = catNames
    lc.categoryAxis.labels.boxAnchor = 'n'
    lc.categoryAxis.labels.angle = 0
    lc.categoryAxis.labels.dy = -2
    lc.categoryAxis.labels.dx = 0
    lc.categoryAxis.labels.fontSize = 9
    lc.categoryAxis.labels.fontName = 'PTAstraSerifReg'
    lc.categoryAxis.labels.leading = 8
    lc.valueAxis.valueMin = min_value
    lc.valueAxis.valueMax = max_value
    lc.valueAxis.valueStep = step
    lc.valueAxis.labels.fontName = 'PTAstraSerifReg'
    lc.valueAxis.labels.fontSize = 9
    drawing.add(lc)
    return drawing
