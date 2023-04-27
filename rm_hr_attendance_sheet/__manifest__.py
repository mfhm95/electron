{
    'name': "HR Attendance Sheet And Policies",

    'summary': """Managing  Attendance Sheets for Employees
        """,
    'description': """
        Employees Attendance Sheet Management   
    """,
    'author': "Ramadan Khalil",
    'website': "rkhalil1990@gmail.com",
    'price': 99,
    'currency': 'EUR',

    'category': 'hr',
    'version': '14.001',
    'images': ['static/description/bannar.jpg'],

    'depends': ['base',
                'hr',
                'hr_payroll',
                'hr_holidays',
                'hr_overtime_request',
                'hr_attendance'],
    'data': [
        'data/ir_sequence.xml',
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/change_att_data_view.xml',
        'views/hr_attendance_sheet_view.xml',
        'views/hr_attendance_policy_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_public_holiday_view.xml',
        'views/attendance_sheet_batch_view.xml',
        'views/planning_view.xml',
        'views/hr_leave_view.xml',
        'views/hr_employee_view.xml',
        'views/resource_calendar_view.xml',

    ],

    'license': 'OPL-1',
    'demo': [
        'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-








