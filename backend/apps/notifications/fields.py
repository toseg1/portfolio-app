"""CITEXT column type (04.8 specifies it explicitly for recipient_email / email).

Django's own `django.contrib.postgres.fields.CITextField` was removed in
5.0 in favour of non-deterministic collations, but 04.8 names the
Postgres `citext` type specifically — this is the small, direct
replacement rather than switching mechanisms.
"""

from django.db import models


class CITextField(models.TextField):
    def db_type(self, connection):
        return "citext"
