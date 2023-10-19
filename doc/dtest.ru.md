# dtest. Тестирование качества данных в БД

Утилита `dtest` выполняет запросы к БД, указанные в спецификациях конфиг-файла, и формирует отчет о результатах тестирования качества данных в файле формата html.

Когда мне нужно убедиться, что в БД нет данных, нарушающих некоторое правило, я пишу запрос, выбирающий данные, нарушающие это правило. Например,

```
-- убедиться, что точка с запятой отсутствует в названиях

select * 
from items 
where name like '%;%'
;
no rows

-- убедиться, что счетчик позиций в заголовке совпадает с числом позиций

select *
from header h
where pos_count != (
    select count(*) from positions p where p.header_id = h.header_id
    )
;
no rows
```

Если запрос не возвращает ничего, это хорошой результат.

Если запрос возвращает одну или больше строк данных, значит, правило нарушено и данные требуется скорректировать.

Пример спецификаций для `dtest` с рассмотренными запросами (слегка модифицированными):

```
import os
import sys

from sources import sources


# MANDATORY constants used by dtest.py
OUT_DIR = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out')

# Optional constants used in specs below
# ...

specs = {
    "Названия без точки с запятой": {
        "source": "prod",
        "query": """"
            select item_id, name
            from items 
            where name like '%;%'
            """"
    },
    "Счетчик позиций в заголовке": {
        "source": "prod",
        "query": """"
            with q as (
                select header_id, count(*) cnt
                from positions p
                group by header_id
            )
            select h.header_id, h.pos_count, q.cnt
            from header h 
                left join q on q.header_id = h.header_id
            where h.pos_count != coalesce(q.cnt, -1)
            """"
    }
}
```

Глобальная переменная `OUT_DIR` задает директорию, в которой формируется отчет о качестве данных.

В тестовом конфиг-файле `dtest-test.py` вы найдете комментарии к каждому из параметров спецификации. Познакомьтесь с ними, чтобы составить исчерпывающее представление обо всех параметрах и их назначении.
