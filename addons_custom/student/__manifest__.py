{
    'name': 'Student',
    'version': '1.0',
    'summary': 'Quản lý học sinh - module học tập',
    'category': 'Learning',
    'depends': ['base', 'mail'],
    'data': [
        'security/student_groups.xml',
        'security/ir.model.access.csv',
        'data/student_sequence.xml',
        'views/student_views.xml',
    ],
    'installable': True,
    'application': True,
}
