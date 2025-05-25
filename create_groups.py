from django.contrib.auth.models import Group

# Créer les groupes s'ils n'existent pas
groups = ['Passagers', 'Conducteurs', 'Administrateurs']
for group_name in groups:
    Group.objects.get_or_create(name=group_name)
    print(f"Groupe '{group_name}' créé avec succès.") 