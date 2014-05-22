# -*- encoding: utf-8 -*-

{
    'name': 'Isa accounting reports mag Layout',
    'version': '0.1',
    'category': 'report',
    'description': """Accounting Isa reports - Fattura Magazzino layout
    Install report_aero_ooo to be able to output to a format
    different from the one of the template.
    """,
    'author': 'ISA srl',
    'website': 'http://www.isa.it',
    'license': 'AGPL-3',
    "depends" : ['account_invoice_layout','account_invoice_ext_isa','l10n_it_account', 'report_aeroo_ooo'],
    "init_xml" : [
        ],
    "update_xml" : [
        'reports.xml',
        ],
    "demo_xml" : [],
    "active": False,
    "installable": True
}