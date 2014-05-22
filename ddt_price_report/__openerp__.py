# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2011 ISA S.R.L.
#    (<http://www.isa.it>). 
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'DDT report with product price',
    'version': '0.1',
    'category': 'Localisation/Italy',
    'description': """DDT report with product price """,
    'author': 'ISA S.R.L.',
    'website': 'www.isa.it',
    'license': 'AGPL-3',
    "depends" : ['l10n_it_sale'],
    "init_xml" : [
        ],
    "update_xml" : [
              'reports.xml',
        ],
    "demo_xml" : [],
    "active": False,
    "installable": True
}
