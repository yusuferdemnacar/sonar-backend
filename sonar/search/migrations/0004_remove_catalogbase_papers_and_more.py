# Generated by Django 4.1.3 on 2022-12-04 22:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0003_articleidentifier_catalogbase_catalogextension_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='catalogbase',
            name='papers',
        ),
        migrations.RemoveField(
            model_name='catalogextension',
            name='papers',
        ),
        migrations.RemoveField(
            model_name='s2agarticleidentifier',
            name='articleidentifier_ptr',
        ),
        migrations.AddField(
            model_name='catalogbase',
            name='s2ag_papers',
            field=models.ManyToManyField(related_name='s2ag_papers_%(class)s', to='search.s2agarticleidentifier'),
        ),
        migrations.AddField(
            model_name='catalogextension',
            name='s2ag_papers',
            field=models.ManyToManyField(related_name='s2ag_papers_%(class)s', to='search.s2agarticleidentifier'),
        ),
        migrations.AlterField(
            model_name='s2agarticleidentifier',
            name='s2ag_paperID',
            field=models.CharField(max_length=255, primary_key=True, serialize=False),
        ),
        migrations.DeleteModel(
            name='ArticleIdentifier',
        ),
    ]