from odoo import fields, models


class DemoHierarchy(models.Model):
    """
    Demo: _order (sắp xếp mặc định) và _parent_store (cấu trúc cây)
    """
    _name = 'demo.hierarchy'
    _description = 'Demo Hierarchy'

    # _order: thứ tự mặc định khi search(), hiển thị list view
    # Không cần order= mỗi lần gọi search()
    _order = 'sequence, name'

    # _parent_store: bật tính năng lưu trữ cây (parent_left/parent_right)
    # Giúp query child_of / parent_of cực nhanh (nested set model)
    _parent_store = True

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)

    # Bắt buộc khi dùng _parent_store
    parent_id = fields.Many2one('demo.hierarchy', string='Cha', ondelete='restrict')
    parent_path = fields.Char(index=True)  # Odoo tự quản lý, không sửa tay

    child_ids = fields.One2many('demo.hierarchy', 'parent_id', string='Con')

    # Dùng child_of trong domain để tìm toàn bộ cây con
    # self.env['demo.hierarchy'].search([('parent_id', 'child_of', some_id)])
