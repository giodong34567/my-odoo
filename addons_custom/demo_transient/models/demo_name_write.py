from odoo import _, api, fields, models


class DemoNameWrite(models.Model):
    """
    Demo: _rec_name / display_name  và  override create() / write()
    """
    _name = 'demo.name.write'
    _description = 'Demo Name & Write'

    # ── _rec_name ─────────────────────────────────────────────────
    # Mặc định Odoo dùng field 'name' làm display label.
    # Đổi sang field khác:
    _rec_name = 'code'

    code = fields.Char(string='Mã', required=True)
    first_name = fields.Char(string='Họ')
    last_name = fields.Char(string='Tên')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Hoàn thành'),
    ], default='draft')
    note = fields.Text()

    # ── display_name (computed) ───────────────────────────────────
    # Khi cần label phức tạp hơn 1 field đơn, override display_name
    # Odoo 17+ dùng cách này thay cho name_get() cũ
    display_name = fields.Char(compute='_compute_display_name', store=False)

    @api.depends('code', 'first_name', 'last_name')
    def _compute_display_name(self):
        for rec in self:
            parts = filter(None, [rec.code, rec.first_name, rec.last_name])
            rec.display_name = ' - '.join(parts) or _('(Chưa đặt tên)')

    # ── Override create() ─────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        """
        Pattern chuẩn để override create:
        1. Xử lý / bổ sung vals trước khi tạo
        2. Gọi super() để tạo record
        3. Xử lý sau khi tạo (post-processing)
        """
        for vals in vals_list:
            # Tự sinh code nếu chưa có
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('demo.name.write') or 'NEW'

            # Normalize: strip khoảng trắng
            if vals.get('first_name'):
                vals['first_name'] = vals['first_name'].strip()

        records = super().create(vals_list)

        # Post-processing: gửi thông báo, tạo record liên quan...
        for rec in records:
            rec.note = f"Tạo lúc: {fields.Datetime.now()}"

        return records  # luôn return kết quả của super()

    # ── Override write() ──────────────────────────────────────────
    def write(self, vals):
        """
        Pattern chuẩn để override write:
        1. Kiểm tra / chặn trước khi ghi
        2. Gọi super()
        3. Xử lý sau khi ghi
        """
        # Chặn đổi state ngược (done => draft) nếu muốn
        if 'state' in vals and vals['state'] == 'draft':
            locked = self.filtered(lambda r: r.state == 'done')
            if locked:
                raise models.ValidationError(
                    _('Không thể đưa về Nháp khi đã Hoàn thành: %s')
                    % ', '.join(locked.mapped('code'))
                )

        result = super().write(vals)

        # Post-processing sau khi ghi
        if 'state' in vals:
            for rec in self:
                rec.note = f"Đổi state => {vals['state']} lúc {fields.Datetime.now()}"

        return result  # luôn return kết quả của super()
