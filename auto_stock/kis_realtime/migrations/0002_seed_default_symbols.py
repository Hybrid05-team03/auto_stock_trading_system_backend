from django.db import migrations


DEFAULT_SYMBOLS = [
    ("exchangeRate", "261240", "달러 환율(ETF 추정)"),
    ("kospi", "069500", "코스피(ETF 추정)"),
    ("kosdaq", "229200", "코스닥(ETF 추정)"),
    ("nasdaq", "133690", "나스닥(ETF 추정)"),
]


def seed_symbols(apps, schema_editor):
    RealtimeSymbol = apps.get_model("kis_realtime", "RealtimeSymbol")
    for identifier, code, name in DEFAULT_SYMBOLS:
        RealtimeSymbol.objects.update_or_create(
            identifier=identifier,
            defaults={"code": code, "name": name},
        )


def unseed_symbols(apps, schema_editor):
    RealtimeSymbol = apps.get_model("kis_realtime", "RealtimeSymbol")
    identifiers = [identifier for identifier, _, _ in DEFAULT_SYMBOLS]
    RealtimeSymbol.objects.filter(identifier__in=identifiers).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("kis_realtime", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_symbols, reverse_code=unseed_symbols),
    ]
