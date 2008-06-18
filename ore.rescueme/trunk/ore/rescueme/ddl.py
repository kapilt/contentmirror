####################################################################
# Copyright (c) Kapil Thangavelu. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
####################################################################
"""
Create the database structure for a content mirror and output to standard out.
"""

from StringIO import StringIO
from ore.rescueme import schema
import sqlalchemy as rdb
import sys

HELP = "zopectl|instance run ddl.py database_type" 

def main( ):
    if not len( sys.argv ) == 2:
        print HELP
        sys.exit(1)

    db_type = sys.argv[1].strip()
    buf = StringIO()    

    def write_statement( statement, parameters=''):
        ddl = statement + parameters
        buf.write( ddl.strip() + ';\n\n' )
        
    db = rdb.create_engine('%s://'%(db_type),
                           strategy='mock',
                           executor=write_statement )

    schema.metadata.drop_all(db)
    schema.metadata.create_all(db)
    print buf.getvalue()
    
if __name__ == '__main__':
    main()