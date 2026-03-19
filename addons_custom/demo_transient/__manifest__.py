{
    'name': 'Demo Transient Model',
    'version': '1.0',
    'summary': 'Module học tập về Transient Model (Wizard) trong Odoo',
    'category': 'Learning',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/demo_employee_views.xml',
        'views/demo_contract_views.xml',
        'views/salary_summary_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
}
