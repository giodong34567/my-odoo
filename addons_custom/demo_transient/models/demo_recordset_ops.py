from odoo import api, fields, models


class DemoRecordsetOps(models.Model):
    """
    Demo: Recordset Arithmetic — phép toán tập hợp trên recordset.

    Recordset trong Odoo là tập hợp các record của cùng 1 model.
    Có thể thực hiện phép toán tập hợp như Python set, nhưng GIỮ THỨ TỰ.
    """
    _name = 'demo.recordset.ops'
    _description = 'Demo Recordset Operations'

    name = fields.Char(required=True)
    tag = fields.Selection([
        ('a', 'Nhóm A'),
        ('b', 'Nhóm B'),
        ('c', 'Nhóm C'),
    ])
    score = fields.Integer(default=0)

    @api.model
    def demo_arithmetic(self):
        all_recs = self.search([])
        group_a  = self.search([('tag', '=', 'a')])
        group_b  = self.search([('tag', '=', 'b')])

        # ── Phép toán tập hợp ─────────────────────────────────────

        # | (union): gộp 2 recordset, loại trùng, GIỮ thứ tự
        a_or_b = group_a | group_b

        # & (intersection): chỉ lấy record có trong CẢ HAI
        common = all_recs & group_a

        # - (difference): lấy record trong all nhưng KHÔNG có trong group_a
        not_a = all_recs - group_a

        # in: kiểm tra record có trong recordset không
        rec = self.browse(1)
        is_in_a = rec in group_a          # True/False

        # ── So sánh ───────────────────────────────────────────────
        same = group_a == group_b         # so sánh theo ids
        is_subset = group_a <= all_recs   # group_a là tập con của all_recs?

        # ── Một số trick hay ──────────────────────────────────────

        # Tạo empty recordset cùng model (hay dùng làm accumulator)
        result = self.env['demo.recordset.ops']
        for rec in all_recs:
            if rec.score > 50:
                result |= rec   # gom dần vào tập kết quả

        # ids: lấy list id (không query DB thêm)
        id_list = all_recs.ids   # [1, 2, 3, ...]

        # ensure_one(): raise nếu recordset không đúng 1 record
        # Dùng ở đầu method chỉ xử lý 1 record
        # self.ensure_one()  => UserError nếu len(self) != 1

        # mapped trả về recordset nếu field là relation
        # (khác với mapped field thường trả về list)
        # children = parent_recs.mapped('child_ids')  # => recordset

        return result
