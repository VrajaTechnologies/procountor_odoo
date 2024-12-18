# -*- coding: utf-8 -*-pack
{

    # App information
    'name': 'Procountor Odoo Connector',
    'category': 'Accounting',
    'version': '1.0.0',
    'summary': """Procountor Odoo Connector
    """,
    'license': 'OPL-1',

    # Dependencies
    'depends': ['account'],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'views/ir_cron.xml',
        'views/procountor_log.xml',
        'views/res_partner.xml',
        'views/product_list.xml',
        'wizard/export_customer_to_procountor.xml',
        'wizard/export_invoice_to_procountor.xml',
        'wizard/procountor_operations_view.xml',
        'views/procountor_instance.xml',
        'views/menu_item.xml',
        'views/account_tax.xml',
        'views/account_move.xml'
    ],

    # Odoo Store Specific
    'images': [],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',
    'price': '',
    'currency': 'EUR',

}
# version changelog
