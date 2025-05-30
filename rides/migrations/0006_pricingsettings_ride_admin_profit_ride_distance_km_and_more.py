# Generated by Django 5.0.1 on 2025-05-23 17:33

import django.core.validators
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0005_alter_profile_options_profile_created_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PricingSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_price_per_km', models.DecimalField(decimal_places=2, default=0.5, help_text='Prix de base par kilomètre', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('driver_profit_percentage', models.DecimalField(decimal_places=2, default=80.0, help_text='Pourcentage du prix total qui revient au conducteur', max_digits=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('admin_profit_percentage', models.DecimalField(decimal_places=2, default=20.0, help_text="Pourcentage du prix total qui revient à l'administrateur", max_digits=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('min_price', models.DecimalField(decimal_places=2, default=5.0, help_text='Prix minimum pour un trajet', max_digits=6, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Paramètre de tarification',
                'verbose_name_plural': 'Paramètres de tarification',
            },
        ),
        migrations.AddField(
            model_name='ride',
            name='admin_profit',
            field=models.DecimalField(decimal_places=2, help_text="Part de l'administrateur", max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='ride',
            name='distance_km',
            field=models.DecimalField(decimal_places=2, help_text='Distance en kilomètres', max_digits=8, null=True),
        ),
        migrations.AddField(
            model_name='ride',
            name='driver_profit',
            field=models.DecimalField(decimal_places=2, help_text='Part du conducteur', max_digits=8, null=True),
        ),
        migrations.AlterField(
            model_name='ride',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=8),
        ),
    ]
