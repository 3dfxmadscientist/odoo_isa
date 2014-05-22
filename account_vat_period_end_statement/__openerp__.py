# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Domsense s.r.l. (<http://www.domsense.com>).
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
    "name": "Period End VAT Statement",
    "version": "0.3",
    'category': 'Generic Modules/Accounting',
    "depends": ["account_voucher", "report_webkit"],
    "author": "Agile Business Group & Domsense",
    "description": """
    
This module helps to register the VAT statement of period end.
    
In order to load the correct amount from tax code, the tax code has to be associated to the account involved in the statement, through the tax code form.

The 'VAT statement' object allows to specify every amount and relative account used by the statement.
By default, the amounts of debit and credit taxes are automatically loaded from the tax codes of the selected period.
Previous debit or credit is loaded from previous VAT statement, according to its payments status.
Confirming the statement, the 'account.move' is created. If you select a payment term, the due date(s) will be set.

The 'tax authority' tab contains information about the payment(s). You can see the statement's result ('authority VAT amount') and the residual amount to pay ('Balance').
The statement can be paid like every other debit: by voucher or 'move.line' reconciliation.

It is advisable the use of account_due_list module.

Specification: http://wiki.openerp-italia.org/doku.php/moduli/vat_period_end_statement

""",
    'website': 'http://www.agilebg.com',
    'init_xml': [],
    'update_xml': [
        'account_view.xml',
        'statement_workflow.xml',
        'security/ir.model.access.csv',
        'reports.xml',
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
