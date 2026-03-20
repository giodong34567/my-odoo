from odoo import _, api, fields, models


class DemoSequenceMail(models.Model):
    """
    Demo: ir.sequence (tự sinh mã) và mail.thread (chatter + tracking)
    """
    _name = 'demo.sequence.mail'
    _description = 'Demo Sequence & Mail Thread'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # mail.thread     => chatter (log, gửi message)
    # mail.activity.mixin => lên lịch activity (todo, call, email...)

    # ── tracking=True: tự log thay đổi vào chatter ───────────────
    name = fields.Char(string='Mã', readonly=True, copy=False, default='New')
    title = fields.Char(string='Tiêu đề', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Xác nhận'),
        ('done', 'Hoàn thành'),
    ], default='draft', tracking=True)  # tracking=True => log khi đổi state
    amount = fields.Float(string='Số tiền', tracking=True)
    note = fields.Text(string='Ghi chú')

    # ── ir.sequence trong create() ────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                # next_by_code: lấy số tiếp theo từ sequence có code này
                # Sequence phải được định nghĩa trong XML data
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'demo.sequence.mail'
                ) or 'New'
        return super().create(vals_list)

    # ── message_post: ghi log thủ công vào chatter ───────────────
    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirmed'})

        # Ghi note vào chatter (không gửi email)
        self.message_post(
            body=_('Đã xác nhận bởi %s') % self.env.user.name,
            subtype_xmlid='mail.mt_note',  # mt_note = internal note
        )

    def action_done(self):
        self.ensure_one()
        self.write({'state': 'done'})

        # Gửi message (có thể notify followers)
        self.message_post(
            body=_('Hoàn thành! Số tiền: %s') % self.amount,
            subtype_xmlid='mail.mt_comment',  # mt_comment = gửi cho followers
        )
