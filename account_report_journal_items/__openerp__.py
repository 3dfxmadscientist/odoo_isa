# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 ISA s.r.l. (<http://www.isa.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Analytic Journal Items Report',
    'version': '0.1',
    'category': '',
    'description': """
            Print report of analytic journal items.
            Stampa report bilancino per centro di costo.

            ATTENZIONE:
                Questo modulo necessita dell'installazione del template personalizzato del cliente.
                Il template si trova nel modulo che personalizza openerp per un dato cliente (es.: modulo 'ISAFlati').
                In mancanza del template, evitare di installare il presente modulo.
       """,
    'author': 'ISA srl',
    'depends': ["report_aeroo_ooo",'account'],
    'update_xml': ["wizard/analytic_journal_report.xml"],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
