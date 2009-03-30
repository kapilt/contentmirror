# many thanks to mike bayer, for helping me track down this bug fix
# http://www.sqlalchemy.org/trac/ticket/1357

import sqlalchemy
from sqlalchemy.sql import expression

def compare(self, other):
    """Compare this ``_BindParamClause`` to the given clause.
    
    Since ``compare()`` is meant to compare statement syntax, this
    method returns True if the two ``_BindParamClauses`` have just
    the same type.
    """
    return isinstance(other, expression._BindParamClause) and other.type.__class__ == self.type.__class__ \
           and self.value == other.value

if sqlalchemy.__version__ < '0.5.4':
    expression._BindParamClause.compare = compare

