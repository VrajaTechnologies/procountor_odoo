# -*- coding: utf-8 -*-pack
{

    # App information
    'name': 'Procountor Odoo Connector ',
    'category': 'Website',
    'version': '1.0.0',
    'summary': """""",
    'license': 'OPL-1',

    # Dependencies
    'depends': ['delivery'],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'views/procountor_instance.xml',
        'views/menu_item.xml',

    ],
    # Odoo Store Specific
    'images': ['static/description/cover.jpg'],

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
