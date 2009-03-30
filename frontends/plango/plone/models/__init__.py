from django.conf import settings
if settings.DATABASE_ENGINE not in ("postgresql_psycopg2", "postgresql"):
    raise ValueError, "You must have a Postgres database to use Plango since it makes a " \
        "special Postgres full text index for the search, you " \
        "could probably remove the search and it would all work ok."

import base
import search