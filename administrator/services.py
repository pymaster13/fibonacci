from django.contrib.auth.models import Permission

from .exceptions import GrantPermissionsError


def grant_permissions(user, perms):
    """Help function to grant permissions to user"""
    try:
        actions = ('add', 'change', 'delete')
        permissions_db = ("ido", "transaction", "user", "news")
        result_perms = []

        for perm in perms:
            if perm in permissions_db:
                for action in actions:
                    codename = f'{action}_{perm}'
                    perm_obj = Permission.objects.get(codename=codename)
                    result_perms.append(perm_obj)

        if 'admin' in perms:
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False

        if result_perms:
            user.user_permissions.set(result_perms)
        else:
            user.user_permissions.clear()

        user.save()

        return True

    except Exception as e:
        print(e)
        raise GrantPermissionsError("Ошибка предоставления прав пользователю.")
