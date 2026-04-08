{
    'name': 'Shopify Integration',
    'version': '18.0.1.0.0',
    'summary': 'Sync products, variants, and orders from Shopify into Odoo',
    'category': 'Technical',
    'depends': ['base', 'sale_management', 'stock', 'mail'],
    'data': [
        'security/shopify_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/shopify_config_views.xml',
        'views/shopify_sync_log_views.xml',
        'views/shopify_wizard_views.xml',
        'views/shopify_menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
