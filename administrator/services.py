from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.db.models import Max

from .exceptions import GrantPermissionsError
from ido.models import QueueUser, IDOParticipant


User = get_user_model()


def grant_permissions(user, perms):
    """Help function to grant permissions to user"""
    try:
        actions = ('add', 'change', 'delete')
        permissions_db = ("ido", "transaction", "user", "news", "statistics")
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


def refresh_queue_places(user):
    """Help function to refresh all queues places
       during set him place by admin"""
    queues = QueueUser.objects.filter(user=user)
    if queues:
        for queue in queues:
            if not user.permanent_place:
                if queue.permanent and queue.is_active:
                    queue.permanent = False
                    ido = queue.ido

                    # Up all lower users with early date and permanent
                    low_queues = QueueUser.objects.filter(
                                    ido=ido,
                                    number__gt=queue.number)
                    for q in low_queues:
                        if q.permanent or q.date < queue.date:
                            q.number -= 1
                            q.save()

                    # Calculating new number
                    low_queues_ = QueueUser.objects.filter(
                                    ido=ido,
                                    permanent=False,
                                    date__gte=queue.date).order_by('number')
                    if low_queues_:
                        new_number = low_queues_[0].number - 1
                        queue.number = new_number
                    else:
                        all_queues = QueueUser.objects.filter(ido=ido)
                        if len(all_queues) > 1:
                            new_number = all_queues.aggregate(Max('number'))
                            queue.number = new_number['number__max'] + 1

                    queue.save()
            else:
                if not queue.permanent and queue.is_active:
                    queue.permanent = True
                    queue.number = user.permanent_place
                    ido = queue.ido

                    # Down all lower users
                    low_queues = QueueUser.objects.filter(
                                    ido=ido,
                                    number__gte=user.permanent_place)

                    for q in low_queues:
                        if q == user:
                            break
                        q.number += 1
                        q.save()

                    queue.save()


def retrieve_users_info(users: list, data: dict = {}):
    for user in users:
        user_data = {}
        user_data['line'] = user.line
        user_data['fio'] = user.fio
        user_data['status'] = user.full_status
        user_data['referal'] = user.partners

        idos = IDOParticipant.objects.filter(user=user)
        summ = sum([ido.allocation for ido in idos if ido.allocation])

        user_data['ido'] = summ if summ else 0

        data[user.email] = user_data
    return data
