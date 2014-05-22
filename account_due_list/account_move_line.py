# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
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

from osv import fields, osv

class account_move_line(osv.osv):
        
    def _get_invoice(self, cr, uid, ids, field_name, arg, context=None):
        invoice_pool = self.pool.get('account.invoice')
        res = {}
        for line in self.browse(cr, uid, ids):
            inv_ids = invoice_pool.search(cr, uid, [('move_id', '=', line.move_id.id)])
            if len(inv_ids)>1:
                raise osv.except_osv(_('Error'), _('Incongruent data: move %s has more than one invoice') % line.move_id.name)
            if inv_ids:
                res[line.id] = inv_ids[0]
	    else:
		res[line.id] = False
        return res
        
    def _get_day(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids):
            if line.date_maturity:
                res[line.id] = line.date_maturity
	    else: res[line.id] = False
        return res
        
    def _get_move_lines(self, cr, uid, ids, context=None):
        invoice_pool = self.pool.get('account.invoice')
        res = []
        for invoice in invoice_pool.browse(cr, uid, ids):
            if invoice.move_id:
                for line in invoice.move_id.line_id:
                    if line.id not in res:
                        res.append(line.id)
        return res

    _inherit = 'account.move.line'

    _columns = {
        'invoice_origin': fields.related('invoice', 'origin', type='char', string='Source Doc', store=False),
        'invoice_date': fields.related('invoice', 'date_invoice', type='date', string='Invoice Date', store=False),
        'partner_ref': fields.related('partner_id', 'ref', type='char', string='Partner Ref', store=False),
        'payment_term_id': fields.related('invoice', 'payment_term', type='many2one', string='Payment Term', store=False, relation="account.payment.term"),
        'stored_invoice_id': fields.function(_get_invoice, method=True, string="Invoice", type="many2one", relation="account.invoice",
            store={
                'account.move.line': (lambda self, cr, uid, ids, c={}: ids, ['move_id'], 10),
                'account.invoice': (_get_move_lines, ['move_id'], 10),
                }),
        'day': fields.function(_get_day, method=True, string="Day", type="char", size=16,
                store={
                'account.move.line': (lambda self, cr, uid, ids, c={}: ids, ['date_maturity'], 10),
                }),
        }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False, submenu=False):
        view_payments_tree_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid, 'account_due_list', 'view_payments_tree')
        if view_id == view_payments_tree_id[1]:
            # Use due list
            result = super(osv.osv, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        else:
            # Use special views for account.move.line object (for ex. tree view contains user defined fields)
            result = super(account_move_line, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar=toolbar, submenu=submenu)
        return result

account_move_line()
