{
    'name': 'mertic payslip report',
    'description': 'mertic payslip report',
    'version': '1.0.0',
    'license': 'LGPL-3',
    'category': 'Crm',
    'author': 'Ayman Tarek',
    'website': '',
    'depends': [
        'hr_payroll',
        'hr',
    ],
    'data': [
        'report/report_payslip_templates.xml',
        'views/hr_work_entry_type.xml',
        'views/contract_type.xml',
    ],
    'application': True,
    'installable': True,
}
