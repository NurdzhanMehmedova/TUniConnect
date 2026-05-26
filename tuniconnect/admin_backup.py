import os
import subprocess

from datetime import datetime

from audit.models import AdminAudit

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from django.db import connection


@staff_member_required
def admin_backup_now(request):

    backup_dir = os.path.join(
        settings.BASE_DIR,
        "backups"
    )

    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    db_settings = settings.DATABASES["default"]

    db_name = db_settings["NAME"]
    db_user = db_settings["USER"]
    db_password = db_settings["PASSWORD"]
    db_host = db_settings["HOST"]
    db_port = db_settings["PORT"]

    backup_file = os.path.join(
        backup_dir,
        f"backup_{timestamp}.sql"
    )

    command = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
        f"--user={db_user}",
        f"--password={db_password}",
        f"--host={db_host}",
        f"--port={db_port}",
        db_name,
        "--result-file",
        backup_file,
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )

        # Размер
        backup_size = round(
            os.path.getsize(backup_file) / (1024 * 1024),
            2
        )

        # Таблици
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]

        AdminAudit.objects.create(
            admin=request.user,
            action="BACKUP",
            target_type="Database",
            description="Created database backup"
        )

        return render(request,
            "admin/backup_success.html",
            {
                "backup_name": os.path.basename(backup_file),
                "backup_path": backup_file,
                "backup_size": backup_size,
                "created_at": timestamp,
                "tables": tables,
                "output": result.stdout or "Backup completed successfully."
            }
        )

    except Exception as e:

        return render(request,
            "admin/backup_success.html",
            {
                "backup_name": "FAILED",
                "backup_path": "-",
                "backup_size": 0,
                "created_at": timestamp,
                "tables": [],
                "output": str(e)
            }
        )