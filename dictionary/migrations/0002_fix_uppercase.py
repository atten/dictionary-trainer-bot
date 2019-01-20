from django.db import migrations

from bot.utils import fix_input_uppercase


def fix_uppercase_phrases(apps, schema_editor):
    from dictionary.models import Phrase, Language
    lang_en = Language.objects.get(code='en')
    lang_ru = Language.objects.get(code='ru')

    phrases = Phrase.objects.filter(text__regex='[A-ZА-Я]')
    phrases_saved = 0
    phrases_deleted = 0

    for phrase in phrases:
        opposite_lang = lang_en if phrase.lang == lang_ru else lang_ru
        line = phrase.verbose_translations(opposite_lang)
        if line != fix_input_uppercase(line):
            phrase.text = phrase.text[0].lower() + phrase.text[1:]

            phrase_lowercase = Phrase.objects.filter(text=phrase.text, lang=phrase.lang, user=phrase.user).first()

            if phrase_lowercase is None:
                phrase.save()
                phrases_saved += 1
            else:
                # если такая же фраза в нижнем регистре существует, перемещаем все текущие переводы в её группу,
                # а текущую фразу удаляем
                for group in phrase_lowercase.phrase_groups.all():
                    group.phrases.add(*list(phrase.translations(opposite_lang)))

                phrase.phrase_groups.all().delete()
                phrase.delete()
                phrases_deleted += 1

    print('Fixed uppercase of %d phrases, removed %d duplicates' % (phrases_saved, phrases_deleted))


class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(fix_uppercase_phrases),
    ]
    dependencies = [
        ('dictionary', '0001_initial'),
    ]
