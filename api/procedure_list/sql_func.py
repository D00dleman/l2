from django.db import connection
from laboratory.settings import TIME_ZONE


def get_procedure_by_params(d_s, d_e, researches_pk):
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT 
            pl.id,
            pharmacotherapy_drugs.mnn,
            to_char(pharmacotherapy_procedurelist.time_create AT TIME ZONE %(tz)s, 'DD.MM.YYYY-HH24:MI:SS') AS create_procedure,
            pharmacotherapy_formrelease.title,
            pharmacotherapy_methodsreception.title,
            pharmacotherapy_procedurelist.dosage,
            pharmacotherapy_procedurelist.units,
            clients_individual.id,
            concat_ws(' ', clients_individual.family, clients_individual.name, clients_individual.patronymic),
            pharmacotherapy_procedurelist.history_id,
            pharmacotherapy_procedurelist.card_id,
            to_char(pl.times_medication AT TIME ZONE %(tz)s, 'DD.MM.YYYY') AS date_execute,
            to_char(pl.times_medication AT TIME ZONE %(tz)s, 'HH24:MI') AS time_execute,
            pl.cancel,
            pl.executor_id,
            pl.prescription_id,
            pl.exec_fio,
            pharmacotherapy_procedurelist.history_id,
            pharmacotherapy_procedurelist.comment,
            pl.who_cancel_id,
            pl.cancel_fio,
            pharmacotherapy_procedurelist.step,
            pharmacotherapy_procedurelist.id,
            pharmacotherapy_procedurelist.cancel
            FROM pharmacotherapy_procedurelist
                LEFT JOIN pharmacotherapy_drugs ON (pharmacotherapy_procedurelist.drug_id=pharmacotherapy_drugs.id)
                LEFT JOIN pharmacotherapy_formrelease ON (pharmacotherapy_procedurelist.form_release_id=pharmacotherapy_formrelease.id)
                LEFT JOIN pharmacotherapy_methodsreception ON (pharmacotherapy_procedurelist.method_id=pharmacotherapy_methodsreception.id)
                LEFT JOIN clients_card ON (pharmacotherapy_procedurelist.card_id=clients_card.id)
                LEFT JOIN clients_individual ON (clients_card.individual_id=clients_individual.id)
                RIGHT JOIN  
                    (SELECT 
                        pharmacotherapy_procedurelisttimes.id, 
                        pharmacotherapy_procedurelisttimes.times_medication, 
                        pharmacotherapy_procedurelisttimes.cancel, 
                        pharmacotherapy_procedurelisttimes.executor_id,
                        pharmacotherapy_procedurelisttimes.prescription_id,
                        doc_exec.fio as exec_fio,
                        pharmacotherapy_procedurelisttimes.who_cancel_id,
                        doc_cancel.fio as cancel_fio
                    FROM pharmacotherapy_procedurelisttimes
                    LEFT JOIN users_doctorprofile as doc_exec ON (pharmacotherapy_procedurelisttimes.executor_id=doc_exec.id)
                    LEFT JOIN users_doctorprofile as doc_cancel ON (pharmacotherapy_procedurelisttimes.who_cancel_id=doc_cancel.id)
                        ) as pl ON pl.prescription_id=pharmacotherapy_procedurelist.id
                    WHERE 
                        pl.times_medication AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
                        AND research_id = ANY(%(id_researches)s)
            ORDER BY clients_individual.family, clients_individual.id, pharmacotherapy_drugs.mnn, pl.times_medication
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE, 'id_researches': researches_pk},
        )
        rows = cursor.fetchall()
    return rows


def get_procedure_all_times(d_s, d_e):
    with connection.cursor() as cursor:
        cursor.execute(
            """ SELECT 
            DISTINCT ON (times_medication) to_char(pharmacotherapy_procedurelisttimes.times_medication AT TIME ZONE %(tz)s, 'HH24:MI') as times_medication
            FROM pharmacotherapy_procedurelisttimes
            WHERE pharmacotherapy_procedurelisttimes.times_medication AT TIME ZONE %(tz)s BETWEEN %(d_start)s AND %(d_end)s
            ORDER BY times_medication
        """,
            params={'d_start': d_s, 'd_end': d_e, 'tz': TIME_ZONE},
        )
        row = cursor.fetchall()
    return row
