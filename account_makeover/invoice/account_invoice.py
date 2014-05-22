# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2013 ISA srl (<http://www.isa.it>)
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

import copy
import time
import openerp.addons.decimal_precision as dp
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp import netsvc
from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp import tools
from openerp.osv.orm import browse_record


class account_invoice_makeover(orm.Model):
    _inherit = "account.invoice"

    def _get_withholding_payment_term(self, cr, uid):
        p_term_obj = self.pool.get('account.payment.term')
        p_term_search = p_term_obj.search(cr, uid,
                                          [('name', '=',
                                            '16th Next Month')],
                                          limit=1)
        if not p_term_search:
            raise orm.except_orm(_('Error!'),
                (_('Payment term "16th Next Month" missing!')))

        p_term_res = p_term_obj.browse(cr, uid, p_term_search,
                                           context=False)
        p_term_id = p_term_res and p_term_res[0].id
        p_term_name = p_term_res and p_term_res[0].name
        return p_term_id, p_term_name

    def _get_min_payment_term(self, move_lines):
        date_maturity_list = []
        for t_line in move_lines:
            t_date_maturity = t_line[2]['date_maturity']
            if t_date_maturity:
                date_maturity_list.append(t_date_maturity)
        
        t_min_payment_term = min(string for string in date_maturity_list)
        
        return t_min_payment_term

    def _new_wht_payment_term(self, cr, uid, move_lines, date_due,
                              withholding_amount):
        p_term_id, p_term_name = self._get_withholding_payment_term(cr, uid)
        t_min_payment_term = self._get_min_payment_term(move_lines)
        if not t_min_payment_term:
            t_min_payment_term = date_due
        payment_term_obj = self.pool.get('account.payment.term')
        new_payment_term = payment_term_obj.compute(cr,
            uid, p_term_id, withholding_amount,
            date_ref=t_min_payment_term or False)
        
        if len(new_payment_term) > 1:
            raise orm.except_orm(_('Error'),
                _('The payment term %s has too many due dates')
                % p_term_name)
            
        if len(new_payment_term) == 0:
            raise orm.except_orm(_('Error'),
                _('The payment term %s does not have due dates')
                % p_term_name)
            
        return new_payment_term

    def _recreate_move_lines(self, invoice_browse, m_lines, old_pt,
                             new_pt, add_pt):
        last_move_line = None
        for t_mline in range(len(m_lines)):
            t_suppl_inv_number = invoice_browse.supplier_invoice_number
            if (m_lines[t_mline][2]['date_maturity'] and
                    m_lines[t_mline][2]['credit'] > 0 and 
                    m_lines[t_mline][2]['name'] == t_suppl_inv_number):
                
                last_move_line = m_lines[t_mline]
                
                for i in range(len(old_pt)):
                    new_pt_date = new_pt[i][0]
                    new_pt_credit = new_pt[i][1]
                    if (old_pt[i][0] == m_lines[t_mline][2]['date_maturity']
                        and old_pt[i][1] == m_lines[t_mline][2]['credit']):
                        m_lines[t_mline][2]['date_maturity'] = new_pt_date
                        m_lines[t_mline][2]['credit'] = new_pt_credit
        if last_move_line:
            new_move_line = copy.deepcopy(last_move_line)
            date_formatted = datetime.strptime(add_pt[0][0],
                                                DF).strftime('%d/%m/%Y')
            t_date = self.pool.get('account.payment.term').check_if_holiday(date_formatted)
            new_move_line[2]['date_maturity'] = datetime.strptime(t_date, '%d/%m/%Y')
            new_move_line[2]['credit'] = invoice_browse.wht_amount
            # invoice_browse.number not yet defined
            new_move_line[2]['name'] = _('Payable withholding - ') + '/'
            new_move_line[2]['is_wht'] = True
            new_move_line[2]['wht_state'] = 'open'
            new_move_line[2]['state'] = 'valid'
            m_lines.append(new_move_line)

        return m_lines

    def _calculate_payment_terms(self, cr, uid, invoice_browse,
                                 move_lines, date_invoice):
        obj_pt = self.pool.get('account.payment.term')
        
        old_pt = obj_pt.compute(cr, uid, invoice_browse.payment_term.id,
            invoice_browse.amount_total,
            date_ref=date_invoice)
        
        new_pt = obj_pt.compute(cr, uid,
            invoice_browse.payment_term.id,
            invoice_browse.net_pay,
            date_ref=date_invoice)
        
        add_pt = self._new_wht_payment_term(cr, uid,
                            move_lines,
                            invoice_browse.date_due,
                            invoice_browse.wht_amount)
        
        return old_pt, new_pt, add_pt

    def _check_withholding_integrity(self, invoice):

        if not invoice.partner_id.wht_account_id:
            raise orm.except_orm(_('Error'),
                  _('The partner does not have an associated Withholding account'))

        if not invoice.partner_id.wht_account_id.wht_payment_term:
            raise orm.except_orm(_('Error'),
                  _('The Withholding account does not have an associated Withholding Payment Term'))

        return

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        return {
            'date_maturity': x.get('date_maturity', False),
            'partner_id': part,
            'name': x['name'][:64],
            'date': date,
            'debit': x['price'] > 0 and x['price'],
            'credit': x['price'] < 0 and -x['price'],
            'account_id': x['account_id'],
            'analytic_lines': x.get('analytic_lines', []),
            'amount_currency': x['price'] > 0 and abs(x.get('amount_currency', False)) or -abs(x.get('amount_currency', False)),
            'currency_id': x.get('currency_id', False),
            'tax_code_id': x.get('tax_code_id', False),
            'tax_amount': x.get('tax_amount', False),
            'ref': x.get('ref', False),
            'quantity': x.get('quantity', 1.00),
            'product_id': x.get('product_id', False),
            'product_uom_id': x.get('uos_id', False),
            'analytic_account_id': x.get('account_analytic_id', False),
            'payment_type': x.get('payment_type', False),
        }

    def onchange_withholding_amount(self, cr, uid, ids, wht_amount=False,
                                    amount_total=False, context=None):
        if not ids:
            return {'value': {
                    'wht_amount': 0.0,
                    'has_wht': False,
                    'net_pay': amount_total,
                    }
            }

        return {'value': {
                    'wht_amount': wht_amount,
                    'has_wht': True,
                    'net_pay': amount_total - wht_amount,
                    }
        }

    def onchange_supplier_invoice_number(self, cr, uid, ids, partner_id,
                                         supplier_invoice_number, context=None):
        warning = {}
        t_invoice_ids = self.search(cr, uid,
                                    [('partner_id', '=', partner_id),
                                     ('supplier_invoice_number', '=', supplier_invoice_number)])
        if t_invoice_ids:
            warning = {
                       'title': _('Warning!'),
                       'message': _('There is another invoice with the same number for this supplier')
                       }
        return {'value': {},
                'warning': warning
                 }

    def finalize_invoice_move_lines(self, cr, uid,
                                    invoice_browse, move_lines):

        move_lines = super(account_invoice_makeover,
                           self).finalize_invoice_move_lines(cr, uid,
                                                             invoice_browse,
                                                             move_lines)

        if (invoice_browse.type in ('in_invoice')
                    and invoice_browse.partner_id.wht_account_id
                    and invoice_browse.wht_amount > 0):

            self._check_withholding_integrity(invoice_browse)

            date_invoice = invoice_browse.date_invoice
            if not date_invoice:
                date_invoice = time.strftime(DF)

            old_pt, new_pt, add_pt = self._calculate_payment_terms(cr, uid,
                                            invoice_browse, move_lines,
                                            date_invoice)

            move_lines = self._recreate_move_lines(invoice_browse,
                                            move_lines, old_pt,
                                            new_pt, add_pt)

        return move_lines

    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id:
                raise orm.except_orm(_('Error!'),
                    _('Journal not defined for this invoice!'))
            if not inv.journal_id.iva_registry_id:
                raise orm.except_orm(_('Error!'),
                    _('You must link %s with a VAT registry!') % (inv.journal_id.name))
            if not inv.journal_id.sequence_id:
                raise orm.except_orm(_('Error!'),
                                     _('Please define sequence on the journal related to this invoice.'))      
            if not inv.invoice_line:
                raise orm.except_orm(_('No Invoice Lines!'),
                                     _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id],
                           {'date_invoice': fields.date.context_today(self,
                                                                      cr,
                                                                      uid,
                                                                      context=context)},
                           context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid,
                                                               inv.company_id.id).currency_id.id
            # create the analytical lines
            # one move line per invoice line
            # iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
            iml = super(account_invoice_makeover, self)._get_analytic_lines(cr, uid, inv.id, context=ctx)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            # self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
            super(account_invoice_makeover, self).check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid,
                                                                   group_check_total_id,
                                                                   context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0)):
                    raise orm.except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise orm.except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

