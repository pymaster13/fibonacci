from .tasks import scan_admin_wallets, retreive_coins_cost


def periodically_run_job():
    print('Scan admin wallets')
    scan_admin_wallets.send()


def periodically_run_job_2():
    print('Scan coins cost')
    retreive_coins_cost.send()
