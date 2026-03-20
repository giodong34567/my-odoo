from odoo import _, fields, models
import logging

_logger = logging.getLogger(__name__)


class DemoCron(models.Model):
    """
    Demo: ir.cron — lên lịch chạy tác vụ tự động (scheduled actions)
    Method được gọi bởi cron phải: không có tham số, dùng @api.model nếu cần
    """
    _name = 'demo.cron'
    _description = 'Demo Cron'

    name = fields.Char(required=True)
    last_run = fields.Datetime(string='Lần chạy cuối', readonly=True)
    run_count = fields.Integer(string='Số lần đã chạy', readonly=True)

    def action_cron_job(self):
        """
        Method này được ir.cron gọi định kỳ.
        Luôn dùng sudo() nếu cần truy cập nhiều record,
        vì cron chạy với user __system__ (uid=1).
        """
        records = self.sudo().search([])
        for rec in records:
            rec.write({
                'last_run': fields.Datetime.now(),
                'run_count': rec.run_count + 1,
            })
        _logger.info("Demo cron chạy xong: cập nhật %d records", len(records))