#             entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
#                 entry_type = 'journal_pur_voucher'
#                 if inv.type == 'in_refund':
#                     entry_type = 'cont_voucher'
            else:
                # ref = self._convert_ref(cr, uid, inv.number)
                ref = super(account_invoice_makeover, self)._convert_ref(cr, uid, inv.number)
#                 entry_type = 'journal_sale_vou'
#                 if inv.type == 'out_refund':
#                     entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            # total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            total, total_currency, iml = super(account_invoice_makeover, self).compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            acc_id = inv.account_id.id

            name = inv['name'] or inv['supplier_invoice_number'] or '/'
            totlines = False
            if inv.payment_term:
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t_line in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t_line[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t_line[1],
                        'account_id': acc_id,
                        'date_maturity': t_line[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                        'payment_type': t_line[2]
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref,
                    'payment_type': None
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

            line = map(lambda x:(0, 0, self.line_get_convert(cr, uid, x, part.id, date, context=ctx)), iml)

            # line = self.group_lines(cr, uid, iml, line, inv)
            line = super(account_invoice_makeover, self).group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise orm.except_orm(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.registration_date, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            ctx.update(invoice=inv)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id, 'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        # self._log_event(cr, uid, ids)
        super(account_invoice_makeover, self)._log_event(cr, uid, ids)
        return True

    def button_display_view_list(self, cr, uid, ids, context=None):
        invoice = self.read(cr, uid, ids)[0]
        if invoice['payment_term']:
            p_term = invoice['payment_term'][0]
            d_invoice = invoice['date_invoice']
            a_total = invoice['amount_total']
            self.onchange_paymentterm(cr, uid, ids, p_term, d_invoice,
                                      a_total, context)
        return True

    def button_reset_taxes(self, cr, uid, ids, context=None):
        self.button_display_view_list(cr, uid, ids, context)
        self.button_display_withholding_amount(cr, uid, ids, context)

        result = super(account_invoice_makeover,
                       self).button_reset_taxes(cr, uid, ids, context)

        return result

    def _check_invoice_partner(self, cr, uid, invoice_type, invoice_partner, is_autoinvoice):
        partner_obj = self.pool.get('res.partner')
        partner_data = partner_obj.browse(cr, uid, invoice_partner)
        if invoice_type in ['in_invoice', 'in_refund']:
            if not partner_data.supplier:
                raise orm.except_orm(_('Error!'),
                                     _('The selected partner must be a Supplier'))
        if invoice_type in ['out_invoice', 'out_refund']:
            if not partner_data.customer and is_autoinvoice != True:
                raise orm.except_orm(_('Error!'),
                                     _('The selected partner must be a Customer'))
        return True

    def _set_invoice_tax(self, cr, user, t_id, ctx):
        ait_obj = self.pool.get('account.invoice.tax')
        cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (t_id,))
        for taxe in ait_obj.compute(cr, user, t_id, context=ctx).values():
            ait_obj.create(cr, user, taxe)

    def _set_partner_context(self, cr, user, context, invoice_partner):
        ctx = context.copy()
        partner_obj = self.pool.get('res.partner')
        partner_data = partner_obj.browse(cr, user, invoice_partner)
        if partner_data.lang:
            ctx.update({'lang':partner_data.lang})
        return ctx

    def _payment_term_contains_bank_transfer(self, cr, user, payment_term_ids):
        p_term_obj = self.pool.get('account.payment.term')
        p_term_data = p_term_obj.browse(cr, user, payment_term_ids)
        has_bank_transfer = False
        for p_term in p_term_data:
            p_term_line_data = p_term.line_ids
            for p_term_line in p_term_line_data:
                if (p_term_line.payment_type
                     and p_term_line.payment_type == 'B'):
                    has_bank_transfer = True
        return has_bank_transfer

    def check_intracee(self, cr, uid, fiscal_position_id):
        t_bool = False
        fiscal_position_obj = self.pool.get('account.fiscal.position')
        for rec in fiscal_position_obj.browse(cr, uid, [fiscal_position_id]):
            if (rec.name == 'Regime Intra comunitario'):
                t_bool = True
        return t_bool

    def check_reverse_charge(self, cr, uid, fiscal_position_id):
        t_bool = False
        fiscal_position_obj = self.pool.get('account.fiscal.position')
        for rec in fiscal_position_obj.browse(cr, uid, [fiscal_position_id]):
            if (rec.name == 'Italia - Reverse Charge'):
                t_bool = True
        return t_bool

    def create(self, cr, user, vals, context=None):
        if context is None:
            context = {}

        invoice_type = context.get('type')
        if (invoice_type in ['in_invoice', 'in_refund'] and 
           'registration_date' in vals and 
           'date_invoice' in vals):
            t_registration_date = vals["registration_date"]
            t_date_invoice = vals["date_invoice"]
            if(t_registration_date and t_date_invoice and t_date_invoice > t_registration_date):
                raise orm.except_orm(_('Error!'),
                                     _('Document Date must be less then Registration Date'))
        if (invoice_type in ['in_invoice', 'in_refund'] and 
           'payment_term' in vals and 
           ('partner_bank_id' not in vals
             or not vals["partner_bank_id"])):
            if self._payment_term_contains_bank_transfer(cr, user, [vals["payment_term"]]):
                raise orm.except_orm(_('Error!'),
                                     _('Il conto bancario è obbligatorio perché il termine di pagamento è di tipo bonifico'))

        invoice_partner = vals["partner_id"]

        is_autoinvoice = False
        if ("fiscal_position" in vals
             and vals["fiscal_position"]
             and self.check_intracee(cr, user, vals["fiscal_position"])):
            is_autoinvoice = True
        self._check_invoice_partner(cr, user, invoice_type, invoice_partner, is_autoinvoice)

        res = super(account_invoice_makeover, self).create(cr,
                                                           user,
                                                           vals,
                                                           context)
        t_id = int(res)

        ctx = None
        if 'recompute_values' in vals and vals['recompute_values']:
            ctx = self._set_partner_context(cr, user, context, invoice_partner)
            self._set_invoice_tax(cr, user, t_id, ctx)

        t_dict = {}

        t_acc_inv = self.browse(cr, user, t_id)
        if(t_acc_inv.type == "in_invoice" or t_acc_inv.type == "in_refund"):
            if(t_acc_inv.supplier_invoice_number):
                t_dict['document_number'] = t_acc_inv.supplier_invoice_number

        wt_amount, t_invoice_id = self._get_wht_amount(cr,
                                                       user,
                                                       t_id,
                                                       context)
        if t_invoice_id:
            t_dict['wht_amount'] = 0.0
            if (wt_amount):
                t_dict['wht_amount'] = wt_amount

        self.write(cr, user, [t_id], t_dict, context)

        return res

    def _check_bank_account_riba(self, cr, uid, vals, t_id):
        t_acc_inv = self.browse(cr, uid, t_id)
        invoice_type = t_acc_inv.type
        if (invoice_type == "out_invoice" or invoice_type == "out_refund"):
            p_term_lines = None
            is_riba = False
            if t_acc_inv.payment_term and not 'payment_term' in vals:
                p_term_lines = t_acc_inv.payment_term.line_ids
            if ('payment_term' in vals and vals['payment_term']):
                p_term_obj = self.pool.get('account.payment.term')
                p_term_data = p_term_obj.browse(cr, uid, vals['payment_term'])
                p_term_lines = p_term_data.line_ids
            if p_term_lines:
                for p_term_line in p_term_lines:
                    if p_term_line.payment_type == 'D':
                        is_riba = True
            if is_riba:
                if (('bank_account' in vals and not vals['bank_account']) or 
                    'bank_account' not in vals and not t_acc_inv.bank_account):
                    raise orm.except_orm(_('Error!'), 
                        _('Il campo "Conto Bancario del Cliente" deve essere compilato poiché il termine di pagamento selezionato prevede le Ricevute Bancarie.'))

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}

        for t_id in ids:
            t_acc_inv = self.browse(cr, uid, t_id)

            invoice_type = t_acc_inv.type
            if 'type' in vals:
                invoice_type = vals['type']

            t_registration_date = t_acc_inv.registration_date
            t_date_invoice = t_acc_inv.date_invoice

            if ('registration_date' in vals):
                t_registration_date = vals["registration_date"]
            if ('date_invoice' in vals):
                t_date_invoice = vals["date_invoice"]
            if (t_registration_date and
                    t_date_invoice and
                    t_date_invoice > t_registration_date and
                    (invoice_type in ['in_invoice', 'in_refund'])):
                raise orm.except_orm(_('Error!'),
                                     _('Document Date must be less then Registration Date'))

            invoice_partner = t_acc_inv.partner_id.id
            if 'partner_id' in vals:
                invoice_partner = vals["partner_id"]

            is_autoinvoice = t_acc_inv.is_autoinvoice
            if 'is_autoinvoice' in vals:
                is_autoinvoice = vals["is_autoinvoice"]

            self._check_invoice_partner(cr, uid, invoice_type, invoice_partner, is_autoinvoice)

            if(invoice_type == "in_invoice" or invoice_type == "in_refund"):
                if('supplier_invoice_number' in vals):
                    vals["document_number"] = vals["supplier_invoice_number"]

            t_payment_term = t_acc_inv.payment_term
            t_partner_bank_id = t_acc_inv.partner_bank_id
            if 'payment_term' in vals:
                t_payment_term = vals["payment_term"]
            if 'partner_bank_id' in vals:
                t_partner_bank_id = vals["partner_bank_id"]
            if isinstance(t_payment_term, browse_record):
                t_payment_term = t_payment_term.id

            if (invoice_type in ['in_invoice', 'in_refund'] and 
               t_payment_term and 
               not t_partner_bank_id):
                if self._payment_term_contains_bank_transfer(cr, uid, [t_payment_term]):
                    raise orm.except_orm(_('Error!'),
                                         _('Il conto bancario è obbligatorio perché il termine di pagamento è di tipo bonifico'))

            self._check_bank_account_riba(cr, uid, vals, t_id)

            ctx = None
            t_recompute_vals = t_acc_inv.recompute_values
            if 'recompute_values' in vals:
                t_recompute_vals = vals['recompute_values']
            if ('tax_line' in vals):
                t_recompute_vals = False
            if t_recompute_vals:
                ctx = self._set_partner_context(cr, uid, context, invoice_partner)
                self._set_invoice_tax(cr, uid, t_id, ctx)
    
            wt_amount, t_invoice_id = self._get_wht_amount(cr,
                                                           uid,
                                                           t_id,
                                                           context)
            if t_invoice_id:
                vals["wht_amount"] = 0.0
                if (wt_amount):
                    vals["wht_amount"] = wt_amount

        res = super(account_invoice_makeover, self).write(cr,
                                                          uid,
                                                          ids,
                                                          vals,
                                                          context)
        return res

    def button_display_withholding_amount(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for t_id in ids:
            wt_amount, t_invoice_id = self._get_wht_amount(cr,
                                                           uid,
                                                           t_id,
                                                           context)

            if t_invoice_id:
                if (wt_amount):
                    self.write(cr, uid,
                               [t_invoice_id],
                               {'wht_amount': wt_amount }, context=context)
                else:
                    self.write(cr, uid,
                               [t_invoice_id],
                               {'wht_amount': 0.0 }, context=context)

        return True

    def _get_wht_amount(self, cr, uid, res_id, ctx):
        inv_data = self.browse(cr, uid, res_id, context=ctx)
        wt_amount = 0.0
        t_invoice_id = None
        for line in inv_data.invoice_line:
            t_invoice_id = line.invoice_id.id
            t_account_id = line.invoice_id.partner_id.wht_account_id
            if (line.invoice_id.type == 'in_invoice' and t_account_id):
                if (line.product_id.has_wht == True):
                    t_price_unit = line.price_unit
                    t_quantity = line.quantity
                    t_wht_tax_rate = t_account_id.wht_tax_rate / 100
                    t_wht_base = t_account_id.wht_base_amount / 100
                    wt_amount = wt_amount + t_quantity * t_price_unit * t_wht_tax_rate * t_wht_base
        return wt_amount, t_invoice_id

    def onchange_partner_id(self, cr, uid, ids, invoice_type, partner_id,
                                date_invoice=False, payment_term=False,
                                partner_bank_id=False, company_id=False):
        """
                Extends the onchange.
        """
        result = super(account_invoice_makeover,
                       self).onchange_partner_id(cr, uid, ids,
                                            invoice_type, partner_id,
                                            date_invoice=date_invoice,
                                            payment_term=payment_term,
                                            partner_bank_id=partner_bank_id,
                                            company_id=company_id)

        self.button_display_withholding_amount(cr, uid, ids, context=None)

        bank_id = None
        if partner_id and invoice_type in ('out_invoice', 'out_refund'):
                t_partner_data = self.pool.get('res.partner').browse(cr, uid, partner_id)
                if t_partner_data.bank_ids:
                    bank_id = t_partner_data.bank_ids[0].id
        result['value']['bank_account'] = bank_id

        ext_obj = self.pool.get('account.exporter.statements')
        exp_ids = ext_obj.search(cr, uid,
                                 [('partner_id', '=', partner_id),
                                  ('letter_status', '=', 'A')])
        if(exp_ids and exp_ids[0]):
            result['value']['exporter_id'] = exp_ids[0]

        return result

    def _net_pay(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context):
            res[invoice.id] = invoice.amount_total - invoice.wht_amount
        return res

    def _has_withholding(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context):
            res[invoice.id] = True if (invoice.wht_amount > 0) else False
        return res

    def _wht_code(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context):
            if (invoice.partner_id.wht_account_id):
                t_wht_name = invoice.partner_id.wht_account_id.name
                t_wht_descr = invoice.partner_id.wht_account_id.description
                res[invoice.id] = t_wht_name + "  " + t_wht_descr
        return res

    def _wht_tax_rate(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context):
            res[invoice.id] = invoice.partner_id.wht_account_id.wht_tax_rate
        return res

    def _wht_base_amount(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context):
            t_base_amount = invoice.partner_id.wht_account_id.wht_base_amount
            res[invoice.id] = t_base_amount
        return res
    
    def _default_last_date_registration(self, cr, uid, context=None):

        t_type = context.get('type', None)
        datetime_today = datetime.strptime(fields.date.context_today(self, cr, uid, context=context), tools.DEFAULT_SERVER_DATE_FORMAT)
        if t_type in ['out_invoice', 'out_refund']:
            return datetime_today.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)

        invoice_ids = self.search(cr, uid,
                                  [('partner_id.supplier', '=', True),
                                   ('state', 'not in', ['cancel', 'paid'])],
                                  limit=1,
                                  order='id desc')
        t_invoice = None
        if invoice_ids:
            t_invoice = self.read(cr, uid, invoice_ids[0], ['registration_date'])
            if t_invoice['registration_date']:
                return t_invoice['registration_date']
        return datetime_today.strftime(tools.DEFAULT_SERVER_DATE_FORMAT)

    def onchange_registration_date(self, cr, uid, ids, date_invoice, registration_date, context=None):
        warning = {}
        if(date_invoice and date_invoice and (date_invoice > registration_date)):
            warning = {
                       'title': _('Warning!'),
                       'message': _('Document Date must be less then Registration Date')
                       }
        return {'value': {},
                'warning': warning,
                 }

    def _get_withholding_maturity_term(self, cr, uid):
        p_term_obj = self.pool.get('account.payment.term')
        p_term_search = p_term_obj.search(cr, uid,
                                          [('name', '=',
                                            '16th Next Month')],
                                          limit=1)
        if not p_term_search:
            raise orm.except_orm(_('Error!'),
                (_('Payment term "16th Next Month" missing!')))

        p_term_data = p_term_obj.browse(cr, uid, p_term_search[0],
                                           context=False)

        if not p_term_data.line_ids:
            raise orm.except_orm(_('Error!'),
                (_('Il calcolo del termine di pagamento "%s" non è corretto!' % p_term_data.name)))

        return p_term_data.id

    def _format_time(self, date):
        return datetime.strptime(date, DF).strftime('%d/%m/%Y')

    def _get_wht_due_line(self, cr, uid, invoice, pterm_list):
        date_maturity_list = []
        for t_line in pterm_list:
            t_date_maturity = t_line[0]
            date_maturity_list.append(t_date_maturity)
        
        t_min_payment_term = min(string for string in date_maturity_list)
        t_currency_name = invoice.currency_id.name
        p_term_id = self._get_withholding_maturity_term(cr, uid)
        pt_obj = self.pool.get('account.payment.term')
        t_wht_amount = invoice.wht_amount
        t_wht_pterm_list = pt_obj.compute(cr, uid, p_term_id,
                                      t_wht_amount,
                                      date_ref=t_min_payment_term or False)
        t_date = self._format_time(t_wht_pterm_list[0][0])
        
        t_date_check = self.pool.get('account.payment.term').check_if_holiday(t_date)
        
        t_new_pterm = {
            'date':t_date_check,
            'amount':invoice.wht_amount,
            'currency_name':t_currency_name}
        return t_new_pterm

    def onchange_paymentterm(self, cr, uid, ids, payment_term=False,
                             date_invoice=False, amount_total=False,
                             context=None):
        if not ids:
            return {'value': {
                    'payment_term_label': '',
                    'payments_preview': [],
                    }
            }
        p_type = _('Not specified')
        payments_preview = []
        invoice = self.browse(cr, uid, ids[0])
        t_amount_total = amount_total
        if (hasattr(invoice, 'has_wht') and invoice.has_wht):
            t_amount_total = invoice.net_pay
        obj_pt = self.pool.get('account.payment.term')
        if payment_term:
            p_type = obj_pt.name_get(cr, uid, [payment_term], context)[0][1]
            pterm_list = obj_pt.compute(cr, uid, payment_term,
                                        t_amount_total, date_ref=date_invoice)
            if pterm_list:
                for line in pterm_list:
                    t_pline = self._get_preview_line(invoice, line)
                    payments_preview.append(t_pline)

                if (hasattr(invoice, 'has_wht') and invoice.has_wht):
                    t_new_pterm = self._get_wht_due_line(cr, uid,
                                                      invoice, pterm_list)
                    payments_preview.append(t_new_pterm)

        return {'value': {
                    'payment_term_label': p_type,
                    'payments_preview': payments_preview,
                    }
        }

    def _get_preview_line(self, invoice, line):
        currency_name = invoice.currency_id.name
        amount_total_line = line[1]
        t_pterm = {
                   'date':self._format_time(line[0]),
                   'amount':amount_total_line,
                   'currency_name':currency_name}
        return t_pterm

    def _get_preview_lines(self, cr, uid, ids, field_name,
                           arg, context=None):
        result = {}
        if ids:
            result[ids[0]] = []
            invoice = self.browse(cr, uid, ids[0])
            t_amount_total = invoice.amount_total
            if (hasattr(invoice, 'has_wht') and invoice.has_wht):
                t_amount_total = invoice.net_pay
            obj_pt = self.pool.get('account.payment.term')
            if invoice.payment_term:
                pterm_list = obj_pt.compute(cr, uid, invoice.payment_term.id,
                                            t_amount_total,
                                            date_ref=invoice.date_invoice)
                if pterm_list:
                    for line in pterm_list:
                        t_pterm = self._get_preview_line(invoice, line)
                        result[ids[0]].append(t_pterm)

                    if (hasattr(invoice, 'has_wht') and invoice.has_wht):
                        t_new_pterm = self._get_wht_due_line(cr, uid,
                                                          invoice, pterm_list)
                        result[ids[0]].append(t_new_pterm)
        return result

    def _get_line_overview(self, invoice, l):
        t_currency = l.currency_id.name or invoice.currency_id.name
        t_date_maturity = self._format_time(l.date_maturity)
        t_line_overview = {'pay_overv_date': t_date_maturity,
                           'pay_overv_amount': l.debit + l.credit,
                           'pay_overv_currency': t_currency}
        return t_line_overview

    def _get_payments_overview(self, cr, uid, ids, field_name,
                               arg, context=None):
        result = {}
        if ids:
            result[ids[0]] = []
            invoice = self.browse(cr, uid, ids[0])
            if invoice.state != 'draft':
                t_filter = [('move_id', '=', invoice.move_id.id),
                            ('date_maturity', '!=', False)]
                mov_line_obj = self.pool.get(
                                                    'account.move.line')
                mov_line_ids = mov_line_obj.search(cr, uid, t_filter,
                                       order='date_maturity')
                mov_line_data = mov_line_obj.browse(cr, uid, mov_line_ids)
                for line in mov_line_data:
                    t_line_overview = self._get_line_overview(invoice, line)
                    result[ids[0]].append(t_line_overview)
        return result

    def _get_payment_term_label(self, cr, uid, ids, field_name,
                                arg, context=None):
        result = {}
        for rec in self.browse(cr, uid, ids, context=context):
            updated_due = self.onchange_paymentterm(cr, uid, ids,
                                    rec.payment_term.id, rec.date_invoice,
                                    rec.amount_total, context)
            t_pterm_label = updated_due['value']['payment_term_label']
            result[rec.id] = t_pterm_label
        return result
    
    def _get_invoice_isa(self, cr, uid, ids, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            result[invoice.id] = True
        return result.keys()
    
    def _get_int_protocol_number(self, cr, uid, ids, field_name, arg,
                                   context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.protocol_number:
                res[invoice.id] = int(invoice.protocol_number)
        return res

    _columns = {
        'bank_account': fields.many2one('res.partner.bank',
                                    'Bank Account of Client',
                                    readonly=True,
                                    states={'draft':[('readonly', False)]}),
        'partner_bank_id': fields.many2one('res.partner.bank',
                                    'Company Bank', readonly=True,
                                    states={'draft':[('readonly', False)]}),
        'document_number': fields.char('Document Number',
                                    size=64),
        'registration_date':fields.date('Registration Date',
                                    states={'draft': [('readonly', False)],
                                            'paid': [('readonly', True)],
                                            'open' :[('readonly', True)],
                                            'close': [('readonly', True)]},
                                    select=True),
        'protocol_number': fields.char('Protocol Number',
                                    size=64,
                                    readonly=True),
        'protocol_date': fields.date('Protocol Date'),

        'wht_amount': fields.float('(-) Withholding amount',
                                    digits_compute=dp.get_precision('Account'),
                                    readonly=True,
                                    states={'draft':[('readonly', False)]}),
        'has_wht': fields.function(_has_withholding),
        'net_pay': fields.function(_net_pay, string="Net Pay"),
        'wht_code': fields.function(_wht_code,
                                    readonly=True,
                                    type="char",
                                    string="Withholding Tax Code"),
        'wht_tax_rate': fields.function(_wht_tax_rate,
                                    string="Withholding Tax Rate"),
        'wht_base_amount': fields.function(_wht_base_amount,
                                    string="Withholding Base Amount"),
        'exporter_id': fields.many2one('account.exporter.statements',
                                     'Exporter Statements'),
        'payments_preview':   fields.function(_get_preview_lines,
                                    type="one2many",
                                    relation='account.invoice.maturity.preview.lines',
                                    string="Maturities preview (calculated at invoice validation time)",
                                    readonly=True),
        'payments_overview':  fields.function(_get_payments_overview,
                                    type="one2many",
                                    relation='account.invoice.maturity.preview.lines',
                                    string="Payments overview", readonly=True),
        'payment_term_label': fields.function(_get_payment_term_label,
                                    type="char",
                                    string="Payment term", readonly=True),
        'recompute_values': fields.boolean('Ricalcola Importi al Salvataggio'),
        'integer_protocol_number': fields.function(_get_int_protocol_number,
                                    method=True,
                                    type='integer',
                                    string='Integer Protocol Number',
                                    store={
                                           'account.invoice': (_get_invoice_isa, ['protocol_number'], 10),
                                           }),
        'is_autoinvoice': fields.boolean('Autofattura'),
        'ref_autoinvoice': fields.many2one('account.invoice',
                                    'Rif. Autofattura'),
    }

    _defaults = {
        'registration_date': _default_last_date_registration,
        'date_invoice': _default_last_date_registration,
        'recompute_values': True,
        'is_autoinvoice': False,
    }

    def invoice_validate(self, cr, uid, ids, context=None):

        res = super(account_invoice_makeover, self).invoice_validate(cr, uid, ids,
                                                             context=context)
        if res:
            for t_id in ids:
                t_invoice_data = self.browse(cr, uid, t_id, context=context)
                t_move_id = t_invoice_data.move_id.id
                t_date_invoice = t_invoice_data.date_invoice
                t_registration_date = t_invoice_data.registration_date
                t_document_number = t_invoice_data.document_number

                if not t_invoice_data.protocol_number:
                    obj_seq = self.pool.get('ir.sequence')
                    t_seq_id = t_invoice_data.journal_id.iva_registry_id.sequence_iva_registry_id.id
    
                    number_next = obj_seq.next_by_id(cr, uid, t_seq_id)

                    self.write(cr, uid, [t_id],
                               {'protocol_number': number_next})

                    self.pool.get('account.move').write(cr, uid,
                                                       [t_move_id],
                                                       {
                                                        'date': t_registration_date,
                                                        'document_date': t_date_invoice,
                                                        'document_number': t_document_number,
                                                        'protocol_number': number_next,
                                                        })
                else:
                    if not t_invoice_data.move_id.protocol_number:
                        self.pool.get('account.move').write(cr, uid,
                                                           [t_move_id],
                                                           {
                                                            'date': t_registration_date,
                                                            'document_date': t_date_invoice,
                                                            'document_number': t_document_number,
                                                            'protocol_number': t_invoice_data.protocol_number,
                                                            })

        return res

    def invoice_pay_customer(self, cr, uid, ids, context=None):

        pay_wizard = super(account_invoice_makeover,
                           self).invoice_pay_customer(cr, uid, ids,
                                                      context=None)

        inv = self.browse(cr, uid, ids[0], context=context)
        if (inv.type == 'in_invoice'):
            pay_wizard['context']['default_amount'] = inv.net_pay

        return pay_wizard

    def copy_translations(self, cr, uid, old_id, new_id, context=None):
        if context is None:
            context = {}

        # avoid recursion through already copied records in case of circular relationship
        seen_map = context.setdefault('__copy_translations_seen', {})
        if old_id in seen_map.setdefault(self._name, []):
            return
        seen_map[self._name].append(old_id)

        trans_obj = self.pool.get('ir.translation')
        t_fields = self.fields_get(cr, uid, context=context)

        translation_records = []
        for field_name, field_def in t_fields.items():
            # we must recursively copy the translations for o2o and o2m
            if field_def['type'] == 'one2many':
                target_obj = self.pool.get(field_def['relation'])
                if (field_name != 'payments_overview'
                       and field_name != 'payments_preview'
                       and field_name != 'has_wht'
                       and field_name != 'net_pay'
                       and field_name != 'wht_code'
                       and field_name != 'wht_tax_rate'
                       and field_name != 'wht_base_amount'
                       and field_name != 'payment_term_label'):
                    old_record, new_record = self.read(cr, uid,
                                                       [old_id, new_id],
                                                       [field_name],
                                                       context=context)
                    # here we rely on the order of the ids to match the translations
                    # as foreseen in copy_data()
                    old_children = sorted(old_record[field_name])
                    new_children = sorted(new_record[field_name])

                    for (old_child, new_child) in zip(old_children, new_children):
                        target_obj.copy_translations(cr, uid, old_child, new_child, context=context)
            # and for translatable fields we keep them for copy
            elif field_def.get('translate'):
                trans_name = ''
                if field_name in self._columns:
                    trans_name = self._name + "," + field_name
                elif field_name in self._inherit_fields:
                    trans_name = self._inherit_fields[field_name][0] + "," + field_name
                if trans_name:
                    trans_ids = trans_obj.search(cr, uid, [
                            ('name', '=', trans_name),
                            ('res_id', '=', old_id)
                    ])
                    translation_records.extend(trans_obj.read(cr, uid,
                                                              trans_ids,
                                                              context=context))

        for record in translation_records:
            del record['id']
            record['res_id'] = new_id
            trans_obj.create(cr, uid, record, context=context)

    def invoice_open(self, cr, uid, ids, *args):

        wf_service = netsvc.LocalService("workflow")
        for t_id in ids:
            wf_service.trg_validate(uid, 'account.invoice',
                                    t_id, 'invoice_open', cr)
        return True

    def action_date_assign(self, cr, uid, ids, *args):

        return super(account_invoice_makeover,
                     self).action_date_assign(cr, uid, ids, *args)

    def action_number(self, cr, uid, ids, context=None):

        return super(account_invoice_makeover,
                     self).action_number(cr, uid, ids, context)
