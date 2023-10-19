# hedwig. Отправка файлов (и не только) по почте

Утилита `hedwig` умеет формировать элекронные письма и отправлять их адресатам, согласно спецификации в конфиг-файле. Письма могут быть как текстовые (`text/plain`), так и в формате html (`text/html`), и могут содержать прикрепленные файлы.

Ниже пример минималистичных спецификаций для отправки сообщений `Hello world!` в текстовом и html форматах. Формат явно задается с помощью расширения имени спецификации:

```
specs = {
    ...
    "helloworld.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} hello world",
            "body": "Hello world!",
            "always": True
        }
    },
    "helloworld.html": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} hello world",
            "body": "&lt;html>&lt;body&gt;&lt;p&gt;Hello world!&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;",
            "always": True
        }
    },
    ...
}
```

Если добавить эти спецификации в тестовый конфиг-файл `hedwig-test.py` и выполнить их, то получим письма следующего содержания:

```
Hello!

Hello world!

Have a good day!
dbang Utilities
```

Приветствие и подпись были добавлены автоматически. Они задаются в конфиг-файле глобальными переменными `TEXT_GREEETING` и `TEXT_SIGNATURE` – для текстовых писем – и `HTML_GREEETING` и `HTML_SIGNATURE` – для писем в формате html.

Приветствие и подпись в письме можно переопределить непосредственно в спецификации. А также добавить пару слов перед подписью с помощью параметра `"finally"`:

```
specs = {
    ...
    "helloworld.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} hello world",
            "greeting": "Салют!\n\n",
            "body": "Hello world!",
            "finally": "\nЖду ответа как соловей лета.\n",
            "signature": "\n\nПока :)\n",
            "always": True
        }
    },
    ...
}
```

В результате получим:

```
Салют!

Hello world!

Жду ответа как соловей лета.

Пока :)
```

А параметр `"always": True` в спецификации нужен для безусловной отправки письма.

Дело в том, что основное назначение и занятие `hedwig` состоит в отправке по почте файлов, созданных утилитами `ddiff`, `dtest`, `dput`. (Само собой, можно отправлять и файлы, созданные другими средствами.) Если файл уже был отправлен, то повторное выполнение спецификации не приводит к его повторной отправке – `hedwig` запоминает время модификации отправленного файла и отправит его снова только после его обновления.

Так, если утилита `dtest` формирует файл с отчетом один раз в сутки, а `hedwig` запускается ежечасно и выполняет все спецификации конфиг-файла, то письмо с отчетом от `dtest` будет отправлено только один раз в течение суток – когда файл с отчетом обновится.

Чтобы отправить письмо безусловно и нужен параметр `"always": True`. При этом не имеет значения, формируется ли письмо на основе файла или содержит просто текст, заданный параметром `"body"`.

Пример спецификаций для формирования тела письма из текстового файла и файла html:

```
import os
import sys

...

specs = {
    ...
    "file.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} file.txt",
            "body": {
                "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'test.txt')
            }
        }
    },
    "file.html": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} file.html",
            "body": {
                "file": os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'test.html')
            }
        }
    },
    ...
}
```

Это спецификации из тестового конфиг-файла `hedwig-test.py`. Выполните их и проверьте результат в вашем почтовом ящике.

Параметр `"body"` спецификации позволяет задать тело письма

* как текст – значением типа `str`, см. пример письма `Hello world!`,
* как файл – словарем (dict) с ключом `"file"`, см. пример выше,
* как комбинацию текстов и файлов – списком (list) строк и словарей.

Пример спецификации письма, где тело письма составляется из текста и содержимого файла:

```
TEST_TEXT_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'out', 'test.txt')
TEXT_GUADEAMUS = """Gaudeamus igitur,
iuvenes dum sumus,
gaudeamus igitur,
iuvenes dum sumus.
Post iucundam iuventutem
post molestam senectutem,
nos habebit humus,
nos habebit humus.
"""

...

specs = {
    ...
    "text and file.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} text and file.txt",
            "body": [
                TEXT_GUADEAMUS,
                {"file": TEST_TEXT_FILE}
             ]
        }
    },
    ...
}
```

Обратите внимание, что письмо по этой спецификации будет отправлено только один раз. Повторные выполнения спецификации не приведут к повторной отправке письма, пока файл `TEST_TEXT_FILE` не будет обновлен. Если же вы захотите отправить письмо безусловно, используйте параметр `"always": True`.

Описание файла, содержимое которого вставляется в тело письма, в общем случае содержит три параметра:

* `"file"` задает путь к файлу,
* `"encoding"` опционально задает кодировку файла, отличную от заданной глобальной переменной `ENCODING`,
* `"substitutions"` опционально задает список пар (паттерн, замена) для выполнения замен в содержимом файла.

Наконец, указать файл, или файлы, которые необходимо прикрепить к письму, чтобы отправить как вложения, можно с помощью параметра `"attachments"` спецификации. Этот параметр задает список прикрепляемых файлов.

Вот пример спецификации письма с прикрепленными файлами:

```
TEST_CSV_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in', 'test.csv')
TEST_XLSX_FILE = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'in', 'test.xlsx')

...

specs = {
    ...
    "with attachments.txt": {
        "mail": {
            "to": "me@my.self",
            "subject": "{dbang} with attachments.txt",
            "body": "See attached files.",
            "finally": '\nSee also MIME types also https://www.google.com/search?q=mime+types\n',
            "attachments": [
                {
                    "file": TEST_CSV_FILE,
                    "MIME": "text/csv",
                    "filename": "countries.csv"
                },
                {
                    "file": TEST_XLSX_FILE,
                    "MIME": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "filename": "countries.xlsx"
                },
            ]
        }
    },
    ...
}
```

В словаре (dict), описывающем прикрепляемый файл,

* `"file"` задает путь к файлу,
* `"MIME"` опционально описывает формат файла,
* `"filename"` опционально задает имя, под которым файл будет прикреплен к письму.

Имеет смысл указывать `"filename"`, если это имя отличается от имени прикрепляемого файла, как в приведенном примере.

В тестовом конфиг-файле `hedwig-test.py` вы найдете комментарии к каждому из параметров спецификации. Познакомьтесь с ними, чтобы составить исчерпывающее представление обо всех параметрах и их назначении.
