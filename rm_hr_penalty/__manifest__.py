# -*- coding: utf-8 -*-
{
    'name': "Hr Penalties Management",
    'summary': """
        """,
    'description': """
    """,
    'author': "Eng.Ramadan Khalil",
    'website': "rkhalil1990@gmail.com",
    'price': 19,
    'currency': 'EUR',
    'category': 'hr',
    'version': '0.1',
    # 'images': ['static/description/bannar.jpg'],

    'depends': ['base','hr','hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/hr_penalty_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'OPL-1',
}