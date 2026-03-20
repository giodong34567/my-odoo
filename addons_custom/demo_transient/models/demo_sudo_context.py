from odoo import api, fields, models


class DemoSudoContext(models.Model):
    """
    Demo: sudo(), with_context(), with_user(), @api.model

    Đây là những kỹ thuật cực kỳ hay dùng trong thực tế Odoo
    nhưng hay bị hiểu sai hoặc dùng sai.
    """
    _name = 'demo.sudo.context'
    _description = 'Demo sudo và context'

    name = fields.Char(string='Tên', required=True)
    note = fields.Text(string='Ghi chú')
    created_by = fields.Char(string='Tạo bởi', readonly=True)

    # ── @api.model ────────────────────────────────────────────────
    # Dùng khi method KHÔNG thao tác trên recordset cụ thể
    # (không có self là list records), thường là utility / factory method
    @api.model
    def get_greeting(self):
        """
        @api.model: self ở đây là model class, không phải recordset.
        Dùng cho các method không cần record cụ thể.
        """
        return f"Xin chào từ {self._name}, user: {self.env.user.name}"

    @api.model_create_multi
    def create(self, vals_list):
        """
        @api.model_create_multi: override create để tự điền created_by.
        Đây là cách chuẩn để override create trong Odoo 16+
        (thay thế @api.model + create(vals) cũ)
        """
        for vals in vals_list:
            vals['created_by'] = self.env.user.name
        return super().create(vals_list)

    # ── sudo() ────────────────────────────────────────────────────
    def action_demo_sudo(self):
        """
        sudo() => chạy với quyền superuser, bỏ qua record rules & ACL.

        Dùng khi:
        - Cần đọc/ghi record mà user hiện tại không có quyền
        - Tạo record hệ thống (log, notification...) trong background

        CẢNH BÁO: Đừng sudo() bừa bãi, dễ tạo lỗ hổng bảo mật.
        """
        self.ensure_one()

        # Không sudo: chỉ thấy record mà user có quyền
        visible_records = self.env['demo.employee'].search([])

        # Có sudo: thấy TẤT CẢ record, bỏ qua record rules
        all_records = self.env['demo.employee'].sudo().search([])

        # sudo với user cụ thể (Odoo 14+)
        # admin_env = self.env['demo.employee'].with_user(1).search([])

        self.note = (
            f"Không sudo: thấy {len(visible_records)} nhân viên\n"
            f"Có sudo:    thấy {len(all_records)} nhân viên"
        )

    # ── with_context() ────────────────────────────────────────────
    def action_demo_context(self):
        """
        with_context() => truyền thêm thông tin vào môi trường thực thi.

        Context là dict được truyền xuyên suốt call chain.
        Dùng để:
        - Tắt/bật behavior (vd: bỏ qua email khi import)
        - Truyền tham số giữa các method
        - Thay đổi ngôn ngữ, timezone tạm thời
        """
        self.ensure_one()

        # Đọc context hiện tại
        current_lang = self.env.context.get('lang', 'không có')

        # Tạo record với context tùy chỉnh
        # 'no_recompute': True => bỏ qua recompute (dùng khi import hàng loạt)
        new_rec = self.with_context(
            no_recompute=True,
            custom_flag='demo_value',
        ).create({'name': f'Tạo từ context demo - {self.name}'})

        # Kiểm tra context trong method được gọi
        flag = self.env.context.get('custom_flag', 'không có')

        self.note = (
            f"Lang hiện tại: {current_lang}\n"
            f"custom_flag:   {flag}\n"
            f"Record mới tạo: {new_rec.name} (id={new_rec.id})"
        )

    # ── with_user() ───────────────────────────────────────────────
    def action_demo_with_user(self):
        """
        with_user(user) => chạy với quyền của user khác.

        Khác sudo():
        - sudo()      => quyền superuser (bỏ qua tất cả)
        - with_user() => đúng quyền của user đó (vẫn bị record rules)

        Dùng khi cần kiểm tra "user X có thấy record này không?"
        """
        self.ensure_one()

        # Chạy với quyền của chính user hiện tại (ví dụ minh họa)
        current_user = self.env.user
        records_as_current = self.env['demo.employee'].with_user(current_user).search([])

        # Chạy với quyền admin (uid=1)
        records_as_admin = self.env['demo.employee'].with_user(1).search([])

        self.note = (
            f"Với user '{current_user.name}': thấy {len(records_as_current)} nhân viên\n"
            f"Với admin:                      thấy {len(records_as_admin)} nhân viên"
        )

    # ── env.ref() và ref() ────────────────────────────────────────
    @api.model
    def get_admin_group(self):
        """
        env.ref('xml_id') => lấy record theo XML ID.
        Cực kỳ hay dùng để lấy group, menu, action... trong code Python.
        """
        admin_group = self.env.ref('base.group_system')
        demo_group = self.env.ref('demo_transient.group_demo_admin', raise_if_not_found=False)
        return {
            'admin_group': admin_group.name,
            'demo_group': demo_group.name if demo_group else 'chưa cài',
        }
