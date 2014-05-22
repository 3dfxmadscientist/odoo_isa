# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
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

from osv import fields,osv
import time
from tools.translate import _

class wizard_select_template_isa(osv.osv_memory):

    _inherit = "wizard.select.invoice.template"
    

    def load_template(self, cr, uid, ids, context=None):
        template_obj = self.pool.get('account.invoice.template')
        template_line_obj = self.pool.get('account.invoice.template.line')
        account_period_obj = self.pool.get('account.period')
        account_invoice_obj = self.pool.get('account.invoice')
        account_invoice_line_obj = self.pool.get('account.invoice.line')
        mod_obj = self.pool.get('ir.model.data')
        entry = {}

        wizard =  self.browse(cr, uid, ids, context=context)[0]
        if not template_obj.check_zero_lines(cr, uid, wizard):
            raise osv.except_osv(_('Error !'), _('At least one amount has to be non-zero!'))
        input_lines = {}
        for template_line in wizard.line_ids:
            input_lines[template_line.sequence] = template_line.amount

        computed_lines = template_obj.compute_lines(cr, uid, wizard.template_id.id, input_lines)

        inv_values = account_invoice_obj.onchange_partner_id(
            cr, uid, ids, wizard.template_id.type, wizard.template_id.partner_id.id)['value']
        inv_values['partner_id'] = wizard.template_id.partner_id.id
        inv_values['account_id'] = wizard.template_id.account_id.id
        inv_values['journal_id'] = wizard.template_id.journal_id.id
        inv_values['type'] = wizard.template_id.type

        analytic_account_id_seq={}
        for wz_line in wizard.line_ids:
            if wz_line.analytic_account_id:
               analytic_account_id_seq[wz_line.sequence]=wz_line.analytic_account_id.id

        inv_id = account_invoice_obj.create(cr, uid, inv_values)
        for line in wizard.template_id.template_line_ids:
            
            analytic_account_id = False
            if analytic_account_id_seq.has_key(line.sequence):
                analytic_account_id=analytic_account_id_seq[line.sequence]
            else:
                if line.analytic_account_id:
                    analytic_account_id = line.analytic_account_id.id

            invoice_line_tax_id = []
            if line.invoice_line_tax_id:
                tax_ids=[]
                for tax in line.invoice_line_tax_id:
                    tax_ids.append(tax.id)
                invoice_line_tax_id.append((6,0, tax_ids))
            val = {
                'name': line.name,
                'invoice_id': inv_id,
                'account_analytic_id': analytic_account_id,
                'account_id': line.account_id.id,
                'invoice_line_tax_id': invoice_line_tax_id,
                'price_unit': computed_lines[line.sequence],
                'product_id': line.product_id.id,
        }
            id_line = account_invoice_line_obj.create(cr, uid, val)
        journal_type='sale'
        if inv_values['type'] in ('out_invoice', 'out_refund'):
            xml_id = 'invoice_form'
        else:
            xml_id = 'invoice_supplier_form'
            journal_type='purchase'
        resource_id = mod_obj.get_object_reference(cr, uid, 'account', xml_id)[1]

        return {
            'domain': "[('id','in', ["+str(inv_id)+"])]",
            'context':{'type':inv_values['type'], 'journal_type': journal_type},
            'name': 'Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': inv_id or False,
        }

wizard_select_template_isa()

class wizard_select_template_line_isa(osv.osv_memory):
    
    _inherit = "wizard.select.invoice.template.line"
    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account'),
        'type_of_amount':fields.char('Type of row', size=10),
    }

wizard_select_template_line_isa()